"""tau7 calibration for study-007 (BRUTE_PLAN_007 calibration_ranges_tau7).

BP5 (BreadthBruteLearner, passive) with the alarm disabled (tau=None) on every calibration case (calibration_ranges_tau7
x 3 mask rates = 450 cases, in-family breadth families only); tau7 = max residual_after over every step of every case,
rounded to 12 decimals. The full BP5 traces are kept (CALIBRATION_007_TRACES.json, audited by the second implementation).
Resumable through <output dir>/CALIBRATION_CHECKPOINT.jsonl. G12: a second run must reproduce CALIBRATION_007.json
byte-for-byte."""
import argparse
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from brute.evaluation import no_time
from experiments.brute_study_007 import run_case_breadth
from experiments.brute_common_007 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,Checkpoint


def _cal(args):
    seed,fam,rate,plan=args
    c=run_case_breadth(seed,fam,rate,plan,None,('BP5',),calibration=True,block='calibration')
    check(c['arms']['BP5']['diagnostics']['first_alarm_step'] is None,'alarm with tau=None')
    return f'{fam}/{seed}/{rate}',no_time(c)


def calibrate(output,workers=6,smoke=False,limit=None):
    output=Path(output);plan=load(PLAN)
    if not smoke:check_freeze()
    R=plan['calibration_ranges_tau7'];check(set(R)==set(plan['in_family_breadth']),'calibration families differ from plan')
    jobs=[(seed,fam,rate,plan) for fam,(lo,hi) in R.items() for seed in range(lo,hi+1) for rate in plan['mask_rates']]
    if limit:jobs=jobs[:limit]
    traces=output.parent/(output.stem+'_TRACES.json');check(not output.exists() and not traces.exists(),'refusing overwrite')
    ck=Checkpoint(output.parent/(output.stem+'_CHECKPOINT.jsonl'))
    todo=[j for j in jobs if f'{j[1]}/{j[0]}/{j[2]}' not in ck.done]
    with ProcessPoolExecutor(workers) as ex:
        for n,fu in enumerate(as_completed([ex.submit(_cal,j) for j in todo])):
            k,c=fu.result();ck.add(k,c);print(f'cal {n+1}/{len(todo)} {k}',flush=True)
    cases=[ck.done[f'{fam}/{seed}/{rate}'] for seed,fam,rate,_ in jobs]
    best=None;arg=None;per={}
    for c in cases:
        for r in c['arms']['BP5']['trace']:
            v=r['residual_after']
            if v is None:continue
            if best is None or v>best:best=v;arg={'family':c['family'],'seed':c['seed'],'mask_rate':c['mask_rate'],'step':r['step']}
            if per.get(c['family']) is None or v>per[c['family']]:per[c['family']]=v
    out={'schema':'brute.calibration.v7','study':plan['study'],'window_W':plan['window_W'],'arm':'BP5',
         'tau7':round(best,12),'tau7_unrounded':best,'argmax':arg,'per_family_max_R':{k:round(v,12) for k,v in sorted(per.items())},
         'calibration_cases':len(jobs),'out_of_family_data_used':False,'plan_sha256':sha(PLAN),
         'freeze_sha256':None if smoke else sha(FREEZE)}
    write_new(traces,{'schema':'brute.calibration_traces.v7','cases':cases});write_new(output,out);return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(STUDY_DIR/'CALIBRATION_007.json'))
    ap.add_argument('--workers',type=int,default=6);ap.add_argument('--smoke',action='store_true');ap.add_argument('--limit',type=int)
    a=ap.parse_args();out=calibrate(a.output,a.workers,a.smoke,a.limit);print({k:v for k,v in out.items() if k!='per_family_max_R'},out['per_family_max_R'])
