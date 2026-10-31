"""Shared helpers for study BRUTE-0470-SCALE20-REPLICATION-NOISE12-050 (experiments/BRUTE_PLAN_050.json; pre-run deviation #173
fixes every definition added here). New file.
The study-050 freeze hashes BRUTE_PLAN_050.json and the v0.47.0 sources; the 025-049 freezes are checked unchanged via the
frozen 049 check. Caps are fixed by the plan (design.cap_rule), not calibrated: chunk C 50000; B20 4000000 per scale20 case;
B12 1500000 per control (clean scale12) and noise12 case; max_chunks None (resume until B) for every arm. Noise (plan
design.parts.n): eps 0.05 (the world's flip rate), eps_bar 0.10 and delta 0.001 (the certify/16n declaration), reads None (the
anytime k rule) for API16N / API16N_b; eps 0 and reads 1 for API16N_c (part c compatibility). The wall guard stays at the
certify/16d defaults (30 s per chunk, 600 s per case)."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_049 import check_freeze as check_freeze_049
from experiments.host_hook_047 import TimerHook

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_050.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_050.json'
STUDY_DIR=ROOT/'results/study-050'
C50=50000;B20=4000000;B12=1500000
BUDGET_OF={'scale20':B20,'control':B12,'noise12':B12}
EPS=0.05;EPS_BAR=0.10;DELTA=0.001
NOISE_OF={'API16N':(EPS,None),'API16N_b':(EPS,None),'API16N_c':(0.0,1)}
E_ARMS=('API16E','API16E_b');N_ARMS=('API16N','API16N_b','API16N_c');ALL_ARMS=E_ARMS+N_ARMS

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze','Checkpoint',
         'repair_torn_tail','wilson','TimerHook','C50','B20','B12','BUDGET_OF','EPS','EPS_BAR','DELTA','NOISE_OF','E_ARMS','N_ARMS',
         'ALL_ARMS','budget_for']


def budget_for(key):return BUDGET_OF[key]


def check_freeze():
    """The study-025 to 049 source freezes (via the frozen 049 check) and the study-050 source freeze."""
    check_freeze_049()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-050 plan changed after source freeze')
    check((frozen['conflict_cap'],frozen['budget_conflicts'])==(C50,dict(BUDGET_OF)),'study-050 caps differ from the freeze')
    check(frozen['noise']=={'eps':EPS,'eps_bar':EPS_BAR,'delta':DELTA,'arms':{k:list(v) for k,v in NOISE_OF.items()}},'study-050 noise settings differ from the freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
