"""Shared helpers for study BRUTE-0410-A16-LOWOBS-AUDIT-044 (experiments/BRUTE_PLAN_044.json; pre-run deviation #161 fixes every
definition added here). New file.
The study-044 freeze hashes BRUTE_PLAN_044.json and the v0.41.0 sources; the 025-043 freezes are checked unchanged via the
frozen 043 check. The host-side hard cap is experiments.solver_proxy_041 (HardHook + one SolverServer child per job), unchanged."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_041 import sealed_cases,final_trace
from experiments.brute_common_043 import check_freeze as check_freeze_043
from experiments.solver_proxy_041 import HardHook,SolverServer,HARD_GRACE

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_044.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_044.json'
STUDY_DIR=ROOT/'results/study-044'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson','HardHook','SolverServer','HARD_GRACE','sealed_cases','final_trace']


def check_freeze():
    """The study-025 to 043 source freezes (via the frozen 043 check) and the study-044 source freeze."""
    check_freeze_043()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-044 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
