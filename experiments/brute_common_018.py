"""Shared helpers for study BRUTE-0160-NOISY-OBSERVATION-018 (paths, frozen learner configuration, freeze chain)."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_013 import PLAN as PLAN013
from experiments.brute_common_017 import check_freeze as check_freeze_017

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_018.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_018.json'
RELEASE_FREEZES=[ROOT/'experiments/BRUTE_RELEASE_FREEZE_0150.json']
STUDY_DIR=ROOT/'results/study-018'
TAU6=1.645215321642

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'learner_plan','Checkpoint','repair_torn_tail','TAU6']


def learner_plan(plan):
    """The frozen learner configuration: the study-013 plan dict read by the frozen experiments.brute_study_012 functions
    (#97 item 4: plan 018 has no tau6 / mask_rates keys). Shared constants are asserted equal; tau6 is the frozen value."""
    p13=load(PLAN013)
    check(p13['tau6']['value']==TAU6,'tau6 of plan 013')
    check(p13['burn_in']==plan['burn_in'] and p13['actions_per_case_2x2']==plan['actions_per_case'],'burn_in / actions per case equal to plan 013')
    check(plan['mask_rate'] in p13['mask_rates'],'mask rate is a plan-013 rate')
    return p13


def check_freeze():
    """Every earlier source / release freeze (brute_common_017.check_freeze), the v0.15.0 release freeze and the study-018
    source freeze must hold (G13)."""
    check_freeze_017()
    for f in RELEASE_FREEZES+[FREEZE]:
        if not f.exists():
            check(f!=FREEZE,'study-018 source freeze missing');continue
        frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN),'study-018 plan changed after source freeze')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
