"""g11 / GS_ref6 driver for study-018: experiments/v0160_reference.audit_case on every transfer-stream case (360 main + 120
stress; GS_ref6 scores the eps 0.02 and eps 0 main cases, the rest is reported), then the mutation test on the main cases
(v0160_reference.mutate: 20 single-field errors in 20 distinct cases, random.Random(20261029), KINDS).

Same method as scripts/run_reference_017.py (checkpoint with fsync, restart skips audited cases, events start /
audit_done / mutation / done, --summarize-only writes the report from the checkpoint; unreached cases are reported, not
failed; uninjected cases are asserted unchanged, so flagged_not_injected is 0 by construction). New (plan
stop_rule.g11_rate_projection (5)): --progress PATH is rewritten every 60 s with cases done, mean audit cost, ETA and
whether the ETA is past --budget (an early warning only; nothing changes).
Labelled: second implementation by the same author, no brute import; not an independent or third-party audit.
"""
from __future__ import annotations
import argparse,hashlib,json,os,sys,threading,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import v0160_reference as R
from experiments.brute_common import load,check
from experiments.brute_common_009 import repair_torn_tail

MUTATE=20
PROGRESS_EVERY=60


def ckey(c):return f"{c['family']}/{c['seed']}/{c['eps']}"


def gated(c):return c.get('block')!='stress' and c['eps'] in (0.0,0.02)


def read_ck(path):
    cases={};events={}
    if Path(path).exists():
        for line in Path(path).read_text().split('\n'):
            if not line.strip():continue
            r=json.loads(line)
            if 'event' in r:events[r['event']]=r
            else:cases[r['case']]=r
    return cases,events


def _append(fh,rec):fh.write(json.dumps(rec,sort_keys=True)+'\n');fh.flush();os.fsync(fh.fileno())


def _audit(x):
    key,c,plan=x;t0=time.time();ok,msg=R.audit_case(c,plan)
    return {'case':key,'ok':ok,'first_difference':msg,'wall_informational':round(time.time()-t0,3)}


def pool_map(jobs,workers):
    if workers<=1:
        for j in jobs:yield _audit(j)
        return
    with ProcessPoolExecutor(workers) as ex:
        for f in as_completed([ex.submit(_audit,j) for j in jobs]):yield f.result()


class Progress:
    def __init__(self,path,total,budget,workers):
        self.path=Path(path) if path else None;self.total=total;self.budget=budget;self.workers=workers
        self.t0=time.time();self.done=0;self.cost=0.0;self.stop=threading.Event();self.lock=threading.Lock()
    def add(self,r):
        with self.lock:self.done+=1;self.cost+=r['wall_informational']
    def write(self):
        if not self.path:return
        with self.lock:
            el=time.time()-self.t0;rate=self.done/el if el>0 and self.done else None
            eta=(self.total-self.done)/rate if rate else None
            rep={'written_at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'elapsed_s':round(el,1),'cases_done':self.done,'cases_total':self.total,
                 'mean_audit_cost_s':round(self.cost/self.done,3) if self.done else None,'workers':self.workers,
                 'eta_s':round(eta,1) if eta is not None else None,'budget_s':self.budget,
                 'eta_past_budget_warning':None if eta is None or self.budget is None else el+eta>self.budget,
                 'note':'early warning only (plan stop_rule.g11_rate_projection (5)): no budget, sample or worker change follows'}
        tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n');tmp.replace(self.path)
    def loop(self):
        while not self.stop.wait(PROGRESS_EVERY):self.write()
    def __enter__(self):
        self.write();self.th=threading.Thread(target=self.loop,daemon=True);self.th.start();return self
    def __exit__(self,*a):self.stop.set();self.write()


def mutation(cases,plan,workers,audited,k=MUTATE):
    if len(cases)<k:return {'event':'mutation','skipped':f'{len(cases)} cases < {k} (smoke only)','passed':None}
    mc,inj=R.mutate(cases,k)
    for i,c in enumerate(cases):
        if i in inj:check(mc[i]!=c,'injection did not change the case')
        else:check(mc[i] is c,'uninjected case changed')
    kinds={}
    for i in sorted(inj):
        diff=sorted(x for x in mc[i] if mc[i].get(x)!=cases[i].get(x));kinds[ckey(cases[i])]=diff
    res={r['case']:r for r in pool_map([(ckey(mc[i]),mc[i],plan) for i in sorted(inj)],workers)}
    base_bad={ckey(cases[i]) for i in inj if not audited.get(ckey(cases[i]),{'ok':True})['ok']}
    det=[{'case':k_,'detected':not r['ok'],'first_difference':r['first_difference'],'changed_sections':kinds[k_]} for k_,r in sorted(res.items())]
    return {'event':'mutation','injected':len(inj),'distinct_cases':len({d['case'] for d in det}),
            'kinds':{x:R.KINDS.count(x) for x in sorted(set(R.KINDS))},'detected_injected':sum(d['detected'] for d in det),
            'injected_on_already_mismatching_case':len(base_bad),'flagged_not_injected':0,
            'flagged_not_injected_basis':'Exact: uninjected cases asserted unchanged','rng':'random.Random(20261029)','details':det,
            'passed':len(inj)==k and all(d['detected'] for d in det) and len({d['case'] for d in det})==k}


def summarize(cases,plan,audited,events,results,src):
    keys=[ckey(c) for c in cases];got=[audited[k] for k in keys if k in audited];bad=[g for g in got if not g['ok']]
    gk={ckey(c) for c in cases if gated(c)};ggot=[audited[k] for k in gk if k in audited]
    rep={'schema':'brute.second-implementation-018.v1','study':plan['study'],
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit',
         'scope':'RGN4 / RGN4_0 / RGN4_or supports (exhaustive <= 4-state Moore machines, per-state mismatch costs), RegionSpace(4) supports at m = 0, B / m / realized flips, RG4 and RGN certificates, wrong flags, counts, summary',
         'source_sha256':src,'results_file':str(results),'results_sha256':hashlib.sha256(Path(results).read_bytes()).hexdigest(),
         'cases_expected':len(keys),'cases_audited':len(got),'cases_not_reached':len(keys)-len(got),'mismatching_cases':len(bad),
         'gated_cases_expected':len(gk),'gated_cases_audited':len(ggot),'gated_mismatching_cases':sum(not g['ok'] for g in ggot),
         'mismatches':bad,'events':{k:{x:y for x,y in v.items() if x!='details'} for k,v in events.items()},
         'audit_wall_informational':round(sum(g['wall_informational'] for g in got),1)}
    if 'mutation' in events:rep['mutation_test']=events['mutation']
    rep['passed']=rep['gated_cases_audited']==len(gk) and rep['gated_mismatching_cases']==0 and rep.get('mutation_test',{}).get('passed') is True
    return rep


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--results',required=True);ap.add_argument('--checkpoint',required=True)
    ap.add_argument('--output',required=True);ap.add_argument('--workers',type=int,default=2);ap.add_argument('--progress')
    ap.add_argument('--budget',type=float);ap.add_argument('--mutate',type=int,default=MUTATE);ap.add_argument('--summarize-only',action='store_true')
    a=ap.parse_args(argv)
    def log(m):print(f"[{time.strftime('%H:%M:%S')}] {m}",flush=True)
    plan=load(R.PLAN);res=load(a.results);cases=res['cases'];check(res['plan']==plan,'results plan differs from BRUTE_PLAN_018')
    src=hashlib.sha256((ROOT/'experiments/v0160_reference.py').read_bytes()).hexdigest()
    Path(a.checkpoint).parent.mkdir(parents=True,exist_ok=True)
    if Path(a.checkpoint).exists():repair_torn_tail(a.checkpoint)
    audited,events=read_ck(a.checkpoint)
    if not a.summarize_only:
        jobs=[(ckey(c),c,plan) for c in cases if ckey(c) not in audited];log(f'{len(cases)-len(jobs)} cached, {len(jobs)} to audit')
        with open(a.checkpoint,'a') as fh,Progress(a.progress,len(jobs),a.budget,a.workers) as P:
            if 'start' not in events:events['start']={'event':'start','t':time.time()};_append(fh,events['start'])
            for n,r in enumerate(pool_map(jobs,a.workers)):
                _append(fh,r);audited[r['case']]=r;P.add(r)
                if (n+1)%24==0 or n+1==len(jobs):log(f'audited {n+1}/{len(jobs)} (mismatching so far {sum(not x["ok"] for x in audited.values())})')
            if 'audit_done' not in events:events['audit_done']={'event':'audit_done','t':time.time()};_append(fh,events['audit_done'])
            main_cases=[c for c in cases if c.get('block')!='stress']
            if a.mutate and 'mutation' not in events:
                events['mutation']=mutation(main_cases,plan,a.workers,audited,a.mutate);_append(fh,events['mutation'])
                m=events['mutation'];log(f"mutation {m.get('detected_injected')}/{m.get('injected')} passed={m['passed']} {m.get('skipped','')}")
            if 'done' not in events:events['done']={'event':'done','t':time.time()};_append(fh,events['done'])
    rep=summarize(cases,plan,audited,events,a.results,src)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    log(json.dumps({k:v for k,v in rep.items() if k not in ('mismatches','mutation_test','events')}))
    log(json.dumps({k:v for k,v in rep.get('mutation_test',{}).items() if k!='details'}))


if __name__=='__main__':main()
