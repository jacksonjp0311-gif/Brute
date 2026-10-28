import unittest
from experiments.brute_common import VerificationError
from scripts.check_seeds_021 import ranges_021,prior_ranges,_overlap,check_run_seeds,smoke_family,main,NEGATIVE


class Seeds021(unittest.TestCase):
    def test_disjoint(self):
        new=ranges_021();prior=prior_ranges();ks=list(new)
        self.assertTrue(any(k.startswith('BRUTE_PLAN_020.json') for k in prior))
        self.assertFalse(any(k.startswith('BRUTE_PLAN_021.json') for k in prior))
        for i,a in enumerate(ks):
            for b in ks[i+1:]:self.assertFalse(_overlap(new[a],new[b]),(a,b))
        for a,r in new.items():
            for b,q in prior.items():self.assertFalse(_overlap(r,q),(a,b))

    def test_runner_refuses(self):
        for blk,seed,fam in NEGATIVE:
            with self.assertRaises(VerificationError):check_run_seeds(blk,[seed],family=fam)
        self.assertTrue(check_run_seeds('smoke',[8790001,8790030,8690001,8690030]))
        self.assertTrue(check_run_seeds('target',[8740001,8740048],family='ood4'))

    def test_layout(self):
        self.assertEqual(smoke_family(8790003),'switch3');self.assertEqual(smoke_family(8790012),'ood4')
        self.assertEqual(smoke_family(8790015),'unaliased2')
        with self.assertRaises(VerificationError):smoke_family(8790016)

    def test_main(self):self.assertEqual(main(),0)


if __name__=='__main__':unittest.main()
