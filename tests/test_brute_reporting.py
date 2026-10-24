"""F6/F8 reporting: burn-in, coverage, selective risk, epsilon floor, v0.89 log-loss."""
import json,unittest
from math import log
from pathlib import Path
from brute.evaluation import run_case,aggregate
ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/'experiments/BRUTE_PLAN_002.json').read_text())


class BruteReporting(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cycle=run_case(930001,'cycle3',.1,PLAN,None)
        cls.ood5=run_case(980002,'ood5',.6,PLAN,None)
        cls.ood4=run_case(970001,'ood4',.1,PLAN,None)

    def test_burn_in_excluded_consistently(self):
        s=aggregate([self.cycle])['cycle3'];b=PLAN['burn_in']
        self.assertEqual(s['steps_all'],44);self.assertEqual(s['steps_post_burn_in'],44-b)
        post=self.cycle['trace'][b:]
        self.assertEqual(s['brute_certs_all'],sum(r['certificate'] is not None for r in self.cycle['trace']))
        self.assertAlmostEqual(s['coverage_post']['brute'],round(sum(r['certificate'] is not None for r in post)/len(post),6))
        self.assertEqual(sum(s['status_breakdown_post'].values()),44-b)
        self.assertAlmostEqual(s['logloss_post']['brute'],round(sum(r['logloss_brute'] for r in post)/len(post),6))

    def test_aggregate_reports_coverage_and_selective_risk(self):
        s=aggregate([self.ood5])['ood5']
        for k in ('brute','v090','v089'):
            self.assertIn(k,s['coverage_post']);self.assertIn(k,s['selective_risk_post'])
        self.assertGreater(s['coverage_post']['v090'],s['coverage_post']['brute'])
        self.assertEqual(s['selective_risk_post']['brute'],None if s['coverage_post']['brute']==0 else s['selective_risk_post']['brute'])

    def test_no_probability_zero_on_any_code(self):
        floor=PLAN['open_world_reserve_epsilon']/4
        for c in (self.cycle,self.ood5,self.ood4):
            for r in c['trace']:
                self.assertGreaterEqual(min(r['probabilities']),floor-1e-12)
                self.assertLessEqual(r['logloss_brute'],-log(floor)+1e-9)

    def test_legacy_logloss_recorded_when_legacy_valid(self):
        broken=self.ood4['diagnostics']['legacy_contradiction_step']
        self.assertIsNotNone(broken)
        for r in self.ood4['trace']:
            self.assertEqual(r['logloss_v089'] is not None,r['step']<=broken)
        self.assertTrue(all(r['logloss_v089'] is not None for r in self.cycle['trace']))


if __name__=='__main__':unittest.main()
