import unittest
import experiments.v0200_reference as R


class Reference0200(unittest.TestCase):
    def test_constants(self):
        self.assertEqual((R.STEPS,R.READINGS,R.SLOTS,R.PREFIX),(88,89,176,28));self.assertEqual(len(R.KINDS),20)
        self.assertEqual(R.ref_D(),[3,4,5,7]);self.assertEqual(R.H,{1:4,2:512,3:139968,4:67108864})
        self.assertEqual(R.arms_for(0.02),('RG4','RGL4','RGNA4','RGN4_or','RGNB4'));self.assertNotIn('RGNB4',R.arms_for(0.05))

    def test_fmin_small(self):
        self.assertEqual(R.fmin_tables(1,(0,1),[0,0],[(0,1),(0,1)]),[0,0])
        self.assertEqual(R.fmin_tables(1,(0,1),[0,0],[(1,1),(0,1)]),[0,1])


if __name__=='__main__':unittest.main()
