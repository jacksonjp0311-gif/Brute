import unittest
from fractions import Fraction
import experiments.v0190_reference as R


class Reference0190(unittest.TestCase):
    def test_constants(self):
        self.assertEqual((R.STEPS,R.READINGS,R.SLOTS,R.BITSLOTS,R.PREFIX),(88,89,176,352,28));self.assertEqual(len(R.KINDS),20)
        self.assertIn('anytime',R.KINDS);self.assertIn('prefix28',R.KINDS)

    def test_anytime_boundary(self):
        m=R.ref_anytime_boundary(120);self.assertEqual(m[:5],[0,1,1,1,1]);self.assertEqual(m[116],10)
        self.assertLess(R.ref_allowance(500,Fraction(1,100)),Fraction(1,100))
        self.assertEqual(R.ref_anytime_boundary(40),m[:41])


if __name__=='__main__':unittest.main()
