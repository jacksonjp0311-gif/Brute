"""Shared helpers for study BRUTE-0450-CERTIFY16D-WALLFREE-SCALE20-048 (experiments/BRUTE_PLAN_048.json; pre-run deviation #169
fixes every definition added here). New file.
The study-048 freeze hashes BRUTE_PLAN_048.json and the v0.45.0 sources; the 025-047 freezes are checked unchanged via the
frozen 047 check. Caps are fixed by the plan (design.cap_rule), not calibrated: C 50000 per call, B16 1500000 per scale16 or
control case, B20 1000000 per scale20 case. The wall guard stays at the certify/16d defaults (30 s per call, 600 s per case)."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_047 import check_freeze as check_freeze_047,sealed046
from experiments.host_hook_047 import TimerHook

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_048.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_048.json'
STUDY_DIR=ROOT/'results/study-048'
C48=50000;B16=1500000;B20=1000000
BUDGET_OF={'scale16':B16,'control':B16,'scale20':B20}

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze','Checkpoint',
         'repair_torn_tail','wilson','TimerHook','sealed046','C48','B16','B20','BUDGET_OF','budget_for']


def budget_for(key):return BUDGET_OF[key]


def check_freeze():
    """The study-025 to 047 source freezes (via the frozen 047 check) and the study-048 source freeze."""
    check_freeze_047()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-048 plan changed after source freeze')
    check((frozen['conflict_cap'],frozen['budget_conflicts'])==(C48,{'scale16':B16,'control':B16,'scale20':B20}),'study-048 caps differ from the freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
