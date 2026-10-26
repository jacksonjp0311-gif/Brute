import unittest
from experiments.brute_common import VerificationError
from scripts.check_seeds_010 import ranges_010,prior_ranges,_overlap,check_run_seeds,g11_mandatory,draw_spot_sample,main,NEGATIVE


class Seeds010(unittest.TestCase):
    def test_disjoint(self):
        new=ranges_010();prior=prior_ranges();ks=list(new)
        self.assertTrue(any(k.startswith('BRUTE_PLAN_009.json') for k in prior))
        for i,a in enumerate(ks):
            for b in ks[i+1:]:self.assertFalse(_overlap(new[a],new[b]),(a,b))
        for a,r in new.items():
            for b,q in prior.items():self.assertFalse(_overlap(r,q),(a,b))

    def test_runner_refuses(self):
        for blk,seed,fam in NEGATIVE:
            with self.assertRaises(VerificationError):check_run_seeds(blk,[seed],family=fam)
        self.assertTrue(check_run_seeds('smoke',[3190001,3190030,2190001,2190030]))

    def test_samples(self):
        G=g11_mandatory();self.assertEqual(sum(len(v) for v in G['2x2'].values())*3,216)
        self.assertEqual(sum(len(v) for v in G['breadth'].values())*3,72)
        S=draw_spot_sample();self.assertEqual(S,draw_spot_sample());self.assertEqual([len(v) for v in S.values()],[3,3])

    def test_main(self):self.assertEqual(main(),0)


if __name__=='__main__':unittest.main()
