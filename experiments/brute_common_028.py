"""Shared helpers for study BRUTE-0250-SOLVER-COST-028 (experiments/BRUTE_PLAN_028.json; deviation #128). New file.
The study-028 freeze hashes BRUTE_PLAN_028.json and the v0.25.0 sources; the 025, 026 and 027 freezes are checked unchanged."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson,FREEZE as FREEZE_026,FREEZE_025
from experiments.brute_common_027 import FREEZE as FREEZE_027,PLAN as PLAN_027

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_028.json'
PLAN_026=ROOT/'experiments/BRUTE_PLAN_026.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_028.json'
STUDY_DIR=ROOT/'results/study-028'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze','Checkpoint',
         'repair_torn_tail','wilson']


def check_freeze():
    """The study-025, 026 and 027 source freezes (unchanged files) and the study-028 source freeze."""
    for f in (FREEZE_025,FREEZE_026,FREEZE_027,FREEZE):
        check(f.exists(),f.name+' missing');frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN),'study-028 plan changed after source freeze')
        if f==FREEZE_026:check(frozen['plan_sha256']==sha(PLAN_026),'study-026 plan changed')
        if f==FREEZE_027:check(frozen['plan_sha256']==sha(PLAN_027),'study-027 plan changed')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
