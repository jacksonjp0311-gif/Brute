"""brute.deferredsplit unit tests (RSXL rule vs the reference, Deferral, license bound, MarginTransfer margin 1 = frozen DLF)."""
import itertools,unittest
from brute.deferredsplit import rsxl_choose,Deferral,license_bound,MarginTransfer
from brute.regionsplit import rsx_choose
from experiments.v0140_reference import rsxl_choice


class DeferredSplit(unittest.TestCase):
    def test_rule_vs_reference(self):
        for t,k0,k1,sp,cb in itertools.product((3,8,9,20),range(5),range(5),(0,1),(False,True)):
            self.assertEqual(rsxl_choose(t,8,[k0,k1],sp,cb),rsxl_choice(t,8,[k0,k1],sp,not cb))
            if not cb:self.assertEqual(rsxl_choose(t,8,[k0,k1],sp,cb),(sp,'sp8'))
            else:self.assertEqual(rsxl_choose(t,8,[k0,k1],sp,cb),rsx_choose(t,8,[k0,k1],sp))
        for bad in ((9,8,[1,2],2,True),(9,8,[1,2],True,True),(9,8,[1,2],0,None),(9,8,[1,2],0,1)):
            with self.assertRaises(ValueError):rsxl_choose(*bad)

    def test_deferral(self):
        d=Deferral();self.assertEqual([d.taken(c) for c in (None,None,1,None,0)],[False,False,True,True,True]);self.assertEqual(d.first_cert_step,3)

    def test_license_bound(self):
        self.assertEqual([license_bound(n,1) for n in (1,2,3,4)],[2,3,4,4]);self.assertEqual([license_bound(n,2) for n in (1,2,3)],[3,4,4])
        for bad in ((2,0),(2,3),(2,True),(0,1),(True,1),(2.0,1)):
            with self.assertRaises(ValueError):license_bound(*bad)

    def test_margin_transfer_bound(self):
        m=MarginTransfer([],2,(0,1),8,margin=2);self.assertEqual(m.license_bound,4)
        with self.assertRaises(ValueError):MarginTransfer([],2,(0,1),8,margin=0)


if __name__=='__main__':unittest.main()
