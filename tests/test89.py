"""Exact, no-reset latent causal learning and missingness/OOD tests."""
import unittest
from random import Random
from bgr89.latent import (LatentLearner,IncompatibleObservation,code_to_bits,machine_catalogue)
from bgr89.worlds import world,actions,FAMILIES
from bgr89.evaluation import run_case
from bgr89.baselines import SuffixFrequency
from experiments.v89_independent_reference import ScalarReference

class TestV89(unittest.TestCase):
    def test_catalogue_sizes_and_opaque_initial_gauge(self):
        for n,expected in ((1,4),(2,256),(3,46656)):
            tr,em=machine_catalogue(n)
            self.assertEqual(len(tr),expected)
            self.assertEqual(len(em),expected)
            self.assertEqual(tr.shape[1:],(n,2))

    def test_independent_scalar_reference_mixed_missingness(self):
        for initial,history in [((0,0),[(0,(None,1)),(1,(1,0)),(0,(None,None))]),
                                ((None,1),[(1,(1,None)),(1,(None,0)),(0,(0,1))])]:
            learner=LatentLearner();reference=ScalarReference()
            learner.initialize(initial);reference.initialize(initial)
            for a,seen in history:
                dist,support=learner.predict(a)
                independent,truth_support,count=reference.predict(a)
                self.assertEqual(support,truth_support)
                for x,y in zip(dist,independent):self.assertAlmostEqual(x,y,places=9)
                self.assertTrue(learner.observe(a,seen) is None)
                self.assertTrue(reference.observe(a,seen))
                self.assertEqual(sum(b.count for b in learner.banks.values()),sum(map(len,reference.groups.values())))
                self.assertEqual(learner.certify_state_count(),reference.certify_class())
                self.assertEqual(learner.certify_sensor_relation(),reference.certify_relation())

    def test_transactional_incompatible_transition(self):
        # Three visible phases with action 0 followed by a fourth distinct
        # hidden phase that cannot be explained by <=3-state machines.
        ood=world(9025,'ood4')
        learner=LatentLearner();hidden=ood.start
        learner.initialize(ood.observed(hidden,.2,-1))
        failed=False
        for t,a in enumerate(actions(9025,35)):
            hidden=ood.next(hidden,a);observed=ood.observed(hidden,.2,t)
            before=[(n,b.count,b.current.copy(),b.active.copy()) for n,b in learner.banks.items()]
            old_len=len(learner.history)
            try:learner.observe(a,observed)
            except IncompatibleObservation:
                failed=True
                self.assertEqual(len(learner.history),old_len)
                for (n,bank),(name,count,pos,mask) in zip(learner.banks.items(),before):
                    self.assertEqual(n,name);self.assertEqual(bank.count,count)
                    self.assertTrue((bank.current==pos).all() and (bank.active==mask).all())
                break
        self.assertTrue(failed)

    def test_conservative_sensor_proof(self):
        a=LatentLearner((1,))
        a.initialize((0,0))
        self.assertEqual(a.certify_sensor_relation(),'equal')
        # The n=1 hypothesis family is a *single constant emission*, known
        # from observation; no hidden unseen sensor code can occur.
        b=LatentLearner()
        b.initialize((0,0))
        self.assertIsNone(b.certify_sensor_relation())

    def test_two_hidden_states_same_visible_code_can_have_different_future(self):
        w=world(1033,'cycle3')
        found=False
        for s in range(w.n):
          for t in range(w.n):
            if s==t or w.emission(s)!=w.emission(t):continue
            for a in (0,1):
              if w.emission(w.next(s,a))!=w.emission(w.next(t,a)):found=True
        self.assertTrue(found,'Alias witnesses force history-dependent prediction')

    def test_no_secret_truth_leak_in_latent_learner(self):
        import inspect,bgr89.latent as latent
        source=inspect.getsource(latent)
        self.assertNotIn('from .worlds',source)
        self.assertNotIn('truth.next',source)

    def test_masks_not_imputed_as_true_bits(self):
        a=LatentLearner()
        a.initialize((None,None))
        count=a.snapshot()['supported_models']
        self.assertEqual(count,4+256+46656)
        a.observe(0,(None,None))
        self.assertEqual(a.snapshot()['supported_models'],count)
        self.assertIsNone(a.certify_state_count())

    def test_in_family_never_false_certifications(self):
        for family in FAMILIES[:-1]:
            for rate in (.1,.45,.7):
                case=run_case(21901,family,rate,steps=35)
                self.assertEqual(case['certification_errors'],0)
                self.assertIsNone(case['contradiction_step'])

    def test_size_not_automatically_identifiable(self):
        c=run_case(21901,'unaliased2',.1,steps=25)
        # Surviving three-state refinements can be observationally identical
        # to true two-state machines; never equate real state labels with the
        # minimal predictive quotient without proof.
        self.assertIsNone(c['state_count_identified'])

    def test_after_ood_rejection_all_new_certifications_abstain(self):
        case=run_case(9025,'ood4',.35,steps=44)
        step=case['contradiction_step']
        self.assertIsNotNone(step)
        self.assertTrue(all(r['certified'] is None and 'latent' not in r['prediction'] for r in case['trace'][step:]))

    def test_ood_errors_recorded_and_not_claimed_globally_sound(self):
        cases=[run_case(21940+j,'ood4',.35,steps=36) for j in range(8)]
        self.assertTrue(any(c['contradiction_step'] is not None for c in cases))
        self.assertTrue(any(c['certification_errors']>0 for c in cases))
        self.assertTrue(all(c['true_n_scoring_only']==4 for c in cases))

if __name__=='__main__':unittest.main()
