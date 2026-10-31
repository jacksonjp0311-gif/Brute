"""Shared helpers for study BRUTE-0430-CERTIFY16-046 (experiments/BRUTE_PLAN_046.json; pre-run deviation #165 fixes every
definition added here). New file.
The study-046 freeze hashes BRUTE_PLAN_046.json and the v0.43.0 sources; the 025-045 freezes are checked unchanged via the
frozen 045 check. The host-side hard cap is experiments.solver_proxy_041 (HardHook + one SolverServer child per job), unchanged;
the study passes them to certify/16 through its public hook / factory parameters (the API itself starts no process).
sealed045(): the sealed 045 main cases (results/study-045/main/RESULTS.json, checked against its SEAL.json)."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_045 import check_freeze as check_freeze_045
from experiments.solver_proxy_041 import HardHook,SolverServer,HARD_GRACE

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_046.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_046.json'
STUDY_DIR=ROOT/'results/study-046'
SEALED045=ROOT/'results/study-045/main'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson','HardHook','SolverServer','HARD_GRACE','sealed045']
_CACHE={}


def sealed045():
    if not _CACHE:
        seal=load(SEALED045/'SEAL.json');check(sha(SEALED045/'RESULTS.json')==seal['results_sha256'],'sealed 045 RESULTS changed')
        check(seal['complete'] is True and seal['smoke'] is False,'sealed 045 not a complete main run')
        _CACHE.update({(c['key'],c['seed']):c for c in load(SEALED045/'RESULTS.json')['cases']})
        check(len(_CACHE)==18,'sealed 045 case count')
    return _CACHE


def check_freeze():
    """The study-025 to 045 source freezes (via the frozen 045 check) and the study-046 source freeze."""
    check_freeze_045()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-046 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
