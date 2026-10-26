"""Write results/study-009/GATES_009_FINAL.json: GATES_009 regenerated from the sealed artifacts (must equal the committed
GATES_009.json byte-for-byte) plus the final-tree GTI run (TEST_SUITE_009_FINAL.json, scripts/run_tests_070.py on the
release tree). This adds no scoring choice: the gated GTI stays the in-cap run; the release statement "GTI PASS" needs
both runs to pass (BRUTE_DEVIATIONS_009 entry 13). Refuses to overwrite; --check verifies it regenerates.
"""
from __future__ import annotations
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_009 import STUDY_DIR,load,dumps,write_new,check,sha


def build(d=STUDY_DIR):
    from scripts.make_gates_009 import build as gates
    d=Path(d);g=gates(d);check((d/'GATES_009.json').read_bytes()==dumps(g),'GATES_009.json does not regenerate')
    ts=load(d/'TEST_SUITE_009_FINAL.json');V=ts['verdict']
    out=dict(g);out['schema']='brute.gates-final.v7_0';out['gates_009_sha256']=sha(d/'GATES_009.json')
    out['GTI_final_tree']={'gated':False,'pass':bool(V['passed']),'verdict':V,'head':ts.get('head'),
                           'tracked_tree_dirty':ts.get('tracked_tree_dirty'),'test_suite_sha256':sha(d/'TEST_SUITE_009_FINAL.json')}
    out['GTI_release_statement']='GTI PASS' if (g['gates']['GTI_test_isolation']['pass'] and V['passed']) else 'GTI FAIL'
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();out=STUDY_DIR/'GATES_009_FINAL.json'
    if a.check:check(out.read_bytes()==dumps(build()),'GATES_009_FINAL.json does not regenerate');print('reproduces')
    else:o=build();write_new(out,o);print(o['GTI_release_statement'],o['failed'])
