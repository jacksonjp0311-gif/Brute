"""Shared helpers for study BRUTE-0230-SCALE-026 (experiments/BRUTE_PLAN_026.json; deviation #123). New file.
The study-026 freeze hashes BRUTE_PLAN_026.json and the v0.23.0 sources; earlier freezes are checked unchanged."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_026.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_026.json'
FREEZE_025=ROOT/'experiments/BRUTE_SOURCE_FREEZE_025.json'
STUDY_DIR=ROOT/'results/study-026'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze','Checkpoint',
         'repair_torn_tail','wilson']


def wilson(x,n,z=1.959963984540054):
    """Wilson 95% interval [lo, hi] for x successes in n trials ([0, 1] when n = 0)."""
    if n==0:return [0.0,1.0]
    p=x/n;d=1+z*z/n;c=p+z*z/(2*n);h=z*((p*(1-p)/n+z*z/(4*n*n))**0.5)
    return [max(0.0,(c-h)/d),min(1.0,(c+h)/d)]


def check_freeze():
    """The study-025 source freeze (unchanged files) and the study-026 source freeze."""
    for f in (FREEZE_025,FREEZE):
        check(f.exists(),f.name+' missing');frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN),'study-026 plan changed after source freeze')
        for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
