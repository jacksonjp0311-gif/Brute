"""Shared helpers for study BRUTE-0280-SIXTEEN-STATE-ID-031 (experiments/BRUTE_PLAN_031.json; no amendment; deviation #134
fixes every definition added here). New file.
The study-031 freeze hashes BRUTE_PLAN_031.json and the v0.28.0 sources; the 025-030 freezes are checked unchanged."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_030 import check_freeze as check_freeze_030,FREEZE as FREEZE_030,PLAN as PLAN_030

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_031.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_031.json'
STUDY_DIR=ROOT/'results/study-031'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson']


def check_freeze():
    """The study-025 to 030 source freezes (unchanged files, via the frozen 030 check) and the study-031 source freeze."""
    check_freeze_030()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-031 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
