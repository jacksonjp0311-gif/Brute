"""Shared helpers for study BRUTE-0390-A16-042 (experiments/BRUTE_PLAN_042.json; pre-run deviation #157 fixes every
definition added here). New file.
The study-042 freeze hashes BRUTE_PLAN_042.json and the v0.39.0 sources; the 025-041 freezes are checked unchanged via the
frozen 041 check. The host-side hard cap is experiments.solver_proxy_041 (HardHook + one SolverServer child per job), unchanged.
Sealed traces (smoke replays only): sealed study-041 part-c replays are of the sealed study-040 scale16 final A14 traces,
rebuilt with the frozen experiments.brute_common_041.final_trace."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_041 import check_freeze as check_freeze_041,sealed_cases,final_trace
from experiments.solver_proxy_041 import HardHook,SolverServer,HARD_GRACE

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_042.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_042.json'
STUDY_DIR=ROOT/'results/study-042'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson','HardHook','SolverServer','HARD_GRACE','sealed_cases','final_trace']


def check_freeze():
    """The study-025 to 041 source freezes (via the frozen 041 check) and the study-042 source freeze."""
    check_freeze_041()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-042 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
