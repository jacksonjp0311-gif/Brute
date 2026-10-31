"""Tests for brute/api/certify16n.py (certify/16n majority front end over an unchanged certify/16e, v0.47.0; BRUTE_PLAN_050).
New file. Worlds use an old development seed (10050003, control_cycle3), outside every study-050 range."""
import ast,json,math,random,unittest
from pathlib import Path
from brute.api import certify16n as N
from brute.api import certify16e as E
from experiments import worlds_043 as W
from experiments import worlds_050 as W50
from experiments.brute_study_033 import StepWorld,passive
ROOT=Path(__file__).resolve().parents[1];DEV=10050003;CAP=50000;BUD=1500000


def world():
    w=W.world(DEV,'control_cycle3');sw=StepWorld(w);_,acts,rd=passive(sw,DEV);return w,sw,acts,rd


def loop_e():
    w,sw,acts,rd=world()
    with E.Certifier16E(rd[0],w.k,3,conflict_cap=CAP,budget_conflicts=BUD) as c:
        for a,o in zip(acts,rd[1:]):c.observe(a,o)
        while (x:=c.propose()) is not None:
            for a in x:c.observe(a,sw.step(a))
        return c.result(),c.record()


def loop_n(eps=0.0,reads=None):
    w,sw,acts,rd=world();nw=W50.NoisyStepWorld(w,DEV,eps);nw.reset()
    k0=reads or N.reads_for(1,0.10,0.001)
    with N.Certifier16N([nw.read() for _ in range(k0)],w.k,3,reads=reads,conflict_cap=CAP,budget_conflicts=BUD) as c:
        for a in acts:nw.step(a);c.observe(a,[nw.read() for _ in range(c.reads_needed())])
        while (x:=c.propose()) is not None:
            for a in x:nw.step(a);c.observe(a,[nw.read() for _ in range(c.reads_needed())])
        return c.result(),c.record(),nw


class API(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(N.API,'brute.certify/16n')

    def test_reads_for(self):
        self.assertEqual([N.reads_for(t,0.10,0.001) for t in (1,10,100,1000,5000)],[27,41,55,69,79])
        for t in (1,7,300):
            k=N.reads_for(t,0.10,0.001);self.assertEqual(k%2,1)
            self.assertLessEqual(2*math.exp(-2*k*0.16),0.001*6/(math.pi**2*t*t)+1e-15)
            self.assertGreater(2*math.exp(-2*(k-2)*0.16),0.001*6/(math.pi**2*t*t))
        with self.assertRaises(ValueError):N.reads_for(0,0.1,0.001)

    def test_majority(self):
        self.assertEqual(N.majority([(1,0),(1,1),(0,0)]),((1,0),[2,1]))
        for bad in ([(1,0),(1,1)],[],[(1,2),(0,0),(0,0)]):
            with self.assertRaises(ValueError):N.majority(bad)

    def test_reads1_eps0_equals_certify16e(self):
        # part c in small: eps 0 and reads 1 give certify/16e's record (canon fields) and result label
        (a,ra),(b,rb,_)=loop_e(),loop_n(0.0,1)
        self.assertEqual((a['label'],a['n_min'],a['conflicts']),(b['label'],b['n_min'],b['conflicts']));self.assertEqual(b['inner_api'],E.API)
        for f in ('call_conflicts','chunk_conflicts','word','M1','M2'):
            self.assertEqual([x.get(f) for x in ra['rounds']],[x.get(f) for x in rb['rounds']],f)
        self.assertEqual(rb['reads_per_obs'],[1]*len(rb['reads_per_obs']))

    def test_noisy_loop_ID_and_deterministic(self):
        (r1,a,nw),(r2,b,_)=loop_n(0.05),loop_n(0.05)
        self.assertEqual((r1['api'],r1['label'],r1['n_min']),('brute.certify/16n','ID',3));self.assertGreater(nw.flipped,0)
        self.assertEqual(json.dumps(r1,sort_keys=True),json.dumps(r2,sort_keys=True));self.assertEqual(a['votes'],b['votes'])
        self.assertEqual(a['reads_per_obs'],[N.reads_for(t+1,0.10,0.001) for t in range(len(a['reads_per_obs']))])
        self.assertIn('delta',json.dumps(r1['soundness']))

    def test_wrong_read_count_refused(self):
        with self.assertRaises(ValueError):N.Certifier16N([(0,1)]*3,3,3,conflict_cap=CAP,budget_conflicts=BUD)
        c=N.Certifier16N([(0,1)]*3,3,3,reads=3,conflict_cap=CAP,budget_conflicts=BUD)
        with self.assertRaises(ValueError):c.observe(0,[(0,1)]*5)
        c.close()

    def test_argument_checks(self):
        for kw in ({'eps_bar':0.5},{'eps_bar':-0.1},{'delta':0},{'delta':1},{'reads':2},{'reads':0}):
            with self.assertRaises(ValueError,msg=str(kw)):N.Certifier16N([(0,1)]*27,3,3,conflict_cap=CAP,budget_conflicts=BUD,**kw)

    def test_noisy_world_reread_preserves_state(self):
        w,_,acts,_=world();nw=W50.NoisyStepWorld(w,DEV,0.3);nw.reset();nw.step(acts[0]);q=nw._h if hasattr(nw,'_h') else None
        r=[nw.read() for _ in range(2001)];self.assertEqual(nw.steps,1);self.assertEqual(nw.reads,2001)
        maj=N.majority(r)[0];code=w.emissions[w.transitions[w.start][acts[0]]];self.assertEqual(maj,W50.bits(code))

    def test_host_agnostic_static(self):
        t=ast.parse((ROOT/'brute/api/certify16n.py').read_text());bad=('os','subprocess','threading','multiprocessing','socket','io','pathlib','shutil','tempfile','random')
        for n in ast.walk(t):
            if isinstance(n,ast.Import):self.assertFalse([a.name for a in n.names if a.name.split('.')[0] in bad])
            if isinstance(n,ast.ImportFrom) and n.module:self.assertNotIn(n.module.split('.')[0],bad)
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):self.assertNotIn(n.func.id,('open','exec','eval','__import__'))

    def test_api_checks_closure(self):
        from scripts.api_checks_046 import closure
        n=closure('brute.api.certify16n');e=closure('brute.api.certify16e')
        self.assertIn('brute.api.certify16n',n);self.assertEqual({m:v for m,v in n.items() if m not in e and (v['bad_imports'] or v['bad_calls'])},{})


if __name__=='__main__':unittest.main()
