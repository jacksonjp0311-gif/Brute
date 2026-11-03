"""Shared helpers for study BRUTE-0630-SEQNOISE24-066 (experiments/BRUTE_PLAN_066.json; the pre-run deviation #206 fixes every
definition added here). New file; built from experiments/brute_common_065.py (frozen). The study-066 freeze hashes
BRUTE_PLAN_066.json and the v0.63.0 study sources; the 025-065 freezes are checked unchanged via the frozen 065 check.
Caps fixed by the plan (design.caps): C 50000, B 8000000, K 400, read_bits 2, node cap 200000, max_chunks None, every arm.
Arms (plan design.arms):
  C20  frozen certify/20p, noise-free, N 20, scale20;
  S30  frozen certify/20s, eps 0.30, eps_bar 0.35, delta 0.001, N 20, scale20 (gated headline at 20);
  C24  frozen certify/32p, noise-free, N 24, scale24;
  S24  certify/32s, eps 0.30, eps_bar 0.35, delta 0.001, N 24, scale24;
  S30b S30 again on the first scale20 seed (determinism).
Stop rule: conflict-only inside a job (in-process 1800 s case guard unchanged as a safety net); runner-level JOB_KILL_S 600 s per job
(one process per job, SIGKILL, KILL record). At most WORKERS jobs alive."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_065 import check_freeze as check_freeze_065

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_066.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_066.json'
STUDY_DIR=ROOT/'results/study-066'
C66=50000;B66=8000000;K66=400;READ_BITS=2;NODE_CAP=200000;DELTA=0.001
ARM_NOISE={'C20':[0.0,None],'S30':[0.30,0.35],'C24':[0.0,None],'S24':[0.30,0.35],'S30b':[0.30,0.35]}
ARM_KEY={'C20':'scale20','S30':'scale20','S30b':'scale20','C24':'scale24','S24':'scale24'}
ARM_BOUND={'C20':20,'S30':20,'S30b':20,'C24':24,'S24':24}
CONTROL={'S30':'C20','S30b':'C20','S24':'C24'}
ALL_ARMS=('C24','S24','C20','S30','S30b');NOISY=('S30','S24','S30b')
WORKERS=7;HARD_KILL_S=1800.0;GUARD_CALL_S=30.0;JOB_KILL_S=600.0;POLL_S=0.5;MAIN_CAP_S=2400.0
STOP_RULE='conflict-only (no hook; 1800 s in-process case guard as safety net; runner SIGKILL at 600 s wall per job -> KILL record)'
NOISE_RNG='random.Random(seed*13+650+int(round(1000*eps))); order (t, read, bit); one random() per bit; flip iff draw < eps'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson','C66','B66','K66','READ_BITS','NODE_CAP','DELTA','ARM_NOISE','ARM_KEY','ARM_BOUND',
         'CONTROL','ALL_ARMS','NOISY','WORKERS','HARD_KILL_S','GUARD_CALL_S','JOB_KILL_S','POLL_S','MAIN_CAP_S','STOP_RULE','NOISE_RNG']


def check_freeze():
    """The study-025 to 065 source freezes (via the frozen 065 check) and the study-066 source freeze."""
    check_freeze_065()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-066 plan changed after source freeze')
    check(frozen['caps']==[C66,B66,K66] and frozen['read_bits']==READ_BITS and frozen['arms']==list(ALL_ARMS),'study-066 caps or arms differ from the freeze')
    check(frozen['node_cap']==NODE_CAP and frozen['arm_bound']==ARM_BOUND and frozen['delta']==DELTA,'study-066 node cap, bounds or delta differ from the freeze')
    check(frozen['workers']==WORKERS and frozen['arm_noise']==ARM_NOISE and frozen['noise_rng']==NOISE_RNG and frozen['arm_key']==ARM_KEY,'study-066 workers, arm noise, keys or rng differ from the freeze')
    check(frozen['stop']=={'hard_kill_s':HARD_KILL_S,'job_kill_s':JOB_KILL_S,'stop_rule':STOP_RULE,'main_cap_s':MAIN_CAP_S},'study-066 stop rule differs')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
