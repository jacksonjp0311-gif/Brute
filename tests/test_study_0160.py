"""Study-018 runner tests: job layout (360 main + 120 stress, one stream), seed checks, flip array (#97 item 5), NoisyWorld
B recount, and one smoke case audited by experiments/v0160_reference.py (0 mismatches)."""
import unittest
import experiments.v0160_reference as REF
from experiments.brute_study_018 import jobs_for,check_job,run_job,flip_array,load,PLAN,key
from experiments.brute_common import VerificationError


class Study0160(unittest.TestCase):
    def test_jobs(self):
        plan=load(PLAN);J=jobs_for(plan,'transfer')
        self.assertEqual(len(J),480);self.assertEqual(len({key(j) for j in J}),480)
        self.assertEqual([j[0] for j in J],['main']*360+['stress']*120);self.assertEqual(jobs_for(plan,'main'),J[:360])
        self.assertEqual(len(jobs_for(plan,'smoke-transfer')),32);self.assertEqual(len(jobs_for(plan,'smoke-api')),4)
        for j in jobs_for(plan,'smoke-transfer')+J[:3]+J[-3:]:check_job(j,plan)
        for bad in (('main','cycle3',8410001,0.05),('stress','cycle3',8410001,0.02),('main','cycle3',8420001,0.0),
                    ('smoke-api','cycle3',8410001,0.02),('transfer','cycle3',8410001,0.0)):
            with self.assertRaises(VerificationError):check_job(bad,plan)

    def test_flip_array(self):
        self.assertFalse(flip_array(8490001,0.0).any());self.assertEqual(flip_array(8490001,0.02).shape,(45,2))
        self.assertTrue((flip_array(8490001,0.05)==REF.flip_array(8490001,0.05)).all())

    def test_case_audit(self):
        plan=load(PLAN);_,c=run_job(('smoke-transfer','switch3',8490003,0.02),plan)
        REF.audit_case(c,plan)
        self.assertEqual(c['noisy']['RGN4_0']['support'],c['bounded']['4']['support'])
        self.assertEqual(sum(b is not None for o in [c['initial_visible']]+[r['observed'] for r in c['arms']['SP8']['trace']] for b in o),c['B'])


if __name__=='__main__':unittest.main()
