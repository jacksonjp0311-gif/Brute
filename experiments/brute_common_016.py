"""Shared helpers for study BRUTE-0140-DEFERRED-SPLIT-016 (paths, frozen learner configuration, freeze chain)."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_015 import check_freeze as check_freeze_015,learner_plan as learner_plan_015

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_016.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_016.json'
RELEASE_FREEZES=[ROOT/'experiments/BRUTE_RELEASE_FREEZE_0130.json']
STUDY_DIR=ROOT/'results/study-016'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'learner_plan','Checkpoint','repair_torn_tail']


def learner_plan(plan):
    """The frozen learner configuration (the study-013 plan dict, via brute_common_015.learner_plan, which asserts tau6,
    burn_in, actions per case and mask rates equal)."""
    return learner_plan_015(plan)


def check_freeze():
    """Every earlier source / release freeze (brute_common_015.check_freeze), the v0.13.0 release freeze and the study-016
    source freeze must hold (G13)."""
    check_freeze_015()
    for f in RELEASE_FREEZES+[FREEZE]:
        if not f.exists():
            check(f!=FREEZE,'study-016 source freeze missing');continue
        frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN),'study-016 plan changed after source freeze')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
