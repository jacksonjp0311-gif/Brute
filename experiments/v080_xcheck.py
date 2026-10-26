"""GX2 driver for study-010 (BRUTE_PLAN_010 xcheck_backend): the frozen experiments/v070_xcheck.py with
--plan experiments/BRUTE_PLAN_010.json.

  symmetric pass: arms B5, BSC7 on the full breadth results (symmetry=True); exactly v070_xcheck.main.
  spot pass (--truncate N): --no-symmetry on SPOT_SAMPLE_010 (B5); every trace is cut to steps 1..N and audited
      with a plan copy whose actions_per_case_breadth = N. A truncated trace is a prefix of the recorded trace
      (Exact: every per-step field depends only on steps <= its own). The end-of-trace fields that v060/v070 compare
      are restricted to the same prefix (implementation reading, disclosed): issued -> entries with step <= N;
      retractions -> kept iff the recorded family contradiction step is <= N; diagnostics first_alarm_step /
      alarm_steps / resume_steps / drift_events -> entries <= N; certificates_issued / certificates_retracted
      recounted. The truncated results file is written next to the checkpoint and never replaces the sealed one.
"""
import argparse,copy,gzip,json,sys
from pathlib import Path
import experiments.v070_xcheck as X
from experiments.brute_common import load,check

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_010.json'


def truncate_arm(A,n):
    A=copy.deepcopy(A);A['trace']=A['trace'][:n];d=A['diagnostics']
    A['issued']=[x for x in A['issued'] if x[0]<=n]
    cs=d.get('contradiction_step')
    if cs is None:
        cs=next((r['step'] for r in A['trace'] if r['family_status_after']=='grammar_contradicted'),None) if A['retractions'] else None
    if cs is None or cs>n:A['retractions']=[]
    d['first_alarm_step']=d['first_alarm_step'] if d.get('first_alarm_step') is not None and d['first_alarm_step']<=n else None
    for f in ('alarm_steps','resume_steps','drift_events'):
        if f in d:d[f]=[s for s in d[f] if s<=n]
    d['certificates_issued']=len(A['issued']);d['certificates_retracted']=len(A['retractions'])
    return A


def truncate_cases(cases,n,arms):
    out=[]
    for c in cases:
        c=dict(c)
        if 'k' in c:c['arms']={a:truncate_arm(v,n) if a in arms else v for a,v in c['arms'].items()};c['steps']=n
        out.append(c)
    return out


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    ap=argparse.ArgumentParser(add_help=False);ap.add_argument('--truncate',type=int);ap.add_argument('--results')
    ap.add_argument('--checkpoint');ap.add_argument('--arms',default='B5,BSC7');ap.add_argument('--plan',default=str(PLAN))
    a,_=ap.parse_known_args(argv)
    check(Path(a.plan).resolve()==PLAN.resolve(),'study-010 xcheck runs with BRUTE_PLAN_010 only')
    rest=[x for x in argv if not x.startswith('--truncate')]
    if a.truncate:
        i=argv.index('--truncate');rest=argv[:i]+argv[i+2:]
        plan=load(PLAN);check(a.truncate<=plan['actions_per_case_breadth'],'truncate beyond trace length')
        pc=dict(plan);pc['actions_per_case_breadth']=a.truncate
        base=Path(a.checkpoint).with_suffix('')
        tp=Path(str(base)+f'_plan_trunc{a.truncate}.json');tr=Path(str(base)+f'_results_trunc{a.truncate}.json.gz')
        if not tr.exists():
            cases=X.load_cases(a.results);arms=tuple(a.arms.split(','))
            with gzip.open(tr,'wt') as f:json.dump({'cases':truncate_cases(cases,a.truncate,arms)},f)
        tp.write_text(json.dumps(pc,indent=1,sort_keys=True)+'\n')
        rest=_set(_set(rest,'--plan',str(tp)),'--results',str(tr))
    else:
        rest=_set(rest,'--plan',a.plan)
        if '--arms' not in rest:rest+=['--arms','B5,BSC7']
    sys.argv=['v070_xcheck']+rest;X.main()


def _set(args,flag,val):
    args=list(args)
    if flag in args:args[args.index(flag)+1]=val
    else:args+=[flag,val]
    return args


if __name__=='__main__':main()
