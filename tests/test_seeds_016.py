import unittest
from experiments.brute_common import VerificationError
from scripts.check_seeds_016 import (ranges_016,prior_ranges,_overlap,check_run_seeds,source_seed,stress_sources,
    smoke_family,smoke_source,smoke_stress_sources,main,NEGATIVE)


class Seeds016(unittest.TestCase):
    def test_disjoint(self):
        new=ranges_016();prior=prior_ranges();ks=list(new)
        self.assertTrue(any(k.startswith('BRUTE_PLAN_015.json') for k in prior))
        self.assertFalse(any(k.startswith('BRUTE_PLAN_016.json') for k in prior))
        for i,a in enumerate(ks):
            for b in ks[i+1:]:self.assertFalse(_overlap(new[a],new[b]),(a,b))
        for a,r in new.items():
            for b,q in prior.items():self.assertFalse(_overlap(r,q),(a,b))

    def test_runner_refuses(self):
        for blk,seed,fam in NEGATIVE:
            with self.assertRaises(VerificationError):check_run_seeds(blk,[seed],family=fam)
        self.assertTrue(check_run_seeds('smoke',[8290001,8290030,8190001,8190030]))
        self.assertTrue(check_run_seeds('ood5',[8260001,8260024]))

    def test_maps(self):
        self.assertEqual(source_seed('cycle3',1),('cycle3',8250001))
        self.assertEqual(source_seed('cycle3',1,negative=True),('switch3',8250025))
        self.assertEqual(source_seed('ood4',24,negative=True),('unaliased2',8250072))
        s=stress_sources('unaliased2');self.assertEqual(len(s),72);self.assertNotIn('unaliased2',{f for f,_ in s})
        self.assertEqual(smoke_family(8290003),'switch3');self.assertEqual(smoke_source(8290003),('switch3',8290023))
        self.assertEqual(smoke_source(8290012),('ood4',8290024));self.assertEqual(smoke_source(8290015,True),('ood4',8290027))
        self.assertEqual(smoke_family(8290016),'ood5');self.assertEqual(len(smoke_stress_sources(8290001)),24)
        self.assertEqual(source_seed('ood4',25),('ood4',8250073));self.assertEqual(source_seed('ood4',48,negative=True),('unaliased2',8250072))
        with self.assertRaises(VerificationError):source_seed('cycle3',25)
        with self.assertRaises(VerificationError):smoke_family(8290020)
        with self.assertRaises(VerificationError):smoke_source(8290016)

    def test_main(self):self.assertEqual(main(),0)


if __name__=='__main__':unittest.main()
