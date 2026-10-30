"""GS_ref14 audit for study-031 (deviation #123 item 11, unchanged; #126; #128; #130; #132; #134: arm S6 is audited by copying it into the S2 slot; built from scripts/run_reference_030.py, frozen): experiments/v0230_reference.py on every scale8 case of a sealed
study directory, 8 processes, a declared per-case wall cap (queries past it are 'not_reached', counted against coverage),
then the 20-mutation test. Writes <study>/REFERENCE_031.json (refuses overwrite). New file.
Pass: 0 mismatches, decided > 0 and mutations detected 20/20.
  PYTHONPATH=. python scripts/run_reference_031.py results/study-031/main [--case-cap 110] [--workers 8]"""
import argparse,copy,json,sys
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_031 import load,write_new,check,sha
from experiments import worlds_026 as W
from experiments.v0230_reference import audit_case,mutate,BUDGET
CASE_CAP=110.0;MUTATIONS=20;FAMILY='scale8'


def _order(steps,k,seed):
    """Deterministic interleaved visit order (stride 7 over steps) so a capped audit still spans the whole horizon."""
    o=[];seen=set()
    for start in range(7):
        for i in range(start,steps,7):
            for b in range(k):o.append((i,b))
    return o


def _s6_as_s2(case):
    """Deviation #134 (as #128, #130, #132): audit S6 with the frozen S2 reference by placing the S6 record in the S2 slot of a copy."""
    c=dict(case);c['arms']={'S2':case['arms']['S6']};return c


def _audit(args):
    case,cap=args;case=_s6_as_s2(case);w=W.world(case['seed'],case['family']);tr=W.trajectory(w,case['seed'],case['eps'])
    steps=len(case['arms']['S2']['sup']);t=perf_counter()
    r=audit_case(case,tr['readings'],tr['actions'],BUDGET,perf_counter()+cap,_order(steps,case['k'],case['seed']))
    r['key']=f"{case['family']}/{case['seed']}/{case['eps']}";r['wall_informational']=perf_counter()-t;return r


def mutation_test(cases,reports,n=MUTATIONS):
    """Mutate n decided S2 answers (seeded) in copies of the case records and re-audit just those queries."""
    by={r['key']:_s6_as_s2(c) for r,c in zip(reports,cases)};pool=[(r['key'],x) for r in reports for x in r['decided_keys'] if x[2] is not None]
    out=[]
    if not pool:return {'mutations':0,'detected':0,'pass':False,'note':'no decided query'}
    import random
    rng=random.Random(260)
    for j in range(n):
        key,(i,b,sup)=rng.choice(pool);case=copy.deepcopy(by[key]);mut=mutate([[i,b,sup]],1,seed=260+j)[0][2]
        case['arms']['S2']['sup'][i][b]=mut;w=W.world(case['seed'],case['family']);tr=W.trajectory(w,case['seed'],case['eps'])
        r=audit_case(case,tr['readings'],tr['actions'],BUDGET,None,[(i,b)])
        out.append({'key':key,'i':i,'b':b,'reference':sup,'mutated':mut,'detected':bool(r['mismatches'])})
    d=sum(x['detected'] for x in out);return {'mutations':n,'detected':d,'pass':d==n,'items':out}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('study');ap.add_argument('--case-cap',type=float,default=CASE_CAP)
    ap.add_argument('--workers',type=int,default=8);a=ap.parse_args(argv)
    d=Path(a.study);res=load(d/'RESULTS.json');cases=[c for c in res['cases'] if c['family']==FAMILY]
    t=perf_counter()
    with ProcessPoolExecutor(a.workers) as ex:reports=list(ex.map(_audit,[(c,a.case_cap) for c in cases]))
    mt=mutation_test(cases,reports)
    tot={k:sum(r[k] for r in reports) for k in ('queries','exact_s2','decided','undecided','not_reached','decided_possible_codes','decided_impossible_codes')}
    mism=[[r['key']]+m for r in reports for m in r['mismatches']]
    out={'schema':'brute.reference.v28_0','study_results_sha256':sha(d/'RESULTS.json'),'family':FAMILY,'arm_audited':'S6','cases':len(cases),
         'node_budget':BUDGET,'case_cap_seconds':a.case_cap,**tot,'coverage_of_exact':(tot['decided']/tot['exact_s2']) if tot['exact_s2'] else 0.0,
         'mismatches':mism,'mismatch_count':len(mism),'mutation_test':mt,
         'per_case':[{k:v for k,v in r.items() if k!='decided_keys'} for r in reports],'elapsed_informational':perf_counter()-t}
    out['PASS']=out['mismatch_count']==0 and tot['decided']>0 and mt['pass']
    write_new(d/'REFERENCE_031.json',out)
    print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','mutation_test')},indent=1),'\nmutations',mt['detected'],'/',mt['mutations'])
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
