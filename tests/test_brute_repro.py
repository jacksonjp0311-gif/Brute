import json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from experiments.brute_common import VerificationError,load,dumps,STUDY_DIR,PLAN
PY=sys.executable


class BruteRepro(unittest.TestCase):
    def test_generators_reproduce_results_bytes(self):
        from scripts import make_gates,make_paired_analysis
        for mod,name in ((make_gates,'GATES.json'),(make_paired_analysis,'PAIRED_ANALYSIS.json')):
            self.assertEqual((STUDY_DIR/name).read_bytes(),dumps(mod.build()),name)

    def test_verify_fails_under_tampered_results(self):
        from scripts.verify_release import verify
        from scripts.make_manifest import tracked
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp)
            for rel in tracked(ROOT)+['MANIFEST.sha256']:
                (tmp/rel).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,tmp/rel)
            self.assertEqual(verify(tmp,fast=True)['status'],'passed')
            for rel,edit in (('results/study-002/GATES.json',lambda s:s.replace('"pass": true','"pass": false',1)),
                             ('results/study-002/SCIENTIFIC.json',lambda s:s.replace('"brute_wrong": false','"brute_wrong": true',1)),
                             ('results/RESEARCH_LEDGER.jsonl',lambda s:s.replace('promotion_gates','promotion_gate',1)),
                             ('brute/core/learner.py',lambda s:s+'\n# tamper\n')):
                original=(tmp/rel).read_text();(tmp/rel).write_text(edit(original))
                self.assertNotEqual(original,(tmp/rel).read_text(),rel)
                with self.assertRaises(VerificationError,msg=rel):verify(tmp,fast=True)
                (tmp/rel).write_text(original)

    def test_audit_not_vacuous_under_python_O(self):
        code=r'''
import json,sys
from experiments.brute_common import load,STUDY_DIR,VerificationError
from experiments.brute_audit import audit_case
d=load(STUDY_DIR/"SCIENTIFIC.json");c=next(c for c in d["cases"] if c["family"]=="ood5")
audit_case(c,d["plan"],d["calibration"]["tau"])
c["trace"][20]["certificate"]=3 if c["trace"][20]["certificate"]!=3 else 2
try:audit_case(c,d["plan"],d["calibration"]["tau"])
except VerificationError:print("CAUGHT");sys.exit(0)
print("MISSED");sys.exit(1)
'''
        r=subprocess.run([PY,'-O','-c',code],cwd=ROOT,capture_output=True,text=True,env={'PYTHONPATH':str(ROOT)})
        self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertIn('CAUGHT',r.stdout)

    def test_no_time_strips_all_timing_keys(self):
        from brute.evaluation import no_time
        obj={'a':1,'elapsed_informational':2.0,'x':[{'time_informational_seconds':3,'b':{'y_informational':4,'z':5}}]}
        self.assertEqual(no_time(obj),{'a':1,'x':[{'b':{'z':5}}]})
        def keys(o):
            if isinstance(o,dict):
                for k,v in o.items():yield k;yield from keys(v)
            elif isinstance(o,list):
                for v in o:yield from keys(v)
        bad=[k for k in keys(load(STUDY_DIR/'SCIENTIFIC.json')) if 'informational' in k or 'elapsed' in k or 'time' in k.split('_')]
        self.assertEqual(bad,[])

    def test_manifest_matches_tracked_files(self):
        from scripts.make_manifest import build
        self.assertEqual((ROOT/'MANIFEST.sha256').read_text(),build(ROOT))

    def test_default_budgets_match_plan(self):
        from brute.core import DEFAULT_MAX_PREFIXES,DEFAULT_EPSILON,DEFAULT_WINDOW,BruteLearner
        from brute.api.service import CALIBRATED_TAU
        plan=load(PLAN)
        self.assertEqual(DEFAULT_MAX_PREFIXES,plan['row_budget_family']);self.assertEqual(DEFAULT_MAX_PREFIXES,plan['row_budget_margin'])
        self.assertEqual(DEFAULT_EPSILON,plan['open_world_reserve_epsilon']);self.assertEqual(DEFAULT_WINDOW,plan['residual_surprise']['window_W'])
        L=BruteLearner();self.assertEqual((L.family_states,L.margin_states),(plan['family_state_cap'],plan['margin_state_cap']))
        self.assertEqual(CALIBRATED_TAU,load(STUDY_DIR/'CALIBRATION.json')['tau'])


if __name__=='__main__':unittest.main()
