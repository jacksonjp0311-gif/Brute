"""Shared helpers for study BRUTE-0260-QUERY-THROUGHPUT-029 (experiments/BRUTE_PLAN_029.json as amended by
experiments/BRUTE_PLAN_029_A1.json; deviation #130). New file.
The study-029 freeze hashes BRUTE_PLAN_029.json, the A1 amendment and the v0.26.0 sources; the 025-028 freezes are
checked unchanged."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson,FREEZE as FREEZE_026,FREEZE_025
from experiments.brute_common_027 import FREEZE as FREEZE_027,PLAN as PLAN_027
from experiments.brute_common_028 import FREEZE as FREEZE_028,PLAN as PLAN_028

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_029.json'
AMENDMENT=ROOT/'experiments/BRUTE_PLAN_029_A1.json'
PLAN_026=ROOT/'experiments/BRUTE_PLAN_026.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_029.json'
STUDY_DIR=ROOT/'results/study-029'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','AMENDMENT','FREEZE','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson']


def check_freeze():
    """The study-025 to 028 source freezes (unchanged files) and the study-029 source freeze (plan and amendment)."""
    for f in (FREEZE_025,FREEZE_026,FREEZE_027,FREEZE_028,FREEZE):
        check(f.exists(),f.name+' missing');frozen=load(f)
        if f==FREEZE:
            check(frozen['plan_sha256']==sha(PLAN),'study-029 plan changed after source freeze')
            check(frozen['amendment_sha256']==sha(AMENDMENT),'study-029 amendment A1 changed after source freeze')
        if f==FREEZE_026:check(frozen['plan_sha256']==sha(PLAN_026),'study-026 plan changed')
        if f==FREEZE_027:check(frozen['plan_sha256']==sha(PLAN_027),'study-027 plan changed')
        if f==FREEZE_028:check(frozen['plan_sha256']==sha(PLAN_028),'study-028 plan changed')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
