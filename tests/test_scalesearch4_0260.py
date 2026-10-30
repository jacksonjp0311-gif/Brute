"""v0.26.0: S4 exact search (brute.scalesearch4) equals the frozen S1 region (RegionSpace) where both answer exactly; the
no-witness ablation and the no-symmetry variant give the same exact answers; pool machines are real; the per-query cap
is hard; identification; brute.certify/14; host-agnostic source. New file."""
import random,unittest,pathlib
from time import perf_counter
from brute import scalesearch as SS
from brute import scalesearch4 as S4
from brute.region import RegionSpace
from experiments import worlds_026 as W
from tests.test_scalesearch_0230 import trace,bits


class EqualsS1(unittest.TestCase):
    def run_pair(self,n_max,k,acts,codes,masked=False,rng=None,**kw):
        A=S4.ScaleRegion4(n_max,k,**kw);B=RegionSpace(n_max,k=k,s=2);obs=[bits(c) for c in codes]
        if masked:obs=[tuple(None if rng.random()<0.3 else b for b in o) for o in obs]
        A.initialize(obs[0]);B.initialize(obs[0]);cmp=0
        try:
            for i,a in enumerate(acts):
                for b in range(k):
                    sa,ua=A.support(b);B.unk=0;sb=B.predict_support(b)
                    if ua==0 and B.unk==0:self.assertEqual(sa,None if sb is None else tuple(sb),(i,b));cmp+=1
                self.assertEqual(A.status=='grammar_contradicted',B.status=='grammar_contradicted')
                A.observe(a,obs[i+1]);B.observe(a,obs[i+1])
        finally:A.close();B.close()
        return cmp

    def test_random_small(self):
        rng=random.Random(260);tot=0
        for _ in range(6):
            n=rng.randrange(1,4);k=rng.choice((2,3));acts,codes=trace(rng,n,k,14);tot+=self.run_pair(4,k,acts,codes)
        self.assertGreater(tot,200)

    def test_nowit_and_nosym(self):
        rng=random.Random(261)
        for kw in ({'witness':False},{'symmetry':False},{'witness':False,'symmetry':False},{'solver':'m22'}):
            acts,codes=trace(rng,3,2,12);self.assertGreater(self.run_pair(4,2,acts,codes,**kw),20,kw)

    def test_masked_and_contradicted(self):
        rng=random.Random(262)
        for _ in range(3):
            acts,codes=trace(rng,3,2,12);self.run_pair(3,2,acts,codes,masked=True,rng=rng)
        acts,codes=trace(random.Random(5),5,2,16);self.run_pair(2,2,acts,codes)

    def test_variants_agree_on_world(self):
        w=W.world(9590001,'scale8');tr=W.trajectory(w,9590001,0);arms=[S4.ScaleRegion4(16,w.k,2),S4.ScaleRegion4(16,w.k,2,witness=False),
                                                                          S4.ScaleRegion4(16,w.k,2,symmetry=False)]
        try:
            for R in arms:R.initialize(tr['readings'][0])
            for i,a in enumerate(tr['actions'][:25]):
                for b in range(w.k):
                    out=[R.support(b) for R in arms];ex=[s for s,u in out if u==0]
                    for s in ex:self.assertEqual(s,ex[0],(i,b))
                for R in arms:R.observe(a,tr['readings'][i+1])
        finally:
            for R in arms:R.close()


class Witnesses(unittest.TestCase):
    def test_pool_machines_consistent(self):
        rng=random.Random(263);acts,codes=trace(rng,4,3,30);R=S4.ScaleRegion4(6,3);R.initialize(bits(codes[0]))
        try:
            for i,a in enumerate(acts):
                for b in range(3):R.support(b)
                R.observe(a,bits(codes[i+1]))
                self.assertLessEqual(len(R.pool),S4.POOL_MAX)
                for M in R.pool:
                    ok,q,_=SS.simulate(M.d,M.e,R.acts,R.masks,0);self.assertTrue(ok);self.assertEqual(q,M.q);self.assertLessEqual(len(M.e),6)
            self.assertGreater(R.queries_by_witness,0)
        finally:R.close()

    def test_nowit_has_no_pool(self):
        rng=random.Random(264);acts,codes=trace(rng,3,2,10);R=S4.ScaleRegion4(4,2,witness=False);R.initialize(bits(codes[0]))
        for i,a in enumerate(acts):
            for b in range(2):R.support(b)
            R.observe(a,bits(codes[i+1]))
        self.assertEqual(len(R.pool),0);self.assertEqual(R.queries_by_witness,0);R.close()


class Budget(unittest.TestCase):
    def test_hard_query_cap(self):
        w=W.world(9590002,'scale12');tr=W.trajectory(w,9590002,0);qs=0.3;R=S4.ScaleRegion4(16,w.k,2,qs);R.initialize(tr['readings'][0])
        qmax=0.0;t0=perf_counter()
        try:
            for i,a in enumerate(tr['actions'][:60]):
                for b in range(w.k):
                    t=perf_counter();R.support(b);qmax=max(qmax,perf_counter()-t)
                t=perf_counter();R.observe(a,tr['readings'][i+1]);qmax=max(qmax,perf_counter()-t)
                if perf_counter()-t0>60:break
        finally:R.close()
        self.assertLessEqual(qmax,qs+0.5,qmax)

    def test_deadline_respected(self):
        w=W.world(9590003,'scale12');tr=W.trajectory(w,9590003,0);R=S4.ScaleRegion4(16,w.k,2);R.initialize(tr['readings'][0])
        try:
            for i,a in enumerate(tr['actions'][:30]):R.observe(a,tr['readings'][i+1])
            t=perf_counter();R.support(0,t+0.2);self.assertLess(perf_counter()-t,0.8)
        finally:R.close()


class Identify(unittest.TestCase):
    def test_cycle3_identified(self):
        w=W.world(9290001,'control_cycle3');tr=W.trajectory(w,9290001,0);R=S4.ScaleRegion4(6,2);R.initialize(tr['readings'][0])
        for i,a in enumerate(tr['actions'][:60]):R.observe(a,tr['readings'][i+1])
        r=R.identify(perf_counter()+30);R.close()
        self.assertEqual(r['n_min'],3);self.assertTrue(r['unique'])
        self.assertEqual(SS.canonical_bfs(*r['model'],0),SS.canonical_bfs(w.transitions,w.emissions,w.start))

    def test_identify_trace_lower_bound(self):
        rng=random.Random(265)
        for _ in range(5):
            n=rng.randrange(2,5);acts,codes=trace(rng,n,2,40);masks=[S4.codes_mask(bits(c),2) for c in codes]
            self.assertLessEqual(S4._lower_bound(masks),n)
            r=S4.identify_trace(masks,acts,2,4,8,perf_counter()+30)
            self.assertIsNotNone(r['n_min']);self.assertLessEqual(r['n_min'],n)


class Certify14(unittest.TestCase):
    D=((0,1),[0,1,0,1,1,0,0,1,1,1,0],[(0,1),(1,None),(0,1),(1,0),(None,1),(0,1),(1,0),(0,0),(1,1),(0,1),(1,None)])

    def test_s4_equals_s3(self):
        from brute.api.certify14 import certify14
        from brute.api.certify13 import certify13
        a=certify14(*self.D,family_bound=3,search='s4');b=certify13(*self.D,family_bound=3,search='s3')
        self.assertEqual(a['api'],'brute.certify/14');self.assertEqual(a['search'],'s4')
        for k in ('supports','unknown','certificates','status'):self.assertEqual(a[k],b[k],k)

    def test_older_unchanged(self):
        from brute.api.certify14 import certify14
        from brute.api.certify13 import certify13
        for kw in ({},{'search':'s2','family_bound':3},{'search':'s3','family_bound':3}):
            a=certify14(*self.D,**kw);b=certify13(*self.D,**kw)
            for k in ('supports','unknown','certificates','status','m'):self.assertEqual(a[k],b[k],(kw,k))

    def test_refusals(self):
        from brute.api.certify14 import Certifier14
        for kw in ({'search':'s5'},{'search':'s4','method':'betting'},{'search':'s4','family_bound':17},{'search':'s4','num_actions':5}):
            with self.assertRaises(ValueError):Certifier14((0,1),**kw)


class HostAgnostic(unittest.TestCase):
    def test_no_io(self):
        for f in ('brute/scalesearch4.py','brute/api/certify14.py'):
            src=(pathlib.Path(__file__).resolve().parents[1]/f).read_text()
            for bad in ('import os','subprocess','threading','multiprocessing','open(','socket','import signal'):
                self.assertNotIn(bad,src,(f,bad))


if __name__=='__main__':unittest.main()
