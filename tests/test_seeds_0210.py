import unittest
from experiments.brute_common import VerificationError
from scripts.check_seeds_024 import ranges_024,prior_ranges,_overlap,check_run_seeds,smoke_family,main,NEGATIVE


class Seeds024(unittest.TestCase):
    def test_disjoint(self):
        new=ranges_024();prior=prior_ranges();ks=list(new)
        self.assertTrue(any(k.startswith('BRUTE_PLAN_023.json') for k in prior))
        self.assertFalse(any(k.startswith('BRUTE_PLAN_024.json') for k in prior))
        for i,a in enumerate(ks):
            for b in ks[i+1:]:self.assertFalse(_overlap(new[a],new[b]),(a,b))
        for a,r in new.items():
            for b,q in prior.items():self.assertFalse(_overlap(r,q),(a,b))

    def test_runner_refuses(self):
        for blk,seed,fam in NEGATIVE:
            with self.assertRaises(VerificationError):check_run_seeds(blk,[seed],family=fam)
        self.assertTrue(check_run_seeds('smoke',[9090001,9090030]))
        self.assertTrue(check_run_seeds('target',[9040001,9040048],family='ood4'))

    def test_layout(self):
        from scripts.check_seeds_024 import MAIN_FAMILIES as F
        self.assertEqual([smoke_family(s) for s in range(9090001,9090009)],[f for f in F for _ in (0,1)])
        self.assertEqual([smoke_family(s) for s in range(9090009,9090013)],list(F))
        with self.assertRaises(VerificationError):smoke_family(9090016)

    def test_main(self):self.assertEqual(main(),0)


if __name__=='__main__':unittest.main()
