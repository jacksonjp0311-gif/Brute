"""Shared helpers for study BRUTE-0600-ANCHOR2B20-063 (experiments/BRUTE_PLAN_063.json; pre-run deviation #200 fixes every
definition added here). New file; built from experiments/brute_common_062.py (frozen). The study-063 freeze hashes
BRUTE_PLAN_063.json and the v0.60.0 study sources; the 025-062 freezes are checked unchanged via the frozen 062 check.
Caps are fixed by the plan text and the capability probe (results/diag-063/CAPABILITY_PROBE_063.json, sha256 frozen):
C 50000, B 8000000, K 400, read_bits 2, declared bound 20, node cap 200000, max_chunks None, every arm. Arms: B2 (frozen
certify/20b, its usual policy; gated control), P2 (new certify/20p, clique-anchored pool; gated headline), P2b (P2 again on the
first N_P2B seeds, reversed order; determinism). Worlds: worlds_058 'scale20' (original 2-bit emissions), key scale20p2.
Stop rule: conflict-only (no host hook; HARD_KILL_S case guard as a safety net; a firing in P2 or P2b fails GDET63).
Workers: one 6-worker pool, max_tasks_per_child=1."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_062 import check_freeze as check_freeze_062

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_063.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_063.json'
STUDY_DIR=ROOT/'results/study-063'
PROBE=ROOT/'results/diag-063/CAPABILITY_PROBE_063.json'
C63=50000;B63=8000000;K63=400;READ_BITS=2;BOUND=20;NODE_CAP=200000;KEY='scale20p2';FAMILY='scale20'
ARM_SPEC={'B2':['scale20p2','scale20',20,'certify20b'],'P2':['scale20p2','scale20',20,'certify20p'],'P2b':['scale20p2','scale20',20,'certify20p']}
ALL_ARMS=('B2','P2','P2b');GATED_DECISION=('P2','B2');KEYS=('scale20p2',)
WORKERS=6;HARD_KILL_S=2400.0;GUARD_CALL_S=30.0
STOP_RULE='conflict-only (no hook; 2400 s case kill as safety net)'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','PROBE','check_freeze','Checkpoint',
         'repair_torn_tail','wilson','C63','B63','K63','READ_BITS','BOUND','NODE_CAP','KEY','FAMILY','ARM_SPEC','ALL_ARMS','GATED_DECISION',
         'KEYS','WORKERS','HARD_KILL_S','GUARD_CALL_S','STOP_RULE']


def check_freeze():
    """The study-025 to 062 source freezes (via the frozen 062 check) and the study-063 source freeze."""
    check_freeze_062()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-063 plan changed after source freeze')
    check(frozen['caps']==[C63,B63,K63] and frozen['read_bits']==READ_BITS and frozen['arms']==list(ALL_ARMS),'study-063 caps or arms differ from the freeze')
    check(frozen['node_cap']==NODE_CAP and frozen['bound']==BOUND,'study-063 node cap or bound differs from the freeze')
    check(frozen['workers']==WORKERS and frozen['arm_spec']==ARM_SPEC,'study-063 workers or arm spec differ from the freeze')
    check(frozen['stop']=={'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'study-063 stop rule differs')
    check(frozen['probe_sha256']==sha(PROBE),'study-063 capability probe changed after the freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
