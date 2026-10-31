"""Shared helpers for study BRUTE-0460-CERTIFY16E-RESUME-SCALE20-049 (experiments/BRUTE_PLAN_049.json; pre-run deviation #171
fixes every definition added here). New file.
The study-049 freeze hashes BRUTE_PLAN_049.json and the v0.46.0 sources; the 025-048 freezes are checked unchanged via the
frozen 048 check. Caps are fixed by the plan (design.cap_rule), not calibrated: chunk C 50000, B16 1500000 per scale16 or control
case, B20 1000000 per scale20 case; max_chunks None (resume until B) for API16E / API16E_b, 1 for API16E_c1. The wall guard
stays at the certify/16d defaults (30 s per chunk, 600 s per case).
sealed048(): the 26 sealed 048 main cases, restored from the committed gzip if needed and checked against main/SEAL.json."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_048 import check_freeze as check_freeze_048
from experiments.host_hook_047 import TimerHook

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_049.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_049.json'
STUDY_DIR=ROOT/'results/study-049'
SEALED048=ROOT/'results/study-048/main'
C49=50000;B16=1500000;B20=1000000
BUDGET_OF={'scale16':B16,'control':B16,'scale20':B20}
MAX_CHUNKS={'API16E':None,'API16E_b':None,'API16E_c1':1}
_C48={}

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze','Checkpoint',
         'repair_torn_tail','wilson','TimerHook','sealed048','C49','B16','B20','BUDGET_OF','MAX_CHUNKS','budget_for']


def budget_for(key):return BUDGET_OF[key]


def sealed048():
    """{(key, seed): case} for the 26 sealed 048 main cases (arms API16D and API16D_b)."""
    if not _C48:
        from scripts.study048_storage import ensure_raw
        ensure_raw();seal=load(SEALED048/'SEAL.json');check(sha(SEALED048/'RESULTS.json')==seal['results_sha256'],'sealed 048 RESULTS changed')
        check(seal['complete'] is True and seal['smoke'] is False,'sealed 048 not a complete main run')
        _C48.update({(c['key'],c['seed']):c for c in load(SEALED048/'RESULTS.json')['cases'] if c['block']=='main'})
        check(len(_C48)==26 and all('API16D' in c['arms'] for c in _C48.values()),'sealed 048 case count')
    return _C48


def check_freeze():
    """The study-025 to 048 source freezes (via the frozen 048 check) and the study-049 source freeze."""
    check_freeze_048()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-049 plan changed after source freeze')
    check((frozen['conflict_cap'],frozen['budget_conflicts'])==(C49,{'scale16':B16,'control':B16,'scale20':B20}),'study-049 caps differ from the freeze')
    check(frozen['max_chunks']==MAX_CHUNKS,'study-049 max_chunks differ from the freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
