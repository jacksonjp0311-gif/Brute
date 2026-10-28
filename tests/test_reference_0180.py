import unittest
import experiments.v0180_reference as R


class Reference0180(unittest.TestCase):
    def test_perbit_rule(self):
        st=[(1,0),(9,1),(10,0)];truth=[[0,3],[2,1],[1,2]]
        sup=[[[0],[3]],[[2,3],[1,0]],[None,[0,2]]]
        pb=R.ref_perbit(st,truth,sup,8)
        self.assertEqual(pb['trace'][0]['bits'],[[None,None],[None,None]])   # burn-in
        self.assertEqual(pb['trace'][1]['bits'],[[1,None],[0,None]])         # {2,3}: high bit 1; {1,0}: high bit 0
        self.assertEqual(pb['trace'][2]['bits'],[[None,None],[None,0]])      # None support; {0,2}: low bit 0
        self.assertEqual(pb['certified_bits'],3);self.assertEqual(pb['false_bits'],0)

    def test_constants(self):
        self.assertEqual((R.STEPS,R.READINGS,R.SLOTS,R.BITSLOTS),(88,89,176,352));self.assertEqual(len(R.KINDS),20)
        self.assertEqual(R.flip_array(8690001,0.02).shape,(89,2))


if __name__=='__main__':unittest.main()
