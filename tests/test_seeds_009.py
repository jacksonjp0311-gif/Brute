import unittest
from experiments.brute_common import VerificationError
from scripts.check_seeds_009 import ranges_009,prior_ranges,_overlap,check_run_seeds,planning_seeds,draw_spot_sample,main


class Seeds009(unittest.TestCase):
    def test_disjoint(self):
        new=ranges_009();prior=prior_ranges();ks=list(new)
        self.assertTrue(any(k.startswith('PLAN.json') for k in prior))
        for i,a in enumerate(ks):
            for b in ks[i+1:]:self.assertFalse(_overlap(new[a],new[b]),(a,b))
        for a,r in new.items():
            for b,q in prior.items():self.assertFalse(_overlap(r,q),(a,b))

    def test_runner_refuses(self):
        for blk,seed,fam in (('smoke',901,None),('smoke',2010001,None),('2x2',2190001,None),('breadth',2010001,None),
                             ('2x2',1880001,None),('2x2',2010025,'cycle3'),('planning',2010009,None),('planning',2080001,None)):
            with self.assertRaises(VerificationError):check_run_seeds(blk,[seed],family=fam)
        self.assertTrue(check_run_seeds('smoke',[2190001,2190030]))

    def test_planning_and_spot(self):
        P=planning_seeds();self.assertEqual(sum(len(v) for v in P.values())*3,144)
        S=draw_spot_sample();self.assertEqual(S,draw_spot_sample())
        self.assertEqual([len(v) for v in S.values()],[6,6,6,6])

    def test_main(self):self.assertEqual(main(),0)


if __name__=='__main__':unittest.main()
