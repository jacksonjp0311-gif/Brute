"""Shared helpers for study BRUTE-0420-A16-NFREE-STOP-045 (experiments/BRUTE_PLAN_045.json; pre-run deviation #163 fixes every
definition added here). New file.
The study-045 freeze hashes BRUTE_PLAN_045.json and the v0.42.0 sources; the 025-044 freezes are checked unchanged via the
frozen 044 check. The host-side hard cap is experiments.solver_proxy_041 (HardHook + one SolverServer child per job), unchanged."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_041 import sealed_cases,final_trace
from experiments.brute_common_044 import check_freeze as check_freeze_044
from experiments.solver_proxy_041 import HardHook,SolverServer,HARD_GRACE

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_045.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_045.json'
STUDY_DIR=ROOT/'results/study-045'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson','HardHook','SolverServer','HARD_GRACE','sealed_cases','final_trace']


def check_freeze():
    """The study-025 to 044 source freezes (via the frozen 044 check) and the study-045 source freeze."""
    check_freeze_044()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-045 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
