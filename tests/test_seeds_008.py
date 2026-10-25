import unittest
from experiments.brute_common import VerificationError
from scripts.check_seeds_008 import ranges_008,prior_ranges,_overlap,check_run_seeds,main


class Seeds008(unittest.TestCase):
    def test_disjoint(self):
        new=ranges_008();prior=prior_ranges();ks=list(new)
        for i,a in enumerate(ks):
            for b in ks[i+1:]:self.assertFalse(_overlap(new[a],new[b]),(a,b))
        for a,r in new.items():
            for b,q in prior.items():self.assertFalse(_overlap(r,q),(a,b))

    def test_runner_refuses(self):
        for blk,seed in (('smoke',901),('smoke',1810001),('2x2',980001),('breadth',1810001),('2x2',1700001)):
            with self.assertRaises(VerificationError):check_run_seeds(blk,[seed])
        self.assertTrue(check_run_seeds('smoke',[980001,980030]))

    def test_main(self):self.assertEqual(main(),0)


if __name__=='__main__':unittest.main()
