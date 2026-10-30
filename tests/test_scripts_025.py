"""v0.22.0 lean scoring scripts: arm set, CP95 facts declared in A2, b6 rule check and the GAPI11 probe."""
import copy,unittest
from scripts import make_gates_025 as G
from scripts.make_gates_018 import cp_upper


class Scripts025(unittest.TestCase):
    def test_arms(self):
        self.assertEqual(G.arms({'eps':0.02}),('RG4','RGB6','RGL4','RGL5','RGNB4','RGN4_or'))
        self.assertEqual(G.arms({'eps':0.05}),('RG4','RGB6','RGL4','RGL5','RGN4_or'))

    def test_cp95_declared(self):
        self.assertAlmostEqual(cp_upper(0,40),0.0722,places=3);self.assertGreater(cp_upper(0,148),0.02);self.assertLessEqual(cp_upper(0,149),0.02)

    def test_expected(self):self.assertEqual(G.EXPECTED,{'main':60,'stress':30,'noisy':40,'eps2':20});self.assertEqual(G.CAP,1800)

    def test_b6_check_detects(self):
        T=list(range(88));c={'b6':{'T':T,'T0':T,'active':[[]]*88,'K':{'1':[0]*88,'2':[0]*88}},'noisy':{'RGB6':{'m':T}}}
        self.assertEqual(G.b6_check(c),[])
        d=copy.deepcopy(c);d['b6']['T'][5]=0;self.assertTrue(G.b6_check(d))

    def test_probe(self):
        p=G.api11_probe();self.assertIsNone(p['error']);self.assertTrue(p['stitched_equals_certify10'] and p['lr_equals_certify9'])


if __name__=='__main__':unittest.main()
