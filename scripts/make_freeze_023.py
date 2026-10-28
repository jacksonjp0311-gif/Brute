"""Write experiments/BRUTE_SOURCE_FREEZE_023.json (study-023 source lock, BRUTE_PLAN_023 process). Refuses to overwrite.

Every earlier source freeze (002..021) and release freeze (v0.7.0_R1 .. v0.19.0) stays in force;
experiments/brute_common_023.check_freeze verifies all of them plus this one (G13).
The scoring scripts (make_gates_023, make_paired_023, make_reproducibility_023, clean_clone_023, tests/test_scoring_023)
are locked separately by the scoring_freeze_023 ledger entry (>= 600 s before run_start_023). tests/test_release_0200.py,
scripts/verify_release_0200.py and scripts/make_release_freeze_0200.py are written at release, after the run, and are not frozen here.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_023 import FREEZE,PLAN,PLAN_021,sha,write_new
FILES=sorted(['brute/lrregion.py','brute/api/certify9.py','brute/release_version_0200.py',
    'experiments/BRUTE_PLAN_023.json','experiments/BRUTE_PLAN_FREEZE_023.json','experiments/BRUTE_PLAN_021.json','experiments/brute_common_023.py',
    'experiments/brute_study_023.py','experiments/v0200_reference.py',
    'scripts/check_seeds_023.py','scripts/hn_recount_023.py','scripts/make_freeze_023.py','scripts/run_reference_023.py','scripts/rate_math_023.py',
    'scripts/run_tests_0200.py','scripts/run_study_023.py','scripts/seal_023.py','scripts/watchdog_023.py','scripts/study023_storage.py',
    'scripts/hbsentinel_023.py','scripts/hb_attribution_023.py','scripts/api_check_023.py','scripts/drill_023.py','scripts/prerun_check_023.py',
    'requirements.txt','requirements-gmc.txt',
    'tests/test_seeds_0200.py','tests/test_study_0200.py','tests/test_lrregion_0200.py','tests/test_certify9_0200.py',
    'tests/test_reference_0200.py','tests/test_scripts_023.py',
    'docs/research/v0.20.0/PLAN_023.md','docs/research/v0.20.0/LR_LEMMA_023.md','docs/research/v0.20.0/BUILD_AUTHORIZATION_023.md',
    'docs/research/v0.20.0/RATE_MATH_023.md','docs/research/v0.20.0/RATE_MATH_023.json',
    'docs/research/BRUTE_DEVIATIONS_023.md','docs/research/BRUTE_DEVIATIONS_023_109.md',
    'results/diag-023/SEEDCHECK_023.json','results/diag-023/HN_RECOUNT_023.json',
    'results/smoke-023/KILL_DRILL_023.json','results/smoke-023/RESUME_DRILL_023.json','results/smoke-023/API_CHECK_023.json'])
DEVS=[108,109]   # deviation numbers in force at the freeze (BRUTE_DEVIATIONS_023*.md, #108 onward)
EXTRA=[x for x in sys.argv[1:] if x.startswith('+')]   # '+path' adds a file written after this script (e.g. a deviations addendum)
FILES=sorted(FILES+[x[1:] for x in EXTRA])


def build(implementation_commits):
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-0200-LR-ANYTIME-023','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,10)]+['experiments/BRUTE_SOURCE_FREEZE_0%d.json'%i for i in range(10,22)]+
                            ['experiments/BRUTE_RELEASE_FREEZE_070_R1.json','experiments/BRUTE_RELEASE_FREEZE_080.json',
                             'experiments/BRUTE_RELEASE_FREEZE_090_R1.json','experiments/BRUTE_RELEASE_FREEZE_0100.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0110.json','experiments/BRUTE_RELEASE_FREEZE_0120.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0130.json','experiments/BRUTE_RELEASE_FREEZE_0140.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0150.json','experiments/BRUTE_RELEASE_FREEZE_0160.json','experiments/BRUTE_RELEASE_FREEZE_0170.json','experiments/BRUTE_RELEASE_FREEZE_0180.json','experiments/BRUTE_RELEASE_FREEZE_0190.json'],
            'plan_sha256':sha(PLAN),'plan_021_sha256':sha(PLAN_021),'preregistration_commit':'f88ad1e','build_authorization_commit':'a54d7e7',
            'seedcheck_commit':'ccbae9b','reference_commits':['e50967d','9e0ca70'],'implementation_commits':implementation_commits,'deviations_in_force':DEVS,
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build([x for x in sys.argv[1:] if not x.startswith('+')]));print(len(FILES),'files frozen')
