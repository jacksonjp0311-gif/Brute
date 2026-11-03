"""Study 070 script tests (new file): reset-free adapter, AST checks, pack/unpack, recount labels, jobs."""
import unittest
from pathlib import Path
from experiments import targets_070 as TG
from experiments import truth_069 as TR
from experiments import brute_study_070 as BS
from scripts.make_gates_070 import adapter_ast_ok,module_imports_ok
from scripts.recount_070 import label
ROOT=Path(__file__).resolve().parents[1]


def rec(name,acts,**kw):
    w=TR.world(name);s=0;r=[w.emissions[0]]
    for a in acts:s=w.transitions[s][a];r.append(w.emissions[s])
    d={'target':name,'N':TR.N_TRUE[name]+1,'actions':BS.pack(acts),'readings':BS.pack(r)};d.update(kw);return d,s


class T(unittest.TestCase):
    def test_adapter_has_no_reset(self):
        t=TG.Target('U3');self.assertFalse(hasattr(t,'reset'));d=t.dec;t.act(2);t.act(0);self.assertIs(t.dec,d);self.assertEqual(t.decoder_objects,1)
        self.assertEqual(TG.replay('U3',[2,0]),[(0,0),(0,0),(1,1)])                  # E1 41 -> U+FFFD A

    def test_ast_checks(self):
        self.assertEqual(adapter_ast_ok(),[])
        bad=ROOT/'experiments/targets_069.py';self.assertTrue(adapter_ast_ok(bad))     # the reset adapter fails the reset-free rule
        for f in ('brute/api/certify32h.py','brute/api/baseline32t.py'):self.assertEqual(module_imports_ok((ROOT/f).read_text()),(True,[]))

    def test_pack(self):
        x=[0,1,2]*1000;p=BS.pack(x);self.assertEqual(BS.unpack(p),x);self.assertEqual(p['len'],3000)

    def test_recount_labels(self):
        w=TR.world('U3');d,s=rec('U3',[2,0,1,1,2]);M=[list(r) for r in w.transitions]
        B=dict(d,api='brute.certify/32h',api_label='IDF',model_T=M,model_E=list(w.emissions),s1=s);self.assertEqual(label(B)[0],'IDF')
        self.assertEqual(label(dict(B,s1=(s+1)%6))[0],'WRONG')
        self.assertEqual(label(dict(B,api_label='ID'))[0],'ID')
        self.assertEqual(label(dict(B,api_label='AMB'))[0],'AMB')
        Tt=dict(d,api='brute.baseline/32t',api_label='ID',transitions=M,emissions=list(w.emissions),origin_step=0);self.assertEqual(label(Tt)[0],'ID')
        self.assertEqual(label(dict(Tt,origin_step=1))[0],'WRONG')
        self.assertEqual(label(dict(Tt,api_label='EXCEEDS_N'))[0],'WRONG')
        bad=dict(B,readings=BS.pack([0]*6));self.assertEqual(label(bad)[0],'TRACE_MISMATCH');self.assertEqual(label({'killed':True})[0],'KILL')

    def test_jobs_and_canon(self):
        j=BS.jobs_for('main');self.assertEqual(len(j),51);self.assertEqual(len(set(j)),51);self.assertIn(('U3',12700101,'Bb'),j)
        self.assertEqual(len(BS.jobs_for('smoke')),10);self.assertEqual(BS.canon({'arm':'B','job_wall_informational':1,'n':6}),{'n':6})
        self.assertEqual(BS.NS['main'],{t:TR.N_TRUE[t]+1 for t in TR.TARGETS})


if __name__=='__main__':unittest.main()
