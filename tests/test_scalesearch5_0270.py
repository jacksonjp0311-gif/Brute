"""v0.27.0: S5 exact search (brute.scalesearch5) equals the frozen S1 region (RegionSpace) and S4 where both answer exactly;
S5_softcap gives the same exact answers; the hard cap holds (tight cap, deadline, tiny build guard); identification;
host-agnostic source. New file."""
import random,unittest,pathlib
from time import perf_counter
from brute import scalesearch5 as S5
from brute import scalesearch4 as S4
from brute.region import RegionSpace
from experiments import worlds_026 as W
from tests.test_scalesearch_0230 import trace,bits


class EqualsS1(unittest.TestCase):
    def run_pair(self,n_max,k,acts,codes,masked=False,rng=None,**kw):
        A=S5.ScaleRegion5(n_max,k,**kw);B=RegionSpace(n_max,k=k,s=2);obs=[bits(c) for c in codes]
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
        rng=random.Random(270);tot=0
        for _ in range(6):
            n=rng.randrange(1,4);k=rng.choice((2,3));acts,codes=trace(rng,n,k,14);tot+=self.run_pair(4,k,acts,codes)
        self.assertGreater(tot,150)

    def test_softcap_and_nowit(self):
        rng=random.Random(271)
        for kw in ({'hard_cap':False},{'witness':False},{'witness':False,'hard_cap':False}):
            acts,codes=trace(rng,3,2,12);self.assertGreater(self.run_pair(4,2,acts,codes,**kw),20,kw)

    def test_masked_and_contradicted(self):
        rng=random.Random(272)
        for _ in range(3):
            acts,codes=trace(rng,3,2,12);self.run_pair(3,2,acts,codes,masked=True,rng=rng)
        acts,codes=trace(random.Random(5),5,2,16);self.run_pair(2,2,acts,codes)

    def test_agrees_with_s4_on_world(self):
        w=W.world(9690001,'scale8');tr=W.trajectory(w,9690001,0)
        arms=[S5.ScaleRegion5(16,w.k,2),S5.ScaleRegion5(16,w.k,2,hard_cap=False),S4.ScaleRegion4(16,w.k,2)];n=0
        try:
            for R in arms:R.initialize(tr['readings'][0])
            for i,a in enumerate(tr['actions'][:25]):
                for b in range(w.k):
                    ex=[s for s,u in (R.support(b) for R in arms) if u==0];n+=len(ex)
                    for s in ex:self.assertEqual(s,ex[0],(i,b))
                for R in arms:R.observe(a,tr['readings'][i+1])
        finally:
            for R in arms:R.close()
        self.assertGreater(n,100)

    def test_no_symmetry_clauses(self):
        R=S5.ScaleRegion5(6,2);R.initialize(bits(1))
        try:R.support(0);self.assertFalse(R.symmetry);self.assertFalse(R.region.symmetry if hasattr(R.region,'symmetry') else False)
        finally:R.close()


class HardCap(unittest.TestCase):
    def _qmax(self,R,tr,steps,limit=60):
        qmax=0.0;t0=perf_counter()
        for i,a in enumerate(tr['actions'][:steps]):
            for b in range(R.k):
                t=perf_counter();R.support(b);qmax=max(qmax,perf_counter()-t)
            R.observe(a,tr['readings'][i+1])
            if perf_counter()-t0>limit:break
        return qmax

    def test_tight_cap(self):
        w=W.world(9690012,'scale12');tr=W.trajectory(w,9690012,0);qs=0.3;R=S5.ScaleRegion5(16,w.k,2,qs);R.initialize(tr['readings'][0])
        try:qmax=self._qmax(R,tr,60)
        finally:R.close()
        self.assertLessEqual(qmax,qs+0.25,qmax)

    def test_deadline_respected(self):
        w=W.world(9690013,'scale12');tr=W.trajectory(w,9690013,0);R=S5.ScaleRegion5(16,w.k,2);R.initialize(tr['readings'][0])
        try:
            for i,a in enumerate(tr['actions'][:30]):R.observe(a,tr['readings'][i+1])
            t=perf_counter();R.support(0,t+0.2);self.assertLess(perf_counter()-t,0.5)
        finally:R.close()

    def test_build_guard(self):
        rng=random.Random(273);acts,codes=trace(rng,3,2,10);R=S5.ScaleRegion5(4,2);R.initialize(bits(codes[0]))
        try:
            R.support(0);R.observe(acts[0],bits(codes[1]));R._build_rate=1e3
            s,u=R.support(1);self.assertGreater(u,0);self.assertEqual(R.build_skips,1);self.assertIsNone(R.region)
        finally:R.close()

    def test_prop_rate_learned(self):
        w=W.world(9690014,'scale12');tr=W.trajectory(w,9690014,0);R=S5.ScaleRegion5(16,w.k,2,1.0);R.initialize(tr['readings'][0])
        try:self._qmax(R,tr,30,20);self.assertGreater(R.chunks,0);self.assertNotEqual(R.prate,S5.PROP_RATE0)
        finally:R.close()


class Identify(unittest.TestCase):
    def test_cycle3_identified(self):
        w=W.world(9290001,'control_cycle3');tr=W.trajectory(w,9290001,0);R=S5.ScaleRegion5(6,2);R.initialize(tr['readings'][0])
        for i,a in enumerate(tr['actions'][:60]):R.observe(a,tr['readings'][i+1])
        r=R.identify(perf_counter()+30);R.close()
        self.assertEqual(r['n_min'],3);self.assertTrue(r['unique'])


class HostAgnostic(unittest.TestCase):
    def test_no_io(self):
        src=(pathlib.Path(__file__).resolve().parents[1]/'brute/scalesearch5.py').read_text()
        for bad in ('import os','subprocess','threading','multiprocessing','open(','socket','import signal'):self.assertNotIn(bad,src,bad)


if __name__=='__main__':unittest.main()
