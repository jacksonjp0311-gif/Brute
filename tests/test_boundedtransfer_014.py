"""brute.boundedtransfer unit tests (decision chain, containment, bounded supports vs the exhaustive reference)."""
import unittest
from brute.boundedtransfer import FB,MARGIN,dlf_decide,rg_decide,bounded_supports,BoundedTransfer
from experiments.v0120_reference import ref_bounded


class Bounded(unittest.TestCase):
    def test_constants(self):self.assertEqual((FB,MARGIN),(4,1))

    def test_chain(self):
        D=dlf_decide
        self.assertEqual(D(3,8,2,None,None,None,None,None),(2,'sp8',None))
        self.assertEqual(D(8,8,None,[1,2],[1],[1],True,1),(None,None,'burn-in'))
        self.assertEqual(D(9,8,None,None,[1],[1],True,1),(None,None,'sp8-support-unavailable'))
        self.assertEqual(D(9,8,None,[1,2],[1],None,None,None),(1,'rg',None))
        self.assertEqual(D(9,8,None,[1,2],[1,3],None,None,None),(None,None,'region-not-singleton'))
        self.assertEqual(D(9,8,None,[1,2],[3],None,None,None),(None,None,'outside-sp8-support'))
        self.assertEqual(D(9,8,None,[1,2],[1,2],[2],False,None),(None,None,'library-refuted'))
        self.assertEqual(D(9,8,None,[1,2],[1,2],[2],True,None),(None,None,'library-split'))
        self.assertEqual(D(9,8,None,[1,2],[1,2],[3],True,3),(None,None,'outside-sp8-support'))
        self.assertEqual(D(9,8,None,[1,2],[1,2],[1,2],True,2),(None,None,'bounded-region-not-singleton'))
        self.assertEqual(D(9,8,None,[1,2],[1,2],[1],True,2),(None,None,'bounded-region-not-singleton'))
        self.assertEqual(D(9,8,None,[1,2],[1,2],[2],True,2),(2,'license',None))
        self.assertEqual(rg_decide(9,8,None,[1,2],[2]),(2,'rg'));self.assertEqual(rg_decide(9,8,None,[1],[2]),(None,None))

    def test_containment(self):
        # whenever RG4 certifies, DLF certifies the same code, for every library state
        import itertools
        S=[None,[0],[1,2],[0,1,2,3]];R=[None,[0],[1],[1,2],[0,1,2,3]]
        for t,s,fb,lic,alive,p in itertools.product((5,9),S,R,R,(None,False,True),(None,0,1,2)):
            g=rg_decide(t,8,None,s,fb)
            if g[0] is not None:self.assertEqual(dlf_decide(t,8,None,s,fb,lic,alive,p)[:2],g)

    def test_bounded_vs_reference(self):
        import random
        rng=random.Random(7190030)
        for _ in range(4):
            acts=[rng.randrange(2) for _ in range(14)]
            obss=[tuple(rng.choice((0,1,None)) if rng.random()<0.4 else rng.randrange(2) for _ in range(2)) for _ in acts]
            got=bounded_supports((0,1),acts,obss,(2,3))
            for n in (2,3):
                ref=ref_bounded(n,(0,1),acts,obss)
                for i,row in enumerate(ref):
                    for b in (0,1):
                        if got[str(n)]['unknown'][i][b]==0:self.assertEqual(got[str(n)]['support'][i][b],row[b])

    def test_margin(self):
        with self.assertRaises(ValueError):BoundedTransfer([],2,(0,0),8,margin=2)
        self.assertEqual(BoundedTransfer([],4,(0,0),8).license_bound,4);self.assertEqual(BoundedTransfer([],2,(0,0),8,0).license_bound,2)


if __name__=='__main__':unittest.main()
