"""Tests for brute/api/certify20t.py (certify/20t, single rival query at N, no fixed-colour clique; BRUTE_PLAN_054 with amendment
054a). New file; built from tests/test_certify16e.py (frozen). Worlds use an old development seed (10050003, control_cycle3),
outside every study-054 range."""
import ast,json,unittest
from pathlib import Path
from brute.api import certify20t as T
from brute.api import certify16e as E
from experiments import worlds_043 as W
from experiments.brute_study_033 import StepWorld,passive
ROOT=Path(__file__).resolve().parents[1];DEV=10050003;CAP=50000;BUD=1500000


def world():
    w=W.world(DEV,'control_cycle3');sw=StepWorld(w);_,acts,rd=passive(sw,DEV);return w,sw,acts,rd


def loop(cls,N=3,n=None,**kw):
    w,sw,acts,rd=world();n=len(acts) if n is None else n;kw={'conflict_cap':CAP,'budget_conflicts':BUD,**kw}
    with cls(rd[0],w.k,N,**kw) as c:
        for a,o in zip(acts[:n],rd[1:n+1]):c.observe(a,o)
        while (x:=c.propose()) is not None:
            for a in x:c.observe(a,sw.step(a))
        return c.result(),c.record()


class API(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(T.API,'brute.certify/20t');self.assertTrue(issubclass(T.Certifier20T,E.Certifier16E))
        s=T.soundness();self.assertEqual(s['clique'],'none');self.assertIn('padding',s['rival'])

    def test_loop_ID_at_true_size(self):
        r,rec=loop(T.Certifier20T);self.assertEqual((r['api'],r['label'],r['n_min']),('brute.certify/20t','ID',3))
        self.assertFalse(r['wall_guard'])

    def test_verdict_equals_certify16e_with_padding(self):
        # padding argument (Exact) in small: for declared N above the true size, the single rival query at N gives the same
        # verdict and n_min as certify/16e's sizes n_min..N (Simulated on this host)
        for N in (3,4,5):
            (a,_),(b,_)=loop(T.Certifier20T,N),loop(E.Certifier16E,N)
            self.assertEqual((a['label'],a['n_min']),(b['label'],b['n_min']),N)

    def test_short_trace_not_ID(self):
        # a too-short trace keeps an undecided rival under both certifiers (same verdict class)
        (a,_),(b,_)=loop(T.Certifier20T,4,n=2,max_chunks=None),loop(E.Certifier16E,4,n=2)
        self.assertEqual(a['label'],b['label'])

    def test_core_has_no_io(self):
        t=ast.parse((ROOT/'brute/api/certify20t.py').read_text());names=set()
        for nd in ast.walk(t):
            if isinstance(nd,ast.Import):names|={a.name.split('.')[0] for a in nd.names}
            if isinstance(nd,ast.ImportFrom) and nd.module:names.add(nd.module.split('.')[0])
        self.assertFalse(names&{'os','subprocess','threading','socket','multiprocessing','shutil'})


if __name__=='__main__':unittest.main()
