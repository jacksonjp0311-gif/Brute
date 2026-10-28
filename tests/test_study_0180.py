"""Study-020 runner tests: job layout (360 main + 120 stress; reproset main[::3]; smoke blocks), seed checks, tag-20 flip
array (#103 item 4), and smoke cases audited by experiments/v0180_reference.py (0 mismatches)."""
import unittest
import experiments.v0180_reference as REF
from experiments.brute_study_020 import jobs_for,check_job,run_job,flip_array,load,PLAN,key
from experiments.brute_common import VerificationError


class Study0180(unittest.TestCase):
    def test_jobs(self):
        plan=load(PLAN);J=jobs_for(plan,'transfer')
        self.assertEqual(len(J),480);self.assertEqual(len({key(j) for j in J}),480)
        self.assertEqual([j[0] for j in J],['main']*360+['stress']*120);self.assertEqual(jobs_for(plan,'main'),J[:360])
        self.assertEqual(jobs_for(plan,'reproset'),J[:360][::3]);self.assertEqual(len(jobs_for(plan,'reproset')),120)
        self.assertEqual({j[3] for j in J[:360]},{0.0,0.01,0.02});self.assertEqual({j[3] for j in J[360:]},{0.05})
        self.assertEqual(len(jobs_for(plan,'smoke-transfer')),32);self.assertEqual(len(jobs_for(plan,'smoke-api')),4)
        self.assertEqual(len(jobs_for(plan,'smoke-drill')),12);self.assertEqual(jobs_for(plan,'smoke-all'),jobs_for(plan,'smoke-transfer'))
        for j in jobs_for(plan,'smoke-transfer')+J[:3]+J[-3:]:check_job(j,plan)
        for bad in (('main',J[0][1],J[0][2],0.05),('stress',J[0][1],J[0][2],0.02),('main','cycle3',8690001,0.0),
                    ('transfer',J[0][1],J[0][2],0.0),('smoke-api','cycle3',8690001,0.02)):
            with self.assertRaises(VerificationError,msg=str(bad)):check_job(bad,plan)

    def test_flip_array(self):
        self.assertFalse(flip_array(8690001,0.0).any());self.assertEqual(flip_array(8690001,0.02).shape,(89,2))
        self.assertTrue((flip_array(8690005,0.05)==REF.flip_array(8690005,0.05)).all())

    def test_case_audit(self):
        plan=load(PLAN)
        for job in (('smoke-transfer','switch3',8690003,0.0),('smoke-transfer','switch3',8690003,0.01)):
            _,c=run_job(job,plan);ok,msg=REF.audit_case(c,plan);self.assertTrue(ok,msg)
            self.assertEqual(c['schema'],'brute.case.v18_0');self.assertEqual(len(c['summary']['per_step']['RGNB4']),88)
            self.assertEqual(c['summary']['perbit']['false_bits'],0)


if __name__=='__main__':unittest.main()
