"""Study-014 runner tests on smoke seeds only: seed refusal, case format audited by experiments/v0120_reference."""
import unittest
from experiments.brute_study_014 import run_job,jobs_for,check_job,dx_bounds,ARMS,load,PLAN
from experiments.brute_common import VerificationError
from experiments.v0120_reference import audit_case,dx_bounds as ref_dx,ARMS as REF_ARMS


class Study014(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.plan=load(PLAN)

    def test_jobs(self):
        J=jobs_for(self.plan,'transfer');self.assertEqual(len(J),288);self.assertEqual(len({j[2] for j in J}),96)
        self.assertEqual(len(jobs_for(self.plan,'smoke-transfer')),8);self.assertEqual(len(jobs_for(self.plan,'smoke-drill')),3)

    def test_refuses(self):
        for j in (('transfer','cycle3',7120001,0.1),('transfer','cycle3',7190001,0.1),('smoke-transfer','cycle3',7110001,0.35),
                  ('smoke-transfer','switch3',7190001,0.35),('smoke-api','cycle3',7190001,0.35),('transfer','cycle3',7110001,0.2)):
            with self.assertRaises(VerificationError):check_job(j,self.plan)

    def test_constants_match_reference(self):
        self.assertEqual(ARMS,REF_ARMS)
        for n in range(1,6):self.assertEqual(dx_bounds(n),ref_dx(n))

    def test_case_audit(self):
        k,c=run_job(('smoke-transfer','unaliased2',7190005,0.35),self.plan)
        self.assertEqual(audit_case(c,self.plan),(True,None));self.assertEqual(len(c['stress']),24)
        for a in ('RG4','DLFp','DLFn','DXp','DXn'):self.assertEqual(c['transfer'][a]['false_certificates'],0,a)


if __name__=='__main__':unittest.main()
