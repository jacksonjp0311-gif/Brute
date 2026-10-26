"""Shared helpers for study BRUTE-090-WINDOW-011 (paths, plan view, freeze chain, checkpoints)."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail,plan006_keys
from experiments.brute_common_010 import check_freeze as check_freeze_010

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_011.json'
PLAN007=ROOT/'experiments/BRUTE_PLAN_007.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_011.json'
RELEASE_FREEZE_080=ROOT/'experiments/BRUTE_RELEASE_FREEZE_080.json'
STUDY_DIR=ROOT/'results/study-011'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','PLAN007','FREEZE','STUDY_DIR',
         'check_freeze','plan_view','plan006_keys','Checkpoint','repair_torn_tail']


def plan_view(plan):
    """As experiments/brute_common_010.plan_view and experiments/v090_reference.plan_view: the frozen BRUTE_PLAN_007
    learner configuration, overridden by every key plan 011 defines (and its rule_constants_frozen)."""
    v=dict(load(PLAN007));v.update(plan);v.update(plan['rule_constants_frozen'])
    check(v['row_budget_enumeration']==160000,'row budget');check(v['jump_window_K']==4,'K');return v


def check_freeze():
    """Study-002..010 source freezes and adopted files (via brute_common_010.check_freeze), the v0.8.0 release freeze,
    and the study-011 source freeze must all hold (G13)."""
    check_freeze_010()
    for f in (RELEASE_FREEZE_080,FREEZE):
        frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN),'study-011 plan changed after source freeze')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
