"""Study-019 runner tests: job layout (360 main + 120 stress + 96 alphabet3, one stream; reproset), seed checks, flip
array (#101 item 4), prefix data, rand4a3 generator, and one main + one alphabet3 smoke case audited by
experiments/v0170_reference.py (0 mismatches)."""
import unittest
import experiments.v0170_reference as REF
from experiments.brute_study_019 import (jobs_for,check_job,run_job,flip_array,world3,prefix_data,load,PLAN,key,_minimal,
                                         _strongly_connected)
from experiments.brute_common import VerificationError


class Study0170(unittest.TestCase):
    def test_jobs(self):
        plan=load(PLAN);J=jobs_for(plan,'transfer')
        self.assertEqual(len(J),576);self.assertEqual(len({key(j) for j in J}),576)
        self.assertEqual([j[0] for j in J],['main']*360+['stress']*120+['alphabet3']*96);self.assertEqual(jobs_for(plan,'main'),J[:360])
        self.assertEqual(jobs_for(plan,'alphabet3'),J[480:]);self.assertEqual(jobs_for(plan,'reproset'),J[:360][::3]+J[480:][::3])
        self.assertEqual(len(jobs_for(plan,'reproset')),152)
        self.assertEqual(len(jobs_for(plan,'smoke-transfer')),32);self.assertEqual(len(jobs_for(plan,'smoke-api')),4)
        self.assertEqual(len(jobs_for(plan,'smoke-a3')),8);self.assertEqual(len(jobs_for(plan,'smoke-drill')),12)
        self.assertEqual(jobs_for(plan,'smoke-all'),jobs_for(plan,'smoke-transfer')+jobs_for(plan,'smoke-a3'))
        for j in jobs_for(plan,'smoke-transfer')+jobs_for(plan,'smoke-a3')+J[:3]+J[-3:]:check_job(j,plan)
        for bad in (('main','cycle3',8510001,0.05),('stress','cycle3',8510001,0.02),('main','cycle3',8520001,0.0),
                    ('main','rand4a3',8550001,0.0),('alphabet3','rand4a3',8550001,0.01),('alphabet3','cycle3',8510001,0.0),
                    ('smoke-api','cycle3',8510009,0.02),('smoke-a3','rand4a3',8590001,0.0),('transfer','cycle3',8510001,0.0)):
            with self.assertRaises(VerificationError,msg=str(bad)):check_job(bad,plan)

    def test_flip_array(self):
        self.assertFalse(flip_array(8590001,0.0).any());self.assertEqual(flip_array(8590001,0.02).shape,(45,2))
        self.assertTrue((flip_array(8590001,0.05)==REF.flip_array(8590001,0.05)).all())

    def test_prefix(self):
        import numpy as np
        F=np.zeros((3,2),dtype=bool);F[1,1]=True
        self.assertEqual(prefix_data([(0,None),(1,1),(None,None)],F),([1,3,3],[0,1,1],[0,0,1]))

    def test_world3(self):
        for s in range(8590016,8590020):
            d,e=world3(s);self.assertEqual((d,e),REF.ref_world3(s));self.assertTrue(_strongly_connected(d) and _minimal(d,e))
        self.assertFalse(_minimal([[0,1,0],[1,0,1],[0,0,0],[0,0,0]],[0,0,0,0]))

    def test_case_audit(self):
        plan=load(PLAN)
        for job in (('smoke-transfer','switch3',8590003,0.02),('smoke-a3','rand4a3',8590018,0.02)):
            _,c=run_job(job,plan);ok,msg=REF.audit_case(c,plan);self.assertTrue(ok,msg)
        self.assertEqual(c['summary']['coverage'].keys(),{'RG4_3','RGN4_3','RGNB4_3'})


if __name__=='__main__':unittest.main()
