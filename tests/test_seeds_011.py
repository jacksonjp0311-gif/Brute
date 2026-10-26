import unittest
from experiments.brute_common import VerificationError
from scripts.check_seeds_011 import ranges_011,prior_ranges,_overlap,check_run_seeds,g11_mandatory,long_sample,main,NEGATIVE


class Seeds011(unittest.TestCase):
    def test_disjoint(self):
        new=ranges_011();prior=prior_ranges();ks=list(new)
        self.assertTrue(any(k.startswith('BRUTE_PLAN_010.json') for k in prior))
        self.assertFalse(any(k.startswith('BRUTE_PLAN_011.json') for k in prior))
        for i,a in enumerate(ks):
            for b in ks[i+1:]:self.assertFalse(_overlap(new[a],new[b]),(a,b))
        for a,r in new.items():
            for b,q in prior.items():self.assertFalse(_overlap(r,q),(a,b))

    def test_runner_refuses(self):
        for blk,seed,fam in NEGATIVE:
            with self.assertRaises(VerificationError):check_run_seeds(blk,[seed],family=fam)
        self.assertTrue(check_run_seeds('smoke',[4190001,4190030,3190001,3190030]))

    def test_samples(self):
        self.assertEqual(sum(len(v) for v in g11_mandatory().values())*3,216)
        self.assertEqual(sum(len(v) for v in long_sample().values())*3,33)

    def test_main(self):self.assertEqual(main(),0)


if __name__=='__main__':unittest.main()
