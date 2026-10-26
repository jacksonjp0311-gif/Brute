"""v0.7.0 S7/SC7/BS7/BSC7 (brute.syncevent) on smoke seeds, checked by the second implementation (v070_reference)."""
import unittest,copy
from experiments.brute_common import load
from experiments.brute_study_009 import run_job,PLAN,run_case_2x2
from experiments import v070_reference as R


class SyncEvent009(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=load(PLAN);cls.view=R.plan_view(cls.plan)
        cls.c2=run_job(('smoke-2x2','cycle3',2190001,0.35),cls.plan)[1]
        cls.cb=run_job(('smoke-breadth','sens3',2190019,0.35),cls.plan)[1]

    def test_2x2_arms_and_reference(self):
        self.assertEqual(sorted(self.c2['arms']),sorted(['S7','SC7','R6','C6','A5','A4','A2']))
        for arm in ('S7','SC7'):
            ok,msg,_=R.audit_trace(self.c2,arm,self.view,self.plan['tau6']['value'],self.plan['tau7']['value'])
            self.assertTrue(ok,(arm,msg))
            d=self.c2['arms'][arm]['diagnostics'];self.assertIn('event_triggers',d)
            for step,trig in d['event_triggers']:self.assertTrue(set(trig)<={'E1','E2','E3'} and trig)

    def test_breadth_reference(self):
        for arm in ('BS7','BSC7'):
            ok,msg,t=R.audit_trace(self.cb,arm,self.view,self.plan['tau6']['value'],self.plan['tau7']['value'])
            self.assertTrue(ok,(arm,msg));self.assertEqual(t['steps_checked'],t['steps'])

    def test_reference_detects_certificate_flip(self):
        c=copy.deepcopy(self.c2);tr=c['arms']['SC7']['trace']
        r=next(r for r in tr if r['certificate'] is not None);r['certificate']=1-r['certificate'] if r['certificate']<2 else 0
        ok,_,_=R.audit_trace(c,'SC7',self.view,self.plan['tau6']['value'],self.plan['tau7']['value']);self.assertFalse(ok)

    def test_rules_differ_only_in_calm_branch(self):
        s,c=self.c2['arms']['S7']['trace'],self.c2['arms']['SC7']['trace']
        rules={r.get('cert_rule') for r in c}
        self.assertTrue(rules<={'Y1k','Y1k-recent','tracked-calm','downgraded',None},rules)
        self.assertTrue({r.get('cert_rule') for r in s}<={'Y1k','Y1k-recent','downgraded',None})


if __name__=='__main__':unittest.main()
