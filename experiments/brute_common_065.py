"""Shared helpers for study BRUTE-0620-SEQNOISE2B20-065 (experiments/BRUTE_PLAN_065.json; the pre-run deviation #204 fixes every
definition added here). New file; built from experiments/brute_common_064.py (frozen). The study-065 freeze hashes
BRUTE_PLAN_065.json and the v0.62.0 study sources; the 025-064 freezes are checked unchanged via the frozen 064 check.
Caps fixed by the plan (design.caps): C 50000, B 8000000, K 400, read_bits 2, node cap 200000, max_chunks None, every arm.
Arms (plan design.arms), all on worlds_065 (worlds_064 'scale20'), declared N 20, inner solver the frozen certify/20p:
  C20  frozen certify/20p, noise-free (reference arm);
  S10  certify/20s, eps 0.10, eps_bar 0.15, delta 0.001;
  S20  certify/20s, eps 0.20, eps_bar 0.25, delta 0.001;
  S30  certify/20s, eps 0.30, eps_bar 0.35, delta 0.001 (gated headline);
  S30b S30 again on the first seed (determinism).
Stop rule: conflict-only (no host hook; HARD_KILL_S case kill as a safety net; any firing fails GDET65).
Workers: one 6-worker pool, max_tasks_per_child=1."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_064 import check_freeze as check_freeze_064

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_065.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_065.json'
STUDY_DIR=ROOT/'results/study-065'
C65=50000;B65=8000000;K65=400;READ_BITS=2;NODE_CAP=200000;BOUND=20;DELTA=0.001
ARM_NOISE={'C20':[0.0,None],'S10':[0.10,0.15],'S20':[0.20,0.25],'S30':[0.30,0.35],'S30b':[0.30,0.35]}
ALL_ARMS=('C20','S10','S20','S30','S30b');NOISY=('S10','S20','S30','S30b');KEY='scale20'
WORKERS=6;HARD_KILL_S=1800.0;GUARD_CALL_S=30.0;MAIN_CAP_S=2400.0
STOP_RULE='conflict-only (no hook; 1800 s case kill as safety net)'
NOISE_RNG='random.Random(seed*13+650+int(round(1000*eps))); order (t, read, bit); one random() per bit; flip iff draw < eps'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson','C65','B65','K65','READ_BITS','NODE_CAP','BOUND','DELTA','ARM_NOISE','ALL_ARMS','NOISY',
         'KEY','WORKERS','HARD_KILL_S','GUARD_CALL_S','MAIN_CAP_S','STOP_RULE','NOISE_RNG']


def check_freeze():
    """The study-025 to 064 source freezes (via the frozen 064 check) and the study-065 source freeze."""
    check_freeze_064()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-065 plan changed after source freeze')
    check(frozen['caps']==[C65,B65,K65] and frozen['read_bits']==READ_BITS and frozen['arms']==list(ALL_ARMS),'study-065 caps or arms differ from the freeze')
    check(frozen['node_cap']==NODE_CAP and frozen['bound']==BOUND and frozen['delta']==DELTA,'study-065 node cap, bound or delta differ from the freeze')
    check(frozen['workers']==WORKERS and frozen['arm_noise']==ARM_NOISE and frozen['noise_rng']==NOISE_RNG,'study-065 workers, arm noise or rng differ from the freeze')
    check(frozen['stop']=={'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE,'main_cap_s':MAIN_CAP_S},'study-065 stop rule differs')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
