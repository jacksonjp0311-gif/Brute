"""Study 076 script tests (new file): pack/canon, recount labels against the oracle truth, gate constants."""
import unittest
from experiments import truth_076 as TR
from experiments import brute_study_076 as BS
from scripts.recount_076 import label
from scripts import make_gates_076 as G


def rec(name,acts,**kw):
    w=TR.world(name);s=0;r=[w.emissions[0]]
    for a in acts:s=w.transitions[s][a];r.append(w.emissions[s])
    d={'target':name,'N':TR.N_TRUE[name]+1,'actions':BS.pack(acts),'readings':BS.pack(r)};d.update(kw);return d,s


class T(unittest.TestCase):
    def test_pack(self):
        x=[0,1,2]*500;p=BS.pack(x);self.assertEqual(BS.unpack(p),x);self.assertEqual(BS.canon({'arm':'C3','job_wall_informational':1,'n':6}),{'n':6})

    def test_recount_labels(self):
        w=TR.world('B5');d,s=rec('B5',[1,2,0,1,2,2,0]);M=[list(r) for r in w.transitions]
        B=dict(d,api='brute.certify/34h',api_label='IDF',model_T=M,model_E=list(w.emissions),s1=s);self.assertEqual(label(B)[0],'IDF')
        self.assertEqual(label(dict(B,s1=(s+1)%5))[0],'WRONG')
        self.assertEqual(label(dict(B,api_label='AMB'))[0],'AMB')
        Tt=dict(d,api='brute.baseline/32t',api_label='ID',transitions=M,emissions=list(w.emissions),origin_step=0);self.assertEqual(label(Tt)[0],'ID')
        self.assertEqual(label(dict(Tt,api_label='EXCEEDS_N'))[0],'WRONG')
        bad=dict(B,readings=BS.pack([0]*8));self.assertEqual(label(bad)[0],'TRACE_MISMATCH');self.assertEqual(label({'killed':True})[0],'KILL')

    def test_gate_constants(self):
        self.assertEqual(G.ORDER[0],'truth_076');self.assertEqual(G.ORDER[1],'plan_076');self.assertEqual(G.DECIDED,('ID','IDF'))
        from experiments import brute_study_076 as S
        self.assertEqual(S.WALL_GUARD_CASE_S,S.JOB_KILL_S);self.assertEqual(S.JOB_KILL_S,900.0)


if __name__=='__main__':unittest.main()
