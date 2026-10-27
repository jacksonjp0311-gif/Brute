"""Shared helpers for study BRUTE-0170-SEQUENTIAL-MARGIN-019 (paths, frozen learner configuration, freeze chain)."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_018 import check_freeze as check_freeze_018,learner_plan,TAU6

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_019.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_019.json'
RELEASE_FREEZES=[ROOT/'experiments/BRUTE_RELEASE_FREEZE_0160.json']
STUDY_DIR=ROOT/'results/study-019'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'learner_plan','Checkpoint','repair_torn_tail','TAU6']


def check_freeze():
    """Every earlier source / release freeze (brute_common_018.check_freeze), the v0.16.0 release freeze and the study-019
    source freeze must hold (G13)."""
    check_freeze_018()
    for f in RELEASE_FREEZES+[FREEZE]:
        if not f.exists():
            check(f!=FREEZE,'study-019 source freeze missing');continue
        frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN),'study-019 plan changed after source freeze')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
