"""GX2' second encoding and GMC counters: agreement with RegionK on random synthetic evidence (dev, no held-out seeds)."""
import random, unittest
from brute.region import RegionK
from brute.xcheck_sat import XRegion, mask_of, replay
from brute.driftsound import y1k_recent


def _evidence(rng):
    n=rng.choice([2,3]);k=2;s=rng.choice([1,2]);m=2**s
    tr=[[rng.randrange(n) for _ in range(k)] for _ in range(n)];em=[rng.randrange(m) for _ in range(n)]
    def mk(c):
        mm=1<<c
        for cc in range(m):
            if rng.random()<0.4:mm|=1<<cc
        return mm
    q=rng.randrange(n);acts=[];masks=[mk(em[q])]
    for _ in range(rng.randrange(0,8)):
        a=rng.randrange(k);q=tr[q][a];acts.append(a);masks.append(mk(em[q]) if rng.random()>0.1 else 1<<rng.randrange(m))
    return rng.choice([n,n+1]),k,m,masks,acts


class XcheckSat(unittest.TestCase):
    def test_mask_of(self):
        self.assertEqual(mask_of([None,None],2),0b1111)
        self.assertEqual(mask_of([1,0],2),1<<2)
        self.assertEqual(mask_of([None,1],2),(1<<1)|(1<<3))

    def test_agrees_with_regionk(self):
        rng=random.Random(11);checks=0
        for _ in range(60):
            n,k,m,masks,acts=_evidence(rng);R=RegionK(n,k,m,masks,acts);X=XRegion(n,k,m,masks,acts)
            try:
                for b in range(k):
                    s1=R.support(b);s2=X.support(b)
                    self.assertEqual(s1[0] if s1 else None,s2[0])
                    if s2[0] is None:continue
                    mask=rng.randrange(1,1<<m)
                    self.assertEqual(tuple(sorted(R.y1k(b,mask)[0])),tuple(X.y1k(b,mask)[0]))
                    t0=rng.randrange(0,len(acts)+1)
                    self.assertEqual(tuple(y1k_recent(R,b,mask,t0)[0]),tuple(X.y1k(b,mask,t0)[0]));checks+=3
                if X.feasible():self.assertEqual(R.saturated()[0],X.saturated()[0])
                self.assertEqual(X.witness_failures,0);self.assertEqual(X.unknown,0)
            finally:X.close();R.close()
        self.assertGreater(checks,60)


class ModelCount(unittest.TestCase):
    def test_counts_agree(self):
        try:import pyganak  # noqa: F401
        except ImportError:self.skipTest('pyganak not installed')
        from brute.modelcount import count_jobs, ganak_counts, blocking_count
        rng=random.Random(3)
        for _ in range(4):
            n,k,m,masks,acts=_evidence(rng);n=min(n,3)
            res=ganak_counts(count_jobs(n,k,m,masks,acts));R=res[('R',)]['count']
            bc,cens,_=blocking_count(n,k,m,masks,acts)
            self.assertIsNotNone(R);self.assertFalse(cens);self.assertEqual(int(R),bc)
            for a in range(k):
                tot=sum(int(res[('fibre',a,c)]['count']) for c in range(m))
                self.assertEqual(tot,int(res[('pairs',a)]['count']));self.assertGreaterEqual(tot,int(R))


if __name__=='__main__':unittest.main()
