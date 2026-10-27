"""Scoring-freeze tests for study-018 (make_gates_018 / make_paired_018 / make_reproducibility_018 / clean_clone_018)."""
import math,unittest
from experiments.brute_common_018 import PLAN,load
import scripts.make_gates_018 as G
import scripts.make_paired_018 as P
import scripts.make_reproducibility_018 as R
import scripts.clean_clone_018 as CC


class TestScoring018(unittest.TestCase):
    def test_cp_upper_exact(self):
        self.assertAlmostEqual(G.cp_upper(0,240),1-0.05**(1/240),places=7)   # k = 0 closed form
        self.assertEqual(G.cp_upper(5,5),1.0)
        p=G.cp_upper(3,240);cdf=sum(math.comb(240,i)*p**i*(1-p)**(240-i) for i in range(4))
        self.assertAlmostEqual(cdf,0.05,places=6)

    def test_p_exceed(self):
        self.assertAlmostEqual(G.p_exceed(10,0.5,9),0.5**10)
        self.assertEqual(G.p_exceed(50,0.0,0),0.0)

    def test_criteria_cover_plan(self):
        crit=set(load(PLAN)['criteria']);built={'GNS_noise_soundness','GN0_control','GS_a6_soundness','G_recount','GS_ref6_reference_audit',
            'GAPI6_certify6','G10_compute','G12_reproducibility','G13_frozen_controls_reproduce','GTI_test_isolation','G_RT_study_runtime','G_HB_heartbeat_gap'}
        self.assertEqual(crit,built)

    def test_bootstrap_registration(self):
        self.assertEqual(P.SEED,20261029);self.assertIn('2000 resamples, seed 20261029',load(PLAN)['metrics']['bootstrap'])

    def test_subsets(self):
        mk=lambda e,b='main':{'eps':e,'block':b}
        self.assertTrue(P.SUBSETS['eps2'](mk(0.02)) and P.SUBSETS['noisy'](mk(0.01)) and not P.SUBSETS['noisy'](mk(0.0)))
        self.assertTrue(P.SUBSETS['stress'](mk(0.05,'stress')) and not P.SUBSETS['eps0'](mk(0.0,'stress')))

    def test_repro_key_matches_job_key(self):
        from experiments.brute_study_018 import jobs_for,key
        j=jobs_for(load(PLAN),'main')[0];fam,seed,eps=j[1],j[2],j[3]
        self.assertEqual(R._key({'block':'main','family':fam,'seed':seed,'eps':eps}),key(j))
        self.assertEqual(len(jobs_for(load(PLAN),'main')[0::3]),120)

    def test_clean_clone_inputs(self):
        self.assertIn('results/study-018/repro/main/SEAL.json',CC.TRACKED)
        self.assertEqual(CC.SCRIPTS,('scripts/make_paired_018.py','scripts/make_reproducibility_018.py','scripts/make_gates_018.py'))


if __name__=='__main__':unittest.main()
