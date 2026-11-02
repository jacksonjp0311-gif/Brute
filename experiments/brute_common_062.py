"""Shared helpers for study BRUTE-0590-WINDOW2B20-062 (experiments/BRUTE_PLAN_062.json; pre-run deviation #198 fixes every
definition added here). New file; built from experiments/brute_common_061.py (frozen). The study-062 freeze hashes
BRUTE_PLAN_062.json and the v0.59.0 study sources; the 025-061 freezes are checked unchanged via the frozen 061 check.
Caps are fixed by the plan (design.caps) and the budget probe (budget_probe_062): C 50000, B = B62, K 400 (window actions
counted), read_bits 2, declared bound 20, max_chunks None, every arm. Arms: B2 (frozen certify/20b, its usual policy; gated
control), W2 (new certify/20w, probe word (0, 1); gated headline), W2b (W2 again on the first N_W2B seeds, reversed order;
determinism). Worlds: worlds_058 'scale20' (original 2-bit emissions), key scale20w2.
Stop rule: conflict-only (no host hook; HARD_KILL_S case guard as a safety net; a firing in W2 or W2b fails GDET62).
Workers: one 8-worker pool, max_tasks_per_child=1."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_061 import check_freeze as check_freeze_061

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_062.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_062.json'
STUDY_DIR=ROOT/'results/study-062'
PROBE=ROOT/'results/diag-062/BUDGET_PROBE_062.json'
C62=50000;B62=8000000;K62=400;READ_BITS=2;BOUND=20;PROBE_WORD=(0,1);KEY='scale20w2';FAMILY='scale20'
ARM_SPEC={'B2':['scale20w2','scale20',20,'certify20b'],'W2':['scale20w2','scale20',20,'certify20w'],'W2b':['scale20w2','scale20',20,'certify20w']}
ALL_ARMS=('B2','W2','W2b');GATED_DECISION=('W2','B2');KEYS=('scale20w2',)
WORKERS=8;HARD_KILL_S=3000.0;GUARD_CALL_S=30.0
STOP_RULE='conflict-only (no hook; 3000 s case kill as safety net)'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','PROBE','check_freeze','Checkpoint',
         'repair_torn_tail','wilson','C62','B62','K62','READ_BITS','BOUND','PROBE_WORD','KEY','FAMILY','ARM_SPEC','ALL_ARMS','GATED_DECISION',
         'KEYS','WORKERS','HARD_KILL_S','GUARD_CALL_S','STOP_RULE']


def check_freeze():
    """The study-025 to 061 source freezes (via the frozen 061 check) and the study-062 source freeze."""
    check_freeze_061()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-062 plan changed after source freeze')
    check(frozen['caps']==[C62,B62,K62] and frozen['read_bits']==READ_BITS and frozen['arms']==list(ALL_ARMS),'study-062 caps or arms differ from the freeze')
    check(frozen['probe_word']==list(PROBE_WORD) and frozen['bound']==BOUND,'study-062 probe word or bound differs from the freeze')
    check(frozen['workers']==WORKERS and frozen['arm_spec']==ARM_SPEC,'study-062 workers or arm spec differ from the freeze')
    check(frozen['stop']=={'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'study-062 stop rule differs')
    check(frozen['probe_sha256']==sha(PROBE) and load(PROBE)['B62']==B62,'study-062 B62 differs from the ledgered budget probe')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
