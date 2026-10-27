"""Study-015 runner tests on smoke seeds only: seed refusal, job layout, case format audited by v0130_reference."""
import unittest
from experiments.brute_study_015 import run_job,jobs_for,check_job,MAIN_ARMS,OOD5_ARMS,load,PLAN
from experiments.brute_common import VerificationError
from experiments.v0130_reference import audit_case,MAIN_ARMS as RM,OOD5_ARMS as RO


class Study015(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=load(PLAN)

    def test_jobs(self):
        J=jobs_for(self.plan,'transfer');self.assertEqual(len(J),360);self.assertEqual(sum(j[1]=='ood5' for j in J),72)
        self.assertEqual(len({j[2] for j in J if j[1]!='ood5'}),96)
        self.assertEqual(sum(j[1]=='ood5' for j in J[::3]),24);self.assertEqual(len(J[::3]),120)
        self.assertEqual(len(jobs_for(self.plan,'smoke-transfer')),10);self.assertEqual(len(jobs_for(self.plan,'smoke-drill')),3)

    def test_refuses(self):
        for j in (('transfer','cycle3',8120001,0.1),('transfer','cycle3',8190001,0.1),('smoke-transfer','cycle3',8110001,0.35),
                  ('smoke-transfer','switch3',8190001,0.35),('smoke-api','cycle3',8190001,0.35),('transfer','cycle3',8110001,0.2),
                  ('transfer','ood5',8110001,0.1),('transfer','ood5',8190016,0.1)):
            with self.assertRaises(VerificationError):check_job(j,self.plan)

    def test_constants(self):self.assertEqual((MAIN_ARMS,OOD5_ARMS),(RM,RO))

    def test_case_audit(self):
        for j in (('smoke-transfer','unaliased2',8190005,0.35),('smoke-transfer','ood5',8190017,0.35)):
            k,c=run_job(j,self.plan);self.assertEqual(audit_case(c,self.plan),(True,None),k)
            if j[1]!='ood5':
                self.assertEqual(len(c['stress']),24)
                for a in ('RG4','RSX4','DLFp','RSXp'):self.assertEqual(c['transfer'][a]['false_certificates'],0,a)


if __name__=='__main__':unittest.main()
