"""Shared helpers for study BRUTE-0120-BOUNDED-TRANSFER-014 (paths, frozen learner configuration, freeze chain)."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_013 import check_freeze as check_freeze_013,PLAN as PLAN013

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_014.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_014.json'
RELEASE_FREEZES=[ROOT/'experiments/BRUTE_RELEASE_FREEZE_0110.json']
STUDY_DIR=ROOT/'results/study-014'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'learner_plan','Checkpoint','repair_torn_tail']


def learner_plan(plan):
    """The frozen learner configuration: the study-013 plan dict, which the frozen experiments.brute_study_012 /
    brute_study_013 functions read (plan_view, plan006_keys, in_family_2x2, actions_per_case_2x2). Plan 014 inherits
    these constants unchanged; this asserts the shared ones are equal."""
    p13=load(PLAN013)
    check(p13['tau6']['value']==plan['tau6']['value'] and p13['tau7']['value']==plan['tau7']['value'],'tau6 / tau7 equal to plan 013')
    check(p13['burn_in']==plan['burn_in'] and p13['actions_per_case_2x2']==plan['actions_per_case'],'burn_in / actions per case equal to plan 013')
    check(p13['mask_rates']==plan['mask_rates'],'mask rates equal to plan 013')
    return p13


def check_freeze():
    """Every earlier source / release freeze (brute_common_013.check_freeze), the v0.11.0 release freeze and the study-014
    source freeze must hold (G13)."""
    check_freeze_013()
    for f in RELEASE_FREEZES+[FREEZE]:
        if not f.exists():
            check(f!=FREEZE,'study-014 source freeze missing');continue
        frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN),'study-014 plan changed after source freeze')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
