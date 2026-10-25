"""Evaluate GT1 (BRUTE_PLAN_008 target (c)) with tests/test_release_060's corruption matrix and the frozen-050 regression,
and write results/study-008/GT1_008.json (refuses overwrite). Run at process step (10), after verify_release_060 exists."""
import collections,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_008 import write_new
from tests.test_release_060 import gt1_matrix,regression_050,MODES,targets

if __name__=='__main__':
    m=gt1_matrix();r=regression_050();c=collections.Counter(m.values())
    ok=set(m.values())=={'VerificationError'} and all(r['files_unchanged'].values()) and r['raised']=='JSONDecodeError'
    obj={'schema':'brute.gt1.v1','pass':ok,'artifacts':targets(),'modes':list(MODES),'cases':len(m),'outcomes':dict(sorted(c.items())),
         'other_exception_types':sum(v.startswith('other:') for v in m.values()),'silent_passes':c.get('silent_pass',0),
         'not_verification_error':{k:v for k,v in m.items() if v!='VerificationError'},'regression_frozen_050':r,
         'note':'artifacts enumerated at evaluation time; GT1_008.json and GATES_008_FINAL.json are written after this run and are covered by the final tests/test_release_060 run'}
    write_new(ROOT/'results/study-008/GT1_008.json',obj);print(json.dumps({k:obj[k] for k in ('pass','cases','outcomes','regression_frozen_050')}))
