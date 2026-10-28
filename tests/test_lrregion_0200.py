"""brute/lrregion.py (BRUTE_PLAN_023): exact offsets D = [3, 4, 5, 7], |H_n|, and T(b) equal to the numpy reference
(exhaustive fmin_n, n <= 4) on short noisy trajectories with no unknowns; witnesses re-simulate; T monotone."""
import unittest
from fractions import Fraction
from brute.lrregion import class_size,lr_offsets,lr_supports,LRBound
import experiments.v0200_reference as R
from tests.test_anytime_0190 import traj


class LRRegion0200(unittest.TestCase):
    def test_offsets(self):
        self.assertEqual([class_size(n) for n in (1,2,3,4)],[4,512,139968,67108864])
        self.assertEqual(lr_offsets(),[3,4,5,7]);self.assertEqual(lr_offsets(),R.ref_D())
        self.assertEqual(lr_offsets(eps_bar=Fraction(1,50),delta_L=Fraction(1,200)),[3,4,5,7]);self.assertIsNone(lr_offsets(eps_bar=0))
        for kw in ({'eps_bar':0.5},{'delta_L':0},{'delta_L':1},{'eps_bar':True}):
            with self.assertRaises(ValueError,msg=str(kw)):lr_offsets(**kw)

    def test_bound_equals_reference(self):
        for seed in (1,2):
            ini,a,o=traj(seed,T=24,flips=3);r=lr_supports(ini,a,o);T=r['lr']['T']
            self.assertEqual(sum(r['lr']['witness_unknowns']),0)
            fm={n:R.fmin_tables(n,ini,a,o) for n in (1,2,3,4)}
            ba=R.ref_anytime_boundary(2+2*len(a),Fraction(1,50),Fraction(1,200));ma=[ba[2*(i+1)] for i in range(len(a))]
            self.assertEqual(T,R.ref_T(fm,ma,R.ref_D()));self.assertEqual(r['m'],T)
            self.assertTrue(all(x<=y for x,y in zip(T,T[1:])))
            for i,W in enumerate(r['lr']['witnesses']):
                for w in W:self.assertLessEqual(R.sim_flips(w,ini,a[:i],o[:i]),w['w'])

    def test_eps0_is_exact(self):
        ini,a,o=traj(3,T=12,flips=0);b=LRBound(eps_bar=0)
        self.assertEqual(b.bound([ini]+list(o),a)['T'],0)


if __name__=='__main__':unittest.main()
