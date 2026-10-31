"""Tests for brute/api/certify16e.py (certify/16e chunked continuation, v0.46.0; BRUTE_PLAN_049). New file; built from
tests/test_certify16d.py (frozen). Worlds use an old development seed (10050003, control_cycle3), outside every study-049 range."""
import ast,json,unittest
from pathlib import Path
from brute.api import certify16e as E
from brute.api import certify16d as D
from experiments import worlds_043 as W
from experiments.brute_study_033 import StepWorld,passive
ROOT=Path(__file__).resolve().parents[1];DEV=10050003;CAP=50000;BUD=1500000


def world():
    w=W.world(DEV,'control_cycle3');sw=StepWorld(w);_,acts,rd=passive(sw,DEV);return w,sw,acts,rd


def loop(cls=E.Certifier16E,n=None,**kw):
    w,sw,acts,rd=world();n=len(acts) if n is None else n;kw={'conflict_cap':CAP,'budget_conflicts':BUD,**kw}
    with cls(rd[0],w.k,3,**kw) as c:
        for a,o in zip(acts[:n],rd[1:n+1]):c.observe(a,o)
        while (x:=c.propose()) is not None:
            for a in x:c.observe(a,sw.step(a))
        return c.result(),c.record()


class API(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(E.API,'brute.certify/16e');self.assertTrue(issubclass(E.Certifier16E,D.Certifier16D))

    def test_soundness_mentions_resume_and_N(self):
        s=json.dumps(E.soundness()).lower();self.assertIn('family_bound',s);self.assertIn('inferred',s)
        r,_=loop();self.assertIn('resume',json.dumps(r['soundness']).lower())

    def test_loop_control_ID(self):
        r,rec=loop();self.assertEqual((r['api'],r['label'],r['n_min'],r['family_bound']),('brute.certify/16e','ID',3,3))
        self.assertFalse(r['wall_guard']);self.assertIsNone(r['max_chunks']);self.assertGreaterEqual(r['chunks'],1)
        for k in ('max_chunks','chunks_total','chunk_wall_max','case_wall'):self.assertIn(k,rec)
        for rr in rec['rounds']:
            self.assertEqual(len(rr['call_chunks']),len(rr['call_conflicts']));self.assertEqual([sum(x) for x in rr['chunk_conflicts']],rr['call_conflicts'])

    def test_max_chunks_1_equals_certify16d(self):
        # part c in small: max_chunks 1 gives certify/16d's label, conflicts and per-call conflict counts (Simulated on this host)
        (a,ra),(b,rb)=loop(max_chunks=1),loop(D.Certifier16D)
        self.assertEqual((a['label'],a['n_min'],a['conflicts']),(b['label'],b['n_min'],b['conflicts']))
        self.assertEqual([x['call_conflicts'] for x in ra['rounds']],[x['call_conflicts'] for x in rb['rounds']])
        self.assertTrue(all(n<=1 for x in ra['rounds'] for n in x['call_chunks']))

    def test_resume_passes_the_chunk_cap(self):
        # _chunk_solve on a stand-in solver that needs 25 conflicts: with chunk C 10 it resumes 3 chunks (10, 10, 5) and answers;
        # max_chunks 1 stops at C (certify/16d behaviour); a spent budget stops as 'budget'
        from types import SimpleNamespace as NS
        class S:
            def __init__(s,need):s.n=0;s.need=need;s.b=None
            def conflicts(s):return s.n
            def conf_budget(s,b):s.b=b
            def solve_limited(s,assumptions=(),expect_interrupt=False):
                k=min(s.b,s.need-s.n);s.n+=k;return True if s.n>=s.need else None
            def interrupt(s):pass
            def clear_interrupt(s):pass
        def run(mc,budget=1000):
            c=E._Case16E(10,budget,600.0,30.0,None,mc);c.t0=None;o=NS(case=c,solves=0,chunks=0,call_conflicts=[],query_walls=[],unknowns=0,capped=0,call_capped=[])
            R=NS(_skip=False,_owner=o,calls=0,s=S(25));return E._chunk_solve(R,[]),o,c
        r,o,c=run(None);self.assertTrue(r);self.assertEqual((o.call_conflicts,c.calls_log[0][:2],o.call_capped),([25],(3,[10,10,5]),[None]))
        r,o,c=run(1);self.assertIsNone(r);self.assertEqual((o.call_conflicts,o.call_capped,c.calls_log[0][0]),([10],['cap'],1))
        r,o,c=run(None,budget=15);self.assertIsNone(r);self.assertEqual((o.call_conflicts,o.call_capped),([15],['budget']))

    def test_record_is_conflict_deterministic(self):
        (r1,a),(r2,b)=loop(),loop();self.assertEqual(json.dumps(r1,sort_keys=True),json.dumps(r2,sort_keys=True))
        self.assertEqual([(x['call_conflicts'],x['chunk_conflicts']) for x in a['rounds']],[(x['call_conflicts'],x['chunk_conflicts']) for x in b['rounds']])

    def test_K_spent_is_AMB(self):
        w,sw,acts,rd=world();r=E.certify16e(rd[0],acts[:2],rd[1:3],w.k,3,conflict_cap=CAP,budget_conflicts=BUD)
        self.assertEqual((r['stop'],r['label']),('K_spent','AMB'))

    def test_spent_budget_is_unknown(self):
        r,rec=loop(n=2,conflict_cap=1,budget_conflicts=1);self.assertEqual((r['stop'],r['label'],r['unknown']),('unknown','IDU',True))

    def test_case_wall_guard_fires(self):
        r,rec=loop(n=2,wall_guard_case_s=0.0);self.assertEqual(r['stop'],'unknown');self.assertTrue(r['wall_guard'])

    def test_argument_checks(self):
        base={'num_actions':3,'family_bound':3,'conflict_cap':CAP,'budget_conflicts':BUD}
        for kw in ({'max_chunks':0},{'max_chunks':-1},{'max_chunks':1.5},{'family_bound':21},{'conflict_cap':0}):
            with self.assertRaises(ValueError,msg=str(kw)):E.Certifier16E((0,1),**{**base,**kw})
        E.Certifier16E((0,1),**{**base,'max_chunks':2}).close()

    def test_host_agnostic_static(self):
        t=ast.parse((ROOT/'brute/api/certify16e.py').read_text());bad=('os','subprocess','threading','multiprocessing','socket','io','pathlib','shutil','tempfile')
        for n in ast.walk(t):
            if isinstance(n,ast.Import):self.assertFalse([a.name for a in n.names if a.name.split('.')[0] in bad])
            if isinstance(n,ast.ImportFrom) and n.module:self.assertNotIn(n.module.split('.')[0],bad)
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):self.assertNotIn(n.func.id,('open','exec','eval','__import__'))

    def test_api_checks_closure(self):
        from scripts.api_checks_046 import closure
        e=closure('brute.api.certify16e');d=closure('brute.api.certify16d')
        self.assertTrue(set(e)-set(d)<={'brute.api.certify16e','brute.api'});self.assertIn('brute.api.certify16e',e)
        self.assertEqual({m:v for m,v in e.items() if m not in d and (v['bad_imports'] or v['bad_calls'])},{})


if __name__=='__main__':unittest.main()
