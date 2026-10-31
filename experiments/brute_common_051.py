"""Shared helpers for study BRUTE-0480-SCALE20-ISOLATED-SYMBREAK-NOISE12-051 (experiments/BRUTE_PLAN_051.json; pre-run deviation
#175 fixes every definition added here). New file.
The study-051 freeze hashes BRUTE_PLAN_051.json and the v0.48.0 sources; the 025-050 freezes are checked unchanged via the
frozen 050 check. Caps are fixed by the plan (design.cap_rule), not calibrated: scale20 chunk C20 12000 and B20 2000000 per case
(certify/16s); controls and part c chunk C 50000 and B12 3000000; noise12 keeps certify/16n's frozen C 50000 and B12 1500000;
max_chunks None (resume until B) for every arm. Noise: eps 0.05, eps_bar 0.10, delta 0.001, the anytime k rule (reads None).
Wall guards stay at the certify/16d defaults (30 s per chunk, 600 s per case); any firing is a gate failure.
Phases (plan design.runtime_fix): phase A runs only the scale20 jobs on 4 workers; phase B runs controls, part c and noise12 on
8 workers after phase A ends; one process."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_050 import check_freeze as check_freeze_050
from experiments.host_hook_047 import TimerHook

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_051.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_051.json'
STUDY_DIR=ROOT/'results/study-051'
C20=12000;B20=2000000;C50=50000;B12=3000000;B12N=1500000
CAPS_OF={'scale20':(C20,B20),'control':(C50,B12),'noise12':(C50,B12N)}
EPS=0.05;EPS_BAR=0.10;DELTA=0.001
NOISE_OF={'API16N':(EPS,None),'API16N_b':(EPS,None)}
S_ARMS=('API16S','API16S_b');C_ARM='API16S_c';E_ARMS=('API16E','API16E_b');N_ARMS=('API16N','API16N_b')
ALL_ARMS=S_ARMS+(C_ARM,)+E_ARMS+N_ARMS
WORKERS_A=4;WORKERS_B=8

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze','Checkpoint',
         'repair_torn_tail','wilson','TimerHook','C20','B20','C50','B12','B12N','CAPS_OF','EPS','EPS_BAR','DELTA','NOISE_OF','S_ARMS',
         'C_ARM','E_ARMS','N_ARMS','ALL_ARMS','WORKERS_A','WORKERS_B','caps_for']


def caps_for(key):return CAPS_OF[key]


def check_freeze():
    """The study-025 to 050 source freezes (via the frozen 050 check) and the study-051 source freeze."""
    check_freeze_050()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-051 plan changed after source freeze')
    check(frozen['caps']=={k:list(v) for k,v in CAPS_OF.items()},'study-051 caps differ from the freeze')
    check(frozen['noise']=={'eps':EPS,'eps_bar':EPS_BAR,'delta':DELTA,'arms':{k:list(v) for k,v in NOISE_OF.items()}},'study-051 noise settings differ from the freeze')
    check(frozen['workers']=={'A':WORKERS_A,'B':WORKERS_B},'study-051 phase workers differ from the freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
