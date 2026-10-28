"""Shared helpers for study BRUTE-0180-HORIZON-020 (paths, frozen learner configuration at the 88-action horizon, freeze chain)."""
import copy
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_018 import learner_plan as learner_plan_018,TAU6
from experiments.brute_common_019 import check_freeze as check_freeze_019

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_020.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_020.json'
RELEASE_FREEZES=[ROOT/'experiments/BRUTE_SOURCE_FREEZE_019.json',ROOT/'experiments/BRUTE_RELEASE_FREEZE_0170.json']
STUDY_DIR=ROOT/'results/study-020'
STEPS=88

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'learner_plan','Checkpoint','repair_torn_tail','TAU6','STEPS']


def learner_plan(plan):
    """#103 item 1: the frozen study-013 learner dict (asserted as study-019) with actions_per_case_2x2 = horizon.steps,
    as an in-memory copy; the frozen file is not changed."""
    p13=copy.deepcopy(learner_plan_018(plan))
    check(plan['horizon']['steps']==STEPS and plan['horizon']['late_window']==[45,88],'plan 020 horizon')
    p13['actions_per_case_2x2']=STEPS;return p13


def check_freeze():
    """Every earlier freeze (brute_common_019.check_freeze), the study-019 source and v0.17.0 release freezes and the
    study-020 source freeze must hold (G13)."""
    check_freeze_019()
    for f in RELEASE_FREEZES+[FREEZE]:
        if not f.exists():
            check(f!=FREEZE,'study-020 source freeze missing');continue
        frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN),'study-020 plan changed after source freeze')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
