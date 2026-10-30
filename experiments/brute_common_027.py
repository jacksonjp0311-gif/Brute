"""Shared helpers for study BRUTE-0240-SCALE-REPLAY-027 (experiments/BRUTE_PLAN_027.json; deviation #126). New file.
The study-027 freeze hashes BRUTE_PLAN_027.json and the v0.24.0 sources; the 025 and 026 freezes are checked unchanged."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson,FREEZE as FREEZE_026,FREEZE_025

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_027.json'
PLAN_026=ROOT/'experiments/BRUTE_PLAN_026.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_027.json'
STUDY_DIR=ROOT/'results/study-027'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze','Checkpoint',
         'repair_torn_tail','wilson']


def check_freeze():
    """The study-025 and study-026 source freezes (unchanged files) and the study-027 source freeze."""
    for f in (FREEZE_025,FREEZE_026,FREEZE):
        check(f.exists(),f.name+' missing');frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN),'study-027 plan changed after source freeze')
        if f==FREEZE_026:check(frozen['plan_sha256']==sha(PLAN_026),'study-026 plan changed')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
