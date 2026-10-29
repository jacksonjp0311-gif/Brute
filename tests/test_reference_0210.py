import unittest
from fractions import Fraction
import experiments.v0210_reference as R


class Reference0210(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(len(R.KINDS),20);self.assertEqual(R.ref_D(),[3,4,5,7])
        self.assertEqual([R.ref_delta(k) for k in range(3)],[Fraction(1,400),Fraction(1,1200),Fraction(1,2400)])
        self.assertLess(sum(R.ref_delta(k) for k in range(60)),Fraction(1,200))
        self.assertEqual([R.ref_epoch(i) for i in (1,28,29,56,57,88,112,113)],[0,0,1,1,2,2,2,3])
        self.assertEqual([e['B'] for e in R.ref_epochs()],[56,112,224])
        self.assertEqual(R.arms_for(0.02),('RG4','RGL4','RGL5','RGNA4','RGN4_or','RGNB4'))

    def test_M_monotone_and_covering(self):
        bits=[min(2*(i+1),2*(i+1)) for i in range(88)];M=R.ref_M(bits,88)
        self.assertTrue(all(M[i]<=M[i+1] for i in range(87)));self.assertEqual((M[27],M[44],M[87]),(5,8,12))


if __name__=='__main__':unittest.main()
