"""Scoring-script checks for study-024 (make_gates_024 / make_paired_024 / clean_clone_024 / early_window_024): registered
constants, arm sets, the certify10 probe, the RGL5 bound recount, the prefix28_rgl5 comparator, the G_PROC log parser and
the no-live-git rule (GCC). No results needed."""
import copy,tempfile,unittest
from pathlib import Path
import scripts.make_gates_024 as G
import scripts.make_paired_024 as P
import scripts.clean_clone_024 as CC
from experiments import v0210_reference as REF


def _case():
    S=88;sup=[[[0,1]]*2 for _ in range(S)];unk=[[0,0] for _ in range(S)]
    bits=[min(i+1,55) for i in range(S)];M=REF.ref_M(bits,S)
    tr=[{'step':i+1,'certificate':[None,None]} for i in range(S)]
    lr5={'delta_L':0.005,'delta_a':0.005,'D':[3,4,5,7],'epochs':REF.ref_epochs(S),'epoch':[REF.ref_epoch(i+1) for i in range(S)],'M':M,'T':list(M),
         'attain':[None]*S,'witnesses':[[] for _ in range(S)],'witness_unknowns':[0]*S,'witness_calls':[0]*S}
    p={'actions':28,'support':sup[:28],'unknown':unk[:28],'m':M[:28],'certifier':{'trace':copy.deepcopy(tr[:28])},'identical':True,
       'lr5':{k:(v[:28] if isinstance(v,list) and len(v)==S else v) for k,v in lr5.items()}}
    return {'eps':0.02,'prefix_bits':bits,'noisy':{'RGL5':{'support':sup,'unknown':unk,'m':list(M)}},'certifiers':{'RGL5':{'trace':tr}},
            'prefix28_rgl5':p,'lr5':lr5}


class T(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(G.FROZEN_KEY,'C_late_RGL4_eps2');self.assertTrue(str(G.FROZEN_REF).endswith('results/study-023/PAIRED_ANALYSIS_023.json'))
        self.assertEqual((G.REPRO_EXPECTED,G.PREFIX,G.D_TABLE),(30,28,[3,4,5,7]));self.assertEqual(G.EXPECTED,{'main':360,'stress':30})
        self.assertEqual((P.SEED,P.B),(23,10000));self.assertIn('RGL5',P.ARMS)
        for x in ('experiments/COMMIT_ORDER_024.json','results/RESEARCH_LEDGER.jsonl','results/study-024/RUN_024.log','results/study-024/LIVE_REFUSAL_024.json'):
            self.assertIn(x,CC.TRACKED)
    def test_arms(self):
        for e in (0.0,0.01,0.05):self.assertEqual(G.arms({'eps':e}),('RG4','RGL4','RGL5','RGNA4','RGN4_or'))
        self.assertEqual(G.arms({'eps':0.02}),('RG4','RGL4','RGL5','RGNA4','RGNB4','RGN4_or'))
    def test_api10_probe(self):
        p=G.api10_probe();self.assertIsNone(p['error']);self.assertEqual((p['default_method'],p['default_answer_method']),('stitched','stitched'))
        self.assertEqual(p['methods'],['stitched','lr','anytime']);self.assertTrue(p['lr_equals_certify9'] and p['anytime_equals_certify9_anytime'])
    def test_lr5_check(self):
        c=_case();self.assertEqual(G.lr5_check(c,c['lr5'],88),[])
        d=_case();d['lr5']['T'][40]-=1;self.assertTrue(any(b[1]=='T' for b in G.lr5_check(d,d['lr5'],88)))
        d=_case();d['lr5']['M'][60]+=1;self.assertTrue(any(b[1]=='M' for b in G.lr5_check(d,d['lr5'],88)))
        d=_case();d['lr5']['epoch'][30]=0;self.assertTrue(any(b[1]=='epoch' for b in G.lr5_check(d,d['lr5'],88)))
        d=_case();d['lr5']['witnesses'][50]=[{'n':1,'w':0,'d':[],'e':[]}];self.assertTrue(any(b[1] in ('T','attain') for b in G.lr5_check(d,d['lr5'],88)))
        d=_case();d['lr5']['D']=[3,4,5,8];self.assertTrue(any(b[1]=='D' for b in G.lr5_check(d,d['lr5'],88)))
    def test_prefix5_check(self):
        c=_case();self.assertEqual(G.prefix5_check(c),[])
        d=_case();d['prefix28_rgl5']['certifier']['trace'][5]['certificate']=[0,None];self.assertIn('certificates',G.prefix5_check(d))
        d=_case();d['prefix28_rgl5']['lr5']['T'][3]+=1;self.assertTrue(G.prefix5_check(d))
        d=_case();del d['prefix28_rgl5'];self.assertEqual(G.prefix5_check(d),['prefix28_rgl5 missing'])
    def test_first_log_line(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td,'RUN_024.log').write_text('[2026-10-29T05:00:00-0400] study_dir /x/results/study-024 RUN_T0 1793264400.5 smoke 0 pid 1\nmore\n')
            self.assertEqual(G.first_log_line(td),{'study_dir':'/x/results/study-024','RUN_T0':'1793264400.5','smoke':'0'})
    def test_no_live_git(self):
        s=Path(G.__file__).read_text();self.assertNotIn('import subprocess',s);self.assertNotIn('subprocess.run',s);self.assertNotIn("_git(",s);self.assertNotIn('/workspace',s)


if __name__=='__main__':unittest.main()
