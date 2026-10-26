import unittest
from experiments.brute_common_013 import load,PLAN,plan_view
from experiments import brute_study_013 as S
from experiments import v0100_reference as R
from experiments.worlds_013 import moore78
from experiments.brute_common import VerificationError

plan=load(PLAN)


class T(unittest.TestCase):
    def test_jobs(self):
        self.assertEqual(len(S.jobs_for(plan,'2x2')),792);self.assertEqual(len(S.jobs_for(plan,'big78')),288)
        self.assertEqual(len(S.jobs_for(plan,'transfer')),288)
        for b in S.BLOCKS:
            for j in S.smoke_jobs(plan,b):S.check_job(j,plan)
    def test_heldout_seed_guard(self):
        with self.assertRaises(VerificationError):S.check_job(('2x2','cycle3',6190001,0.35),plan)
        with self.assertRaises(VerificationError):S.check_job(('transfer','cycle3',6010001,0.35),plan)
    def test_j10_reference(self):
        k,c=S.run_job(S.smoke_jobs(plan,'2x2')[0],plan)
        self.assertEqual(set(c['arms']),set(S.ARMS_2X2))
        for arm in ('J10','SP8'):self.assertEqual(R.audit_trace(c,arm,plan_view(plan),plan['tau6']['value'])[:2],(True,None))
    def test_moore78(self):
        for s in (6190017,6190018):
            w=moore78(s);self.assertEqual(w.n,7+s%2);self.assertEqual(len(set(w.emissions)),4)
    def test_scope_files(self):
        import brute.soundtransfer as ST,inspect
        src=inspect.getsource(ST)
        for bad in ('EVALUATOR_ONLY','true_hidden','actual'):self.assertNotIn(bad,src)


if __name__=='__main__':unittest.main()
