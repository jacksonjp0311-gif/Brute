"""G13: tau must reproduce byte-for-byte from the v0.2.0 learner on the passive sequence (P) and from v0.1.1 (C).

Same rule as study-002/003: alarm disabled, tau = max windowed surprise over every step of every in-family
calibration case (study-001 heldout seeds of the 5 in-family families, 3 mask rates).
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
from experiments.brute_common_004 import PLAN,FREEZE,STUDY_DIR,CALIBRATION_002,load,sha,write_new,check_freeze,check
from experiments.brute_calibrate_003 import CAL_RANGES
from experiments.brute_study_004 import _trajectory


def _cal(args):
    seed,fam,rate,plan=args
    _,_,o=_trajectory('P',seed,fam,rate,plan,None,lambda:None)
    return fam,seed,rate,[(r['step'],r['residual_after']) for r in o['trace']],[(r['step'],r['residual_after']) for r in o['control_trace']]


def calibrate_check(workers=4):
    plan=load(PLAN);check_freeze();ref=load(CALIBRATION_002)
    check(set(CAL_RANGES)==set(plan['in_family']),'calibration families differ from plan')
    jobs=[(seed,fam,rate,plan) for fam,(lo,hi) in CAL_RANGES.items() for seed in range(lo,hi+1) for rate in plan['mask_rates']]
    with ProcessPoolExecutor(workers) as ex:res=list(ex.map(_cal,jobs))
    best={'P':(None,None),'C':(None,None)};per={'P':{},'C':{}}
    for fam,seed,rate,tp,tc in res:
        for arm,trace in (('P',tp),('C',tc)):
            for step,R in trace:
                if R is None:continue
                if best[arm][0] is None or R>best[arm][0]:best[arm]=(R,{'family':fam,'seed':seed,'mask_rate':rate,'step':step})
                if per[arm].get(fam) is None or R>per[arm][fam]:per[arm][fam]=R
    tau=best['P'][0]
    return {'schema':'brute.calibration-check.v2','study':plan['study'],'window_W':plan['residual_surprise']['window_W'],
            'tau':tau,'argmax':best['P'][1],'tau_v011_control':best['C'][0],'argmax_v011_control':best['C'][1],
            'tau_study002':ref['tau'],'argmax_study002':ref['argmax'],
            'tau_reproduced':tau==ref['tau']==plan['residual_surprise']['tau'] and best['C'][0]==ref['tau']
                             and per['P']==ref['per_family_max_R'] and per['C']==ref['per_family_max_R'],
            'per_family_max_R':per['P'],'per_family_max_R_v011_control':per['C'],'per_family_max_R_study002':ref['per_family_max_R'],
            'calibration_cases':len(jobs),'out_of_family_data_used':False,'study002_calibration_sha256':sha(CALIBRATION_002),
            'plan_sha256':sha(PLAN),'freeze_sha256':sha(FREEZE)}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(STUDY_DIR/'CALIBRATION_CHECK.json'))
    ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
    out=calibrate_check(a.workers);write_new(a.output,out);print(out)
