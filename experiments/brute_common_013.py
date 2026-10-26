"""Shared helpers for study BRUTE-0110-SOUND-TRANSFER-013 (paths, plan view, freeze chain, checkpoints)."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail,plan006_keys
from experiments.brute_common_012 import check_freeze as check_freeze_012

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_013.json'
PLAN007=ROOT/'experiments/BRUTE_PLAN_007.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_013.json'
RELEASE_FREEZES=[ROOT/'experiments/BRUTE_RELEASE_FREEZE_0100.json']
STUDY_DIR=ROOT/'results/study-013'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','PLAN007','FREEZE','STUDY_DIR',
         'check_freeze','plan_view','plan006_keys','Checkpoint','repair_torn_tail']


def plan_view(plan):
    """The frozen BRUTE_PLAN_007 learner configuration, overridden by every key plan 013 defines."""
    v=dict(load(PLAN007));v.update(plan);v.update(plan['rule_constants_frozen'])
    check(v['row_budget_enumeration']==160000,'row budget');check(v['jump_window_K']==4,'K');return v


def check_freeze():
    """Every earlier source / release freeze (via brute_common_012.check_freeze), the v0.10.0 release freeze and the
    study-013 source freeze must hold (G13)."""
    check_freeze_012()
    for f in RELEASE_FREEZES+[FREEZE]:
        if not f.exists():
            check(f!=FREEZE,'study-013 source freeze missing');continue
        frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN),'study-013 plan changed after source freeze')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
