"""v0.23.0: S2 exact search (brute.scalesearch) equals the frozen RegionK region, its witnesses are real machines,
identification, the tolerant variant, worlds_026 and host-agnostic source."""
import random,unittest,pathlib
from brute import scalesearch as SS
from brute.region import RegionSpace
from brute.noisyregion import tolerant_region
from experiments import worlds_026 as W


def trace(rng,n,k,T,m=4):
    d=[[rng.randrange(n) for _ in range(k)] for _ in range(n)];e=[rng.randrange(m) for _ in range(n)];q=0;acts=[];codes=[e[0]]
    for _ in range(T):a=rng.randrange(k);q=d[q][a];acts.append(a);codes.append(e[q])
    return acts,codes


def bits(c):return ((c>>1)&1,c&1)


class EqualsRegionK(unittest.TestCase):
    def run_pair(self,n_max,k,acts,codes,masked=False,rng=None):
        A=SS.ScaleRegion(n_max,k);B=RegionSpace(n_max,k=k,s=2)
        obs=[bits(c) for c in codes]
        if masked:obs=[tuple(None if rng.random()<0.3 else b for b in o) for o in obs]
        A.initialize(obs[0]);B.initialize(obs[0]);cmp=0
        try:
            for i,a in enumerate(acts):
                for b in range(k):
                    sa,ua=A.support(b);B.unk=0;sb=B.predict_support(b)
                    if ua==0 and B.unk==0:self.assertEqual(sa,sb,(i,b));cmp+=1
                self.assertEqual(A.status=='grammar_contradicted',B.status=='grammar_contradicted')
                A.observe(a,obs[i+1]);B.observe(a,obs[i+1])
        finally:A.close();B.close()
        return cmp

    def test_random_small(self):
        rng=random.Random(230);tot=0
        for _ in range(6):
            n=rng.randrange(1,4);k=rng.choice((2,3));acts,codes=trace(rng,n,k,14)
            tot+=self.run_pair(4,k,acts,codes)
        self.assertGreater(tot,200)

    def test_masked_and_contradicted(self):
        rng=random.Random(231)
        for _ in range(3):
            acts,codes=trace(rng,3,2,12);self.run_pair(3,2,acts,codes,masked=True,rng=rng)
        acts,codes=trace(random.Random(5),5,2,16);self.run_pair(2,2,acts,codes)   # 5-state data in a <=2 family


class Witnesses(unittest.TestCase):
    def test_pool_and_chain_machines_consistent(self):
        rng=random.Random(232);acts,codes=trace(rng,4,3,30);R=SS.ScaleRegion(6,3);R.initialize(bits(codes[0]))
        for i,a in enumerate(acts):
            for b in range(3):R.support(b)
            R.observe(a,bits(codes[i+1]))
            masks=R.masks
            for P in R.pool:
                ok,q,_=SS.simulate(P['d'],P['e'],R.actions,masks,P['start']);self.assertTrue(ok);self.assertEqual(q,P['q'])
                self.assertLessEqual(len(P['e']),6)
        R.close()

    def test_canonical_bfs(self):
        d=((1,2),(0,0),(2,1));e=(1,0,3)
        self.assertEqual(SS.canonical_bfs(d,e,2),(((0,1),(2,2),(1,0)),(3,0,1)))

    def test_greedy_fold_consistent(self):
        rng=random.Random(233);acts,codes=trace(rng,3,2,40);f=SS.greedy_fold(acts,codes,8,2)
        self.assertIsNotNone(f);self.assertTrue(SS.simulate(f[0],f[1],acts,[1<<c for c in codes])[0])


class Identify(unittest.TestCase):
    def test_cycle3_identified(self):
        w=W.world(9290001,'control_cycle3');tr=W.trajectory(w,9290001,0);R=SS.ScaleRegion(6,2);R.initialize(tr['readings'][0])
        for i,a in enumerate(tr['actions'][:60]):R.observe(a,tr['readings'][i+1])
        r=R.identify();R.close()
        self.assertEqual(r['n_min'],3);self.assertTrue(r['unique'])
        self.assertEqual(SS.canonical_bfs(*r['model']),SS.canonical_bfs(w.transitions,w.emissions,w.start))

    def test_unexercised_not_unique(self):
        R=SS.ScaleRegion(3,2);R.initialize((0,0));R.observe(0,(0,1));r=R.identify();R.close()
        self.assertEqual(r['n_min'],2);self.assertFalse(r['unique'])


class Tolerant(unittest.TestCase):
    def test_equals_frozen_tolerant(self):
        rng=random.Random(234)
        for _ in range(4):
            acts,codes=trace(rng,2,2,10);rd=[tuple(b^(rng.random()<0.15) for b in bits(c)) for c in codes];m=rng.randrange(0,3)
            A=SS.ScaleTolerant(3,rd,acts,m,2,2);B=tolerant_region(3,rd,acts,m,2,2)
            try:
                self.assertEqual(A.feasible,B.feasible)
                if A.feasible:
                    for b in range(2):self.assertEqual(A.support(b),B.support(b))
            finally:A.close();B.close()


class Worlds(unittest.TestCase):
    def test_scale_worlds_minimal_strong(self):
        from experiments.worlds_007 import minimal_states
        for f,n in W.SCALE.items():
            w=W.world(9290002,f);self.assertEqual((w.n,w.k,w.s),(n,3,2));self.assertEqual(minimal_states(w),n)
            self.assertTrue(W._strong(w.transitions,n));self.assertEqual(w,W.world(9290002,f))

    def test_trajectory(self):
        w=W.world(9290003,'scale8');t0=W.trajectory(w,9290003,0);t1=W.trajectory(w,9290003,0.05)
        self.assertEqual(len(t0['actions']),176);self.assertEqual(len(t0['readings']),177)
        self.assertEqual(t0['readings'],[W.bits(c) for c in t0['latent']]);self.assertNotEqual(t1['readings'],[W.bits(c) for c in t1['latent']])


class HostAgnostic(unittest.TestCase):
    def test_no_io(self):
        for f in ('brute/scalesearch.py','brute/scalebetting.py'):
            src=(pathlib.Path(__file__).resolve().parents[1]/f).read_text()
            for bad in ('import os','subprocess','threading','multiprocessing','open(','socket','import signal'):
                self.assertNotIn(bad,src,(f,bad))


if __name__=='__main__':unittest.main()
