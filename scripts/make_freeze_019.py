"""Write experiments/BRUTE_SOURCE_FREEZE_019.json (study-019 source lock, BRUTE_PLAN_019 process). Refuses to overwrite.

Every earlier source freeze (002..018) and release freeze (v0.7.0_R1 .. v0.16.0) stays in force;
experiments/brute_common_019.check_freeze verifies all of them plus this one (G13).
The scoring scripts (make_gates_019, make_paired_019, make_reproducibility_019, clean_clone_019, tests/test_scoring_019)
are locked separately by the scoring_freeze_019 ledger entry (>= 600 s before run_start_019). tests/test_release_0170.py
and scripts/verify_release_0170.py are written at release, after the run, and are not frozen here.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_019 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/seqmargin.py','brute/region3.py','brute/api/certify7.py','brute/release_version_0170.py',
    'experiments/BRUTE_PLAN_019.json','experiments/BRUTE_PLAN_FREEZE_019.json','experiments/brute_common_019.py',
    'experiments/brute_study_019.py','experiments/v0170_reference.py',
    'scripts/check_seeds_019.py','scripts/make_freeze_019.py','scripts/run_reference_019.py','scripts/rate_math_019.py',
    'scripts/run_tests_0170.py','scripts/run_study_019.py','scripts/seal_019.py','scripts/watchdog_019.py','scripts/study019_storage.py',
    'scripts/hbsentinel_019.py','scripts/hb_attribution_019.py',
    'requirements.txt','requirements-gmc.txt',
    'tests/test_seeds_0170.py','tests/test_study_0170.py','tests/test_seqmargin_0170.py','tests/test_api_certify7_0170.py',
    'tests/test_reference_0170.py','tests/test_scripts_019.py',
    'docs/research/BRUTE_DEVIATIONS_019.md',
    'docs/research/v0.17.0/PLAN_019.md','docs/research/v0.17.0/RATE_MATH_019.md','docs/research/v0.17.0/RATE_MATH_019.json',
    'results/diag-019/SEEDCHECK_019.json','results/smoke-019/KILL_DRILL_019.json'])
EXTRA=[x for x in sys.argv[1:] if x.startswith('+')]   # '+path' adds a file written after this script (e.g. a deviations addendum)
FILES=sorted(FILES+[x[1:] for x in EXTRA])


def build(implementation_commits):
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-0170-SEQUENTIAL-MARGIN-019','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,10)]+['experiments/BRUTE_SOURCE_FREEZE_0%d.json'%i for i in range(10,19)]+
                            ['experiments/BRUTE_RELEASE_FREEZE_070_R1.json','experiments/BRUTE_RELEASE_FREEZE_080.json',
                             'experiments/BRUTE_RELEASE_FREEZE_090_R1.json','experiments/BRUTE_RELEASE_FREEZE_0100.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0110.json','experiments/BRUTE_RELEASE_FREEZE_0120.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0130.json','experiments/BRUTE_RELEASE_FREEZE_0140.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0150.json','experiments/BRUTE_RELEASE_FREEZE_0160.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'c11a852','deviations_commit':'9feaffd','seedcheck_commit':'36c4d66',
            'reference_commits':['cc33769'],'implementation_commits':implementation_commits,'deviations_in_force':[101],
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build([x for x in sys.argv[1:] if not x.startswith('+')]));print(len(FILES),'files frozen')
