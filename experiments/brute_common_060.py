"""Shared helpers for study BRUTE-0570-SCALE24W-060 (experiments/BRUTE_PLAN_060.json; pre-run deviation #194 fixes every
definition added here). New file; built from experiments/brute_common_059.py (frozen). The study-060 freeze hashes
BRUTE_PLAN_060.json and the v0.57.0 study sources; the 025-059 freezes are checked unchanged via the frozen 059 check.
Caps are fixed by the plan (design.caps): C 50000, B 8000000, K 400, read_bits 4, max_chunks None, every arm.
Arms: S24 (key scale24w, family scale24r4, bound 24; gated), S24b (S24 again, reversed seed order; determinism),
S32 (key scale32w, family scale32r4, bound 32; soundness gated, decisions reported only). All through certify/32b.
Stop rule: conflict-only (no host hook; 3600 s case guard as a safety net; a firing in S24 or S24b fails GDET60).
Workers: one 8-worker pool, max_tasks_per_child=1."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_059 import check_freeze as check_freeze_059

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_060.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_060.json'
STUDY_DIR=ROOT/'results/study-060'
C60=50000;B60=8000000;K60=400;READ_BITS=4
ARM_SPEC={'S24':['scale24w','scale24r4',24],'S24b':['scale24w','scale24r4',24],'S32':['scale32w','scale32r4',32]}
ALL_ARMS=('S24','S24b','S32');GATED_DECISION=('S24',);KEYS=('scale24w','scale32w')
WORKERS=8;HARD_KILL_S=3600.0;GUARD_CALL_S=30.0
STOP_RULE='conflict-only (no hook; 3600 s case kill as safety net)'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze','Checkpoint',
         'repair_torn_tail','wilson','C60','B60','K60','READ_BITS','ARM_SPEC','ALL_ARMS','GATED_DECISION','KEYS','WORKERS','HARD_KILL_S',
         'GUARD_CALL_S','STOP_RULE']


def check_freeze():
    """The study-025 to 059 source freezes (via the frozen 059 check) and the study-060 source freeze."""
    check_freeze_059()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-060 plan changed after source freeze')
    check(frozen['caps']==[C60,B60,K60] and frozen['read_bits']==READ_BITS and frozen['arms']==list(ALL_ARMS),'study-060 caps or arms differ from the freeze')
    check(frozen['workers']==WORKERS and frozen['arm_spec']==ARM_SPEC,'study-060 workers or arm spec differ from the freeze')
    check(frozen['stop']=={'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'study-060 stop rule differs')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
