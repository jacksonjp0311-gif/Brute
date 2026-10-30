"""v0.25.0: S3 exact search (brute.scalesearch3) equals the frozen RegionK region and S2 where both answer exactly, its
witnesses are real machines, the clique bound is a lower bound, the per-query budget is hard, identification,
brute.certify/13 and host-agnostic source. New file."""
import random,unittest,pathlib
from time import perf_counter
from brute import scalesearch as SS
from brute import scalesearch3 as S3
from brute.region import RegionSpace
from experiments import worlds_026 as W
from tests.test_scalesearch_0230 import trace,bits


class EqualsRegionK(unittest.TestCase):
    def run_pair(self,n_max,k,acts,codes,masked=False,rng=None,solver=S3.SOLVER):
        A=S3.ScaleRegion3(n_max,k,solver=solver);B=RegionSpace(n_max,k=k,s=2);C=SS.ScaleRegion(n_max,k)
        obs=[bits(c) for c in codes]
        if masked:obs=[tuple(None if rng.random()<0.3 else b for b in o) for o in obs]
        A.initialize(obs[0]);B.initialize(obs[0]);C.initialize(obs[0]);cmp=0
        try:
            for i,a in enumerate(acts):
                for b in range(k):
                    sa,ua=A.support(b);B.unk=0;sb=B.predict_support(b);sc,uc=C.support(b)
                    if ua==0 and B.unk==0:self.assertEqual(sa,sb,(i,b));cmp+=1
                    if ua==0 and uc==0:self.assertEqual(sa,sc,(i,b))
                self.assertEqual(A.status=='grammar_contradicted',B.status=='grammar_contradicted')
                A.observe(a,obs[i+1]);B.observe(a,obs[i+1]);C.observe(a,obs[i+1])
        finally:A.close();B.close();C.close()
        return cmp

    def test_random_small(self):
        rng=random.Random(250);tot=0
        for _ in range(6):
            n=rng.randrange(1,4);k=rng.choice((2,3));acts,codes=trace(rng,n,k,14);tot+=self.run_pair(4,k,acts,codes)
        self.assertGreater(tot,200)

    def test_single_solvers_and_portfolio(self):
        rng=random.Random(251)
        for sv in ('m22','mcb','cd195','m22+mcb'):
            acts,codes=trace(rng,3,2,12);self.assertGreater(self.run_pair(4,2,acts,codes,solver=sv),20)

    def test_masked_and_contradicted(self):
        rng=random.Random(252)
        for _ in range(3):
            acts,codes=trace(rng,3,2,12);self.run_pair(3,2,acts,codes,masked=True,rng=rng)
        acts,codes=trace(random.Random(5),5,2,16);self.run_pair(2,2,acts,codes)


class Witnesses(unittest.TestCase):
    def test_pool_machines_consistent(self):
        rng=random.Random(253);acts,codes=trace(rng,4,3,30);R=S3.ScaleRegion3(6,3);R.initialize(bits(codes[0]))
        for i,a in enumerate(acts):
            for b in range(3):R.support(b)
            R.observe(a,bits(codes[i+1]))
            for P in R.pool:
                ok,q,_=SS.simulate(P['d'],P['e'],R.actions,R.masks,P['start']);self.assertTrue(ok);self.assertEqual(q,P['q'])
                self.assertLessEqual(len(P['e']),6)
        self.assertEqual(set(R.timing),{'repair','add_step','feasible','chain','solve_support'})
        self.assertEqual(sum(R.S.wins),R.S.wins[0]+R.S.wins[1]);R.close()


class CliqueBound(unittest.TestCase):
    def test_lower_bound(self):
        rng=random.Random(254)
        for _ in range(8):
            n=rng.randrange(2,6);acts,codes=trace(rng,n,2,40);R=S3.ScaleRegion3(8,2);R.initialize(bits(codes[0]))
            for i,a in enumerate(acts):R.observe(a,bits(codes[i+1]))
            lb=R.cheap_lb();r=R.identify();R.close()
            self.assertLessEqual(lb,n);self.assertGreaterEqual(lb,1)
            if r.get('n_min') is not None:self.assertLessEqual(lb,r['n_min'])

    def test_clique_lb_graph(self):
        self.assertEqual(S3.clique_lb([],5),1)
        self.assertEqual(S3.clique_lb([(0,1),(1,2),(0,2),(2,3)],3),3)


class Budget(unittest.TestCase):
    def test_hard_query_budget(self):
        w=W.world(9490001,'scale12');tr=W.trajectory(w,9490001,0);qs=0.3;R=S3.ScaleRegion3(16,w.k,2,qs);R.initialize(tr['readings'][0])
        qmax=0.0;t0=perf_counter();u=0
        try:
            for i,a in enumerate(tr['actions'][:40]):
                for b in range(w.k):
                    t=perf_counter();_,x=R.support(b);qmax=max(qmax,perf_counter()-t);u+=x
                t=perf_counter();R.observe(a,tr['readings'][i+1]);qmax=max(qmax,perf_counter()-t)
                if perf_counter()-t0>60:break
        finally:R.close()
        self.assertLessEqual(qmax,qs+0.5,qmax)

    def test_glucose_not_default(self):
        self.assertNotIn('g3',S3.SOLVER.split('+'));self.assertNotIn('g4',S3.SOLVER.split('+'))


class Identify(unittest.TestCase):
    def test_cycle3_identified(self):
        w=W.world(9290001,'control_cycle3');tr=W.trajectory(w,9290001,0);R=S3.ScaleRegion3(6,2);R.initialize(tr['readings'][0])
        for i,a in enumerate(tr['actions'][:60]):R.observe(a,tr['readings'][i+1])
        r=R.identify();R.close()
        self.assertEqual(r['n_min'],3);self.assertTrue(r['unique'])
        self.assertEqual(SS.canonical_bfs(*r['model']),SS.canonical_bfs(w.transitions,w.emissions,w.start))


class Certify13(unittest.TestCase):
    D=((0,1),[0,1,0,1,1,0,0,1,1,1,0],[(0,1),(1,None),(0,1),(1,0),(None,1),(0,1),(1,0),(0,0),(1,1),(0,1),(1,None)])

    def test_s3_equals_s2(self):
        from brute.api.certify13 import certify13
        from brute.api.certify12 import certify12
        a=certify13(*self.D,family_bound=3,search='s3');b=certify12(*self.D,family_bound=3,search='s2')
        self.assertEqual(a['api'],'brute.certify/13');self.assertEqual(a['search'],'s3')
        for k in ('supports','unknown','certificates','status'):self.assertEqual(a[k],b[k],k)

    def test_region_and_s2_unchanged(self):
        from brute.api.certify13 import certify13
        from brute.api.certify12 import certify12
        for kw in ({},{'search':'s2','family_bound':3}):
            a=certify13(*self.D,**kw);b=certify12(*self.D,**kw)
            for k in ('supports','unknown','certificates','status','m'):self.assertEqual(a[k],b[k],(kw,k))

    def test_refusals(self):
        from brute.api.certify13 import Certifier13
        for kw in ({'search':'s4'},{'search':'s3','method':'betting'},{'search':'s3','family_bound':17},{'search':'s3','num_actions':5}):
            with self.assertRaises(ValueError):Certifier13((0,1),**kw)


class HostAgnostic(unittest.TestCase):
    def test_no_io(self):
        for f in ('brute/scalesearch3.py','brute/api/certify13.py'):
            src=(pathlib.Path(__file__).resolve().parents[1]/f).read_text()
            for bad in ('import os','subprocess','threading','multiprocessing','open(','socket','import signal'):
                self.assertNotIn(bad,src,(f,bad))


if __name__=='__main__':unittest.main()
