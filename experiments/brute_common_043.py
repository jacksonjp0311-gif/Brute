"""Shared helpers for study BRUTE-0400-A16-LOWOBS-043 (experiments/BRUTE_PLAN_043.json; pre-run deviation #159 fixes every
definition added here). New file.
The study-043 freeze hashes BRUTE_PLAN_043.json and the v0.40.0 sources; the 025-042 freezes are checked unchanged via the
frozen 042 check. The host-side hard cap is experiments.solver_proxy_041 (HardHook + one SolverServer child per job), unchanged.
Sealed traces (smoke replays only): sealed study-041 part-c replays are of the sealed study-040 scale16 final A14 traces,
rebuilt with the frozen experiments.brute_common_041.final_trace."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_041 import sealed_cases,final_trace
from experiments.brute_common_042 import check_freeze as check_freeze_042
from experiments.solver_proxy_041 import HardHook,SolverServer,HARD_GRACE

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_043.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_043.json'
STUDY_DIR=ROOT/'results/study-043'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson','HardHook','SolverServer','HARD_GRACE','sealed_cases','final_trace']


def check_freeze():
    """The study-025 to 042 source freezes (via the frozen 042 check) and the study-043 source freeze."""
    check_freeze_042()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-043 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
