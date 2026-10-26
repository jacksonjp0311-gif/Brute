"""experiments/brute_study_011.py + scripts/run_reference_011.py
on smoke seeds only (4190001-4190030): arms, trace fields, seed guard, smoke selection, J9 / SP8 audit."""
import json,tempfile,unittest
from pathlib import Path
import experiments.brute_study_011 as S
import experiments.v090_reference as R
from experiments.brute_common import VerificationError
from experiments.brute_common_011 import load,PLAN
import scripts.run_reference_011 as G


class Study011(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=load(PLAN);_,cls.case=S.run_job(('smoke-2x2','cycle3',4190001,0.35),cls.plan)

    def test_arms_and_fields(self):
        c=self.case;self.assertEqual(tuple(c['arms']),S.ARMS_2X2);self.assertEqual(c['schema'],'brute.case.v9_0')
        J=c['arms']['J9'];self.assertEqual(len(J['trace']),44)
        self.assertTrue(all('hull_union' in r and 'hull_unknown' in r for r in J['trace']))
        self.assertTrue(all('hull_union' not in r for r in c['arms']['SP8']['trace']))
        self.assertEqual(J['diagnostics']['window_K'],4)
        for r in J['trace']:
            if r['certificate'] is not None:self.assertTrue(r['cert_rule'].endswith('+whull'))

    def test_j9_certifies_subset_of_hull(self):
        for r in self.case['arms']['J9']['trace']:
            if r['certificate'] is not None and r['hull_union'] is not None:
                self.assertEqual(r['hull_union'][str(r['action'])],[r['certificate']])

    def test_reference_agrees(self):
        v=R.plan_view(self.plan)
        for a in ('J9','SP8'):
            ok,msg,_=R.audit_trace(self.case,a,v,self.plan['tau6']['value']);self.assertTrue(ok,(a,msg))

    def test_seed_guard(self):
        with self.assertRaises(VerificationError):S.run_job(('2x2','cycle3',4190001,0.35),self.plan)
        with self.assertRaises(VerificationError):S.run_job(('smoke-2x2','cycle3',4010001,0.35),self.plan)

    def test_smoke_and_heldout_jobs(self):
        J=S.smoke_jobs(self.plan,'2x2');self.assertEqual(len(J),16);self.assertTrue(all(4190001<=j[2]<=4190016 for j in J))
        H=S.jobs_for(self.plan,'2x2');self.assertEqual(len(H),792);self.assertEqual(sum(j[1]=='drift4' for j in H),288)

    def test_g11_mandatory_is_216(self):
        self.assertEqual(len(G.mandatory_keys(self.plan,'2x2')),216)


if __name__=='__main__':unittest.main()
