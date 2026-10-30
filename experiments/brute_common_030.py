"""Shared helpers for study BRUTE-0270-SYMMETRY-FREE-030 (experiments/BRUTE_PLAN_030.json; no amendment; deviation #132
fixes every definition added here). New file.
The study-030 freeze hashes BRUTE_PLAN_030.json and the v0.27.0 sources; the 025-029 freezes are checked unchanged."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson,FREEZE as FREEZE_026,FREEZE_025
from experiments.brute_common_027 import FREEZE as FREEZE_027,PLAN as PLAN_027
from experiments.brute_common_028 import FREEZE as FREEZE_028,PLAN as PLAN_028
from experiments.brute_common_029 import FREEZE as FREEZE_029,PLAN as PLAN_029,AMENDMENT as AMENDMENT_029

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_030.json'
PLAN_026=ROOT/'experiments/BRUTE_PLAN_026.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_030.json'
STUDY_DIR=ROOT/'results/study-030'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson']


def check_freeze():
    """The study-025 to 029 source freezes (unchanged files) and the study-030 source freeze (plan)."""
    for f in (FREEZE_025,FREEZE_026,FREEZE_027,FREEZE_028,FREEZE_029,FREEZE):
        check(f.exists(),f.name+' missing');frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN),'study-030 plan changed after source freeze')
        if f==FREEZE_026:check(frozen['plan_sha256']==sha(PLAN_026),'study-026 plan changed')
        if f==FREEZE_027:check(frozen['plan_sha256']==sha(PLAN_027),'study-027 plan changed')
        if f==FREEZE_028:check(frozen['plan_sha256']==sha(PLAN_028),'study-028 plan changed')
        if f==FREEZE_029:
            check(frozen['plan_sha256']==sha(PLAN_029),'study-029 plan changed')
            check(frozen['amendment_sha256']==sha(AMENDMENT_029),'study-029 amendment changed')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
