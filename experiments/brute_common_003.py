"""Shared helpers for study BRUTE-011-FALLBACK-003 (paths, freeze check). Reuses the frozen
study-002 helpers for hashing and no-overwrite writes."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new,check_freeze as check_freeze_002

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_003.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_003.json'
STUDY_DIR=ROOT/'results/study-003'
CALIBRATION_002=ROOT/'results/study-002/CALIBRATION.json'
DRIFT_STEPS=(12,23,34)   # trace steps whose hidden transition is perturbed in drift4 (bgr90.worlds.step: t>0, t%11==0)

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR',
         'CALIBRATION_002','DRIFT_STEPS','check_freeze']


def check_freeze():
    """Study-002 source freeze AND study-003 source freeze must both hold."""
    check_freeze_002()
    frozen=load(FREEZE)
    for rel,digest in frozen['sha256_files'].items():
        check(sha(ROOT/rel)==digest,'study-003 source freeze invalid: '+rel)
    return frozen
