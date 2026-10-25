"""Incremental GX2' encoding: every query answer equals the frozen full re-encoding XRegion (dev, synthetic evidence)."""
import random, unittest
from brute.xcheck_sat import XRegion
from brute.xcheck_sat_incremental import IncSolver


def _world(rng):
    n=rng.choice([2,3,4]);k=rng.choice([2,3]);s=rng.choice([1,2]);m=2**s
    tr=[[rng.randrange(n) for _ in range(k)] for _ in range(n)];em=[rng.randrange(m) for _ in range(n)]
    return n,k,m,tr,em


def _mask(rng,m,c):
    mm=1<<c
    for cc in range(m):
        if rng.random()<0.4:mm|=1<<cc
    return mm


def _all(X,L,k,m,rng,t0s):
    """Every query on one region; X is an XRegion (L None) or an IncSolver (L its layer)."""
    inc=L is not None;out=[]
    f=X.feasible(L) if inc else X.feasible();out.append(('feasible',f))
    out.append(('saturated',X.saturated(L) if inc else X.saturated()))
    for b in range(k):
        out.append(('support',b,X.support(L,b) if inc else X.support(b)))
        for mask in (1,(1<<m)-1,3%(1<<m) or 1):
            out.append(('y1k',b,mask,X.y1k(L,b,mask) if inc else X.y1k(b,mask)))
            for t0 in t0s:out.append(('y1kr',b,mask,t0,X.y1k(L,b,mask,t0) if inc else X.y1k(b,mask,t0)))
    return out


class IncrementalEqualsFull(unittest.TestCase):
    def _walk(self,seed,steps=7,symmetry=False):
        rng=random.Random(seed);n,k,m,tr,em=_world(rng);N=rng.choice([n,n+1]);I=IncSolver(N,k,m,symmetry=symmetry);checks=0
        try:
            q=rng.randrange(n);masks=[_mask(rng,m,em[q])];acts=[]
            for t in range(steps):
                L=I.layer(masks,acts);t0s=sorted({0,len(acts)//2,len(acts)})
                X=XRegion(N,k,m,masks,acts)
                try:self.assertEqual(_all(I,L,k,m,None,t0s),_all(X,None,k,m,None,t0s))
                finally:X.close()
                checks+=1
                # hypothetical one-step extensions (single codes), as in the LU-R score
                for a in range(k):
                    for c in range(m):
                        if rng.random()<0.5:continue
                        Le=I.layer(masks+[1<<c],acts+[a]);Xe=XRegion(N,k,m,masks+[1<<c],acts+[a])
                        try:
                            self.assertEqual(I.feasible(Le),Xe.feasible())
                            if Xe.feasible():
                                self.assertEqual(I.saturated(Le),Xe.saturated())
                                for b in range(k):self.assertEqual(I.support(Le,b),Xe.support(b))
                        finally:Xe.close()
                        checks+=1
                a=rng.randrange(k);q=tr[q][a]
                mk=_mask(rng,m,em[q]) if rng.random()>0.15 else 1<<rng.randrange(m)  # sometimes contradicting
                masks.append(mk);acts.append(a)
            self.assertEqual(I.witness_failures,0);self.assertEqual(I.unknown,0)
        finally:I.close()
        return checks

    def test_random_walks(self):
        total=sum(self._walk(s) for s in range(25))
        self.assertGreater(total,200)

    def test_random_walks_symmetry(self):
        """With first-visit naming every answer is still equal to the frozen XRegion (no symmetry breaking)."""
        total=sum(self._walk(s,symmetry=True) for s in range(25,50))
        self.assertGreater(total,200)

    def test_divergent_evidence_rebuilds(self):
        """Switching to evidence that is not an extension of the main trajectory (another arm) rebuilds and stays exact."""
        rng=random.Random(5);n,k,m,tr,em=3,2,4,[[1,2],[2,0],[0,1]],[0,1,2]
        for sym in (False,True):self._divergent(sym)

    def _divergent(self,sym):
        I=IncSolver(3,2,4,symmetry=sym)
        try:
            for masks,acts in [([1,2,4],[0,0]),([1,2,4,1],[0,0,0]),([1],[]),([1,4],[1]),([1,4,2,1],[1,0,1])]:
                L=I.layer(masks,acts);X=XRegion(3,2,4,masks,acts)
                try:self.assertEqual(_all(I,L,2,4,None,[0,len(acts)]),_all(X,None,2,4,None,[0,len(acts)]))
                finally:X.close()
            self.assertGreaterEqual(I.rebuilds,2)
        finally:I.close()


if __name__=='__main__':unittest.main()
