"""Calibrate the residual-surprise threshold tau on IN-FAMILY calibration cases only.

Calibration cases = study-001 heldout seeds of the five in-family families
(disjoint from the study-002 heldout seeds). The alarm is disabled (tau=None);
tau is the maximum windowed surprise R_t seen at any step of any case.
"""
import argparse
from experiments.brute_common import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check
from brute.evaluation import run_case

CAL_RANGES={'cycle3':[930001,930024],'switch3':[940001,940024],'unstructured3':[950001,950024],
            'unaliased2':[960001,960024],'ood4':[970001,970024]}


def calibrate():
    plan=load(PLAN);check_freeze()
    check(set(CAL_RANGES)==set(plan['residual_surprise']['calibration_set']['families']),'calibration families differ from plan')
    tau=None;argmax=None;per_family={};cases=0
    for fam,(lo,hi) in CAL_RANGES.items():
        fam_max=None
        for seed in range(lo,hi+1):
            for rate in plan['mask_rates']:
                c=run_case(seed,fam,rate,plan,None);cases+=1
                for r in c['trace']:
                    R=r['residual_after']
                    if R is None:continue
                    if fam_max is None or R>fam_max:fam_max=R
                    if tau is None or R>tau:tau=R;argmax={'family':fam,'seed':seed,'mask_rate':rate,'step':r['step']}
        per_family[fam]=fam_max
    return {'schema':'brute.calibration.v1','study':plan['study'],'window_W':plan['residual_surprise']['window_W'],
            'tau':tau,'argmax':argmax,'per_family_max_R':per_family,'calibration_cases':cases,
            'out_of_family_data_used':False,'plan_sha256':sha(PLAN),'freeze_sha256':sha(FREEZE)}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(STUDY_DIR/'CALIBRATION.json'))
    out=calibrate();write_new(ap.parse_args().output,out);print(out)
