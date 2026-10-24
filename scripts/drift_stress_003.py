"""R4 (reported, not gated): v0.1.1 on the study-001 drift4 seeds 990001..990024 (DESIGN data, already
seen while scoping v0.1.1). Amendment A6: tau from results/study-002/CALIBRATION.json."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_003 import STUDY_DIR,PLAN,CALIBRATION_002,load,dumps,write_new,check,sha
from experiments.brute_study_003 import run_case_003,aggregate_003
from brute.evaluation import no_time

OUT=STUDY_DIR/'DRIFT_STRESS_R4.json'
SEEDS=(990001,990024)


def build():
    plan=load(PLAN);tau=load(CALIBRATION_002)['tau'];check(tau==plan['residual_surprise']['tau'],'A6 tau')
    cases=[run_case_003(s,'drift4',m,plan,tau) for s in range(SEEDS[0],SEEDS[1]+1) for m in plan['mask_rates']]
    S=no_time(aggregate_003(cases,plan))["drift4"]
    keep=('cases','v0.1.1','v0.1.0','v0.90','retraction_reasons','retracted_wrong','wrong_certs_in_never_contradicted_cases',
          'baselines_logloss_post','ablation_logloss_post','forecast_source_steps_post')
    wrong=[{'seed':c['seed'],'mask_rate':c['mask_rate'],'step':r['step'],'drift_step':r['drift_step'],'certificate':r['certificate'],
            'actual':r['actual_emission_EVALUATOR_ONLY']} for c in cases for r in c['trace'] if r['brute_wrong']]
    return {'schema':'brute.drift-stress.v1','criterion':'R4_drift_stress_replay (reported, not gated; design data)',
            'seeds':list(SEEDS),'tau':tau,'tau_source_sha256':sha(CALIBRATION_002),
            'summary':{k:S[k] for k in keep},'wrong_certificates':wrong}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();obj=build()
    if a.check:check(OUT.read_bytes()==dumps(obj),'DRIFT_STRESS_R4.json does not reproduce');print('R4 reproduces')
    else:write_new(OUT,obj);print(dumps(obj).decode())
