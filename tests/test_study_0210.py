"""Study-024 runner tests: job layout (360 main + 30 stress; reproset main[::6]; smoke blocks), seed checks, arm sets, and
one eps-0.02 smoke case audited by experiments/v0210_reference.py (0 mismatches; RGL5 plus the carried arms via strip)."""
import unittest
import experiments.v0210_reference as REF
from experiments.brute_study_024 import jobs_for,check_job,run_job,flip_array,load,PLAN,key,arms_for
from experiments.brute_common import VerificationError


class Study0210(unittest.TestCase):
    def test_jobs(self):
        plan=load(PLAN);J=jobs_for(plan,'transfer')
        self.assertEqual(len(J),390);self.assertEqual(len({key(j) for j in J}),390)
        self.assertEqual([j[0] for j in J],['main']*360+['stress']*30);self.assertEqual(jobs_for(plan,'main'),J[:360])
        self.assertEqual(jobs_for(plan,'reproset'),J[:360][::6]);self.assertEqual(len(jobs_for(plan,'reproset')),60)
        self.assertEqual({j[3] for j in J[:360]},{0.0,0.01,0.02});self.assertEqual({j[3] for j in J[360:]},{0.05})
        self.assertEqual(len(jobs_for(plan,'smoke-transfer')),32);self.assertEqual(len(jobs_for(plan,'smoke-api')),4)
        for j in jobs_for(plan,'smoke-transfer')+J[:3]+J[-3:]:check_job(j,plan)
        for bad in (('main',J[0][1],J[0][2],0.05),('stress',J[0][1],J[0][2],0.02),('main','cycle3',9090001,0.0),('transfer',J[0][1],J[0][2],0.0)):
            with self.assertRaises(VerificationError,msg=str(bad)):check_job(bad,plan)

    def test_arms(self):
        self.assertEqual(flip_array(9090001,0.02).shape,(89,2));self.assertFalse(flip_array(9090001,0.0).any())
        self.assertEqual(tuple(arms_for(0.02)),REF.arms_for(0.02));self.assertIn('RGL5',arms_for(0.0))

    def test_case_audit(self):
        from scripts.check_seeds_024 import smoke_family
        plan=load(PLAN);job=('smoke-transfer',smoke_family(9090005),9090005,0.02)
        _,c=run_job(job,plan);ok,msg=REF.audit_case(c,plan);self.assertTrue(ok,msg)
        self.assertEqual(c['schema'],'brute.case.v21_0');self.assertEqual(len(c['summary']['per_step']['RGL5']),88)
        self.assertTrue(c['prefix28_rgl5']['identical']);self.assertEqual(len(c['lr5']['T']),88)


if __name__=='__main__':unittest.main()
