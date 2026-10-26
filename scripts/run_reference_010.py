"""G11 driver for study-010 (BRUTE_PLAN_010 samples.g11_*, criteria.G11_second_implementation).

One stream per block (g11_2x2: arms J8, SP8, SC7; g11_breadth: arms BSC7, BSP8). Order: every trace of the mandatory
sample (scripts/check_seeds_010.g11_mandatory, all masks) first, then (2x2 only) the mutation test, then the rest of the
block best effort. Every audited (case, arm) trace is appended to --checkpoint (fsync), so a budget stop leaves partial
evidence; a restart skips audited traces. --summarize-only writes the report from the checkpoint (unreached traces are
reported, not failed).

Mutation test (2x2 stream): experiments/v080_reference.mutate(mandatory cases, 20, random.Random(20261026),
j8=4, sp8=4) and an audit of the 20 injected traces only. Implementation reading (disclosed): a trace that was not
injected is byte-identical to the original (asserted), so its audit result equals the unmutated audit result (Exact) and
is not recomputed; flagged_not_injected is therefore 0 by construction and the original mismatches are carried over.
"""
from __future__ import annotations
import argparse,hashlib,json,os,time,copy
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from experiments import v080_reference as R
from experiments.brute_common import load,check
from experiments.brute_common_009 import repair_torn_tail
from scripts.check_seeds_010 import g11_mandatory

ROOT=Path(__file__).resolve().parents[1]
ARMS={'2x2':('J8','SP8','SC7'),'breadth':('BSC7','BSP8')}
MUTATE=20


def ckey(c):return f"{c['family']}/{c['seed']}/{c['mask_rate']}"


def mandatory_keys(plan,block):
    M=g11_mandatory(plan)[block];return {f'{f}/{s}/{m}' for f,ss in M.items() for s in ss for m in plan['mask_rates']}


def read_ck(path):
    traces={};events={}
    if Path(path).exists():
        for line in Path(path).read_text().split('\n'):
            if not line.strip():continue
            r=json.loads(line)
            if 'event' in r:events[r['event']]=r
            else:traces[(r['case'],r['arm'])]=r
    return traces,events


def _audit(x):
    key,c,arms,view,tau6,tau7=x;out=[]
    for a in arms:
        if a not in c['arms']:continue
        t0=time.time();ok,msg,t=R.audit_trace(c,a,view,tau6,tau7)
        out.append({'case':key,'arm':a,'ok':ok,'first_difference':msg,'counts':t if a in R.ARMS_BREADTH else None,
                    'steps':len(c['arms'][a]['trace']),'wall_informational':round(time.time()-t0,3)})
    return out


def _append(fh,rec):fh.write(json.dumps(rec,sort_keys=True)+'\n');fh.flush();os.fsync(fh.fileno())


def audit_many(cases,arms,view,tau6,tau7,workers,fh,done,log):
    jobs=[(ckey(c),c,tuple(a for a in arms if (ckey(c),a) not in done),view,tau6,tau7) for c in cases]
    jobs=[j for j in jobs if j[2]]
    if workers<=1:it=(_audit(j) for j in jobs)
    else:
        ex=ProcessPoolExecutor(workers);futs=[ex.submit(_audit,j) for j in jobs];it=(f.result() for f in as_completed(futs))
    n=0
    for out in it:
        for r in out:_append(fh,r);done[(r['case'],r['arm'])]=r
        n+=1
        if n%10==0 or n==len(jobs):log(f'audited {n}/{len(jobs)} cases')
    if workers>1:ex.shutdown()


def mutation(mand,arms,view,tau6,tau7,base,k=MUTATE):
    mc,inj=R.mutate(mand,k,arms=arms)
    check(len(inj)==k,'mutation count')
    for i,c in enumerate(mand):
        for a in arms:
            if a in c['arms'] and (i,a) not in inj:check(mc[i]['arms'][a]==c['arms'][a],'uninjected trace changed')
            if (i,a) in inj:check(mc[i]['arms'][a]!=c['arms'][a],'injection did not change the trace')
    det=[]
    for i,a in sorted(inj):
        ok,msg,_=R.audit_trace(mc[i],a,view,tau6,tau7);det.append({'case':ckey(mc[i]),'arm':a,'detected':not ok,'first_difference':msg})
    base_bad={(ckey(mand[i]),a) for i,a in inj if not base[(ckey(mand[i]),a)]['ok']}
    return {'event':'mutation','injected':len(inj),'injected_j8':sum(a=='J8' for _,a in inj),'injected_sp8':sum(a=='SP8' for _,a in inj),
            'detected_injected':sum(d['detected'] for d in det),'injected_on_already_mismatching_trace':len(base_bad),
            'flagged_not_injected':0,'flagged_not_injected_basis':'Exact: uninjected traces asserted byte-identical',
            'rng':'random.Random(20261026)','details':det,
            'passed':all(d['detected'] for d in det) and len(inj)==k and sum(a=='J8' for _,a in inj)>=4 and sum(a=='SP8' for _,a in inj)>=4}


def summarize(block,cases,plan,traces,events,results,src,M):
    arms=ARMS[block];exp={'mandatory':[],'rest':[]}
    for c in cases:
        for a in arms:
            if a in c['arms']:exp['mandatory' if ckey(c) in M else 'rest'].append((ckey(c),a))
    rep={'schema':'brute.second-implementation-010.v1','study':plan['study'],'block':block,'arms':list(arms),
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit',
         'source_sha256':src,'results_file':str(results),'results_sha256':hashlib.sha256(Path(results).read_bytes()).hexdigest(),
         'tau6':plan['tau6']['value'],'tau7':plan['tau7']['value']}
    for part,keys in exp.items():
        got=[traces[k] for k in keys if k in traces];bad=[g for g in got if not g['ok']]
        rep[part]={'traces_expected':len(keys),'traces_audited':len(got),'traces_not_reached':len(keys)-len(got),
                   'mismatching_traces':len(bad),'mismatches':bad,'per_arm':{a:{'expected':sum(k[1]==a for k in keys),
                   'audited':sum(g['arm']==a for g in got),'mismatching':sum(g['arm']==a and not g['ok'] for g in bad)} for a in arms}}
    rep['mandatory_complete']=rep['mandatory']['traces_not_reached']==0
    rep['mandatory_samples_present']=sorted({k[0] for k in exp['mandatory']})==sorted(M)
    rep['events']={k:{x:y for x,y in v.items() if x!='details'} for k,v in events.items()}
    if 'mutation' in events:rep['mutation_test']=events['mutation']
    cov={}
    for (ck,a),g in traces.items():
        if g['counts']:
            f=ck.split('/')[0];d=cov.setdefault(f'{f}/{a}',{'steps':0,'steps_checked':0,'traces_budget_stopped':0})
            d['steps']+=g['counts']['steps'];d['steps_checked']+=g['counts']['steps_checked'];d['traces_budget_stopped']+=g['counts']['budget_stop'] is not None
    rep['breadth_steps_checked']=cov
    rep['rest_mismatch_fails_g11']=True
    return rep


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=ARMS,required=True);ap.add_argument('--results',required=True)
    ap.add_argument('--checkpoint',required=True);ap.add_argument('--output',required=True);ap.add_argument('--workers',type=int,default=2)
    ap.add_argument('--mutate',type=int,default=MUTATE);ap.add_argument('--summarize-only',action='store_true')
    ap.add_argument('--no-rest',action='store_true',help='smoke only: stop after the mandatory sample')
    ap.add_argument('--smoke-all-mandatory',action='store_true',help='smoke only (seeds 3190001-3190030): treat every case as mandatory')
    a=ap.parse_args(argv);out=Path(a.output)
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    plan=load(R.PLAN);view=R.plan_view(plan);tau6=plan['tau6']['value'];tau7=plan['tau7']['value'];arms=ARMS[a.block]
    src=hashlib.sha256((ROOT/'experiments/v080_reference.py').read_bytes()).hexdigest()
    def log(m):print(f"[{time.strftime('%H:%M:%S')}] g11_{a.block}: {m}",flush=True)
    cases=json.loads(Path(a.results).read_text())['cases'];M=mandatory_keys(plan,a.block)
    if a.smoke_all_mandatory:
        lo,hi=plan['smoke_seeds']['range'];check(all(lo<=c['seed']<=hi for c in cases),'--smoke-all-mandatory on non-smoke seeds');M={ckey(c) for c in cases}
    mand=[c for c in cases if ckey(c) in M];rest=[c for c in cases if ckey(c) not in M]
    Path(a.checkpoint).parent.mkdir(parents=True,exist_ok=True);repair_torn_tail(a.checkpoint)
    traces,events=read_ck(a.checkpoint)
    if not a.summarize_only:
        with open(a.checkpoint,'a') as fh:
            if 'start' not in events:events['start']={'event':'start','t':time.time()};_append(fh,events['start'])
            log(f'mandatory sample: {len(mand)} cases (expected {len(M)}), rest {len(rest)} cases')
            audit_many(mand,arms,view,tau6,tau7,a.workers,fh,traces,log)
            if 'mandatory_done' not in events:
                events['mandatory_done']={'event':'mandatory_done','t':time.time(),'wall_since_start':round(time.time()-events['start']['t'],1)}
                _append(fh,events['mandatory_done']);log(f"mandatory done ({events['mandatory_done']['wall_since_start']} s since first start)")
            if a.block=='2x2' and a.mutate and 'mutation' not in events:
                events['mutation']=mutation(mand,arms,view,tau6,tau7,traces,a.mutate);_append(fh,events['mutation'])
                log(f"mutation {events['mutation']['detected_injected']}/{events['mutation']['injected']} passed={events['mutation']['passed']}")
            if not a.no_rest:audit_many(rest,arms,view,tau6,tau7,a.workers,fh,traces,log)
    rep=summarize(a.block,cases,plan,traces,events,a.results,src,M)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    log(json.dumps({'mandatory':{k:v for k,v in rep['mandatory'].items() if k!='mismatches'},'rest_audited':rep['rest']['traces_audited'],
                    'mutation':{k:v for k,v in rep.get('mutation_test',{}).items() if k!='details'}}))


if __name__=='__main__':main()
