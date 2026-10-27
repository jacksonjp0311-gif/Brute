"""Study-017 runner tests on smoke seeds only: seed refusal, job layout, case format audited by v0150_reference."""
import unittest
from experiments.brute_study_017 import run_job,jobs_for,check_job,MAIN_ARMS,OOD5_ARMS,load,PLAN
from experiments.brute_common import VerificationError
from experiments.v0150_reference import audit_case,MAIN_ARMS as RM,OOD5_ARMS as RO


class Study017(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=load(PLAN)

    def test_jobs(self):
        J=jobs_for(self.plan,'transfer');self.assertEqual(len(J),432);self.assertEqual(sum(j[1]=='ood5' for j in J),72)
        self.assertEqual(len({j[2] for j in J if j[1]!='ood5'}),120)
        self.assertEqual(sum(j[1]=='ood5' for j in J[::3]),24);self.assertEqual(len(J[::3]),144)
        self.assertEqual(len(jobs_for(self.plan,'smoke-transfer')),10);self.assertEqual(len(jobs_for(self.plan,'smoke-drill')),3)

    def test_refuses(self):
        for j in (('transfer','cycle3',8190001,0.1),('transfer','cycle3',8390001,0.1),('smoke-transfer','cycle3',8310001,0.35),
                  ('smoke-transfer','switch3',8390001,0.35),('smoke-api','cycle3',8390001,0.35),('transfer','cycle3',8310001,0.2),
                  ('transfer','ood5',8310001,0.1),('transfer','ood5',8390016,0.1)):
            with self.assertRaises(VerificationError):check_job(j,self.plan)

    def test_constants(self):self.assertEqual((MAIN_ARMS,OOD5_ARMS),(RM,RO))

    def test_case_audit(self):
        for j in (('smoke-transfer','unaliased2',8390005,0.35),('smoke-transfer','ood5',8390017,0.35)):
            k,c=run_job(j,self.plan);self.assertEqual(audit_case(c,self.plan),(True,None),k)
            if j[1]!='ood5':
                self.assertEqual(len(c['stress']),24)
                for a in ('RG4','RGLX4','RGL4','RSXL4','DLFa_p','DLFa_n'):self.assertEqual(c['transfer'][a]['false_certificates'],0,a)
                self.assertEqual(c['transfer']['RSXL4']['first_cert_step'],c['transfer']['RG4']['first_cert_step'])


if __name__=='__main__':unittest.main()
