import unittest
from experiments.brute_common_012 import load,PLAN,plan_view
from experiments import brute_study_012 as S
from experiments import v0100_reference as R
from experiments.worlds_012 import moore78
from brute.transfer import learn_motifs,expand
from experiments.brute_common import VerificationError

plan=load(PLAN)


class T(unittest.TestCase):
    def test_jobs(self):
        self.assertGreater(len(S.jobs_for(plan,'2x2')),0);self.assertEqual(len(S.jobs_for(plan,'big78')),144)
        self.assertEqual(len(S.jobs_for(plan,'transfer')),288)
        for b in S.BLOCKS:
            for j in S.smoke_jobs(plan,b):S.check_job(j,plan)
    def test_heldout_seed_guard(self):
        with self.assertRaises(VerificationError):S.check_job(('2x2','cycle3',5190001,0.35),plan)
    def test_j10_reference(self):
        k,c=S.run_job(S.smoke_jobs(plan,'2x2')[0],plan)
        for arm in ('J10','SP8'):self.assertEqual(R.audit_trace(c,arm,plan_view(plan),plan['tau6']['value'])[:2],(True,None))
    def test_transfer_reference(self):
        for j in S.smoke_jobs(plan,'transfer')[::2]:
            k,c=S.run_job(j,plan);self.assertEqual(R.audit_transfer_case(c,plan),(True,None))
            self.assertEqual(c['transfer']['TRp']['false_certificates'],0)
    def test_moore78(self):
        for s in (5190017,5190018):
            w=moore78(s);self.assertEqual(w.n,7+s%2);self.assertEqual(len(set(w.emissions)),4)
    def test_library_matches_reference(self):
        for fam in ('cycle3','ood4'):
            lib=R.ref_library(fam,5190021);acts,codes=None,None
            codes,acts=R.ref_source_obs(5190021,fam)
            L=learn_motifs(codes,acts)
            for k in ('min_n','status','motif_count','motifs'):self.assertEqual(L[k],lib[k])


if __name__=='__main__':unittest.main()
