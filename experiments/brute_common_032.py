"""Shared helpers for study BRUTE-0290-ROBUST-PERCEPTION-032 (experiments/BRUTE_PLAN_032.json; no amendment; deviation
#136 fixes every definition added here). New file.
The study-032 freeze hashes BRUTE_PLAN_032.json and the v0.29.0 sources; the 025-031 freezes are checked unchanged."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_031 import check_freeze as check_freeze_031

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_032.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_032.json'
STUDY_DIR=ROOT/'results/study-032'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson']


def check_freeze():
    """The study-025 to 031 source freezes (unchanged files, via the frozen 031 check) and the study-032 source freeze."""
    check_freeze_031()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-032 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
