"""Scoring-freeze tests for study-019 (make_gates_019 / make_paired_019 / make_reproducibility_019 / clean_clone_019)."""
import math,unittest
from experiments.brute_common_019 import PLAN,load
import scripts.make_gates_019 as G
import scripts.make_paired_019 as P
import scripts.make_reproducibility_019 as R
import scripts.clean_clone_019 as CC


class TestScoring019(unittest.TestCase):
    def test_cp_upper_exact(self):
        self.assertAlmostEqual(G.cp_upper(0,240),1-0.05**(1/240),places=7)
        self.assertAlmostEqual(G.cp_upper(0,48),1-0.05**(1/48),places=7)
        p=G.cp_upper(2,48);cdf=sum(math.comb(48,i)*p**i*(1-p)**(48-i) for i in range(3))
        self.assertAlmostEqual(cdf,0.05,places=6)

    def test_criteria_cover_plan(self):
        built={'GNB_sequential_margin','GNB_post_burn_control','GA3_alphabet3_soundness','GS_a7_soundness','G_recount',
               'GS_ref7_reference_audit','GAPI7_certify7','G10_compute','G12_reproducibility','G13_frozen_controls_reproduce',
               'GTI_test_isolation','G_RT_study_runtime','G_HB_heartbeat_gap'}
        self.assertEqual(set(load(PLAN)['criteria']),built)
        self.assertEqual(set(load(PLAN)['non_gated_reports']),{'R_gn0_full','R_boundary','R_RG4_noise','R_stress','R_oracle','R_bound',
                         'R_alphabet3_coverage','R_rates','R_heartbeat_attribution'})

    def test_bootstrap_registration(self):
        self.assertEqual(P.SEED,20261030);self.assertIn('2000 resamples, seed 20261030',load(PLAN)['metrics']['bootstrap'])

    def test_subsets(self):
        mk=lambda e,b='main',s='brute.case.v17_0':{'eps':e,'block':b,'schema':s}
        self.assertTrue(P.SUBSETS['eps2'](mk(0.02)) and P.SUBSETS['noisy'](mk(0.01)) and not P.SUBSETS['noisy'](mk(0.0)))
        self.assertTrue(P.SUBSETS['stress'](mk(0.05,'stress')) and not P.SUBSETS['eps0'](mk(0.0,'stress')))
        a=mk(0.02,'alphabet3','brute.case3.v17_0')
        self.assertFalse(any(f(a) for f in P.SUBSETS.values()));self.assertTrue(P.A3_SUBSETS['a3_eps2'](a) and not P.A3_SUBSETS['a3_eps0'](a))

    def test_api_expectation(self):
        from brute.api.certify7 import CONDITIONAL_ON
        self.assertEqual(G.API_EXPECT['conditional_on'],CONDITIONAL_ON);self.assertTrue(G.api_soundness()['matches'])

    def test_repro_key_matches_job_key(self):
        from experiments.brute_study_019 import jobs_for,key
        plan=load(PLAN);J=jobs_for(plan,'reproset');self.assertEqual(len(J),G.REPRO_EXPECTED)
        for j in (J[0],J[-1]):self.assertEqual(R._key({'block':j[0],'family':j[1],'seed':j[2],'eps':j[3]}),key(j))
        self.assertEqual(len(jobs_for(plan,'smoke-all')[0::3]),14)

    def test_expected_counts(self):
        from experiments.brute_study_019 import jobs_for
        self.assertEqual(sum(G.EXPECTED.values()),len(jobs_for(load(PLAN),'transfer')))

    def test_clean_clone_inputs(self):
        self.assertIn('results/study-019/repro/reproset/SEAL.json',CC.TRACKED)
        self.assertEqual(CC.SCRIPTS,('scripts/make_paired_019.py','scripts/make_reproducibility_019.py','scripts/make_gates_019.py'))


if __name__=='__main__':unittest.main()
