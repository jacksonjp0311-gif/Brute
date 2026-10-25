"""Shared helpers for study BRUTE-020-ACTIVE-004 (paths, freeze chain). Reuses the frozen study-002/003 helpers."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_003 import check_freeze as check_freeze_003

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_004.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_004.json'
STUDY_DIR=ROOT/'results/study-004'
CALIBRATION_002=ROOT/'results/study-002/CALIBRATION.json'
DRIFT_STEPS=(12,23,34)
POST_JUMP_STEPS=(13,24,35)

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR',
         'CALIBRATION_002','DRIFT_STEPS','POST_JUMP_STEPS','check_freeze']


def check_freeze():
    """Study-002 and study-003 source freezes AND the study-004 source freeze must all hold."""
    check_freeze_003()
    frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-004 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():
        check(sha(ROOT/rel)==digest,'study-004 source freeze invalid: '+rel)
    return frozen
