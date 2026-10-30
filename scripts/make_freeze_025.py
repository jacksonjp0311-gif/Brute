"""Lean source freeze for study-025 (A2): writes experiments/COMMIT_ORDER_025.json (ledger events from build_authorization_025)
and experiments/BRUTE_SOURCE_FREEZE_025.json (plan, A1, A2, plan-021 and source/scoring/test hashes). Refuses overwrite.
  PYTHONPATH=. python scripts/make_freeze_025.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_025 import PLAN,PLAN_A1,PLAN_021,FREEZE,sha,write_new
PLAN_A2=ROOT/'experiments/BRUTE_PLAN_025_A2.json';ORDER=ROOT/'experiments/COMMIT_ORDER_025.json'
FILES=['brute/bettingregion.py','brute/api/certify11.py','brute/release_version_0220.py','experiments/brute_common_025.py','experiments/brute_study_025.py',
       'experiments/v0220_reference.py','experiments/BRUTE_PLAN_025.json','experiments/BRUTE_PLAN_025_A1.json','experiments/BRUTE_PLAN_025_A2.json',
       'scripts/check_seeds_025.py','scripts/api_check_025.py','scripts/hn_recount_025.py','scripts/make_gates_025.py','scripts/make_paired_025.py',
       'scripts/run_reference_025.py','scripts/run_tests_0220.py','scripts/study025_storage.py','scripts/make_freeze_025.py',
       'tests/test_bettingregion_0220.py','tests/test_certify11_0220.py','tests/test_scripts_025.py','tests/test_study_0220.py',
       'docs/research/v0.22.0/BETTING_LEMMA_025.md','docs/research/v0.22.0/AMENDMENT_025_A1.md','docs/research/v0.22.0/AMENDMENT_025_A2.md',
       'docs/research/BRUTE_DEVIATIONS_025_119.md','docs/research/BRUTE_DEVIATIONS_025_120.md','results/diag-025/HN_RECOUNT_025.json',
       'results/smoke-025/../diag-025/SEEDCHECK_025.json','experiments/COMMIT_ORDER_025.json']


def main():
    L=[json.loads(x) for x in (ROOT/'results/RESEARCH_LEDGER.jsonl').read_text().splitlines() if x.strip()]
    i0=next(i for i,e in enumerate(L) if e.get('event')=='build_authorization_025')
    ev=[{'event':e['event'],'commit':e.get('commit'),'note_time':str(e.get('note',''))[:25]} for e in L[i0:]]
    write_new(ORDER,{'schema':'brute.commit-order.v1','study':'BRUTE-0220-BETTING-CS-025','order':[e['event'] for e in ev],'entries':ev})
    files={f:sha((ROOT/f).resolve()) for f in sorted(set(str(Path(f)) if '..' not in f else str((ROOT/f).resolve().relative_to(ROOT)) for f in FILES))}
    write_new(FREEZE,{'schema':'brute.source-freeze.v1','study':'BRUTE-0220-BETTING-CS-025','process':'lean (A2)','plan_sha256':sha(PLAN),
        'plan_a1_sha256':sha(PLAN_A1),'plan_a2_sha256':sha(PLAN_A2),'plan_021_sha256':sha(PLAN_021),'sha256_files':files})
    print(len(files),'files frozen')


if __name__=='__main__':main()
