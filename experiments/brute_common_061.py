"""Shared helpers for study BRUTE-0580-BUDGET24W-061 (experiments/BRUTE_PLAN_061.json; pre-run deviation #196 fixes every
definition added here). New file; built from experiments/brute_common_060.py (frozen). The study-061 freeze hashes
BRUTE_PLAN_061.json and the v0.58.0 study sources; the 025-060 freezes are checked unchanged via the frozen 060 check.
Caps are fixed by the plan (design.caps) and the budget probe (budget_probe_061): C 50000, B = B61, K 400, read_bits 4,
max_chunks None, every arm. Arms: S24 (key scale24w, family scale24r4, bound 24; gated), S24b (S24 again on the first N24B seeds,
reversed order; determinism), S32 (key scale32w, family scale32r4, bound 32; soundness gated, decisions reported only).
All through the frozen certify/32b (v0.57.0); no new API.
Stop rule: conflict-only (no host hook; HARD_KILL_S case guard as a safety net; a firing in S24 or S24b fails GDET61).
Workers: one 8-worker pool, max_tasks_per_child=1."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_060 import check_freeze as check_freeze_060

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_061.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_061.json'
STUDY_DIR=ROOT/'results/study-061'
PROBE=ROOT/'results/diag-061/BUDGET_PROBE_061.json'
C61=50000;B61=24000000;K61=400;READ_BITS=4
ARM_SPEC={'S24':['scale24w','scale24r4',24],'S24b':['scale24w','scale24r4',24],'S32':['scale32w','scale32r4',32]}
ALL_ARMS=('S24','S24b','S32');GATED_DECISION=('S24',);KEYS=('scale24w','scale32w')
WORKERS=8;HARD_KILL_S=3000;GUARD_CALL_S=30.0
STOP_RULE='conflict-only (no hook; 3000 s case kill as safety net)'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','PROBE','check_freeze','Checkpoint',
         'repair_torn_tail','wilson','C61','B61','K61','READ_BITS','ARM_SPEC','ALL_ARMS','GATED_DECISION','KEYS','WORKERS','HARD_KILL_S',
         'GUARD_CALL_S','STOP_RULE']


def check_freeze():
    """The study-025 to 060 source freezes (via the frozen 060 check) and the study-061 source freeze."""
    check_freeze_060()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-061 plan changed after source freeze')
    check(frozen['caps']==[C61,B61,K61] and frozen['read_bits']==READ_BITS and frozen['arms']==list(ALL_ARMS),'study-061 caps or arms differ from the freeze')
    check(frozen['workers']==WORKERS and frozen['arm_spec']==ARM_SPEC,'study-061 workers or arm spec differ from the freeze')
    check(frozen['stop']=={'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'study-061 stop rule differs')
    check(frozen['probe_sha256']==sha(PROBE) and load(PROBE)['B61']==B61,'study-061 B61 differs from the ledgered budget probe')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
