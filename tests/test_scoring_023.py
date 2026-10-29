"""Scoring-script checks for study-023 (make_gates_023 / make_paired_023 / clean_clone_023): registered constants, the arm
sets per eps, the certify9 probe, the LR bound recount and the RGL4 prefix28 comparator. No results needed."""
import copy,unittest
import scripts.make_gates_023 as G
import scripts.make_paired_023 as P
import scripts.clean_clone_023 as CC
from brute.anytimemargin import anytime_boundary


def _lr(T,steps):
    return {'T':T,'attain':[None]*steps,'witnesses':[[] for _ in range(steps)],'witness_unknowns':[0]*steps,'witness_calls':[0]*steps}


def _case():
    S=88;sup=[[[0,1]]*2 for _ in range(S)];unk=[[0,0] for _ in range(S)];B=176;ba=anytime_boundary(B,0.02,0.005)
    bits=[min(2*(i+1),B) for i in range(S)];T=[ba[b] for b in bits]
    tr=[{'step':i+1,'certificate':[None,None]} for i in range(S)]
    lr={'delta_L':0.005,'delta_a':0.005,'D':[3,4,5,7],'anytime_boundary':ba,**_lr(T,S)}
    p={'actions':28,'support':sup[:28],'unknown':unk[:28],'m':T[:28],'certifier':{'trace':copy.deepcopy(tr[:28])},'identical':True,
       'lr':{k:v[:28] for k,v in _lr(T,S).items()}}
    return {'eps':0.02,'B':B,'prefix_bits':bits,'noisy':{'RGL4':{'support':sup,'unknown':unk,'m':T}},'certifiers':{'RGL4':{'trace':tr}},'prefix28':p,'lr':lr}


class T(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(G.FROZEN_CI,(0.214962,0.317332));self.assertEqual(G.REPRO_EXPECTED,60);self.assertEqual(G.PREFIX,28)
        self.assertEqual(G.EXPECTED,{'main':360,'stress':30});self.assertEqual(G.D_TABLE,[3,4,5,7])
        self.assertEqual((P.SEED,P.B),(23,10000));self.assertIn('RGL4',P.ARMS)
        self.assertTrue(any('API_CHECK_023' in x for x in CC.TRACKED) and any('RESUME_DRILL_023' in x for x in CC.TRACKED))
    def test_arms(self):
        for e in (0.0,0.01,0.05):self.assertEqual(G.arms({'eps':e}),('RG4','RGL4','RGNA4','RGN4_or'))
        self.assertEqual(G.arms({'eps':0.02}),('RG4','RGL4','RGNA4','RGNB4','RGN4_or'))
    def test_api9_probe(self):
        p=G.api9_probe();self.assertIsNone(p['error']);self.assertEqual((p['default_method'],p['default_answer_method']),('lr','lr'))
        self.assertTrue(p['anytime_equals_certify8']);self.assertEqual(p['methods'],['lr','anytime'])
    def test_lr_check(self):
        c=_case();self.assertEqual(G.lr_check(c,c['lr'],88),[])
        d=_case();d['lr']['T'][40]-=1;self.assertTrue(any(b[1]=='T' for b in G.lr_check(d,d['lr'],88)))
        d=_case();d['lr']['witnesses'][50]=[{'n':1,'w':0,'d':0,'e':0}];self.assertTrue(any(b[1] in ('T','attain') for b in G.lr_check(d,d['lr'],88)))
        d=_case();d['lr']['D']=[3,4,5,8];self.assertTrue(any(b[1]=='D' for b in G.lr_check(d,d['lr'],88)))
    def test_prefix_check(self):
        c=_case();self.assertEqual(G.prefix_check(c),[])
        d=_case();d['prefix28']['certifier']['trace'][5]['certificate']=[0,None];self.assertIn('certificates',G.prefix_check(d))
        d=_case();d['prefix28']['lr']['T'][3]+=1;self.assertTrue(G.prefix_check(d))
        d=_case();del d['prefix28'];self.assertEqual(G.prefix_check(d),['prefix28 missing'])


if __name__=='__main__':unittest.main()
