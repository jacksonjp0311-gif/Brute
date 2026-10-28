"""brute/anytimemargin.py (BRUTE_PLAN_021): anytime boundary equals the experiments/v0190_reference.py dict DP, is
prefix-stable, spends A(b) < delta; AnytimeRegionSpace equals the frozen SeqMarginRegionSpace run with the same boundary."""
import random,unittest
from fractions import Fraction
from brute.anytimemargin import anytime_boundary,AnytimeBoundary,allowance,anytime_supports,PI_U
from brute.seqmargin import seqmargin_supports
import experiments.v0190_reference as R


def traj(seed,T=30,flips=2):
    rnd=random.Random(seed);out=[[0,1],[1,0]];st=0;acts=[];obs=[]
    nxt=[[0,1],[1,1]]
    for _ in range(T):
        a=rnd.randrange(2);st=nxt[st][a];o=list(out[st]);acts.append(a);obs.append(o)
    for i in rnd.sample(range(T),flips):obs[i][rnd.randrange(2)]^=1
    return (0,1),acts,[tuple(o) for o in obs]


class Anytime0190(unittest.TestCase):
    def test_reference_and_prefix(self):
        m=anytime_boundary(256);self.assertEqual(m,R.ref_anytime_boundary(256,Fraction(1,50),Fraction(1,100)))
        B=AnytimeBoundary();self.assertEqual(B.extend(40),m[:41]);self.assertEqual(B.extend(10),m[:11]);self.assertEqual(B.extend(256),m)
        self.assertEqual(PI_U,Fraction(355,113));self.assertTrue(all(x<=y for x,y in zip(m,m[1:])))
        self.assertLess(allowance(10**4),Fraction(1,100));self.assertEqual(allowance(0),0)
        self.assertEqual([m[b] for b in (4,8,12,16,32,116)],[1,2,2,3,5,10])

    def test_validation(self):
        for bad in (-1,True,1.5):
            with self.assertRaises(ValueError):anytime_boundary(bad)
        for kw in ({'eps_bar':0.5},{'delta':0},{'delta':1}):
            with self.assertRaises(ValueError):anytime_boundary(4,**kw)

    def test_region_space_equals_fixed_boundary(self):
        for seed in (1,2):
            ini,a,o=traj(seed);bd=anytime_boundary(2+2*len(a))
            A=anytime_supports(ini,a,o,4);F=seqmargin_supports(ini,a,o,4,bd)
            self.assertEqual(A['support'],F['support']);self.assertEqual(A['m'],F['m'])


if __name__=='__main__':unittest.main()
