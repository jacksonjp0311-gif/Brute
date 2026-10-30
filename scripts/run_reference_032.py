"""GS_ref audit for study-032 (BRUTE_PLAN_032 GS_ref; deviation #136; built from scripts/run_reference_031.py, frozen):
experiments/v0290_reference.py (SAT-free flip-budget reference) on arm S7 of every noisy_scale8 case of a sealed study
directory, 8 processes, a declared per-case wall cap (queries past it are 'not_reached'), then the 20-mutation test.
Writes <study>/REFERENCE_032.json (refuses overwrite). New file.
Pass: 0 mismatches, decided > 0 and mutations detected 20/20.
  PYTHONPATH=. python scripts/run_reference_032.py results/study-032/main [--case-cap 110] [--workers 8]"""
import argparse,copy,json,sys
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_032 import load,write_new,check,sha
from experiments import worlds_026 as W
from experiments.v0290_reference import audit_case,mutate,BUDGET
CASE_CAP=110.0;MUTATIONS=20;FAMILY='noisy_scale8';ARM='S7'


def _order(steps,k):
    o=[]
    for start in range(7):
        for i in range(start,steps,7):
            for b in range(k):o.append((i,b))
    return o


def _tr(case):w=W.world(case['seed'],case['family'][len('noisy_'):]);return W.trajectory(w,case['seed'],case['eps'])


def _audit(args):
    case,cap=args;tr=_tr(case);steps=len(case['arms'][ARM]['sup']);t=perf_counter()
    r=audit_case(case,tr['readings'],tr['actions'],ARM,BUDGET,perf_counter()+cap,_order(steps,case['k']))
    r['key']=f"{case['family']}/{case['seed']}/{case['eps']}";r['wall_informational']=perf_counter()-t;return r


def mutation_test(cases,reports,n=MUTATIONS):
    by={r['key']:c for r,c in zip(reports,cases)};pool=[(r['key'],x) for r in reports for x in r['decided_keys'] if x[2] is not None]
    out=[]
    if not pool:return {'mutations':0,'detected':0,'pass':False,'note':'no decided query'}
    import random
    rng=random.Random(290)
    for j in range(n):
        key,(i,b,sup)=rng.choice(pool);case=copy.deepcopy(by[key]);mut=mutate([[i,b,sup]],1,seed=290+j)[0][2]
        case['arms'][ARM]['sup'][i][b]=mut;tr=_tr(case)
        r=audit_case(case,tr['readings'],tr['actions'],ARM,BUDGET,None,[(i,b)])
        out.append({'key':key,'i':i,'b':b,'reference':sup,'mutated':mut,'detected':bool(r['mismatches'])})
    d=sum(x['detected'] for x in out);return {'mutations':n,'detected':d,'pass':d==n,'items':out}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('study');ap.add_argument('--case-cap',type=float,default=CASE_CAP)
    ap.add_argument('--workers',type=int,default=8);ap.add_argument('--family',default=FAMILY);a=ap.parse_args(argv)
    d=Path(a.study);res=load(d/'RESULTS.json');cases=[c for c in res['cases'] if c['family']==a.family]
    t=perf_counter()
    with ProcessPoolExecutor(a.workers) as ex:reports=list(ex.map(_audit,[(c,a.case_cap) for c in cases]))
    mt=mutation_test(cases,reports)
    tot={k:sum(r[k] for r in reports) for k in ('queries','exact','decided','undecided','not_reached','checked_codes','decided_possible_codes','decided_impossible_codes')}
    mism=[[r['key']]+m for r in reports for m in r['mismatches']]
    out={'schema':'brute.reference.v29_0','study_results_sha256':sha(d/'RESULTS.json'),'family':a.family,'arm_audited':ARM,'cases':len(cases),
         'node_budget':BUDGET,'case_cap_seconds':a.case_cap,**tot,'coverage_of_exact':(tot['decided']/tot['exact']) if tot['exact'] else 0.0,
         'mismatches':mism,'mismatch_count':len(mism),'mutation_test':mt,
         'per_case':[{k:v for k,v in r.items() if k!='decided_keys'} for r in reports],'elapsed_informational':perf_counter()-t}
    out['PASS']=out['mismatch_count']==0 and tot['decided']>0 and mt['pass']
    write_new(d/'REFERENCE_032.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','mutation_test','mismatches')},indent=1),'\nmutations',mt['detected'],'/',mt['mutations'])
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
