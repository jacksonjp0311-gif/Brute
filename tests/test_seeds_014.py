import unittest
from experiments.brute_common import VerificationError
from scripts.check_seeds_014 import (ranges_014,prior_ranges,_overlap,check_run_seeds,source_seed,stress_sources,
    smoke_family,smoke_source,smoke_stress_sources,main,NEGATIVE)


class Seeds014(unittest.TestCase):
    def test_disjoint(self):
        new=ranges_014();prior=prior_ranges();ks=list(new)
        self.assertTrue(any(k.startswith('BRUTE_PLAN_013.json') for k in prior))
        self.assertFalse(any(k.startswith('BRUTE_PLAN_014.json') for k in prior))
        for i,a in enumerate(ks):
            for b in ks[i+1:]:self.assertFalse(_overlap(new[a],new[b]),(a,b))
        for a,r in new.items():
            for b,q in prior.items():self.assertFalse(_overlap(r,q),(a,b))

    def test_runner_refuses(self):
        for blk,seed,fam in NEGATIVE:
            with self.assertRaises(VerificationError):check_run_seeds(blk,[seed],family=fam)
        self.assertTrue(check_run_seeds('smoke',[7190001,7190030,6190001,6190030]))

    def test_maps(self):
        self.assertEqual(source_seed('cycle3',1),('cycle3',7150001))
        self.assertEqual(source_seed('cycle3',1,negative=True),('switch3',7150025))
        self.assertEqual(source_seed('ood4',24,negative=True),('unaliased2',7150072))
        s=stress_sources('unaliased2');self.assertEqual(len(s),72);self.assertNotIn('unaliased2',{f for f,_ in s})
        self.assertEqual(smoke_family(7190003),'switch3');self.assertEqual(smoke_source(7190003),('switch3',7190023))
        self.assertEqual(smoke_source(7190012),('ood4',7190024));self.assertEqual(smoke_source(7190015,True),('ood4',7190027))
        self.assertEqual(len(smoke_stress_sources(7190001)),24)
        with self.assertRaises(VerificationError):smoke_family(7190020)

    def test_main(self):self.assertEqual(main(),0)


if __name__=='__main__':unittest.main()
