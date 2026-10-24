"""Study-003 tooling: control arm == frozen v0.1.0 runner; the independent reference passes on real
cases (including retractions) and rejects tampering; the reference imports no brute module."""
import copy,subprocess,sys,unittest
from pathlib import Path
from experiments.brute_common_003 import PLAN,load,VerificationError
from experiments.brute_study_003 import run_case_003
from experiments.v011_independent_reference import audit_case,ref_reason
from brute.evaluation import run_case

ROOT=Path(__file__).resolve().parents[1]
P=load(PLAN);TAU=P['residual_surprise']['tau']


class Study003(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # design-data seeds (study-001 drift4, used for R4) -- not study-003 heldout seeds
        cls.ret=run_case_003(990005,'drift4',0.35,P,TAU)
        cls.inf=run_case_003(930001,'cycle3',0.1,P,TAU)

    def test_control_arm_equals_frozen_runner(self):
        for c,(s,f,m) in ((self.ret,(990005,'drift4',0.35)),(self.inf,(930001,'cycle3',0.1))):
            r=run_case(s,f,m,P,TAU)
            for x,y in zip(c['control_trace'],r['trace']):
                self.assertEqual(x,{k:y[k] for k in x})

    def test_in_family_v011_identical_to_control(self):
        for x,y in zip(self.inf['trace'],self.inf['control_trace']):
            for k in ('probabilities','status','reason','certificate'):self.assertEqual(x[k],y[k])

    def test_reference_passes_with_retractions(self):
        t=audit_case(self.ret,P,TAU)
        self.assertEqual(t['retractions'],4)
        self.assertEqual(t['retraction_reasons'],{'falsified_by_observation':1,'scope_withdrawn':1,'unverifiable_masked':2})
        audit_case(self.inf,P,TAU)

    def test_reference_rejects_tampering(self):
        def bad(fn):
            c=copy.deepcopy(self.ret);fn(c)
            with self.assertRaises(VerificationError):audit_case(c,P,TAU)
        post=next(i for i,r in enumerate(self.ret['trace']) if r['reason']=='FAMILY_CONTRADICTED')
        def p_post(c):pr=c['trace'][post]['probabilities'];pr[0],pr[1]=pr[1]+1e-6,pr[0]-1e-6
        def p_pre(c):pr=c['trace'][0]['probabilities'];pr[0],pr[1]=pr[0]+1e-9,pr[1]-1e-9
        def src(c):c['trace'][post]['forecast_source']='suffix1' if c['trace'][post]['forecast_source']!='suffix1' else 'margin_n5'
        def reason(c):c['retractions'][0]['reason']='scope_withdrawn'
        def control(c):c['control_trace'][3]['certificate']=0
        for fn in (p_post,p_pre,src,reason,control):bad(fn)

    def test_g8_reason_rule(self):
        self.assertEqual(ref_reason(3,(0,None)),'falsified_by_observation')
        self.assertEqual(ref_reason(3,(1,1)),'scope_withdrawn')
        self.assertEqual(ref_reason(3,(1,None)),'unverifiable_masked')
        self.assertEqual(ref_reason(3,(None,None)),'unverifiable_masked')

    def test_reference_imports_no_brute(self):
        code=('import sys;import experiments.v011_independent_reference;'
              "bad=[m for m in sys.modules if m=='brute' or m.startswith('brute.')];print(bad);sys.exit(1 if bad else 0)")
        r=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env={'PYTHONPATH':str(ROOT)},capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        src=(ROOT/'experiments/v011_independent_reference.py').read_text()
        import re;self.assertIsNone(re.search(r'^\s*(from|import)\s+brute\b',src,re.M))


if __name__=='__main__':unittest.main()
