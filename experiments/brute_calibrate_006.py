"""tau6 calibration for study-006 (BRUTE_PLAN_006 alarm_rule.tau6_calibration).

P4 (ResumeBruteLearner) with the alarm disabled (tau=None: no alarm, no resume) on the passive sequence of every
calibration case (calibration_ranges_tau6 x 3 mask rates); tau6 = max residual over every step of every case, rounded
to 12 decimals. In-family calibration data only. G13: a second run must reproduce the file byte-for-byte."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from bgr89.worlds import actions
from brute.resume import ResumeBruteLearner
from experiments.worlds_006 import world
from experiments.brute_common_006 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check


def _cal(args):
    seed,fam,rate,plan=args
    truth=world(seed,fam);h=truth.start;init=truth.observed(h,rate,-1)
    L=ResumeBruteLearner(plan['family_state_cap'],plan['margin_state_cap'],plan['row_budget_family'],plan['row_budget_margin'],
                         plan['prediction_smoothing'],plan['open_world_reserve_epsilon'],plan['residual_surprise']['window_W'],None,None)
    L.initialize(init);out=[]
    for i,a in enumerate(actions(seed,plan['actions_per_case'])):
        h=truth.next(h,a);L.observe(a,truth.observed(h,rate,i))
        if L.residual is not None:out.append((i+1,L.residual))
    check(L.alarm_step is None,'alarm with tau=None')
    return fam,seed,rate,out


def calibrate(workers=4,smoke=False):
    plan=load(PLAN)
    if not smoke:check_freeze()
    R=plan['calibration_ranges_tau6'];check(set(R)==set(plan['in_family_original']),'calibration families differ from plan')
    jobs=[(seed,fam,rate,plan) for fam,(lo,hi) in R.items() for seed in range(lo,hi+1) for rate in plan['mask_rates']]
    with ProcessPoolExecutor(workers) as ex:res=list(ex.map(_cal,jobs,chunksize=4))
    best=None;arg=None;per={}
    for fam,seed,rate,tr in res:
        for step,r in tr:
            if best is None or r>best:best=r;arg={'family':fam,'seed':seed,'mask_rate':rate,'step':step}
            if per.get(fam) is None or r>per[fam]:per[fam]=r
    return {'schema':'brute.calibration.v6','study':plan['study'],'window_W':plan['residual_surprise']['window_W'],
            'tau6':round(best,12),'tau6_unrounded':best,'argmax':arg,'per_family_max_R':{k:round(v,12) for k,v in sorted(per.items())},
            'calibration_cases':len(jobs),'out_of_family_data_used':False,'plan_sha256':sha(PLAN),
            'freeze_sha256':None if smoke else sha(FREEZE)}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(STUDY_DIR/'CALIBRATION_006.json'))
    ap.add_argument('--workers',type=int,default=4);ap.add_argument('--smoke',action='store_true');a=ap.parse_args()
    out=calibrate(a.workers,a.smoke);write_new(a.output,out);print({k:v for k,v in out.items() if k!='per_family_max_R'},out['per_family_max_R'])
