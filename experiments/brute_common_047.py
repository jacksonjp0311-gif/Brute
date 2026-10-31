"""Shared helpers for study BRUTE-0440-CERTIFY16D-SCALE20-047 (experiments/BRUTE_PLAN_047.json; pre-run deviation #167 fixes
every definition added here). New file.
The study-047 freeze hashes BRUTE_PLAN_047.json and the v0.44.0 sources; the 025-046 freezes are checked unchanged via the
frozen 046 check. A16_N and API16 keep the 046 host-side hard cap (experiments.solver_proxy_041: HardHook + one SolverServer child
per job), unchanged. API16D / API16D_b use the in-process pysat solver (certify16d.counted16d) and the host wall guard
experiments.host_hook_047.TimerHook, both passed through certify/16d's public hook / factory parameters.
sealed045() / sealed046(): the sealed 045 main cases and the sealed 046 main fresh cases, each checked against its SEAL.json."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_046 import check_freeze as check_freeze_046,sealed045
from experiments.solver_proxy_041 import HardHook,SolverServer,HARD_GRACE
from experiments.host_hook_047 import TimerHook

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_047.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_047.json'
CALIBRATION=ROOT/'results/diag-047/CAP_CALIBRATION_047.json'
STUDY_DIR=ROOT/'results/study-047'
SEALED046=ROOT/'results/study-046/main'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','CALIBRATION','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson','HardHook','SolverServer','HARD_GRACE','TimerHook','sealed045','sealed046','caps']
_C46={}


def sealed046():
    """{(key, seed): case} for the 18 sealed 046 fresh main cases (block 'main', arms API16 and A16_N)."""
    if not _C46:
        seal=load(SEALED046/'SEAL.json');check(sha(SEALED046/'RESULTS.json')==seal['results_sha256'],'sealed 046 RESULTS changed')
        check(seal['complete'] is True and seal['smoke'] is False,'sealed 046 not a complete main run')
        _C46.update({(c['key'],c['seed']):c for c in load(SEALED046/'RESULTS.json')['cases'] if c['block']=='main'})
        check(len(_C46)==18 and all('A16_N' in c['arms'] for c in _C46.values()),'sealed 046 case count')
    return _C46


def caps():
    """(conflict_cap C, budget_conflicts B) from the ledgered smoke calibration (cap_calibration_047)."""
    c=load(CALIBRATION);check(c['schema']=='brute.capcal.v44' and c['conflict_cap']>0 and c['budget_conflicts']>0,'calibration');return c['conflict_cap'],c['budget_conflicts']


def check_freeze():
    """The study-025 to 046 source freezes (via the frozen 046 check) and the study-047 source freeze."""
    check_freeze_046()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-047 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
