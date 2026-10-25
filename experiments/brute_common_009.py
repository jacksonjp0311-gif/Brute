"""Shared helpers for study BRUTE-070-SYNCPLAN-009 (paths, plan view, freeze chain, checkpoints)."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_007 import Checkpoint
from experiments.brute_common_008 import check_freeze as check_freeze_008,plan006_keys

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_009.json'
PLAN007=ROOT/'experiments/BRUTE_PLAN_007.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_009.json'
RELEASE_FREEZE_060_R1=ROOT/'experiments/BRUTE_RELEASE_FREEZE_060_R1.json'
STUDY_DIR=ROOT/'results/study-009'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','PLAN007','FREEZE','STUDY_DIR',
         'check_freeze','plan_view','plan006_keys','Checkpoint','check_adopted']


def plan_view(plan):
    """As experiments/brute_common_008.plan_view and experiments/v070_reference.plan_view: the frozen BRUTE_PLAN_007
    learner configuration, overridden by every key plan 009 defines (and its rule_constants_frozen)."""
    v=dict(load(PLAN007));v.update(plan);v.update(plan['rule_constants_frozen'])
    check(v['row_budget_enumeration']==160000,'row budget');return v


def check_adopted(plan=None):
    plan=plan or load(PLAN)
    for rel,digest in plan['adopted_files']['files'].items():check(sha(ROOT/rel)==digest,'adopted file changed: '+rel)


def check_freeze():
    """Study-002..008 source freezes (via brute_common_008.check_freeze), the v0.6.0 release freeze r1, the adopted
    files, and the study-009 source freeze must all hold."""
    check_freeze_008()
    check_adopted()
    for f in (RELEASE_FREEZE_060_R1,FREEZE):
        frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN),'study-009 plan changed after source freeze')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
