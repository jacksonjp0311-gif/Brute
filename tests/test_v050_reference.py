"""Self-checks of the v0.5.0 second implementation (no brute import). Seeds here are smoke seeds outside every study range."""
import unittest
from experiments import v050_reference as R
from experiments.v90_independent_reference import ref_initial,ref_support,ref_observe
from experiments.v030_independent_reference import score,y1k_union
from bgr89.worlds import world,actions

SMOKE=(901,902,903)


class TestGeneralisedEnumeration(unittest.TestCase):
    def test_k2_s2_equals_frozen_v090_reference(self):
        """With k=2, m=4 the generalised rows give the same supports, saturation, Y1k and LU-R scores as the frozen code."""
        for fam in ('cycle3','switch3','unstructured3'):
            for seed in SMOKE:
                w=world(seed,fam);h=w.start;o=w.observed(h,0.35,-1)
                a4=ref_initial(o);b4=R.k_initial(R.codes_of(o,2),2);a5=ref_initial(o);b5=R.k_initial(R.codes_of(o,2),2);s='supported'
                for i,a in enumerate(actions(seed,30)):
                    for b in (0,1):
                        self.assertEqual(ref_support(a4,b,4),R.k_support(b4,b,4,2,4))
                        self.assertEqual(ref_support(a5,b,5),R.k_support(b5,b,5,2,4))
                        self.assertEqual(y1k_union(a4,b,R.codes_of(o,2),4),R.k_y1k(b4,b,R.codes_of(o,2),4,2,4))
                        self.assertEqual(score(a4,s,a5,s,False,b,4,5,160000,160000,True),R.k_score(b4,s,b5,s,False,b,4,5,2,4,160000))
                    self.assertEqual(all(len(m.outputs)==4 for m in a4),R.k_saturated(b4,4))
                    h=w.next(h,a);o=w.observed(h,0.35,i)
                    a4,s=ref_observe(a4,a,o,4,160000);b4,t=R.k_observe(b4,a,R.codes_of(o,2),4,2,160000);self.assertEqual(s,t)
                    a5,_=ref_observe(a5,a,o,5,160000);b5,_=R.k_observe(b5,a,R.codes_of(o,2),5,2,160000)
                    self.assertEqual(len(a4),len(b4));self.assertEqual(len(a5),len(b5))
                    if s!='supported':break

    def test_budget_raises(self):
        with self.assertRaises(R.RefBudget):
            r=R.k_initial(frozenset(range(4)),2)
            for a in (0,1,0,1,1,0):r,_=R.k_observe(r,a,frozenset(range(4)),6,2,50)

    def test_breadth_worlds_shape(self):
        for fam,(n,k,s) in {'big6':(6,2,2),'sens3':(4,2,3),'act3':(4,3,2),'ood6s3':(6,2,3)}.items():
            w=R.breadth_world(901,fam);self.assertEqual((w.n,w.k,w.s),(n,k,s))
            self.assertTrue(all(0<=x<2**s for x in w.emissions));self.assertEqual(len(R.passive_actions(901,64,k)),64)
        self.assertEqual(R.passive_actions(901,44,2),actions(901,44))

    def test_choose(self):
        self.assertEqual(R.choose([0.,0.,0.],2),2);self.assertEqual(R.choose([0.,1.,1.],0),1)
        self.assertEqual(R.choose([1.,1.,0.],2,[3.,2.,0.]),1);self.assertEqual(R.choose([1.,1.],0,[2.,2.]),0)


if __name__=='__main__':unittest.main()
