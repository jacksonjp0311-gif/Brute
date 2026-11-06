"""Tests for brute.certify/34h (v0.70.0): bitset preprocess + separating-word policy, no homing batch."""
import unittest
from brute.api.certify34h import API,Certifier34H,soundness
from brute.api.certify33h import Certifier33H

class T(unittest.TestCase):
    def test_api(self):
        self.assertEqual(API,'brute.certify/34h')
        self.assertIn('separating word only',soundness()['policy'])

    def test_no_batch_on_short_trace(self):
        c=Certifier34H((0,0),num_actions=2,family_bound=2,read_bits=2,seed=1,K=200,conflict_cap=5000,budget_conflicts=100000)
        try:
            for _ in range(50):
                w=c.propose()
                if w is None:break
                self.assertLessEqual(len(w),20,msg='34h must not append a 400-step homing batch')
                for a in w:c.observe(a,(0,0))
            R=c.result()
            self.assertIsNotNone(R.get('label'))
            self.assertEqual(R.get('batches'),0)
        finally:c.close()

    def test_inherits_bitset_preprocess(self):
        self.assertTrue(issubclass(Certifier34H,Certifier33H))
        self.assertTrue(callable(Certifier34H._p20))

if __name__=='__main__':unittest.main()
