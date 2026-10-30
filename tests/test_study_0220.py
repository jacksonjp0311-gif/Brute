"""v0.22.0 lean study (BRUTE_PLAN_025_A2): the declared lean block and the amendment lock."""
import json,unittest
from collections import Counter
from experiments import brute_study_025 as S
from experiments.brute_common_025 import load,PLAN,sha,ROOT


class LeanBlock(unittest.TestCase):
    def test_counts(self):
        J=S.jobs_for(load(PLAN),'lean');self.assertEqual(len(J),90)
        self.assertEqual(Counter((b,e) for b,f,s,e in J),{('main',0.0):20,('main',0.01):20,('main',0.02):20,('stress',0.05):30})
        self.assertEqual(len(set(map(S.key,J))),90)

    def test_jobs_valid(self):
        p=load(PLAN)
        for j in S.jobs_for(p,'lean'):S.check_job(j,p)

    def test_a2_declares_counts(self):
        a2=load(ROOT/'experiments/BRUTE_PLAN_025_A2.json')
        self.assertEqual(a2['cases']['total'],90);self.assertEqual(a2['run']['cap_s'],1800)
        self.assertEqual(a2['authorization']['card'],'t130s540')
        self.assertEqual(a2['amends_sha256'],sha(PLAN))

    def test_heldout(self):self.assertIn('lean',S.HELDOUT)


if __name__=='__main__':unittest.main()
