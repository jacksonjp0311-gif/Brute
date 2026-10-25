"""v0.4.0 unit tests: perm4 generator, ResumeBruteLearner resume rule, ConstraintRegion vs the enumeration."""
import unittest
from brute.resume import ResumeBruteLearner
from brute.geometry import ConstraintRegion
from experiments.worlds_006 import perm4


class Perm4(unittest.TestCase):
    def test_bijections_and_alias(self):
        for seed in range(50):
            w=perm4(seed)
            for a in (0,1):self.assertEqual(sorted(t[a] for t in w.transitions),[0,1,2,3])
            self.assertEqual(sorted(map(w.emissions.count,set(w.emissions))),[1,1,2])
            self.assertEqual(w.family,'perm4');self.assertEqual(perm4(seed).transitions,w.transitions)


class Resume(unittest.TestCase):
    def test_args(self):
        with self.assertRaises(ValueError):ResumeBruteLearner(depth=3)
        with self.assertRaises(ValueError):ResumeBruteLearner(fibre_w=1)

    def _stream(self,tau,seed=930002,family='cycle3',mask=.35):
        from brute.api.service_v040 import BruteServiceV040
        from tests.test_api_contract_v011 import stream
        reqs,_=stream(seed,family,mask,'brute.api/1.4');s=BruteServiceV040(tau=tau)
        for q in reqs:s.handle(q)
        return s.sessions['s']

    def test_resume_rule(self):
        L=self._stream(0.3)
        self.assertGreaterEqual(L.resumes,1);self.assertEqual(L.first_alarm_step,L.alarm_steps[0])
        self.assertIsNone(L.attestation)
        for r in L.resume_steps:self.assertTrue(any(a<r for a in L.alarm_steps))
        for r in L.resume_steps:   # a resume needs >= W steps after the alarm that it clears
            self.assertGreaterEqual(r-max(a for a in L.alarm_steps if a<r),L.window)
        d=L.diagnostics()
        for k in ('first_alarm_step','alarm_steps','resume_steps','resumes'):self.assertIn(k,d)

    def test_default_flags(self):
        self.assertEqual((ResumeBruteLearner.resume,ResumeBruteLearner.depth,ResumeBruteLearner.fibre_w),(True,1,0))


class Region(unittest.TestCase):
    def test_tiny(self):
        # constant code 2 under action 0: the 1-state machine is the unique quotient point; next code is 2
        r=ConstraintRegion(4,[1<<2]*4,[0,0,0]);self.assertTrue(r.feasible);self.assertEqual(r.support(0),(2,));r.close()
        # a contradiction is impossible for complete machines with masks only, but an empty mask is infeasible
        r=ConstraintRegion(2,[1<<2,0],[0]);self.assertFalse(r.feasible);r.close()


if __name__=='__main__':unittest.main()
