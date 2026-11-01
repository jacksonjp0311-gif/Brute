"""Shared helpers for study BRUTE-0530-SCALE20-LSTAR-056 (experiments/BRUTE_PLAN_056.json, no amendment; pre-run
deviation #185 fixes every definition added here). New file; built from experiments/brute_common_055.py (frozen).
The study-056 freeze hashes BRUTE_PLAN_056.json and the v0.53.0 study sources; the 025-055 freezes are
checked unchanged via the frozen 055 check. Caps are fixed by the plan (design.caps), not calibrated:
  scale20t: C20 50000, B20 2000000, family_bound 20; compat20t: C 50000, B 3000000, family_bound 16.
Stop rule everywhere: conflict-only (no host hook is passed, so no per-chunk wall interrupt; the API's case guard is set to the
plan's 900 s hard job kill as a safety net only; any firing fails GDET55 for scale20t and is a published failure elsewhere).
Workers: 8 = a 4-worker pool for scale20t (18 jobs) and a 4-worker pool for compat20t (12 jobs), concurrent, one process."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_055 import check_freeze as check_freeze_055
from brute.api.certify20l import HYP_ROUNDS

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_056.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_056.json'
STUDY_DIR=ROOT/'results/study-056'
C50=50000;B16=3000000;C20=50000;B20=2000000
CAPS_OF={'scale20t':(C20,B20),'compat20t':(C50,B16)}
BOUND_OF={'scale20t':20,'compat20t':16}
T_ARMS=('API20L','API20L_b');E_ARMS=('API16E20','API16E');ALL_ARMS=T_ARMS+E_ARMS
ARMS_OF={'scale20t':('API20L','API20L_b','API16E20'),'compat20t':('API20L','API16E')}
WORKERS=8;WORKERS_S=4;WORKERS_C=4;HARD_KILL_S=900.0
STOP_RULE='conflict-only (no hook; 900 s case kill as safety net)'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze','Checkpoint',
         'repair_torn_tail','wilson','C50','B16','C20','B20','CAPS_OF','BOUND_OF','T_ARMS','E_ARMS','ALL_ARMS','ARMS_OF','WORKERS',
         'WORKERS_S','WORKERS_C','HARD_KILL_S','STOP_RULE','caps_for','HYP_ROUNDS']


def caps_for(key):return CAPS_OF[key]


def check_freeze():
    """The study-025 to 055 source freezes (via the frozen 055 check) and the study-056 source freeze."""
    check_freeze_055()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-056 plan changed after source freeze')
    check(frozen['caps']=={k:list(v) for k,v in CAPS_OF.items()},'study-056 caps differ from the freeze')
    check(frozen['bounds']==BOUND_OF and frozen['arms']=={k:list(v) for k,v in ARMS_OF.items()},'study-056 bounds or arms differ from the freeze')
    check(frozen['workers']=={'total':WORKERS,'scale20t':WORKERS_S,'compat20t':WORKERS_C},'study-056 workers differ from the freeze')
    check(frozen['stop']=={'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'study-056 stop rule differs from the freeze')
    check(frozen.get('hyp_rounds')==HYP_ROUNDS,'study-056 hypothesis rounds differ from the freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
