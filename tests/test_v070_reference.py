"""Second implementation v070_reference: mutation detection on a smoke P7 trace (planned action flips)."""
import unittest
from experiments.brute_common import load
from experiments.brute_study_009 import run_job,PLAN
from experiments import v070_reference as R


class Reference070(unittest.TestCase):
    def test_mutation_detected(self):
        plan=load(PLAN);c=run_job(('smoke-planning','cycle3',2190025,0.35),plan)[1]
        mc,inj=R.mutate([c],1,arms=('P7',),p7_actions=1);self.assertEqual(inj,{(0,'P7')})
        v=R.plan_view(plan);t6,t7=plan['tau6']['value'],plan['tau7']['value']
        self.assertTrue(R.audit_trace(c,'P7',v,t6,t7)[0]);self.assertFalse(R.audit_trace(mc[0],'P7',v,t6,t7)[0])


if __name__=='__main__':unittest.main()
