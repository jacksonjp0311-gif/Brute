"""v0.39.0: arm A16 (brute.scalesearch16). New file. stop_check16 gives stop_check14's stop and n_min on random small traces
(native and child-process solver; A16 is exact: no consistent machine is excluded) and adds apartness pair clauses; the cube
path, forced on every query, gives the same verdicts and logs cube calls; active16 ends with a valid stop and its final model
is consistent with the final trace; host-agnostic."""
import pathlib,random,unittest
from time import perf_counter
from brute import scalesearch14 as S14
from brute import scalesearch16 as S16
from brute.scalesearch import simulate
from brute.scalesearch10 import _Owner10,_capped_solve
from experiments.solver_proxy_041 import SolverServer,HardHook
from tests.test_encaudit16_0380 import trace,cases

FAR=lambda:perf_counter()+120


class ForcedH16(S16.H16):
    def query(self,o,deadline,assume):self._first=True;return super().query(o,deadline,assume)
    def _solve(self,assume):
        if self._first:self._first=False;return None
        return _capped_solve(self,assume)


class ForcedPool16(S16.Pool16):
    def get(self,n,masks,acts):
        self._update(masks,acts)
        if n not in self.inc:self.inc[n]=ForcedH16(n,self.k,self.m,self,self.solver)
        return self.inc[n].sync(masks,acts)


class TA16(unittest.TestCase):
    def test_stop_check16_equals_frozen(self):
        n_=0;stops=set();pairs=0
        for k,m,N,d,e,masks,acts in cases(4201,80):
            b=S14.stop_check14(masks,acts,k,m,N,FAR());a=S16.stop_check16(masks,acts,k,m,N,FAR());stops.add(b['stop'])
            self.assertEqual((a['stop'],a['n_min']),(b['stop'],b['n_min']));pairs+=a['audit']['pairs'];n_+=1
            self.assertTrue(all(c['phase'] in ('least','rival','cube') for c in a['audit']['calls']))
        self.assertGreaterEqual(len(stops),2);self.assertGreater(pairs,0);self.assertEqual(n_,80)

    def test_proxy_equals_native(self):
        S=SolverServer();H=HardHook();n_=0
        try:
            for k,m,N,d,e,masks,acts in cases(4202,30):
                b=S14.stop_check14(masks,acts,k,m,N,FAR());a=S16.stop_check16(masks,acts,k,m,N,FAR(),hook=H,factory=S.factory)
                self.assertEqual((a['stop'],a['n_min']),(b['stop'],b['n_min']));n_+=1
        finally:S.close()
        self.assertEqual(S.kills,0);self.assertGreater(H.armed,20);self.assertEqual(n_,30)

    def test_cube_path_forced(self):
        n_=0;cubes=0
        for k,m,N,d,e,masks,acts in cases(4204,40):
            b=S14.stop_check14(masks,acts,k,m,N,FAR());P=ForcedPool16(k,m)
            try:
                a=S14.stop_check14(masks,acts,k,m,N,FAR(),max(1,P.lower(masks,acts)),9.0,'g3',_Owner10(9.0),P)
                cubes+=sum(1 for c in P.calls if c['phase']=='cube');cc=P.cube_counts()
                self.assertEqual(cc['cubes'],sum(1 for c in P.calls if c['phase']=='cube'))
            finally:P.close()
            self.assertEqual((a['stop'],a['n_min']),(b['stop'],b['n_min']));n_+=1
        self.assertGreater(cubes,n_)

    def test_active16_valid(self):
        rng=random.Random(4203);k,m,N=2,2,3;n_=0;stops=set()
        for i in range(20):
            nt=rng.randint(2,3);d=[[rng.randrange(nt) for _ in range(k)] for _ in range(nt)];e=[rng.randrange(m) for _ in range(nt)]
            masks,acts=trace(rng,d,e,4,k);st={'q':0}
            for a in acts:st['q']=d[st['q']][a]
            def ob(a):st['q']=d[st['q']][a];return 1<<e[st['q']]
            x=S16.active16(masks,acts,k,m,N,ob,FAR(),16);stops.add(x['stop'])
            self.assertIn(x['stop'],('ID','IDF','K_spent','unknown'))
            if x['final']['model'] is not None:
                self.assertTrue(simulate(x['final']['model'][0],x['final']['model'][1],x['acts'],x['masks'])[0])
            self.assertIn('cube',x);n_+=1
        self.assertEqual(n_,20);self.assertIn('ID',stops)

    def test_host_agnostic(self):
        src=pathlib.Path(S16.__file__).read_text()
        for bad in ('import os','import threading','import subprocess','open(','socket','import time\n','print(','solver_proxy'):self.assertNotIn(bad,src)
        self.assertEqual((S16.QUERY_S14,S16.K14,S16.BUDGET14),(9.0,128,240.0))


if __name__=='__main__':unittest.main()
