"""Shared helpers for study BRUTE-0310-SOUND-ACTIVE-ID-034 (experiments/BRUTE_PLAN_034.json; no amendment; deviation
#140 fixes every definition added here). New file.
The study-034 freeze hashes BRUTE_PLAN_034.json and the v0.31.0 sources; the 025-033 freezes are checked unchanged."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_033 import check_freeze as check_freeze_033

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_034.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_034.json'
STUDY_DIR=ROOT/'results/study-034'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson']


def check_freeze():
    """The study-025 to 033 source freezes (unchanged files, via the frozen 033 check) and the study-034 source freeze."""
    check_freeze_033()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-034 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
