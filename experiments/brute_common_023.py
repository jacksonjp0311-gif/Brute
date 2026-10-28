"""Shared helpers for study BRUTE-0200-LR-ANYTIME-023 (paths, the study-021 88-action learner configuration, freeze chain).
BRUTE_PLAN_023 says mask_rate / horizon / learner are "as study-021": they are read from the frozen BRUTE_PLAN_021.json
(deviation #108 item 2), and the study-023 freeze hashes both plan files."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_018 import TAU6
from experiments.brute_common_021 import learner_plan as learner_plan_021,check_freeze as check_freeze_021,PLAN as PLAN_021

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_023.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_023.json'
RELEASE_FREEZES=[ROOT/'experiments/BRUTE_RELEASE_FREEZE_0190.json']
STUDY_DIR=ROOT/'results/study-023'
STEPS=88

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','PLAN_021','FREEZE','STUDY_DIR','check_freeze',
         'learner_plan','base_plan','Checkpoint','repair_torn_tail','TAU6','STEPS']


def base_plan():
    """The frozen study-021 plan (mask_rate, burn_in, horizon, learner)."""
    p=load(PLAN_021);check(p['mask_rate']==0.35 and p['burn_in']==8 and p['horizon']['steps']==STEPS,'plan 021 constants');return p


def learner_plan(plan=None):
    return learner_plan_021(base_plan())


def check_freeze():
    """Every earlier freeze (brute_common_021.check_freeze), the v0.19.0 release freeze and the study-023 source freeze."""
    check_freeze_021()
    for f in RELEASE_FREEZES+[FREEZE]:
        if not f.exists():
            check(f!=FREEZE,'study-023 source freeze missing');continue
        frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN) and frozen['plan_021_sha256']==sha(PLAN_021),'study-023 plan changed after source freeze')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
