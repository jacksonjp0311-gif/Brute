"""v0.28.0: S6 exact search (brute.scalesearch6) equals the frozen S1 region (RegionSpace) and S5 where both answer
exactly; S6_noorder gives the same exact answers; the incremental solver extends without rebuilding; ordering; the hard
cap holds; the identify probe (identify6); host-agnostic source. New file."""
import random,unittest,pathlib
from time import perf_counter
from brute import scalesearch6 as S6
from brute import scalesearch5 as S5
from brute.region import RegionSpace
from experiments import worlds_026 as W
from tests.test_scalesearch_0230 import trace,bits


class EqualsS1(unittest.TestCase):
    def run_pair(self,n_max,k,acts,codes,masked=False,rng=None,**kw):
        A=S6.ScaleRegion6(n_max,k,**kw);B=RegionSpace(n_max,k=k,s=2);obs=[bits(c) for c in codes]
        if masked:obs=[tuple(None if rng.random()<0.3 else b for b in o) for o in obs]
        A.initialize(obs[0]);B.initialize(obs[0]);cmp=0
        try:
            for i,a in enumerate(acts):
                for b in A.order():
                    sa,ua=A.support(b);B.unk=0;sb=B.predict_support(b)
                    if ua==0 and B.unk==0:self.assertEqual(sa,None if sb is None else tuple(sb),(i,b));cmp+=1
                self.assertEqual(A.status=='grammar_contradicted',B.status=='grammar_contradicted')
                A.observe(a,obs[i+1]);B.observe(a,obs[i+1])
        finally:A.close();B.close()
        return cmp

    def test_random_small(self):
        rng=random.Random(280);tot=0
        for _ in range(6):
            n=rng.randrange(1,4);k=rng.choice((2,3));acts,codes=trace(rng,n,k,14);tot+=self.run_pair(4,k,acts,codes)
        self.assertGreater(tot,150)

    def test_noorder_and_nowit(self):
        rng=random.Random(281)
        for kw in ({'ordered':False},{'witness':False},{'witness':False,'ordered':False}):
            acts,codes=trace(rng,3,2,12);self.assertGreater(self.run_pair(4,2,acts,codes,**kw),20,kw)

    def test_masked_and_contradicted(self):
        rng=random.Random(282)
        for _ in range(3):
            acts,codes=trace(rng,3,2,12);self.run_pair(3,2,acts,codes,masked=True,rng=rng)
        acts,codes=trace(random.Random(5),5,2,16);self.run_pair(2,2,acts,codes)

    def test_agrees_with_s5_on_world(self):
        w=W.world(9790001,'scale8');tr=W.trajectory(w,9790001,0)
        arms=[S6.ScaleRegion6(16,w.k,2),S6.ScaleRegion6(16,w.k,2,ordered=False),S5.ScaleRegion5(16,w.k,2)];n=0
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


class Incremental(unittest.TestCase):
    def test_one_solver_many_steps(self):
        rng=random.Random(283);acts,codes=trace(rng,3,2,12);R=S6.ScaleRegion6(4,2,witness=False);R.initialize(bits(codes[0]))
        try:
            for i,a in enumerate(acts):
                R.support(0);R.support(1);R.observe(a,bits(codes[i+1]))
            R.support(0)
            self.assertEqual(R.builds,1);self.assertGreater(R.extends,5);self.assertEqual(R.region.T,len(acts))
        finally:R.close()

    def test_order(self):
        R=S6.ScaleRegion6(4,3);R.initialize(bits(1))
        try:
            R.wit=[{0,1,2},{0},set()];self.assertEqual(R.order(),[0,1,2])
            R.wit=[set(),{0,1,2,3},{0}];self.assertEqual(R.order(),[1,2,0])
            R.ordered=False;self.assertEqual(R.order(),[0,1,2])
        finally:R.close()


class HardCap(unittest.TestCase):
    def test_tight_cap(self):
        w=W.world(9790012,'scale12');tr=W.trajectory(w,9790012,0);qs=0.3;R=S6.ScaleRegion6(16,w.k,2,qs);R.initialize(tr['readings'][0])
        qmax=0.0;t0=perf_counter()
        try:
            for i,a in enumerate(tr['actions'][:60]):
                for b in R.order():
                    t=perf_counter();R.support(b);qmax=max(qmax,perf_counter()-t)
                R.observe(a,tr['readings'][i+1])
                if perf_counter()-t0>60:break
        finally:R.close()
        self.assertLessEqual(qmax,qs+0.25,qmax)

    def test_deadline_respected(self):
        w=W.world(9790013,'scale12');tr=W.trajectory(w,9790013,0);R=S6.ScaleRegion6(16,w.k,2);R.initialize(tr['readings'][0])
        try:
            for i,a in enumerate(tr['actions'][:30]):R.observe(a,tr['readings'][i+1])
            t=perf_counter();R.support(0,t+0.2);self.assertLess(perf_counter()-t,0.5)
        finally:R.close()


class Identify(unittest.TestCase):
    def test_cycle3_identified(self):
        w=W.world(9790029,'control_cycle3');tr=W.trajectory(w,9790029,0);R=S6.ScaleRegion6(6,w.k);R.initialize(tr['readings'][0])
        for i,a in enumerate(tr['actions'][:60]):R.observe(a,tr['readings'][i+1])
        r=R.identify(perf_counter()+30);R.close()
        self.assertEqual(r['n_min'],3);self.assertTrue(r['unique']);self.assertFalse(r['second_found'])

    def test_ambiguous_short_trace(self):
        # two readings of one 2-code machine: a second machine (different unexercised transition) exists
        r=S6.identify6([0b01,0b10],[0],2,4,4,perf_counter()+10)
        self.assertEqual(r['n_min'],2);self.assertFalse(r['unique']);self.assertTrue(r['second_found']);self.assertFalse(r['unknown'])

    def test_deadline(self):
        r=S6.identify6([0b01,0b10],[0],2,4,4,perf_counter()-1);self.assertTrue(r['unknown'])


class HostAgnostic(unittest.TestCase):
    def test_no_io(self):
        src=(pathlib.Path(__file__).resolve().parents[1]/'brute/scalesearch6.py').read_text()
        for bad in ('import os','subprocess','threading','multiprocessing','open(','socket','import signal'):self.assertNotIn(bad,src,bad)


if __name__=='__main__':unittest.main()
