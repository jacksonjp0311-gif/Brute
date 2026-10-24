"""Run pre-registered study BRUTE-010-ABSTENTION-002. No overwrites; SHA-256 seal."""
import argparse,time
from pathlib import Path
from experiments.brute_common import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check
from brute.evaluation import run_case,aggregate,no_time


def run(output,calibration):
    output=Path(output);plan=load(PLAN);check_freeze();cal=load(calibration)
    check(cal['plan_sha256']==sha(PLAN) and cal['freeze_sha256']==sha(FREEZE),'calibration was made under a different plan/freeze')
    for name in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):
        check(not (output/name).exists(),'refusing overwrite '+str(output/name))
    tau=cal['tau'];cases=[];started=time.perf_counter()
    for fam,(lo,hi) in plan['heldout_ranges'].items():
        for seed in range(lo,hi+1):
            for rate in plan['mask_rates']:cases.append(run_case(seed,fam,rate,plan,tau))
        print('study-002 completed',fam,len(cases),'cases',flush=True)
    result={'schema':'brute.study.v1','plan':plan,'calibration':cal,'cases':cases,'summary':aggregate(cases),
            'total_elapsed_informational':time.perf_counter()-started}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':sha(FREEZE),
        'calibration_sha256':sha(calibration),'case_count':len(cases)})
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(STUDY_DIR))
    ap.add_argument('--calibration',default=str(STUDY_DIR/'CALIBRATION.json'));a=ap.parse_args()
    run(a.output,a.calibration);print('done')
