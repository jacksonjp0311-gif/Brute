"""Shared helpers for study BRUTE-0550-READBITS-058 (experiments/BRUTE_PLAN_058.json; pre-run deviation #190 fixes every
definition added here). New file; built from experiments/brute_common_057.py (frozen). The study-058 freeze hashes
BRUTE_PLAN_058.json and the v0.55.0 study sources; the 025-057 freezes are checked unchanged via the frozen 057 check.
Caps are fixed by the plan (design.caps): C 50000, B 2000000, K 400, family_bound 20, max_chunks None, every arm.
Stop rule: conflict-only (no host hook; the certify/20b case guard is the plan's 900 s hard kill, a safety net only; any firing
fails GDET58). Workers: one 8-worker pool, max_tasks_per_child=1."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_057 import check_freeze as check_freeze_057
from experiments import worlds_058 as W58

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_058.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_058.json'
STUDY_DIR=ROOT/'results/study-058'
C58=50000;B58=2000000;K58=400;BOUND=20;KEY='scale20b'
ARM_FAMILY={'B2':'scale20','B2R':'scale20r2','B3':'scale20r3','B4':'scale20r4','B4_b':'scale20r4'}
ALL_ARMS=('B2','B2R','B3','B4','B4_b')
WORKERS=8;HARD_KILL_S=900.0;GUARD_CALL_S=30.0
STOP_RULE='conflict-only (no hook; 900 s case kill as safety net)'
EMISSION_RNG=W58.EMISSION_RNG

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze','Checkpoint',
         'repair_torn_tail','wilson','C58','B58','K58','BOUND','KEY','ARM_FAMILY','ALL_ARMS','WORKERS','HARD_KILL_S','GUARD_CALL_S',
         'STOP_RULE','EMISSION_RNG']


def check_freeze():
    """The study-025 to 057 source freezes (via the frozen 057 check) and the study-058 source freeze."""
    check_freeze_057()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-058 plan changed after source freeze')
    check(frozen['caps']==[C58,B58,K58] and frozen['bound']==BOUND and frozen['arms']==list(ALL_ARMS),'study-058 caps, bound or arms differ from the freeze')
    check(frozen['workers']==WORKERS and frozen['arm_family']==ARM_FAMILY,'study-058 workers or arm families differ from the freeze')
    check(frozen['stop']=={'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE} and frozen['emission_rng']==EMISSION_RNG,'study-058 stop rule or RNG differs')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
