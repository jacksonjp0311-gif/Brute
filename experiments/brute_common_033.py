"""Shared helpers for study BRUTE-0300-ACTIVE-EXPERIMENTS-033 (experiments/BRUTE_PLAN_033.json; no amendment; deviation
#138 fixes every definition added here). New file.
The study-033 freeze hashes BRUTE_PLAN_033.json and the v0.30.0 sources; the 025-032 freezes are checked unchanged."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_032 import check_freeze as check_freeze_032

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_033.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_033.json'
STUDY_DIR=ROOT/'results/study-033'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson']


def check_freeze():
    """The study-025 to 032 source freezes (unchanged files, via the frozen 032 check) and the study-033 source freeze."""
    check_freeze_032()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-033 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
