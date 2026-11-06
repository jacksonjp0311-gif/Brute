"""Study 071 script tests (new file): jobs, canon/pack, recount labels for certify/32x records, gates helpers."""
import unittest
from pathlib import Path
from experiments import truth_069 as TR
from experiments import brute_study_071 as BS
from scripts.recount_071 import label
from scripts import make_gates_071 as G
ROOT=Path(__file__).resolve().parents[1]


def rec(name,acts,**kw):
    w=TR.world(name);s=0;r=[w.emissions[0]]
    for a in acts:s=w.transitions[s][a];r.append(w.emissions[s])
    d={'target':name,'N':TR.N_TRUE[name]+1,'actions':BS.pack(acts),'readings':BS.pack(r)};d.update(kw);return d,s


class T(unittest.TestCase):
    def test_jobs(self):
        j=BS.jobs_for('main');self.assertEqual(len(j),25);self.assertEqual(len(set(j)),25)
        self.assertEqual(sorted({a for _,_,a in j}),['B','H','H12','T','T12']);self.assertEqual(len(BS.jobs_for('smoke')),4)
        self.assertEqual(BS.NS['plus1'],{t:TR.N_TRUE[t]+1 for t in TR.TARGETS});self.assertEqual(BS.WORKERS,3);self.assertEqual(BS.RLIMIT_AS,int(1.8*(1<<30)))

    def test_pack_canon(self):
        x=[0,1,2]*500;p=BS.pack(x);self.assertEqual(BS.unpack(p),x)
        self.assertEqual(BS.canon({'arm':'H','job_wall_informational':1,'n':6}),{'n':6})

    def test_recount_labels_32x(self):
        w=TR.world('U3');d,s=rec('U3',[2,0,1,1,2]);M=[list(r) for r in w.transitions]
        X=dict(d,api='brute.certify/32x',api_label='IDF',x={'label':'IDF','hyp_T':M,'hyp_E':list(w.emissions),'q_star':s,'assumes_resync':False})
        self.assertEqual(label(X)[0],'IDF')
        self.assertEqual(label(dict(X,x=dict(X['x'],q_star=(s+1)%6)))[0],'WRONG')
        self.assertEqual(label(dict(X,x=dict(X['x'],assumes_resync=True)))[0],'WRONG')
        self.assertEqual(label(dict(X,api_label='HYP_REJECTED'))[0],'HYP_REJECTED')
        self.assertEqual(label(dict(X,readings=BS.pack([0]*6)))[0],'TRACE_MISMATCH');self.assertEqual(label({'killed':True})[0],'KILL')

    def test_gate_helpers(self):
        self.assertEqual(G.adapter_ast_ok(),[]);self.assertEqual(G.module_imports_ok((ROOT/'brute/api/certify32x.py').read_text()),(True,[]))
        self.assertEqual(G.ORDER[0],'plan_071');self.assertIn('GN12_71_attempt',G.ATTEMPT)


if __name__=='__main__':unittest.main()
