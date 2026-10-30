"""v0.22.0: RGB6 betting levels (BETTING_LEMMA_025 §2) and the Exact non-activation fact at 178 bits."""
import unittest
from fractions import Fraction as F
from brute import bettingregion as BR


class BettingLevels(unittest.TestCase):
    def test_default_levels(self):
        self.assertEqual(BR.LEVELS,((0,F(1,50),F(1,400),None),(1,F(1,100),F(1,800),F(1,800)),(2,F(1,200),F(1,800),F(1,800))))
        self.assertEqual(BR.THRESHOLD,800)

    def test_eps_bar_range(self):
        for bad in (0,0.5,0.7):
            with self.assertRaises(ValueError):BR.make_levels(eps_bar=bad)
        L,a0=BR.make_levels(eps_bar=0.05,delta=0.02);self.assertEqual(a0,F(1,200));self.assertEqual(L[2][1],F(1,80))

    def test_lambdas(self):
        self.assertEqual(BR.lambdas(F(1,100)),[F(25,99),F(50,99),F(25,33),F(100,99)])

    def test_wealth_validation(self):
        for t,b in ((-1,3),(True,3),(1,-2)):
            with self.assertRaises(ValueError):BR.wealth(F(1,100),t,b)

    def test_no_activation_at_178_bits(self):
        for j in (1,2):self.assertLess(BR.wealth(BR.LEVELS[j][1],0,178),BR.THRESHOLD)

    def test_activation_bits(self):
        def first(p):
            b=1
            while BR.wealth(p,0,b)<BR.THRESHOLD:b+=1
            return b
        # the lemma's sufficient bound (1/(1-p))^b >= 800 needs 666 / 1334 bits; the exact mixture wealth needs at least that
        import math
        for p,lb in ((F(1,100),666),(F(1,200),1334)):
            self.assertEqual(math.ceil(math.log(800)/-math.log(1-float(p))),lb);self.assertGreaterEqual(first(p),lb)


if __name__=='__main__':unittest.main()
