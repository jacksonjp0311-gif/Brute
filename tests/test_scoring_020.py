"""Scoring-freeze tests for study-020 (make_gates_020 / make_paired_020 / make_reproducibility_020 / clean_clone_020)."""
import math,unittest
import numpy as np
from experiments.brute_common_020 import PLAN,load
import scripts.make_gates_020 as G
import scripts.make_paired_020 as P
import scripts.make_reproducibility_020 as R
import scripts.clean_clone_020 as CC


class TestScoring020(unittest.TestCase):
    def test_cp_upper_exact(self):
        self.assertAlmostEqual(G.cp_upper(0,240),1-0.05**(1/240),places=7)
        p=G.cp_upper(2,240);cdf=sum(math.comb(240,i)*p**i*(1-p)**(240-i) for i in range(3))
        self.assertAlmostEqual(cdf,0.05,places=6)

    def test_criteria_cover_plan(self):
        built={'GLH_horizon','GLH_early_control','GS_a8_soundness','G_recount','GS_ref8_reference_audit','GAPI8','G10_compute',
               'G12_reproducibility','G13_frozen_controls_reproduce','GTI_test_isolation','G_RT_study_runtime','G_HB_heartbeat_gap'}
        self.assertEqual(set(load(PLAN)['criteria']),built);self.assertEqual(G.EARLY_CI,(0.04053,0.065436))

    def test_bootstrap(self):
        self.assertEqual((P.SEED,P.B),(20261028,10000));self.assertIn('10000 resamples',load(PLAN)['metrics']['CI'])
        cs=[{'v':float(i%2)} for i in range(10)];r=P.contrast(cs,lambda c:c['v'],'x')
        self.assertEqual(r['mean'],0.5);self.assertEqual(r,P.contrast(cs,lambda c:c['v'],'x'));self.assertLess(r['ci95'][0],0.5)
        rng=np.random.default_rng(20261028);D=np.array([c['v'] for c in cs]);b=D[rng.integers(0,10,size=(10000,10))].mean(1)
        self.assertEqual(r['ci95'],[round(float(np.percentile(b,2.5)),6),round(float(np.percentile(b,97.5)),6)])

    def test_subsets(self):
        mk=lambda e,b='main':{'eps':e,'block':b}
        self.assertTrue(P.SUBSETS['eps2'](mk(0.02)) and P.SUBSETS['noisy'](mk(0.01)) and not P.SUBSETS['noisy'](mk(0.0)))
        self.assertTrue(P.SUBSETS['stress'](mk(0.05,'stress')) and P.SUBSETS['stress'](mk(0.05,'smoke-transfer')) and not P.SUBSETS['eps0'](mk(0.0,'stress')))
        self.assertTrue(G.is_main(mk(0.01)) and not G.is_main(mk(0.05,'stress')))

    def test_perbit_recount_bit_order(self):self.assertEqual([G._bit(2,0),G._bit(2,1)],[1,0])

    def test_api_expectation(self):
        from brute.api.certify7 import CONDITIONAL_ON
        self.assertEqual(G.API_EXPECT['conditional_on'],CONDITIONAL_ON);self.assertTrue(G.api_soundness()['matches'])

    def test_repro_key_matches_job_key(self):
        from experiments.brute_study_020 import jobs_for,key
        plan=load(PLAN);J=jobs_for(plan,'reproset');self.assertEqual(len(J),G.REPRO_EXPECTED)
        for j in (J[0],J[-1]):self.assertEqual(R._key({'block':j[0],'family':j[1],'seed':j[2],'eps':j[3]}),key(j))
        self.assertEqual(len(jobs_for(plan,'smoke-all')[0::3]),11)

    def test_expected_counts(self):
        from experiments.brute_study_020 import jobs_for
        self.assertEqual(sum(G.EXPECTED.values()),len(jobs_for(load(PLAN),'transfer')))

    def test_clean_clone_inputs(self):
        self.assertIn('results/study-020/repro/reproset/SEAL.json',CC.TRACKED)
        self.assertEqual(CC.SCRIPTS,('scripts/make_paired_020.py','scripts/make_reproducibility_020.py','scripts/make_gates_020.py'))


if __name__=='__main__':unittest.main()
