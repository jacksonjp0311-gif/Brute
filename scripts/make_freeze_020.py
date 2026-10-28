"""Write experiments/BRUTE_SOURCE_FREEZE_020.json (study-020 source lock, BRUTE_PLAN_020 process). Refuses to overwrite.

Every earlier source freeze (002..019) and release freeze (v0.7.0_R1 .. v0.17.0) stays in force;
experiments/brute_common_020.check_freeze verifies all of them plus this one (G13).
The scoring scripts (make_gates_020, make_paired_020, make_reproducibility_020, clean_clone_020, tests/test_scoring_020)
are locked separately by the scoring_freeze_020 ledger entry (>= 600 s before run_start_020). tests/test_release_0180.py
and scripts/verify_release_0180.py are written at release, after the run, and are not frozen here.
"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_020 import FREEZE,PLAN,sha,write_new
FILES=sorted(['brute/perbit.py','brute/release_version_0180.py',
    'experiments/BRUTE_PLAN_020.json','experiments/BRUTE_PLAN_FREEZE_020.json','experiments/brute_common_020.py',
    'experiments/brute_study_020.py','experiments/v0180_reference.py',
    'scripts/check_seeds_020.py','scripts/make_freeze_020.py','scripts/run_reference_020.py','scripts/rate_math_020.py',
    'scripts/run_tests_0180.py','scripts/run_study_020.py','scripts/seal_020.py','scripts/watchdog_020.py','scripts/study020_storage.py',
    'scripts/hbsentinel_020.py','scripts/hb_attribution_020.py',
    'requirements.txt','requirements-gmc.txt',
    'tests/test_seeds_0180.py','tests/test_study_0180.py','tests/test_perbit_0180.py',
    'tests/test_reference_0180.py','tests/test_scripts_020.py',
    'docs/research/BRUTE_DEVIATIONS_020.md',
    'docs/research/v0.18.0/PLAN_020.md','docs/research/v0.18.0/RATE_MATH_020.md','docs/research/v0.18.0/RATE_MATH_020.json',
    'results/diag-020/SEEDCHECK_020.json','results/smoke-020/KILL_DRILL_020.json'])
EXTRA=[x for x in sys.argv[1:] if x.startswith('+')]   # '+path' adds a file written after this script (e.g. a deviations addendum)
FILES=sorted(FILES+[x[1:] for x in EXTRA])


def build(implementation_commits):
    return {'schema':'brute.source-freeze.v1','study':'BRUTE-0180-HORIZON-020','status':'frozen',
            'also_requires':['experiments/BRUTE_SOURCE_FREEZE_00%d.json'%i for i in range(2,10)]+['experiments/BRUTE_SOURCE_FREEZE_0%d.json'%i for i in range(10,20)]+
                            ['experiments/BRUTE_RELEASE_FREEZE_070_R1.json','experiments/BRUTE_RELEASE_FREEZE_080.json',
                             'experiments/BRUTE_RELEASE_FREEZE_090_R1.json','experiments/BRUTE_RELEASE_FREEZE_0100.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0110.json','experiments/BRUTE_RELEASE_FREEZE_0120.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0130.json','experiments/BRUTE_RELEASE_FREEZE_0140.json',
                             'experiments/BRUTE_RELEASE_FREEZE_0150.json','experiments/BRUTE_RELEASE_FREEZE_0160.json','experiments/BRUTE_RELEASE_FREEZE_0170.json'],
            'plan_sha256':sha(PLAN),'preregistration_commit':'8048c95','deviations_commit':'b5ec732','seedcheck_commit':'5e6407a',
            'reference_commits':['5ac2ec9'],'implementation_commits':implementation_commits,'deviations_in_force':[103,104],
            'sha256_files':{rel:sha(ROOT/rel) for rel in FILES}}


if __name__=='__main__':
    write_new(FREEZE,build([x for x in sys.argv[1:] if not x.startswith('+')]));print(len(FILES),'files frozen')
