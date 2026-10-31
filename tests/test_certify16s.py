"""Tests for brute/api/certify16s.py (certify/16s unvisited-block symmetry breaking, v0.48.0; BRUTE_PLAN_051). New file.
Worlds use an old development seed (10050003, control_cycle3), outside every study-051 range."""
import ast,json,unittest
from pathlib import Path
from brute.api import certify16e as E
from brute.api import certify16s as S
from experiments import worlds_043 as W
from experiments.brute_study_033 import StepWorld,passive
ROOT=Path(__file__).resolve().parents[1];DEV=10050003


def loop(cls,N,B=300000):
    w=W.world(DEV,'control_cycle3');sw=StepWorld(w);_,acts,rd=passive(sw,DEV)
    with cls(rd[0],w.k,N,conflict_cap=50000,budget_conflicts=B) as c:
        for a,o in zip(acts,rd[1:]):c.observe(a,o)
        while (x:=c.propose()) is not None:
            for a in x:c.observe(a,sw.step(a))
        return c.result(),c.record()


class API(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(S.API,'brute.certify/16s');self.assertTrue(issubclass(S.Certifier16S,E.Certifier16E))
        s=json.dumps(S.soundness()).lower();self.assertIn('family_bound',s);self.assertIn('unvisited',s)

    def test_same_label_as_16e(self):
        # verdict preservation in small (Simulated on this host): same label and n_min as certify/16e at N 3 and 6
        for N in (3,6):
            (a,ra),(b,rb)=loop(S.Certifier16S,N),loop(E.Certifier16E,N)
            self.assertEqual((a['label'],a['n_min']),(b['label'],b['n_min']));self.assertEqual(a['api'],'brute.certify/16s')
            self.assertGreater(ra['sym_clauses'],0);self.assertEqual(ra['encoding'],S.ENCODING)

    def test_host_agnostic(self):
        t=ast.parse((ROOT/'brute/api/certify16s.py').read_text());bad={'os','subprocess','threading','socket','io','multiprocessing'}
        for n in ast.walk(t):
            if isinstance(n,ast.Import):self.assertFalse({a.name.split('.')[0] for a in n.names}&bad)
            if isinstance(n,ast.ImportFrom):self.assertNotIn((n.module or '').split('.')[0],bad)


if __name__=='__main__':unittest.main()
