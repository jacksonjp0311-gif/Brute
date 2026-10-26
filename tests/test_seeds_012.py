import unittest
from experiments.brute_common import VerificationError
from scripts.check_seeds_012 import (ranges_012,prior_ranges,_overlap,check_run_seeds,g11_mandatory,g11_optional,long_sample,
    source_seed,main,NEGATIVE)


class Seeds012(unittest.TestCase):
    def test_disjoint(self):
        new=ranges_012();prior=prior_ranges();ks=list(new)
        self.assertTrue(any(k.startswith('BRUTE_PLAN_011.json') for k in prior))
        self.assertFalse(any(k.startswith('BRUTE_PLAN_012.json') for k in prior))
        for i,a in enumerate(ks):
            for b in ks[i+1:]:self.assertFalse(_overlap(new[a],new[b]),(a,b))
        for a,r in new.items():
            for b,q in prior.items():self.assertFalse(_overlap(r,q),(a,b))

    def test_runner_refuses(self):
        for blk,seed,fam in NEGATIVE:
            with self.assertRaises(VerificationError):check_run_seeds(blk,[seed],family=fam)
        self.assertTrue(check_run_seeds('smoke',[5190001,5190030,4190001,4190030]))

    def test_samples(self):
        self.assertEqual(sum(len(v) for v in g11_mandatory().values())*3,216)
        self.assertEqual(sum(len(v) for v in g11_optional().values())*3,54)
        self.assertEqual(sum(len(v) for v in long_sample().values())*3,33)
        self.assertEqual(source_seed('cycle3',1),('cycle3',5150001))
        self.assertEqual(source_seed('cycle3',1,negative=True),('switch3',5150025))
        self.assertEqual(source_seed('ood4',24,negative=True),('unaliased2',5150072))

    def test_main(self):self.assertEqual(main(),0)


if __name__=='__main__':unittest.main()
