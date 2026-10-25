"""Shared helpers for study BRUTE-040-GEOMETRY-006 (paths, freeze chain)."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_005 import check_freeze as check_freeze_005,is_stale,DRIFT_STEPS,POST_JUMP_STEPS,FIRST_DRIFT

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_006.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_006.json'
STUDY_DIR=ROOT/'results/study-006'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','DRIFT_STEPS',
         'POST_JUMP_STEPS','FIRST_DRIFT','check_freeze','is_stale']


def check_freeze():
    """Study-002..005 source freezes AND the study-006 source freeze must all hold."""
    check_freeze_005()
    frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-006 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():
        check(sha(ROOT/rel)==digest,'study-006 source freeze invalid: '+rel)
    return frozen
