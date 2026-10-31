"""Shared helpers for study BRUTE-0490-CERTIFY16N-NOISE12-052 (experiments/BRUTE_PLAN_052.json; pre-run deviation #177 fixes
every definition added here). New file.
The study-052 freeze hashes BRUTE_PLAN_052.json and the v0.49.0 study sources; the 025-051 freezes are checked unchanged via the
frozen 051 check. Caps are fixed by the plan (design.caps), not calibrated: noise12 and noise12_bar keep certify/16n's C 50000 and
B12N 1500000; the compat controls (both arms) use C 50000 and B12 3000000; max_chunks None (resume until B) for every arm.
Noise: API16N / API16N_b at eps 0.05 and API16N_bar at eps 0.10, all with eps_bar 0.10, delta 0.001 and the anytime k rule
(reads None); API16N_c at eps 0 with reads 1 (the 050 part c eps-0 path). Wall guards stay at the certify/16d defaults (30 s
per chunk, 600 s per case); any firing is a gate failure. One phase on 8 workers; one process. No new API."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_051 import check_freeze as check_freeze_051
from experiments.host_hook_047 import TimerHook

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_052.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_052.json'
STUDY_DIR=ROOT/'results/study-052'
C50=50000;B12=3000000;B12N=1500000
CAPS_OF={'noise12':(C50,B12N),'noise12_bar':(C50,B12N),'compat':(C50,B12)}
EPS=0.05;EPS_HI=0.10;EPS_BAR=0.10;DELTA=0.001
NOISE_OF={'API16N':(EPS,None),'API16N_b':(EPS,None),'API16N_bar':(EPS_HI,None),'API16N_c':(0.0,1)}
E_ARMS=('API16E',);N_ARMS=('API16N','API16N_b','API16N_bar','API16N_c');ALL_ARMS=N_ARMS+E_ARMS
WORKERS=8

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze','Checkpoint',
         'repair_torn_tail','wilson','TimerHook','C50','B12','B12N','CAPS_OF','EPS','EPS_HI','EPS_BAR','DELTA','NOISE_OF','E_ARMS',
         'N_ARMS','ALL_ARMS','WORKERS','caps_for']


def caps_for(key):return CAPS_OF[key]


def check_freeze():
    """The study-025 to 051 source freezes (via the frozen 051 check) and the study-052 source freeze."""
    check_freeze_051()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-052 plan changed after source freeze')
    check(frozen['caps']=={k:list(v) for k,v in CAPS_OF.items()},'study-052 caps differ from the freeze')
    check(frozen['noise']=={'eps':EPS,'eps_hi':EPS_HI,'eps_bar':EPS_BAR,'delta':DELTA,'arms':{k:list(v) for k,v in NOISE_OF.items()}},'study-052 noise settings differ from the freeze')
    check(frozen['workers']==WORKERS,'study-052 workers differ from the freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
