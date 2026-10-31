"""Shared helpers for study BRUTE-0380-ENC-AUDIT-041 (experiments/BRUTE_PLAN_041.json; deviation #154 fixes every
definition added here). New file.
The study-041 freeze hashes BRUTE_PLAN_041.json and the v0.38.0 sources; the 025-040 freezes are checked unchanged via the
frozen 040 check. The host-side hard cap is experiments.solver_proxy_041 (HardHook + one SolverServer child per job).
Sealed traces (part 1): final A14 traces rebuilt from the sealed RESULTS (study-039 worlds_039, study-040 worlds_040) as
the seeded passive prefix (worlds_026.trajectory, eps 0) plus the arm's extra_acts / extra_masks."""
import gzip,json
from pathlib import Path
from brute.region import codes_mask
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_040 import check_freeze as check_freeze_040
from experiments.solver_proxy_041 import HardHook,SolverServer,HARD_GRACE

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_041.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_041.json'
STUDY_DIR=ROOT/'results/study-041'
SEALED={'039':ROOT/'results/study-039/main/RESULTS.json.gz','040':ROOT/'results/study-040/main/RESULTS.json.gz'}

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','SEALED','check_freeze',
         'Checkpoint','repair_torn_tail','wilson','HardHook','SolverServer','HARD_GRACE','sealed_cases','final_trace']


def check_freeze():
    """The study-025 to 040 source freezes (unchanged files, via the frozen 040 check) and the study-041 source freeze."""
    check_freeze_040()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-041 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen


_CACHE={}


def sealed_cases(study):
    if study not in _CACHE:_CACHE[study]={(c['key'],c['seed']):c for c in json.load(gzip.open(SEALED[study]))['cases']}
    return _CACHE[study]


def final_trace(study,case,arm='A14'):
    from experiments import worlds_026 as W26
    W=__import__('experiments.worlds_'+study,fromlist=['world'])
    a=case['arms'][arm];tr=W26.trajectory(W.world(case['seed'],case['family']),case['seed'],0.0)
    acts=list(tr['actions'])+list(a['extra_acts']);masks=[codes_mask(tuple(r),W26.S_BITS) for r in tr['readings']]+list(a['extra_masks'])
    check(len(masks)==len(acts)+1,'trace shape');return masks,acts
