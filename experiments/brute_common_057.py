"""Shared helpers for study BRUTE-0540-SCALE20-COVERFIRST-057 (experiments/BRUTE_PLAN_057.json; pre-run deviation #188 fixes
every definition added here). New file; built from experiments/brute_common_056.py (frozen). The study-057 freeze hashes
BRUTE_PLAN_057.json and the v0.54.0 study sources; the 025-056 freezes are checked unchanged via the frozen 056 check.
Caps are fixed by the plan (design.caps), not calibrated: C20 50000, B20 2000000, family_bound 20, every arm.
Stop rule: conflict-only (no host hook; the certify/16e case guard is the plan's 900 s hard kill, a safety net only; any firing
fails GDET57). Workers: one 8-worker pool, max_tasks_per_child=1."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_056 import check_freeze as check_freeze_056
from brute.api import cover20 as CV

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_057.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_057.json'
STUDY_DIR=ROOT/'results/study-057'
C20=50000;B20=2000000;BOUND=20;KEY='scale20v';FAMILY='scale20'
BASE_ARM='API16E20';PRE_ARMS=('COV_O','LEN_R');X_ARMS=('COV_X','COV_X_b')
ALL_ARMS=('API16E20','COV_O','LEN_R','COV_X','COV_X_b');EXT_ARMS=('COV_O','LEN_R','COV_X','COV_X_b')
WORKERS=8;HARD_KILL_S=900.0
STOP_RULE='conflict-only (no hook; 900 s case kill as safety net)'
COVER={'h':CV.H,'steps':CV.STEPS,'api':CV.API}
LEN_RNG='random.Random(seed*7+57).randrange(k)'
ORACLE_RULE='BFS shortest path (actions in index order) to the nearest state with an unexercised action, take its lowest unexercised action; repeat until every pair reachable from the post-prefix state is exercised'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze','Checkpoint',
         'repair_torn_tail','wilson','C20','B20','BOUND','KEY','FAMILY','BASE_ARM','PRE_ARMS','X_ARMS','ALL_ARMS','EXT_ARMS','WORKERS',
         'HARD_KILL_S','STOP_RULE','COVER','LEN_RNG','ORACLE_RULE']


def check_freeze():
    """The study-025 to 056 source freezes (via the frozen 056 check) and the study-057 source freeze."""
    check_freeze_056()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-057 plan changed after source freeze')
    check(frozen['caps']==[C20,B20] and frozen['bound']==BOUND and frozen['arms']==list(ALL_ARMS),'study-057 caps, bound or arms differ from the freeze')
    check(frozen['workers']==WORKERS,'study-057 workers differ from the freeze')
    check(frozen['stop']=={'hard_kill_s':HARD_KILL_S,'stop_rule':STOP_RULE},'study-057 stop rule differs from the freeze')
    check(frozen.get('cover')==COVER and frozen.get('len_rng')==LEN_RNG and frozen.get('oracle_rule')==ORACLE_RULE,'study-057 explorer settings differ from the freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
