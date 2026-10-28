"""Scoring-script checks for study-021 (make_gates_021 / make_paired_021 / clean_clone_021): registered constants, the arm
sets per eps, the certify8 soundness probe, the boundary prefix check and the prefix28 comparator. No results needed."""
import copy,unittest
import scripts.make_gates_021 as G
import scripts.make_paired_021 as P
import scripts.clean_clone_021 as CC
from brute.anytimemargin import anytime_boundary


def _case():
    sup=[[[0,1]]*2 for _ in range(89)];unk=[0]*89;m=[1]*89
    tr=[{'step':i,'certificate':[None,None]} for i in range(89)]
    p={'actions':28,'support':sup[:28],'unknown':unk[:28],'m':m[:28],'certifier':{'trace':copy.deepcopy(tr[:28])},'identical':True}
    return {'eps':0.02,'noisy':{'RGNA4':{'support':sup,'unknown':unk,'m':m}},'certifiers':{'RGNA4':{'trace':tr}},'prefix28':p}


class T(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(G.FROZEN_CI,(0.00119,0.004167));self.assertEqual(G.REPRO_EXPECTED,60);self.assertEqual(G.PREFIX,28)
        self.assertEqual((P.SEED,P.B),(20261028,10000));self.assertIn('RGNA4',P.ARMS)
        self.assertTrue(any('API_CHECK_021' in x for x in CC.TRACKED) and any('RESUME_DRILL_021' in x for x in CC.TRACKED))
    def test_arms(self):
        self.assertEqual(G.arms({'eps':0.0}),('RG4','RGNA4','RGN4_or'));self.assertEqual(G.arms({'eps':0.05}),('RG4','RGNA4','RGN4_or'))
        for e in (0.01,0.02):self.assertEqual(G.arms({'eps':e}),('RG4','RGNA4','RGNB4','RGN4_or'))
    def test_api8_probe(self):self.assertTrue(G.api8_probe()['matches']);self.assertTrue(G.api_soundness()['matches'])
    def test_boundary_prefix(self):
        big=anytime_boundary(512)
        for L in (0,28,56,88,176,511):self.assertEqual(big[:L+1],anytime_boundary(L))
    def test_prefix_check(self):
        c=_case();self.assertEqual(G.prefix_check(c),[])
        d=_case();d['prefix28']['certifier']['trace'][5]['certificate']=[0,None];self.assertIn('certificates',G.prefix_check(d))
        d=_case();d['prefix28']['m'][3]=2;self.assertIn('m',G.prefix_check(d))
        d=_case();del d['prefix28'];self.assertEqual(G.prefix_check(d),['prefix28 missing'])


if __name__=='__main__':unittest.main()
