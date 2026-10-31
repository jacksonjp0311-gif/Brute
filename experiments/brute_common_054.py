"""Shared helpers for study BRUTE-0510-SCALE20-SINGLERIVAL-054a (experiments/BRUTE_PLAN_054.json as amended pre-data by
experiments/BRUTE_PLAN_054a.json; pre-run deviation #181 fixes every definition added here). New file.
The study-054 freeze hashes BRUTE_PLAN_054.json, BRUTE_PLAN_054a.json and the v0.51.0 study sources; the 025-053 freezes are
checked unchanged via the frozen 053 check. Caps are fixed by the plan (design.caps), not calibrated:
  scale20t: C20 50000, B20 2000000, family_bound 20; compat20t: C 50000, B 3000000, family_bound 16.
Stop rule everywhere: conflict-only (no host hook is passed, so no per-chunk wall interrupt; the API's case guard is set to the
plan's 900 s hard job kill as a safety net only; any firing fails GDET54 for scale20t and is a published failure elsewhere).
Workers: 8 = a 4-worker pool for scale20t (18 jobs) and a 4-worker pool for compat20t (12 jobs), concurrent, one process."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_053 import check_freeze as check_freeze_053

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_054.json'
AMEND=ROOT/'experiments/BRUTE_PLAN_054a.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_054.json'
STUDY_DIR=ROOT/'results/study-054'
C50=50000;B16=3000000;C20=50000;B20=2000000
CAPS_OF={'scale20t':(C20,B20),'compat20t':(C50,B16)}
BOUND_OF={'scale20t':20,'compat20t':16}
T_ARMS=('API20T','API20T_b');E_ARMS=('API16E20','API16E');ALL_ARMS=T_ARMS+E_ARMS
ARMS_OF={'scale20t':('API20T','API20T_b','API16E20'),'compat20t':('API20T','API16E')}
WORKERS=8;WORKERS_S=4;WORKERS_C=4;HARD_KILL_S=900.0
STOP_RULE='conflict-only (no hook; 900 s case kill as safety net)'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','AMEND','FREEZE','STUDY_DIR','check_freeze','Checkpoint',
         'repair_torn_tail','wilson','C50','B16','C20','B20','CAPS_OF','BOUND_OF','T_ARMS','E_ARMS','ALL_ARMS','ARMS_OF','WORKERS',
         'WORKERS_S','WORKERS_C','HARD_KILL_S','STOP_RULE','caps_for']


def caps_for(key):return CAPS_OF[key]


def check_freeze():
    """The study-025 to 053 source freezes (via the frozen 053 check) and the study-054 source freeze."""
    check_freeze_053()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-054 plan changed after source freeze')
    check(frozen['amendment_sha256']==sha(AMEND),'study-054 amendment 054a changed after source freeze')
    check(frozen['caps']=={k:list(v) for k,v in CAPS_OF.items()},'study-054 caps differ from the freeze')
    check(frozen['bounds']==BOUND_OF and frozen['arms']=={k:list(v) for k,v in ARMS_OF.items()},'study-054 bounds or arms differ from the freeze')
    check(frozen['workers']=={'total':WORKERS,'scale20t':WORKERS_S,'compat20t':WORKERS_C},'study-054 workers differ from the freeze')
    check(frozen['stop']=={'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'study-054 stop rule differs from the freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
