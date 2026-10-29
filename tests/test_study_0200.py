"""Study-023 runner tests: job layout (360 main + 30 stress = first quarter of each range, deviation #110; reproset main[::6]; smoke
blocks), seed checks, tag-23 flip array, arm sets, and one eps-0.02 smoke case audited by experiments/v0200_reference.py
(0 mismatches; RGL4, RGNA4, RGNB4, RGN4_or and the 28-action RGL4 prefix control)."""
import unittest
import experiments.v0200_reference as REF
from experiments.brute_study_023 import jobs_for,check_job,run_job,flip_array,load,PLAN,key
from experiments.brute_common import VerificationError


class Study0200(unittest.TestCase):
    def test_jobs(self):
        plan=load(PLAN);J=jobs_for(plan,'transfer')
        self.assertEqual(len(J),390);self.assertEqual(len({key(j) for j in J}),390)
        self.assertEqual([j[0] for j in J],['main']*360+['stress']*30);self.assertEqual(jobs_for(plan,'main'),J[:360])
        self.assertEqual(jobs_for(plan,'reproset'),J[:360][::6]);self.assertEqual(len(jobs_for(plan,'reproset')),60)
        self.assertEqual({j[3] for j in J[:360]},{0.0,0.01,0.02});self.assertEqual({j[3] for j in J[360:]},{0.05})
        st={(j[1],j[2]) for j in J[360:]};self.assertIn(('ood4',8940012),st);self.assertNotIn(('ood4',8940013),st)
        self.assertIn(('cycle3',8910006),st);self.assertNotIn(('cycle3',8910007),st)
        self.assertEqual(len(jobs_for(plan,'smoke-transfer')),32);self.assertEqual(len(jobs_for(plan,'smoke-api')),4)
        for j in jobs_for(plan,'smoke-transfer')+J[:3]+J[-3:]:check_job(j,plan)
        for bad in (('main',J[0][1],J[0][2],0.05),('stress',J[0][1],J[0][2],0.02),('main','cycle3',8990001,0.0),
                    ('transfer',J[0][1],J[0][2],0.0)):
            with self.assertRaises(VerificationError,msg=str(bad)):check_job(bad,plan)

    def test_flip_array_and_arms(self):
        self.assertFalse(flip_array(8990001,0.0).any());self.assertEqual(flip_array(8990001,0.02).shape,(89,2))
        self.assertTrue((flip_array(8990005,0.05)==REF.flip_array(8990005,0.05)).all())
        self.assertEqual(REF.arms_for(0.0),('RG4','RGL4','RGNA4','RGN4_or'))

    def test_case_audit(self):
        plan=load(PLAN);job=('smoke-transfer','unaliased2',8990005,0.02)
        _,c=run_job(job,plan);ok,msg=REF.audit_case(c,plan);self.assertTrue(ok,msg)
        self.assertEqual(c['schema'],'brute.case.v20_0');self.assertEqual(len(c['summary']['per_step']['RGL4']),88)
        self.assertNotIn('perbit',c['summary']);self.assertTrue(c['prefix28']['identical'])


if __name__=='__main__':unittest.main()
