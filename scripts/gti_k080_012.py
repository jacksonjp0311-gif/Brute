"""Non-gated report R_GTI_K080 (deviation #50): clean-tag check for test_release_080 after the v0.9.0 release.

Since v0.9.0, RELEASE.json says 0.9.0, so the three test_release_080 tests that pin 0.8.0 fail on the v0.10.0 tree.
These are the same kind of superseded-release failure as K_060 / K_070, but the frozen GTI criterion of BRUTE_PLAN_012
has no K_080 rule, so GTI_test_isolation is scored as frozen (expected FAIL). This script records, for the report only,
whether each such failure passes on a clean worktree of tag v0.8.0 with the same per-module runner.
Writes results/study-012/GTI_K080_012.json (refuses to overwrite).
"""
from __future__ import annotations
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.run_tests_0100 import clean_run

K080={f'test_release_080.Release080.{t}' for t in ('test_version_consistent','test_fast_verify_passes','test_untampered_copy_passes')}


def build(suite):
    V=suite['verdict'];und=set(V['undeclared_failures']);rv=sorted(t for t in und if t.startswith('test_release_080.'))
    t0=time.time();c=clean_run('v0.8.0','test_release_080.py') if rv else None
    ok=bool(rv) and set(rv)<=K080 and c is not None and all(c['results'].get(t,['missing'])[0]=='ok' for t in rv)
    rest=sorted(und-set(rv)) if ok else sorted(und)
    other=all(V['clauses'][k] for k in V['clauses'] if k!='i_only_declared_failures')
    return {'schema':'brute.gti-k080.v1','gated':False,'report':'R_GTI_K080','test_suite_head':suite['head'],
            'k080_failures':rv,'clean_tag':'v0.8.0','clean_results':c and c['results'],'k080_rule_applies':ok,
            'undeclared_after_k080':rest,'gti_would_pass_with_k080':ok and not rest and other,
            'wall_informational':round(time.time()-t0,1)}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--suite',default=str(ROOT/'results/study-012/TEST_SUITE_012.json'))
    ap.add_argument('--output',default=str(ROOT/'results/study-012/GTI_K080_012.json'));a=ap.parse_args()
    out=Path(a.output)
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    r=build(json.loads(Path(a.suite).read_text()));out.write_text(json.dumps(r,indent=1,sort_keys=True)+'\n')
    print(json.dumps({k:r[k] for k in ('k080_failures','k080_rule_applies','undeclared_after_k080','gti_would_pass_with_k080')}))
