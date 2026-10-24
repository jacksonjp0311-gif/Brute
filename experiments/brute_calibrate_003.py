"""G7(c): tau must reproduce byte-for-byte with v0.1.1 code (plan residual_surprise.calibration_check).

Same rule as study-002 (experiments/brute_calibrate.py): alarm disabled, tau = max windowed surprise
over every step of every in-family calibration case (study-001 heldout seeds of the 5 in-family
families, 3 mask rates). Computed for the v0.1.1 learner and, as a cross-check, the v0.1.0 control.
"""
import argparse
from experiments.brute_common_003 import PLAN,FREEZE,STUDY_DIR,CALIBRATION_002,load,sha,write_new,check_freeze,check
from experiments.brute_study_003 import run_case_003

CAL_RANGES={'cycle3':[930001,930024],'switch3':[940001,940024],'unstructured3':[950001,950024],
            'unaliased2':[960001,960024],'ood4':[970001,970024]}


def calibrate_check():
    plan=load(PLAN);check_freeze();ref=load(CALIBRATION_002)
    check(set(CAL_RANGES)==set(plan['in_family']),'calibration families differ from plan')
    best={'v0.1.1':(None,None),'v0.1.0':(None,None)};per_family={};cases=0
    for fam,(lo,hi) in CAL_RANGES.items():
        fam_max=None
        for seed in range(lo,hi+1):
            for rate in plan['mask_rates']:
                c=run_case_003(seed,fam,rate,plan,None);cases+=1
                for arm,trace in (('v0.1.1',c['trace']),('v0.1.0',c['control_trace'])):
                    for r in trace:
                        R=r['residual_after']
                        if R is None:continue
                        if best[arm][0] is None or R>best[arm][0]:best[arm]=(R,{'family':fam,'seed':seed,'mask_rate':rate,'step':r['step']})
                        if arm=='v0.1.1' and (fam_max is None or R>fam_max):fam_max=R
        per_family[fam]=fam_max
    tau=best['v0.1.1'][0]
    return {'schema':'brute.calibration-check.v1','study':plan['study'],'window_W':plan['residual_surprise']['window_W'],
            'tau':tau,'argmax':best['v0.1.1'][1],'tau_v010_control':best['v0.1.0'][0],
            'tau_study002':ref['tau'],'argmax_study002':ref['argmax'],
            'tau_reproduced':tau==ref['tau']==plan['residual_surprise']['tau'] and best['v0.1.0'][0]==ref['tau'] and per_family==ref['per_family_max_R'],
            'per_family_max_R':per_family,'per_family_max_R_study002':ref['per_family_max_R'],'calibration_cases':cases,
            'out_of_family_data_used':False,'study002_calibration_sha256':sha(CALIBRATION_002),
            'plan_sha256':sha(PLAN),'freeze_sha256':sha(FREEZE)}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(STUDY_DIR/'CALIBRATION_CHECK.json'))
    out=calibrate_check();write_new(ap.parse_args().output,out);print(out)
