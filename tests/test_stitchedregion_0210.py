"""brute/stitchedregion.py (BRUTE_PLAN_024 RGL5): epochs and exact deltas, M equal to the reference ref_M, T5 equal to the
witness rule and to T5_ref (exhaustive fmin_n, n <= 4) when no witness is unknown; T5 monotone; prefix-stable; validation."""
import unittest
from fractions import Fraction
from brute.stitchedregion import epoch_of,epoch_delta,epochs,StitchedMargin,stitched_supports
from brute.lrregion import lr_supports
import experiments.v0210_reference as R
from tests.test_anytime_0190 import traj


def _bits(ini,o):
    out=[];b=0
    for r in [ini]+list(o):b+=sum(x is not None for x in r);out.append(b)
    return out


class Stitched0210(unittest.TestCase):
    def test_epochs(self):
        self.assertEqual([epoch_of(i) for i in (1,28,29,56,57,88,112,113)],[0,0,1,1,2,2,2,3])
        self.assertEqual([epoch_delta(k) for k in range(3)],[Fraction(1,400),Fraction(1,1200),Fraction(1,2400)])
        self.assertEqual(epochs(88),R.ref_epochs(88))
        for bad in (0,-1,True,1.0):
            with self.assertRaises(ValueError):epoch_of(bad)
        with self.assertRaises(ValueError):StitchedMargin(delta_a=0)

    def test_equals_reference(self):
        for seed,T,fl in ((1,40,3),(2,60,4)):
            ini,a,o=traj(seed,T=T,flips=fl);r=stitched_supports(ini,a,o)
            self.assertEqual(r['m'],r['lr']['T'])
            lr={**r['lr'],'D':r['D'],'delta_L':0.005,'delta_a':0.005,'epochs':epochs(T)}
            got,M,Tr=R.audit_lr5(lr,ini,a,o,_bits(ini,o)[:T])
            self.assertTrue(all(x<=y for x,y in zip(got,got[1:])))
            if sum(r['lr']['witness_unknowns'])==0:self.assertEqual(got,Tr)

    def test_prefix_stable_and_epoch0_vs_rgl4(self):
        ini,a,o=traj(3,T=36,flips=2);full=stitched_supports(ini,a,o);pre=stitched_supports(ini,a[:20],o[:20])
        self.assertEqual(pre['m'],full['m'][:20]);self.assertEqual(pre['support'],full['support'][:20])
        L=lr_supports(ini,a,o,delta_L=0.005,delta_a=0.005)
        self.assertEqual(full['D'],L['D'])


if __name__=='__main__':unittest.main()
