"""Shared helpers for study BRUTE-0560-NOISYWIDE-059 (experiments/BRUTE_PLAN_059.json; pre-run deviation #192 fixes every
definition added here). New file; built from experiments/brute_common_058.py (frozen). The study-059 freeze hashes
BRUTE_PLAN_059.json and the v0.56.0 study sources; the 025-058 freezes are checked unchanged via the frozen 058 check.
Caps are fixed by the plan (design.caps): C 50000, B 2000000, K 400, family_bound 20, max_chunks None, every arm.
Arms (eps, eps_bar): C4 (0, None: certify/20b), N4_05 (0.05, 0.10), N4_10 (0.10, 0.15), N4_10b (0.10, 0.15), NEG4 (0.25, 0.10);
delta 0.001 in every certify/20n arm. Stop rule: conflict-only (no host hook; 900 s case guard as a safety net; any firing fails
GDET59). Workers: one 8-worker pool, max_tasks_per_child=1."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_058 import check_freeze as check_freeze_058
from experiments import worlds_059 as W59

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_059.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_059.json'
STUDY_DIR=ROOT/'results/study-059'
C59=50000;B59=2000000;K59=400;BOUND=20;KEY='scale20n';DELTA=0.001;READ_BITS=4
ARM_NOISE={'C4':[0.0,None],'N4_05':[0.05,0.10],'N4_10':[0.10,0.15],'N4_10b':[0.10,0.15],'NEG4':[0.25,0.10]}
ALL_ARMS=('C4','N4_05','N4_10','N4_10b','NEG4');GATED_ARMS=('C4','N4_05','N4_10','N4_10b');NOISY_GATED=('N4_05','N4_10','N4_10b')
WORKERS=8;HARD_KILL_S=900.0;GUARD_CALL_S=30.0
STOP_RULE='conflict-only (no hook; 900 s case kill as safety net)'
NOISE_RNG=W59.NOISE_RNG

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze','Checkpoint',
         'repair_torn_tail','wilson','C59','B59','K59','BOUND','KEY','DELTA','READ_BITS','ARM_NOISE','ALL_ARMS','GATED_ARMS','NOISY_GATED',
         'WORKERS','HARD_KILL_S','GUARD_CALL_S','STOP_RULE','NOISE_RNG']


def check_freeze():
    """The study-025 to 058 source freezes (via the frozen 058 check) and the study-059 source freeze."""
    check_freeze_058()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-059 plan changed after source freeze')
    check(frozen['caps']==[C59,B59,K59] and frozen['bound']==BOUND and frozen['arms']==list(ALL_ARMS),'study-059 caps, bound or arms differ from the freeze')
    check(frozen['workers']==WORKERS and frozen['arm_noise']==ARM_NOISE and frozen['delta']==DELTA,'study-059 workers, noise or delta differ from the freeze')
    check(frozen['stop']=={'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE} and frozen['noise_rng']==NOISE_RNG,'study-059 stop rule or RNG differs')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
