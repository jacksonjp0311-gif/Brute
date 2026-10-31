"""v0.38.0: audit variants E0-E4 (brute.encaudit16) and the hard per-call cap (experiments.solver_proxy_041). New file.
E0 / E3 / E4 equal the frozen stop_check14 / stop_check15 / stop_check15(cube) and active14 / active15 (stop, n_min) with the
native and with the child-process solver; E1 and E2 give stop_check14's stop and n_min on random small traces (every
variant is exact: no consistent machine is excluded); E1 adds pair clauses and E2 none; the cube path is forced; a
hung child is killed at the hard deadline (wall <= s + 1.0 + slack), the call reads as capped and the next call replays the
clause log into a fresh child and gives the native verdict; host-agnostic."""
import pathlib,random,time,unittest
from time import perf_counter
from brute import scalesearch14 as S14
from brute import scalesearch15 as S15
from brute import encaudit16 as EA
from brute.scalesearch10 import _Owner10,_capped_solve
from experiments.solver_proxy_041 import SolverServer,HardHook,HARD_GRACE

FAR=lambda:perf_counter()+120


def trace(rng,d,e,T,k):
    q=0;acts=[];masks=[1<<e[0]]
    for _ in range(T):a=rng.randrange(k);q=d[q][a];acts.append(a);masks.append(1<<e[q])
    return masks,acts


def cases(seed,trials):
    rng=random.Random(seed)
    for _ in range(trials):
        k=rng.randint(2,3);m=rng.choice((2,4));N=rng.randint(2,4);nt=rng.randint(1,N)
        d=[[rng.randrange(nt) for _ in range(k)] for _ in range(nt)];e=[rng.randrange(m) for _ in range(nt)]
        masks,acts=trace(rng,d,e,rng.randint(2,14),k);yield k,m,N,d,e,masks,acts


class ForcedH15(EA.H15):
    def query(self,o,deadline,assume):self._first=True;return super().query(o,deadline,assume)
    def _solve(self,assume):
        if self._first:self._first=False;return None
        return _capped_solve(self,assume)


class ForcedPool(EA.PoolE15):
    def get(self,n,masks,acts):
        self._update(masks,acts)
        if n not in self.inc:self.inc[n]=ForcedH15(n,self.k,self.m,self,self.solver,True)
        return self.inc[n].sync(masks,acts)


class TAudit(unittest.TestCase):
    def test_stop_check_variants_equal_frozen(self):
        n_=0;stops=set();pairs=0
        for k,m,N,d,e,masks,acts in cases(4101,60):
            b=S14.stop_check14(masks,acts,k,m,N,FAR());stops.add(b['stop'])
            ref={'E0':b,'E3':S15.stop_check15(masks,acts,k,m,N,FAR()),'E4':S15.stop_check15(masks,acts,k,m,N,FAR(),cube=True)}
            for v in EA.VARIANTS:
                a=EA.stop_check_audit(v,masks,acts,k,m,N,FAR())
                self.assertEqual((a['stop'],a['n_min']),(b['stop'],b['n_min']),v)
                if v in ref:self.assertEqual((a['stop'],a['n_min']),(ref[v]['stop'],ref[v]['n_min']))
                self.assertTrue(all(c['phase'] in ('least','rival','cube') for c in a['audit']['calls']))
                if v=='E1':pairs+=a['audit']['pairs']
                if v=='E2':self.assertEqual(a['audit']['pairs'],0)
                n_+=1
        self.assertGreaterEqual(len(stops),2);self.assertGreater(n_,250);self.assertGreater(pairs,0)

    def test_proxy_equals_native(self):
        S=SolverServer();H=HardHook();n_=0
        try:
            for k,m,N,d,e,masks,acts in cases(4102,25):
                b=S14.stop_check14(masks,acts,k,m,N,FAR())
                for v in EA.VARIANTS:
                    a=EA.stop_check_audit(v,masks,acts,k,m,N,FAR(),hook=H,factory=S.factory)
                    self.assertEqual((a['stop'],a['n_min']),(b['stop'],b['n_min']),v);n_+=1
        finally:S.close()
        self.assertEqual(S.kills,0);self.assertGreater(H.armed,100);self.assertEqual(n_,125)

    def test_active_arms_equal_frozen(self):
        rng=random.Random(4103);k,m,N=2,2,3;n_=0
        for i in range(16):
            nt=rng.randint(2,3);d=[[rng.randrange(nt) for _ in range(k)] for _ in range(nt)];e=[rng.randrange(m) for _ in range(nt)]
            masks,acts=trace(rng,d,e,4,k)
            for arm,v in EA.ARM_VARIANT.items():
                for proxy in (False,True):
                    st={'q':0}
                    for a in acts:st['q']=d[st['q']][a]
                    def ob(a):st['q']=d[st['q']][a];return 1<<e[st['q']]
                    st2={'q':st['q']}
                    def ob2(a):st2['q']=d[st2['q']][a];return 1<<e[st2['q']]
                    if arm=='A14':ref=S14.active14(masks,acts,k,m,N,ob,FAR(),16)
                    else:ref=S15.active15(masks,acts,k,m,N,ob,FAR(),16,cube=(arm=='A15_cube'))
                    S=SolverServer() if proxy else None
                    try:x=EA.active_audit(v,masks,acts,k,m,N,ob2,FAR(),16,hook=HardHook() if proxy else None,
                                          factory=S.factory if proxy else EA.native)
                    finally:
                        if S:S.close()
                    self.assertEqual((x['stop'],x['final']['n_min']),(ref['stop'],ref['final']['n_min']));n_+=1
        self.assertEqual(n_,96)

    def test_cube_path_forced(self):
        n_=0;cubes=0
        for k,m,N,d,e,masks,acts in cases(4104,40):
            b=S14.stop_check14(masks,acts,k,m,N,FAR());P=ForcedPool(k,m,cube=True)
            try:
                a=S14.stop_check14(masks,acts,k,m,N,FAR(),max(1,P.lower(masks,acts)),9.0,'g3',_Owner10(9.0),P)
                cubes+=sum(1 for c in P.calls if c['phase']=='cube')
            finally:P.close()
            self.assertEqual((a['stop'],a['n_min']),(b['stop'],b['n_min']));n_+=1
        self.assertGreater(cubes,n_)

    def test_hard_kill_and_replay(self):
        from pysat.examples.genhard import PHP
        S=SolverServer(soft=False);H=HardHook()
        try:
            p=S.factory('g3');p.add_clause([1,2]);p.add_clause([-1]);self.assertTrue(p.solve_limited([]))
            q=S.factory('g3')
            for c in PHP(10).clauses:q.add_clause(c)
            t=time.monotonic();tok=H.arm(q.interrupt,1.0);r=q.solve_limited([]);H.disarm(tok);w=time.monotonic()-t
            self.assertIsNone(r);self.assertEqual(S.kills,1);self.assertLessEqual(w,1.0+HARD_GRACE+0.5);self.assertGreaterEqual(w,1.0+HARD_GRACE-0.05)
            p.add_clause([-2,3]);self.assertTrue(p.solve_limited([-1]));self.assertEqual(sorted(p.get_model()),[-1,2,3]);self.assertEqual(p.replays,1)
            self.assertFalse(p.solve_limited([-3]))
        finally:S.close()

    def test_capped_solve_reads_kill_as_capped(self):
        from pysat.examples.genhard import PHP
        S=SolverServer(soft=False);H=HardHook()
        try:
            P=EA.make_pool('E0',2,2,factory=S.factory);R=P.get(1,[1,1],[0])
            off=R.nv
            for c in PHP(10).clauses:R.s.add_clause([x+off if x>0 else x-off for x in c])
            o=_Owner10(1.0,H);R._owner=o;R._dl=perf_counter()+60;r=_capped_solve(R,[])
            self.assertIsNone(r);self.assertEqual(o.capped,1);self.assertLessEqual(max(o.query_walls),1.0+HARD_GRACE+0.5);P.close()
        finally:S.close()

    def test_host_agnostic(self):
        src=pathlib.Path(EA.__file__).read_text()
        for bad in ('import os','import threading','import subprocess','open(','socket','import time\n','print(','solver_proxy'):self.assertNotIn(bad,src)
        self.assertEqual((EA.QUERY_S14,EA.K14,EA.BUDGET14),(9.0,128,240.0));self.assertEqual(EA.ARM_VARIANT,{'A14':'E0','A15':'E3','A15_cube':'E4'})


if __name__=='__main__':unittest.main()
