"""Write experiments/BRUTE_SOURCE_FREEZE_024.json (study-024 source lock, BRUTE_PLAN_024). Refuses to overwrite.
Adapted from scripts/make_freeze_023.py (frozen). Every file below is hashed; experiments/brute_common_024.check_freeze
verifies all of them plus every earlier freeze (G13). experiments/COMMIT_ORDER_024.json (G_PROC c) is frozen here.
The scoring scripts (make_gates_024, make_paired_024, make_reproducibility_024, clean_clone_024(+_gitclone),
early_window_024, tests/test_scoring_024) are locked separately by the scoring_freeze_024 ledger entry (>= 600 s before
run_start_024). tests/test_release_0210*.py, scripts/verify_release_0210*.py and scripts/make_release_freeze_0210*.py are
written at release, after run_end, and are not frozen here.
    $PY scripts/make_freeze_024.py <implementation commit> ... [+extra/path]
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_024 import FREEZE,PLAN,PLAN_021,sha,write_new,load
FILES=sorted(['brute/stitchedregion.py','brute/api/certify10.py','brute/release_version_0210.py',
    'experiments/BRUTE_PLAN_024.json','experiments/BRUTE_PLAN_021.json','experiments/brute_common_024.py',
    'experiments/brute_study_024.py','experiments/v0210_reference.py','experiments/COMMIT_ORDER_024.json',
    'scripts/check_seeds_024.py','scripts/hn_recount_024.py','scripts/make_freeze_024.py','scripts/run_reference_024.py','scripts/rate_math_024.py',
    'scripts/run_tests_0210.py','scripts/run_study_024.py','scripts/seal_024.py','scripts/watchdog_024.py','scripts/study024_storage.py',
    'scripts/hbsentinel_024.py','scripts/hb_attribution_024.py','scripts/api_check_024.py','scripts/drill_024.py','scripts/prerun_check_024.py',
    'scripts/launch_study_024.py',
    'tests/test_seeds_0210.py','tests/test_study_0210.py','tests/test_stitchedregion_0210.py','tests/test_certify10_0210.py',
    'tests/test_reference_0210.py','tests/test_scripts_024.py',
    'docs/research/v0.21.0/PLAN_024.md','docs/research/v0.21.0/STITCHED_LEMMA_024.md','docs/research/v0.21.0/BUILD_AUTHORIZATION_024.md',
    'docs/research/v0.21.0/RATE_MATH_024.md','docs/research/v0.21.0/RATE_MATH_024.json',
    'docs/research/BRUTE_DEVIATIONS_024_115.md','docs/research/BRUTE_DEVIATIONS_024_116.md',
    'results/diag-024/SEEDCHECK_024.json','results/diag-024/HN_RECOUNT_024.json',
    'results/smoke-024/KILL_DRILL_024.json','results/smoke-024/RESUME_DRILL_024.json','results/smoke-024/API_CHECK_024.json'])
DEVS=[115,116]   # deviation numbers in force at the freeze (BRUTE_DEVIATIONS_024_*.md, #115 onward); '+path' files add more
EXTRA=[x for x in sys.argv[1:] if x.startswith('+')]
FILES=sorted(FILES+[x[1:] for x in EXTRA])
DEVS=sorted(set(DEVS+[int(Path(x).stem.rsplit('_',1)[1]) for x in FILES if Path(x).name.startswith('BRUTE_DEVIATIONS_024_')]))


def build(implementation_commits):
    co=load(ROOT/'experiments/COMMIT_ORDER_024.json')
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-0210-STITCHED-LR-024','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_023.json','experiments/BRUTE_RELEASE_FREEZE_0200.json','experiments/BRUTE_RELEASE_FREEZE_0200_R1.json',
                             '(and through brute_common_023.check_freeze every earlier source / release freeze)'],
            'plan_sha256':sha(PLAN),'plan_021_sha256':sha(PLAN_021),'commit_order_sha256':sha(ROOT/'experiments/COMMIT_ORDER_024.json'),
            'commit_order':co,'implementation_commits':implementation_commits,'deviations_in_force':DEVS,
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build([x for x in sys.argv[1:] if not x.startswith('+')]));print(len(FILES),'files frozen')
