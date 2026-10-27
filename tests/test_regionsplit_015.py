"""brute.regionsplit unit tests (RSX rule, evidence bound, EB decision chain, agreement with the reference)."""
import itertools,unittest
from brute.regionsplit import bounded_sizes,rsx_choose,evidence_bound,eb_decide
from brute.boundedtransfer import rg_decide
from experiments.v0130_reference import rsx_choice


class RegionSplit(unittest.TestCase):
    def test_sizes(self):self.assertEqual(bounded_sizes((([1,2],0),(None,1))),[2,0])

    def test_rsx_vs_reference(self):
        for t,k0,k1,sp in itertools.product((3,8,9,20),range(5),range(5),(0,1)):
            self.assertEqual(rsx_choose(t,8,[k0,k1],sp),rsx_choice(t,8,[k0,k1],sp))
        with self.assertRaises(ValueError):rsx_choose(9,8,[1,2],2)

    def test_bound(self):
        self.assertEqual(evidence_bound({1:False,2:False,3:True,4:True},1),(3,4))
        self.assertEqual(evidence_bound({1:True,2:True,3:True,4:True},2),(1,3))
        self.assertEqual(evidence_bound({1:False,2:False,3:False,4:False},1),(None,None))
        with self.assertRaises(ValueError):evidence_bound({1:True},0)

    def test_eb_chain(self):
        self.assertEqual(eb_decide(3,8,2,None,None,None,None),(2,'sp8'))
        self.assertEqual(eb_decide(8,8,None,[1,2],[1,2],[1],3),(None,None))
        self.assertEqual(eb_decide(9,8,None,[1,2],[1],[2],3),(1,'rg'))
        self.assertEqual(eb_decide(9,8,None,[1,2],[1,2],[2],3),(2,'eb'))
        self.assertEqual(eb_decide(9,8,None,[1,2],[1,2],[3],3),(None,None))
        self.assertEqual(eb_decide(9,8,None,None,[1],[1],3),(None,None))
        self.assertEqual(eb_decide(9,8,None,[1,2],[1,2],None,None),(None,None))

    def test_containment(self):
        S=[None,[0],[1,2],[0,1,2,3]];R=[None,[0],[1],[1,2],[0,1,2,3]]
        for t,s,fb,rb,bd in itertools.product((5,9),S,R,R,(None,2,4)):
            g=rg_decide(t,8,None,s,fb)
            if g[0] is not None:self.assertEqual(eb_decide(t,8,None,s,fb,rb,bd),g)


if __name__=='__main__':unittest.main()
