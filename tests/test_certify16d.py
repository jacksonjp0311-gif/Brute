"""Tests for brute/api/certify16d.py (certify/16d, v0.44.0; BRUTE_PLAN_047). New file; built from tests/test_certify16.py (frozen).
Worlds use an old development seed (10050003, control_cycle3), outside every study-047 range."""
import ast,json,unittest
from pathlib import Path
from brute.api import certify16d as C
from experiments import worlds_043 as W
from experiments.brute_study_033 import StepWorld,passive
ROOT=Path(__file__).resolve().parents[1];DEV=10050003;CAP=294000;BUD=7840000


def world():
    w=W.world(DEV,'control_cycle3');sw=StepWorld(w);_,acts,rd=passive(sw,DEV);return w,sw,acts,rd


def loop(n=None,**kw):
    w,sw,acts,rd=world();n=len(acts) if n is None else n;kw={'conflict_cap':CAP,'budget_conflicts':BUD,**kw}
    with C.Certifier16D(rd[0],w.k,3,**kw) as c:
        for a,o in zip(acts[:n],rd[1:n+1]):c.observe(a,o)
        while (x:=c.propose()) is not None:
            for a in x:c.observe(a,sw.step(a))
        return c.result(),c.record()


class API(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(C.API,'brute.certify/16d');self.assertEqual(C.SEARCHES,('a16d',));self.assertEqual(C.A16D_MAX_BOUND,20)
        self.assertEqual((C.GUARD_CASE_S,C.GUARD_CALL_S),(600.0,30.0))

    def test_soundness_is_conditional_on_N(self):
        s=json.dumps(C.soundness()).lower();self.assertIn('family_bound',s);self.assertIn('inferred',s);self.assertIn('conflicts',s)

    def test_loop_control_ID(self):
        r,rec=loop();self.assertEqual((r['api'],r['label'],r['n_min'],r['family_bound']),('brute.certify/16d','ID',3,3))
        self.assertFalse(r['wall_guard']);self.assertEqual(rec['conflicts_spent'],r['conflicts'])
        for k in ('model','calls','unknown','soundness','used','rounds','conflicts','capped'):self.assertIn(k,r)

    def test_record_is_conflict_deterministic(self):
        # GDET in small: two runs give the same result and the same per-call conflicts (Simulated on this host)
        (r1,a),(r2,b)=loop(),loop();self.assertEqual(json.dumps(r1,sort_keys=True),json.dumps(r2,sort_keys=True))
        self.assertEqual([x['call_conflicts'] for x in a['rounds']],[x['call_conflicts'] for x in b['rounds']])

    def test_K_spent_is_AMB(self):
        w,sw,acts,rd=world();r=C.certify16d(rd[0],acts[:2],rd[1:3],w.k,3,conflict_cap=CAP,budget_conflicts=BUD)
        self.assertEqual((r['stop'],r['label']),('K_spent','AMB'))

    def test_spent_budget_is_unknown(self):
        r,rec=loop(2,conflict_cap=1,budget_conflicts=1);self.assertEqual((r['stop'],r['label'],r['unknown']),('unknown','IDU',True))
        self.assertLessEqual(rec['conflicts_spent'],2)

    def test_case_wall_guard_fires(self):
        r,rec=loop(2,wall_guard_case_s=0.0);self.assertEqual(r['stop'],'unknown');self.assertTrue(r['wall_guard']);self.assertTrue(rec['guard_events'])

    def test_argument_checks(self):
        base={'num_actions':3,'family_bound':3,'conflict_cap':CAP,'budget_conflicts':BUD}
        for kw in ({'family_bound':21},{'family_bound':0},{'num_actions':5},{'K':-1},{'conflict_cap':0},{'budget_conflicts':0},
                   {'conflict_cap':None},{'budget_conflicts':None},{'conflict_cap':1.5}):
            with self.assertRaises(ValueError,msg=str(kw)):C.Certifier16D((0,1),**{**base,**kw})
        with self.assertRaises(ValueError):C.Certifier16D((0,1),search='a16',**base)
        C.Certifier16D((0,1),**{**base,'family_bound':20}).close()

    def test_observe_rules(self):
        w,sw,acts,rd=world();c=C.Certifier16D(rd[0],w.k,3,conflict_cap=CAP,budget_conflicts=BUD)
        with self.assertRaises(ValueError):c.observe(w.k,rd[1])
        with self.assertRaises(RuntimeError):c.result()
        c.close()

    def test_host_agnostic_static(self):
        t=ast.parse((ROOT/'brute/api/certify16d.py').read_text());bad=('os','subprocess','threading','multiprocessing','socket','io','pathlib','shutil','tempfile')
        for n in ast.walk(t):
            if isinstance(n,ast.Import):self.assertFalse([a.name for a in n.names if a.name.split('.')[0] in bad])
            if isinstance(n,ast.ImportFrom) and n.module:self.assertNotIn(n.module.split('.')[0],bad)
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):self.assertNotIn(n.func.id,('open','exec','eval','__import__'))

    def test_api_checks_closure(self):
        from scripts.api_checks_046 import closure
        d=closure('brute.api.certify16d');s=closure('brute.api.certify16')
        self.assertEqual(set(d)-set(s),{'brute.api.certify16d'});self.assertEqual({m:v for m,v in d.items() if m not in s and (v['bad_imports'] or v['bad_calls'])},{})


if __name__=='__main__':unittest.main()
