"""Shared helpers for study BRUTE-0220-BETTING-CS-025 (adapted from experiments/brute_common_024.py, frozen).
Same design as study-024: mask_rate / horizon / learner come from the frozen BRUTE_PLAN_021.json, and the study-025 freeze
hashes BRUTE_PLAN_025.json, its amendment BRUTE_PLAN_025_A1.json and BRUTE_PLAN_021.json."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_018 import TAU6
from experiments.brute_common_021 import PLAN as PLAN_021
from experiments.brute_common_024 import base_plan,learner_plan,check_freeze as check_freeze_024

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_025.json'
PLAN_A1=ROOT/'experiments/BRUTE_PLAN_025_A1.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_025.json'
FREEZE_024=ROOT/'experiments/BRUTE_SOURCE_FREEZE_024.json'
RELEASE_FREEZES=[ROOT/'experiments/BRUTE_RELEASE_FREEZE_0210.json']
STUDY_DIR=ROOT/'results/study-025'
STEPS=88

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','PLAN_A1','PLAN_021','FREEZE','STUDY_DIR','check_freeze',
         'learner_plan','base_plan','Checkpoint','repair_torn_tail','TAU6','STEPS','criteria']


def criteria():
    """Effective criteria = BRUTE_PLAN_025 criteria with amendment A1 applied (GBC_headline.b strict)."""
    p=load(PLAN);a=load(PLAN_A1);check(a['amends_sha256']==sha(PLAN),'A1 amends this plan');c=a['effective_criteria']
    check({k:v for k,v in c.items() if k!='GBC_headline'}=={k:v for k,v in p['criteria'].items() if k!='GBC_headline'},'A1 keeps other criteria')
    return c


def check_freeze():
    """Every earlier freeze (study-024 chain incl. its source freeze), the v0.21.0 release freeze and the study-025 source freeze."""
    if FREEZE_024.exists():check_freeze_024()
    for f in RELEASE_FREEZES+[FREEZE]:
        if not f.exists():
            check(f!=FREEZE,'study-025 source freeze missing');continue
        frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN) and frozen['plan_a1_sha256']==sha(PLAN_A1) and frozen['plan_021_sha256']==sha(PLAN_021),
                           'study-025 plan changed after source freeze')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
