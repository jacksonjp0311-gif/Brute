"""Shared helpers for study BRUTE-0150-BOUNDED-LOOKAHEAD-017 (paths, frozen learner configuration, freeze chain)."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_016 import check_freeze as check_freeze_016,learner_plan as learner_plan_016

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_017.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_017.json'
RELEASE_FREEZES=[ROOT/'experiments/BRUTE_RELEASE_FREEZE_0140.json']
STUDY_DIR=ROOT/'results/study-017'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'learner_plan','Checkpoint','repair_torn_tail']


def learner_plan(plan):
    """The frozen learner configuration (the study-013 plan dict, via brute_common_016.learner_plan, which asserts tau6,
    burn_in, actions per case and mask rates equal)."""
    return learner_plan_016(plan)


def check_freeze():
    """Every earlier source / release freeze (brute_common_016.check_freeze), the v0.14.0 release freeze and the study-017
    source freeze must hold (G13)."""
    check_freeze_016()
    for f in RELEASE_FREEZES+[FREEZE]:
        if not f.exists():
            check(f!=FREEZE,'study-017 source freeze missing');continue
        frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN),'study-017 plan changed after source freeze')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
