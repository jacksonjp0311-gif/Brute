"""Shared helpers for study BRUTE-030-CHANGEPOINT-005 (paths, freeze chain). Reuses the frozen study-002..004 helpers."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_004 import check_freeze as check_freeze_004

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_005.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_005.json'
STUDY_DIR=ROOT/'results/study-005'
CALIBRATION_002=ROOT/'results/study-002/CALIBRATION.json'
DRIFT_STEPS=(12,23,34)
POST_JUMP_STEPS=(13,24,35)
FIRST_DRIFT=12

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR',
         'CALIBRATION_002','DRIFT_STEPS','POST_JUMP_STEPS','FIRST_DRIFT','check_freeze','is_stale']


def is_stale(step):
    """Plan metric stale_false_certificate: a non-drift step after the first drift step."""
    return step>FIRST_DRIFT and step not in DRIFT_STEPS


def check_freeze():
    """Study-002/003/004 source freezes AND the study-005 source freeze must all hold."""
    check_freeze_004()
    frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-005 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():
        check(sha(ROOT/rel)==digest,'study-005 source freeze invalid: '+rel)
    return frozen
