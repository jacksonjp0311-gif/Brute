"""Unit tests for brute/driftsound.py (v0.6.0 R6/C6/BR6/BC6). Smoke seeds 980001-980030 only (BRUTE_PLAN_008)."""
import unittest
from brute.driftsound import DriftSoundLearner,BreadthDriftLearner,y1k_recent,RULES
from brute.region import RegionSpace
from experiments.brute_common_008 import load,PLAN,plan_view,plan006_keys
from experiments.brute_study_008 import run_case_2x2,check_job
from bgr90.symbolic import mask_for_observation
from experiments.worlds_008 import world,next_hidden
from bgr89.worlds import actions


class TestDriftSound(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=load(PLAN);cls.v=plan_view(cls.plan);check_job(('smoke-2x2','cycle3',980001,0.35),cls.plan)
        cls.case=run_case_2x2(980001,'cycle3',0.35,cls.plan,cls.plan['tau6']['value'],arms=('R6','C6','A5'),block='smoke-2x2')

    def test_rules(self):
        self.assertEqual(RULES,('RO','CT'))
        with self.assertRaises(ValueError):DriftSoundLearner(4,5,160000,160000,0.7,0.02,8,1.6,None,rule='X')

    def test_actions_equal_a5(self):
        A=[r['action'] for r in self.case['arms']['A5']['trace']]
        for arm in ('R6','C6'):self.assertEqual([r['action'] for r in self.case['arms'][arm]['trace']],A)

    def test_certificates_subset_relations(self):
        """R6 certificates are a subset of A5's (aged edges only add codes); C6 certificates are a superset of A5's."""
        def certs(arm):
            out=set()
            for r in self.case['arms'][arm]['trace']:
                for x in (r,r['counterfactual']):
                    if x['certificate'] is not None:out.add((r['step'],x is r))
            return out
        self.assertLessEqual(certs('R6'),certs('A5'));self.assertGreaterEqual(certs('C6'),certs('A5'))

    def test_y1k_recent_matches_y1k_without_aged_edges(self):
        truth=world(980001,'cycle3');h=truth.start;sp=RegionSpace(4,160000)
        sp.initialize(truth.observed(h,0.35,-1))
        for i,a in enumerate(actions(980001,12)):
            h=next_hidden(truth,h,a,i)
            sp.observe(a,truth.observed(h,0.35,i))
        if sp.status!='supported':self.skipTest('region not supported')
        m=mask_for_observation(sp.evidence[-1][1])
        for b in (0,1):
            y=sp.y1k(b,m);r0,_=y1k_recent(sp.region,b,m,0);rT,_=y1k_recent(sp.region,b,m,sp.region.T)
            self.assertEqual(r0,y);self.assertTrue(set(y)<=set(rT))
        sp.close()

    def test_cert_rule_and_events_recorded(self):
        for arm in ('R6','C6'):
            d=self.case['arms'][arm]['diagnostics'];self.assertIn('drift_events',d);self.assertEqual(d['rule'],'RO' if arm=='R6' else 'CT')
            for r in self.case['arms'][arm]['trace']:
                for x in (r,r['counterfactual']):
                    self.assertIn(x['cert_rule'],(None,'Y1k','Y1k-recent','tracked-calm','downgraded'))
                    if x['certificate'] is not None:self.assertIn(x['cert_rule'],('Y1k','Y1k-recent','tracked-calm'))

    def test_retry_keeps_rule(self):
        p6=plan006_keys(self.v)
        L=DriftSoundLearner(p6['family_state_cap'],p6['margin_state_cap'],160000,160000,p6['prediction_smoothing'],
                            p6['open_world_reserve_epsilon'],8,self.plan['tau6']['value'],None,rule='CT')
        truth=world(980001,'cycle3');L.initialize(truth.observed(truth.start,0.35,-1))
        N=L.retry();self.assertIsInstance(N,DriftSoundLearner);self.assertEqual(N.rule,'CT');N.close();L.close()


if __name__=='__main__':unittest.main()
