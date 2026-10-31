"""Shared helpers for study BRUTE-0500-NOISE16-SCALE20-CONFLICTSTOP-053 (experiments/BRUTE_PLAN_053.json; pre-run deviation #179
fixes every definition added here). New file.
The study-053 freeze hashes BRUTE_PLAN_053.json and the v0.50.0 study sources; the 025-052 freezes are checked unchanged via the
frozen 052 check. Caps are fixed by the plan (design.caps), not calibrated:
  part A: noise16 and noise16_bar C 50000, B16N 1500000; compat16 (both arms) C 50000, B16 3000000; family_bound 16;
          wall guards at the certify/16d defaults (30 s per chunk via the host hook, 600 s per case); any firing is a gate failure;
  part B: scale20c C20 50000, B20 2000000, family_bound 20, conflict-only stop: no host hook is passed (no per-chunk wall
          interrupt; the solver runs every chunk to its conflict count), and the API's case guard is set to the plan's 900 s hard
          job kill (safety net only; any firing fails GS20C_det53).
Noise (part A): API16N16 / API16N16_b at eps 0.05 and API16N16_bar at eps 0.10, all with eps_bar 0.10, delta 0.001 and the
anytime k rule (reads None); API16N16_c at eps 0 with reads 1 (the 050 part c eps-0 path). The plan names the noise16_bar and
compat16 arm 'API16N16'; distinct record names are used so every (eps, reads) setting is fixed per arm (#179).
Workers: 8 = 1 dedicated serial worker for part B + 7 for part A, concurrent in one phase, one process. No new API."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_052 import check_freeze as check_freeze_052
from experiments.host_hook_047 import TimerHook

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_053.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_053.json'
STUDY_DIR=ROOT/'results/study-053'
C50=50000;B16=3000000;B16N=1500000;C20=50000;B20=2000000
CAPS_OF={'noise16':(C50,B16N),'noise16_bar':(C50,B16N),'compat16':(C50,B16),'scale20c':(C20,B20)}
EPS=0.05;EPS_HI=0.10;EPS_BAR=0.10;DELTA=0.001
NOISE_OF={'API16N16':(EPS,None),'API16N16_b':(EPS,None),'API16N16_bar':(EPS_HI,None),'API16N16_c':(0.0,1)}
B_ARMS=('API16E20','API16E20_b');E_ARMS=('API16E',)+B_ARMS
N_ARMS=('API16N16','API16N16_b','API16N16_bar','API16N16_c');ALL_ARMS=N_ARMS+E_ARMS
WORKERS=8;WORKERS_A=7;WORKERS_B=1
PART_B_KEYS=('scale20c',);HARD_KILL_B_S=900.0;STOP_RULE={'A':'conflict budget + wall guards (30 s chunk hook, 600 s case)','B':'conflict-only (no hook; 900 s case kill as safety net)'}

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze','Checkpoint',
         'repair_torn_tail','wilson','TimerHook','C50','B16','B16N','C20','B20','CAPS_OF','EPS','EPS_HI','EPS_BAR','DELTA','NOISE_OF',
         'E_ARMS','B_ARMS','N_ARMS','ALL_ARMS','WORKERS','WORKERS_A','WORKERS_B','PART_B_KEYS','HARD_KILL_B_S','STOP_RULE','caps_for']


def caps_for(key):return CAPS_OF[key]


def check_freeze():
    """The study-025 to 052 source freezes (via the frozen 052 check) and the study-053 source freeze."""
    check_freeze_052()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-053 plan changed after source freeze')
    check(frozen['caps']=={k:list(v) for k,v in CAPS_OF.items()},'study-053 caps differ from the freeze')
    check(frozen['noise']=={'eps':EPS,'eps_hi':EPS_HI,'eps_bar':EPS_BAR,'delta':DELTA,'arms':{k:list(v) for k,v in NOISE_OF.items()}},'study-053 noise settings differ from the freeze')
    check(frozen['workers']=={'total':WORKERS,'A':WORKERS_A,'B':WORKERS_B},'study-053 workers differ from the freeze')
    check(frozen['part_b']=={'keys':list(PART_B_KEYS),'hard_kill_s':HARD_KILL_B_S,'stop_rule':STOP_RULE['B']},'study-053 part B stop rule differs from the freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
