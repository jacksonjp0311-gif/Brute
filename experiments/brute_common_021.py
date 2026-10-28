"""Shared helpers for study BRUTE-0190-ANYTIME-021 (paths, the frozen 88-action learner configuration, freeze chain)."""
import copy
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_018 import learner_plan as learner_plan_018,TAU6
from experiments.brute_common_020 import check_freeze as check_freeze_020

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_021.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_021.json'
RELEASE_FREEZES=[ROOT/'experiments/BRUTE_RELEASE_FREEZE_0180.json']
STUDY_DIR=ROOT/'results/study-021'
STEPS=88

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'learner_plan','Checkpoint','repair_torn_tail','TAU6','STEPS']


def learner_plan(plan):
    """As study-020: the frozen study-013 learner dict with actions_per_case_2x2 = horizon.steps (in-memory copy)."""
    p13=copy.deepcopy(learner_plan_018(plan))
    check(plan['horizon']['steps']==STEPS and plan['horizon']['late_window']==[45,88],'plan 021 horizon')
    p13['actions_per_case_2x2']=STEPS;return p13


def check_freeze():
    """Every earlier freeze (brute_common_020.check_freeze), the v0.18.0 release freeze and the study-021 source freeze."""
    check_freeze_020()
    for f in RELEASE_FREEZES+[FREEZE]:
        if not f.exists():
            check(f!=FREEZE,'study-021 source freeze missing');continue
        frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN),'study-021 plan changed after source freeze')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
