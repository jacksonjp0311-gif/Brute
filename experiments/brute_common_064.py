"""Shared helpers for study BRUTE-0610-SCALE2B24-064 (experiments/BRUTE_PLAN_064.json; the pre-run deviation fixes every
definition added here). New file; built from experiments/brute_common_063.py (frozen). The study-064 freeze hashes
BRUTE_PLAN_064.json and the v0.61.0 study sources; the 025-063 freezes are checked unchanged via the frozen 063 check.
Caps are fixed by the plan text (results/diag-064/CAPABILITY_PROBE_064.json, sha256 frozen): C 50000, B 8000000, K 400,
read_bits 2, node cap 200000, max_chunks None, every arm. Arms (plan design.arms):
  P24  certify/32p at declared N 24 on worlds_064 'scale24' (gated headline);
  B24  frozen certify/32b at declared N 24, 'scale24', first N_B24 seeds (reported time-capped control, not gated);
  P20  frozen certify/20p at declared N 20 on worlds_064 'scale20' (gated replication);
  P20b P20 again on the first N_P20B seeds, reversed order (determinism).
Stop rule: conflict-only (no host hook; HARD_KILL_S case guard as a safety net; a firing in P24, P20 or P20b fails GDET64;
in B24 it ends the record before 8M, disclosed). Workers: one 6-worker pool, max_tasks_per_child=1."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_063 import check_freeze as check_freeze_063

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_064.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_064.json'
STUDY_DIR=ROOT/'results/study-064'
PROBE=ROOT/'results/diag-064/CAPABILITY_PROBE_064.json'
REFDIAG=ROOT/'results/diag-064/REF_PIN_DIAG_064.json'
C64=50000;B64=8000000;K64=400;READ_BITS=2;NODE_CAP=200000
ARM_SPEC={'P24':['scale24p','scale24',24,'certify32p'],'B24':['scale24p','scale24',24,'certify32b'],
          'P20':['scale20p','scale20',20,'certify20p'],'P20b':['scale20p','scale20',20,'certify20p']}
ALL_ARMS=('P24','B24','P20','P20b');GATED_DECISION=('P24','P20');KEYS=('scale20p','scale24p')
WORKERS=6;HARD_KILL_S=1800.0;GUARD_CALL_S=30.0;MAIN_CAP_S=2400.0
STOP_RULE='conflict-only (no hook; 1800 s case kill as safety net)'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','PROBE','REFDIAG','check_freeze',
         'Checkpoint','repair_torn_tail','wilson','C64','B64','K64','READ_BITS','NODE_CAP','ARM_SPEC','ALL_ARMS','GATED_DECISION',
         'KEYS','WORKERS','HARD_KILL_S','GUARD_CALL_S','MAIN_CAP_S','STOP_RULE']


def check_freeze():
    """The study-025 to 063 source freezes (via the frozen 063 check) and the study-064 source freeze."""
    check_freeze_063()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-064 plan changed after source freeze')
    check(frozen['caps']==[C64,B64,K64] and frozen['read_bits']==READ_BITS and frozen['arms']==list(ALL_ARMS),'study-064 caps or arms differ from the freeze')
    check(frozen['node_cap']==NODE_CAP,'study-064 node cap differs from the freeze')
    check(frozen['workers']==WORKERS and frozen['arm_spec']==ARM_SPEC,'study-064 workers or arm spec differ from the freeze')
    check(frozen['stop']=={'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE,'main_cap_s':MAIN_CAP_S},'study-064 stop rule differs')
    check(frozen['probe_sha256']==sha(PROBE) and frozen['refdiag_sha256']==sha(REFDIAG),'study-064 probe or reference diagnostic changed after the freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
