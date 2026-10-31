"""v0.37.0: A15 / A15_cube (brute.scalesearch15). New file; built from tests/test_scalesearch14_0360.py (frozen).
apart_matrix equals a brute-force apartness check; the greedy clique is pairwise apart and starts at position 0; the pooled
least n of Inc15 equals the frozen least14 and an exhaustive enumeration; stop_check15 (with and without the cube split) gives
stop_check14's stop and n_min; the cube path is exercised by a subclass whose first (un-cubed) call of every query reports
'capped' (so every verdict comes from the cubes) and still gives stop_check14's verdicts; A15 ID stops are checked by
enumeration; a prefix change is refused;
GINC15: on every sealed study-039 final trace where A14 decided (scale12, perm12, control: 30 cases), stop_check15 with and
without the cube split gives A14's final stop and n_min (Exact); host-agnostic."""
import gzip,itertools,json,pathlib,random,unittest
from time import perf_counter
from brute import scalesearch14 as S14
from brute import scalesearch15 as S
from brute.region import codes_mask
from brute.scalesearch import simulate
from brute.scalesearch10 import _Owner10,_capped_solve
from experiments.worlds_026 import S_BITS

FAR=lambda:perf_counter()+120
ROOT=pathlib.Path(__file__).resolve().parents[1]
SEALED039=ROOT/'results/study-039/main/RESULTS.json.gz'


def machines(n,k,m):
    for d in itertools.product(range(n),repeat=n*k):
        D=[list(d[q*k:(q+1)*k]) for q in range(n)]
        for E in itertools.product(range(m),repeat=n):yield D,list(E)


def differs(d1,e1,s1,d2,e2,s2):
    k=len(d1[0]);seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return True
        for a in range(k):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return False


def trace(rng,d,e,T,k):
    q=0;acts=[];masks=[1<<e[0]]
    for _ in range(T):a=rng.randrange(k);q=d[q][a];acts.append(a);masks.append(1<<e[q])
    return masks,acts


def apart_bf(masks,acts,t,u):
    T=len(acts);j=0
    while True:
        if not masks[t+j]&masks[u+j]:return True
        if u+j>=T or acts[t+j]!=acts[u+j]:return False
        j+=1


class ForcedCube(S.Inc15):
    """The first (un-cubed) call of every query reports capped (None), so Inc15.query's own cube split gives every verdict."""
    def query(self,o,deadline,assume):
        self._first=True;return super().query(o,deadline,assume)

    def _solve(self,assume):
        if self._first:self._first=False;return None
        return _capped_solve(self,assume)


class ForcedPool(S.Pool15):
    def get(self,n,masks,acts):
        self._update(masks,acts)
        if n not in self.inc:self.inc[n]=ForcedCube(n,self.k,self.m,self,self.solver,True)
        return self.inc[n].sync(masks,acts)


def final_trace039(case):
    from experiments import worlds_026 as W26
    from experiments import worlds_039 as W
    a=case['arms']['A14'];tr=W26.trajectory(W.world(case['seed'],case['family']),case['seed'],0.0)
    acts=list(tr['actions'])+list(a['extra_acts']);masks=[codes_mask(tuple(r),W26.S_BITS) for r in tr['readings']]+list(a['extra_masks'])
    return masks,acts


class T15(unittest.TestCase):
    def test_apart_matrix_and_clique(self):
        rng=random.Random(4001);n_=0
        for _ in range(30):
            k=rng.randint(2,3);m=rng.randint(2,4);nt=rng.randint(1,5);d=[[rng.randrange(nt) for _ in range(k)] for _ in range(nt)]
            e=[rng.randrange(m) for _ in range(nt)];masks,acts=trace(rng,d,e,rng.randint(0,14),k)
            masks=[x|(1<<rng.randrange(m) if rng.random()<0.2 else 0) for x in masks];A=S.apart_matrix(masks,acts)
            for t in range(len(masks)):
                for u in range(t+1,len(masks)):self.assertEqual(bool(A[t][u]),apart_bf(masks,acts,t,u));n_+=1
            C=S.greedy_clique(A);self.assertEqual(C[0],0)
            for i,a in enumerate(C):
                for b in C[i+1:]:self.assertTrue(S._ap(A,a,b))
        self.assertGreater(n_,300)

    def test_least_equals_least14_and_enumeration(self):
        rng=random.Random(4002);k,m=2,2;checked=0
        for _ in range(12):
            nt=rng.randint(1,3);d=[[rng.randrange(nt) for _ in range(k)] for _ in range(nt)];e=[rng.randrange(m) for _ in range(nt)]
            masks,acts=trace(rng,d,e,12,k)
            for cube in (False,True):
                P=S.Pool15(k,m,cube=cube)
                try:
                    for T in (3,6,9,12):
                        mk,ac=masks[:T+1],acts[:T];P14=S14.Pool14(k,m)
                        try:b=S14.least14(_Owner10(30),P14,mk,ac,3,FAR())
                        finally:P14.close()
                        a=S.least14(_Owner10(30),P,mk,ac,3,FAR(),P.lower(mk,ac))
                        best=min(n for n in (1,2,3) if any(simulate(D,E,ac,mk)[0] for D,E in machines(n,k,m)))
                        self.assertEqual(a[:2],b[:2]);self.assertEqual(a[:2],('ok',best));self.assertTrue(simulate(a[2][0],a[2][1],ac,mk)[0]);checked+=1
                finally:P.close()
        self.assertGreater(checked,80)

    def _cmp(self,seed,pool_factory=None,trials=60,need_cubes=False):
        rng=random.Random(seed);n_=0;stops=set();cubes=0
        for _ in range(trials):
            k=rng.randint(2,3);m=rng.choice((2,4));N=rng.randint(2,4);nt=rng.randint(1,N)
            d=[[rng.randrange(nt) for _ in range(k)] for _ in range(nt)];e=[rng.randrange(m) for _ in range(nt)]
            masks,acts=trace(rng,d,e,rng.randint(2,14),k)
            b=S14.stop_check14(masks,acts,k,m,N,FAR())
            if pool_factory is None:
                for cube in (False,True):
                    a=S.stop_check15(masks,acts,k,m,N,FAR(),cube=cube);self.assertEqual((a['stop'],a['n_min']),(b['stop'],b['n_min']));n_+=1
            else:
                P=pool_factory(k,m)
                try:a=S.stop_check15(masks,acts,k,m,N,FAR(),P=P);cubes+=P.cube_counts()['cubes']
                finally:P.close()
                self.assertEqual((a['stop'],a['n_min']),(b['stop'],b['n_min']));n_+=1
            stops.add(b['stop'])
        self.assertGreaterEqual(len(stops),2)
        if need_cubes:self.assertGreater(cubes,n_)
        return n_

    def test_stop_check15_equals_stop_check14(self):self.assertGreater(self._cmp(4003),100)

    def test_cube_path_forced(self):
        self.assertGreater(self._cmp(4004,lambda k,m:ForcedPool(k,m,cube=True),need_cubes=True),50)

    def test_ID_stop_checked_by_enumeration(self):
        rng=random.Random(3903);k,m=2,2;N=3;ids=0;words=0
        for _ in range(40):
            nt=rng.randint(2,3);d=[[rng.randrange(nt) for _ in range(k)] for _ in range(nt)];e=[rng.randrange(m) for _ in range(nt)]
            masks,acts=trace(rng,d,e,4,k);st={'q':0}
            for a in acts:st['q']=d[st['q']][a]
            def ob(a):st['q']=d[st['q']][a];return 1<<e[st['q']]
            x=S.active15(masks,acts,k,m,N,ob,FAR(),16,cube=bool(_%2));self.assertLessEqual(x['used'],16)
            words+=sum(1 for r in x['rounds'] if 'obs' in r)
            if x['stop']!='ID':continue
            ids+=1;M1=x['final']['model'];s1=x['final']['s1']
            for nn in range(1,N+1):
                for D,E in machines(nn,k,m):
                    ok,s2,_=simulate(D,E,x['acts'],x['masks'])
                    if not ok:continue
                    self.assertFalse(differs(M1[0],M1[1],s1,D,E,s2));self.assertFalse(differs(M1[0],M1[1],0,D,E,0))
            self.assertFalse(differs(M1[0],M1[1],0,d,e,0))
        self.assertGreater(ids,5);self.assertGreater(words,0)

    def test_prefix_change_refused(self):
        P=S.Pool15(2,2);I=P.get(2,[1,2],[0])
        with self.assertRaises(ValueError):I.sync([1,1,2],[0,1])
        P.close()

    def test_GINC15_sealed_039_traces(self):
        d=json.load(gzip.open(SEALED039));items=[];t=perf_counter()
        cs=[c for c in d['cases'] if c['key'] in ('scale12','perm12','control') and c['arms']['A14']['stop']!='unknown']
        for c in cs:
            masks,acts=final_trace039(c);r=c['arms']['A14']['rounds'][-1];k=c['k'];m=1<<S_BITS
            for cube in (False,True):
                a=S.stop_check15(masks,acts,k,m,c['N'],perf_counter()+600,cube=cube)
                items.append([c['key'],c['seed'],cube,[r['check'],r['n_min']],[a['stop'],a['n_min']]])
        bad=[x for x in items if x[3]!=x[4]]
        self.assertEqual(len(cs),30);self.assertEqual(bad,[])
        print('\nGINC15',json.dumps({'cases':len(cs),'checks':len(items),'mismatches':len(bad),'wall_informational':round(perf_counter()-t,1)}))

    def test_constants_and_host_agnostic(self):
        self.assertEqual((S.QUERY_S14,S.K14,S.BUDGET14),(9.0,128,240.0))
        src=pathlib.Path(S.__file__).read_text()
        for bad in ('import os','import threading','import subprocess','open(','socket','import time\n','print('):self.assertNotIn(bad,src)


if __name__=='__main__':unittest.main()
