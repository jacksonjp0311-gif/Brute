"""g11 / GS_ref driver for study-014: experiments/v0120_reference.audit_case on every transfer case, then the mutation test
(BRUTE_PLAN_014 criteria.GS_ref_reference_audit, second_implementation.checkpoint).

Order: every case of --results (block order) is audited and appended to --checkpoint (fsync; a restart skips audited
cases); event audit_done; the mutation test (v0120_reference.mutate: 20 single-field errors in 20 distinct cases,
random.Random(20261026), kinds 6 bounded / 6 dlf / 4 stress / 2 rg / 2 dx) on the injected copies only; event
mutation; event done. Implementation reading (as study-013, disclosed): a case that was not injected is unchanged
(asserted), so its audit equals the recorded audit (Exact) and is not recomputed; flagged_not_injected is 0 by
construction. --summarize-only writes the report from the checkpoint (unreached cases are reported, not failed).
Labelled: second implementation by the same author, no brute import; not an independent or third-party audit.
"""
from __future__ import annotations
import argparse,hashlib,json,os,sys,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import v0120_reference as R
from experiments.brute_common import load,check
from experiments.brute_common_009 import repair_torn_tail

MUTATE=20


def ckey(c):return f"{c['family']}/{c['seed']}/{c['mask_rate']}"


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


def mutation(cases,plan,workers,audited,k=MUTATE):
    if len(cases)<k:return {'event':'mutation','skipped':f'{len(cases)} cases < {k} (smoke only)','passed':None}
    mc,inj=R.mutate(cases,k)
    for i,c in enumerate(cases):
        if i in inj:check(mc[i]!=c,'injection did not change the case')
        else:check(mc[i] is c,'uninjected case changed')
    kinds={}
    for i in sorted(inj):
        diff=sorted(x for x in ('bounded','transfer','stress','summary') if mc[i][x]!=cases[i][x]);kinds[ckey(cases[i])]=diff
    res={r['case']:r for r in pool_map([(ckey(mc[i]),mc[i],plan) for i in sorted(inj)],workers)}
    base_bad={ckey(cases[i]) for i in inj if not audited.get(ckey(cases[i]),{'ok':True})['ok']}
    det=[{'case':k_,'detected':not r['ok'],'first_difference':r['first_difference'],'changed_sections':kinds[k_]} for k_,r in sorted(res.items())]
    return {'event':'mutation','injected':len(inj),'distinct_cases':len({d['case'] for d in det}),
            'kinds':{x:R.KINDS.count(x) for x in sorted(set(R.KINDS))},'detected_injected':sum(d['detected'] for d in det),
            'injected_on_already_mismatching_case':len(base_bad),'flagged_not_injected':0,
            'flagged_not_injected_basis':'Exact: uninjected cases asserted unchanged','rng':'random.Random(20261026)','details':det,
            'passed':len(inj)==k and all(d['detected'] for d in det) and len({d['case'] for d in det})==k}


def summarize(cases,plan,audited,events,results,src):
    keys=[ckey(c) for c in cases];got=[audited[k] for k in keys if k in audited];bad=[g for g in got if not g['ok']]
    rep={'schema':'brute.second-implementation-014.v1','study':plan['study'],
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit',
         'scope':'bounded supports (exhaustive, n = 2..5 on SP8, dx_bounds on LX); RG2-5, DLF, DLF0, AT, LX, DX (all fields); summary; stress counts',
         'source_sha256':src,'results_file':str(results),'results_sha256':hashlib.sha256(Path(results).read_bytes()).hexdigest(),
         'cases_expected':len(keys),'cases_audited':len(got),'cases_not_reached':len(keys)-len(got),'mismatching_cases':len(bad),
         'mismatches':bad,'events':{k:{x:y for x,y in v.items() if x!='details'} for k,v in events.items()},
         'audit_wall_informational':round(sum(g['wall_informational'] for g in got),1)}
    if 'mutation' in events:rep['mutation_test']=events['mutation']
    rep['passed']=rep['cases_not_reached']==0 and not bad and rep.get('mutation_test',{}).get('passed') is True
    return rep


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--results',required=True);ap.add_argument('--checkpoint',required=True)
    ap.add_argument('--output',required=True);ap.add_argument('--workers',type=int,default=2)
    ap.add_argument('--mutate',type=int,default=MUTATE);ap.add_argument('--summarize-only',action='store_true')
    a=ap.parse_args(argv)
    def log(m):print(f"[{time.strftime('%H:%M:%S')}] {m}",flush=True)
    plan=load(R.PLAN);res=load(a.results);cases=res['cases'];check(res['plan']==plan,'results plan differs from BRUTE_PLAN_014')
    src=hashlib.sha256((ROOT/'experiments/v0120_reference.py').read_bytes()).hexdigest()
    Path(a.checkpoint).parent.mkdir(parents=True,exist_ok=True)
    if Path(a.checkpoint).exists():repair_torn_tail(a.checkpoint)
    audited,events=read_ck(a.checkpoint)
    if not a.summarize_only:
        with open(a.checkpoint,'a') as fh:
            if 'start' not in events:events['start']={'event':'start','t':time.time()};_append(fh,events['start'])
            jobs=[(ckey(c),c,plan) for c in cases if ckey(c) not in audited];log(f'{len(cases)-len(jobs)} cached, {len(jobs)} to audit')
            for n,r in enumerate(pool_map(jobs,a.workers)):
                _append(fh,r);audited[r['case']]=r
                if (n+1)%12==0 or n+1==len(jobs):log(f'audited {n+1}/{len(jobs)} (mismatching so far {sum(not x["ok"] for x in audited.values())})')
            if 'audit_done' not in events:events['audit_done']={'event':'audit_done','t':time.time()};_append(fh,events['audit_done'])
            if a.mutate and 'mutation' not in events:
                events['mutation']=mutation(cases,plan,a.workers,audited,a.mutate);_append(fh,events['mutation'])
                log(f"mutation {events['mutation']['detected_injected']}/{events['mutation']['injected']} passed={events['mutation']['passed']}")
            if 'done' not in events:events['done']={'event':'done','t':time.time()};_append(fh,events['done'])
    rep=summarize(cases,plan,audited,events,a.results,src)
    out=Path(a.output);out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    log(json.dumps({k:v for k,v in rep.items() if k not in ('mismatches','mutation_test','events')}))
    log(json.dumps({k:v for k,v in rep.get('mutation_test',{}).items() if k!='details'}))


if __name__=='__main__':main()
