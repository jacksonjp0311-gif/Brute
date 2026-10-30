"""v0.29.0: S7 noise-tolerant exact search (brute.scalesearch7). Exact S7 answers equal a brute-force enumeration of every
<= n machine within the flip budget; with budget 0 they equal S5; at eps 0 S7 never contradicts S5; S7 keeps the true
next code when realised flips <= B; the flip budget formula; S7_contra (ScaleRegion5C) reports grammar_contradicted on a
contradicted trace and otherwise equals S5; the hard cap holds; host-agnostic source. New file."""
import itertools,random,unittest,pathlib
from time import perf_counter
from brute import scalesearch7 as S7
from brute import scalesearch5 as S5
from tests.test_scalesearch_0230 import trace,bits


def brute_support(n,k,m,acts,readings,b,bound):
    """Every complete machine on n states from state 0 (covers every <= n machine); codes reachable after b within bound."""
    out=set();Q=range(n)
    for dd in itertools.product(Q,repeat=n*k):
        d=[list(dd[q*k:(q+1)*k]) for q in Q]
        for e in itertools.product(range(m),repeat=n):
            if S7.machine_flips(d,e,acts,readings,2)<=bound:
                q=0
                for a in acts:q=d[q][a]
                out.add(e[d[q][b]])
    return tuple(sorted(out)) if out else None


def noisy(rng,codes,p):return [tuple(x^(rng.random()<p) for x in bits(c)) for c in codes]


class Budget(unittest.TestCase):
    def test_formula(self):
        self.assertEqual([S7.flip_budget(t) for t in (0,1,2,10,100,354)],[0,1,1,2,10,27])
        self.assertEqual(S7.flip_budget(354,0.0),0)

    def test_machine_flips(self):
        d=[[1,0],[0,1]];e=[0,3]
        self.assertEqual(S7.machine_flips(d,e,[0,0],[(0,0),(1,1),(0,1)],2),1)


class EqualsEnumeration(unittest.TestCase):
    def run_case(self,rng,eps_assumed,p,T=9):
        n0=rng.randrange(1,3);acts,codes=trace(rng,n0,2,T);obs=noisy(rng,codes,p)
        A=S7.ScaleRegion7(2,2,eps_assumed=eps_assumed);A.initialize(obs[0]);cmp=0
        try:
            for i in range(T):
                for b in range(2):
                    s,u=A.support(b)
                    if u==0:self.assertEqual(s,brute_support(2,2,4,acts[:i],obs[:i+1],b,A.bound),(i,b,A.bound));cmp+=1
                A.observe(acts[i],obs[i+1])
        finally:A.close()
        return cmp

    def test_random(self):
        rng=random.Random(290);tot=0
        for eps,p in ((0.2,0.15),(0.05,0.05),(0.0,0.0),(0.3,0.3)):
            for _ in range(3):tot+=self.run_case(rng,eps,p)
        self.assertGreater(tot,150)


class VersusS5(unittest.TestCase):
    def test_budget0_equals_s5_and_eps0_contains(self):
        rng=random.Random(291);eq=cont=0
        for _ in range(5):
            n=rng.randrange(1,4);acts,codes=trace(rng,n,3,16);obs=[bits(c) for c in codes]
            A=S7.ScaleRegion7(4,3,eps_assumed=0.0);C=S7.ScaleRegion7(4,3);B=S5.ScaleRegion5(4,3)
            for R in (A,B,C):R.initialize(obs[0])
            try:
                for i,a in enumerate(acts):
                    for b in range(3):
                        sa,ua=A.support(b);sb,ub=B.support(b);sc,uc=C.support(b)
                        if ua==0 and ub==0:self.assertEqual(sa,sb);eq+=1
                        if uc==0 and ub==0 and sb is not None:self.assertTrue(set(sb)<=set(sc));cont+=1
                    for R in (A,B,C):R.observe(a,obs[i+1])
            finally:
                for R in (A,B,C):R.close()
        self.assertGreater(eq,100);self.assertGreater(cont,100)

    def test_truth_kept_within_budget(self):
        rng=random.Random(292);chk=0
        for _ in range(6):
            n=rng.randrange(2,4);k=2
            d=[[rng.randrange(n) for _ in range(k)] for _ in range(n)];e=[rng.randrange(4) for _ in range(n)]
            q=0;acts=[];st=[0]
            for _ in range(20):a=rng.randrange(k);q=d[q][a];acts.append(a);st.append(q)
            obs=noisy(rng,[e[s] for s in st],0.05)
            A=S7.ScaleRegion7(4,k);A.initialize(obs[0])
            try:
                for i in range(20):
                    for b in range(k):
                        s,u=A.support(b)
                        if u==0 and S7.machine_flips(d,e,acts[:i],obs[:i+1],2)<=A.bound:
                            self.assertIsNotNone(s);self.assertIn(e[d[st[i]][b]],s);chk+=1
                    A.observe(acts[i],obs[i+1])
            finally:A.close()
        self.assertGreater(chk,50)


class Contra(unittest.TestCase):
    def test_contradicted(self):
        obs=[(0,0),(1,1),(0,0),(1,1)]
        C=S7.ScaleRegion5C(1,1);C.initialize(obs[0])
        for o in obs[1:]:C.observe(0,o)
        self.assertEqual(C.support(0),(None,0));self.assertEqual(C.status,'grammar_contradicted');C.close()
        A=S7.ScaleRegion7(1,1,eps_assumed=1.0);A.initialize(obs[0])
        for o in obs[1:]:A.observe(0,o)
        s,u=A.support(0);self.assertEqual(u,0);self.assertIsNotNone(s);A.close()

    def test_equals_s5(self):
        rng=random.Random(293);cmp=0
        for _ in range(4):
            acts,codes=trace(rng,3,2,14);obs=[bits(c) for c in codes]
            A=S7.ScaleRegion5C(4,2);B=S5.ScaleRegion5(4,2);A.initialize(obs[0]);B.initialize(obs[0])
            try:
                for i,a in enumerate(acts):
                    for b in range(2):
                        sa,ua=A.support(b);sb,ub=B.support(b)
                        if ua==0 and ub==0:self.assertEqual(sa,sb);cmp+=1
                    A.observe(a,obs[i+1]);B.observe(a,obs[i+1])
            finally:A.close();B.close()
        self.assertGreater(cmp,50)


class HardCap(unittest.TestCase):
    def test_cap(self):
        rng=random.Random(294);acts,codes=trace(rng,12,3,60);obs=noisy(rng,codes,0.05)
        A=S7.ScaleRegion7(16,3,query_s=0.5);A.initialize(obs[0]);worst=0.0
        try:
            for i,a in enumerate(acts):
                for b in range(3):t=perf_counter();A.support(b);worst=max(worst,perf_counter()-t)
                A.observe(a,obs[i+1])
        finally:A.close()
        self.assertLess(worst,1.0)


class HostAgnostic(unittest.TestCase):
    def test_no_io(self):
        src=(pathlib.Path(__file__).resolve().parents[1]/'brute/scalesearch7.py').read_text()
        for bad in ('import os','subprocess','threading','multiprocessing','open(','socket','import signal'):self.assertNotIn(bad,src,bad)


if __name__=='__main__':unittest.main()
