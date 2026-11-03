"""Tests for brute/api/certify20s.py (v0.62.0, BRUTE_PLAN_065). New file. Small random worlds only (fast); 20-state behaviour is the
study's job. certify/20s must: compute the plan's threshold (smallest m with read_bits r^m/(1+r^m) <= delta 6/(pi^2 t^2)); settle each
bit at the first |lead| >= m; accept only exact stopping sequences; equal certify/20p exactly at eps_bar 0 (one reading per
observation) and, whenever every settled reading is correct, on noisy re-reads; stay sound; keep K accounting; stay host-agnostic."""
import ast,json,math,random,unittest
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys;sys.path.insert(0,str(ROOT))
from brute.api import certify20p as P
from brute.api import certify20s as S
from scripts.api_checks_059 import _small,_bits
from scripts.api_checks_063 import _sound
from brute.evaluation import no_time
from scripts.api_checks_063 import _rm_walls
from experiments.brute_common import dumps
KW=dict(K=60,conflict_cap=5000,budget_conflicts=200000)
DROP=('api','soundness','inner_api','eps_bar','delta','observations','reads_total','reads_max','reads_per_obs','thresholds','settle_at')


def run(make,T,em,seed,sb,feed):
    """make(first) -> certifier; feed(c, clean) -> what observe() gets."""
    r=random.Random(seed+1);acts=[r.randrange(3) for _ in range(40)];q=0;words=[]
    c=make(_bits(em[q],sb))
    try:
        for a in acts:q=T[q][a];c.observe(a,feed(c,_bits(em[q],sb)))
        while True:
            x=c.propose()
            if x is None:break
            words.append(list(x))
            for a in x:q=T[q][a];c.observe(a,feed(c,_bits(em[q],sb)))
        R=dict(c.record());res=dict(c.result())
    finally:c.close()
    for d in (R,res):
        for f in DROP:d.pop(f,None)
    return no_time(_rm_walls({'res':res,'rec':R})),words,q,R


class Noisy:
    def __init__(self,seed,eps):self.rng=random.Random(seed);self.eps=eps;self.n=0;self.err=0
    def first(self,clean,eb,sb,delta=0.001):
        m=S.threshold(1,eb,delta,sb);rs=[]
        while True:
            rs.append(self.one(clean))
            if S.settle(rs,m,sb)[0] is not None:return rs
    def one(self,clean):self.n+=1;return tuple(b^1 if self.rng.random()<self.eps else b for b in clean)
    def feed(self,c,clean):
        rs=[]
        while True:
            rs.append(self.one(clean))
            if not c.more(rs):return rs


class T20S(unittest.TestCase):
    def test_threshold_exact(self):
        for eb in (0.05,0.15,0.25,0.35,0.45):
            r=Fraction(eb).limit_denominator(10**6);r=r/(1-r)
            for t in (1,2,3,10,100,500,5000):
                m=S.threshold(t,eb,0.001,2);x=0.001*6/(math.pi**2*t*t)
                self.assertLessEqual(2*float(r**m/(1+r**m)),x*(1+1e-12),(eb,t))
                if m>1:self.assertGreater(2*float(r**(m-1)/(1+r**(m-1))),x*(1-1e-12),(eb,t))
        self.assertEqual(S.threshold(7,0,0.001,2),1)
        self.assertEqual([S.threshold(1,e,0.001,2) for e in (0.15,0.25,0.35)],[5,8,14])
        self.assertLessEqual(S.threshold(2,0.25,0.001,2),S.threshold(3,0.25,0.001,2))
        for bad in (0,-1,1.5,True):
            with self.assertRaises((ValueError,TypeError)):S.threshold(bad,0.2,0.001,2)

    def test_settle(self):
        v,at,lead=S.settle([(1,0),(1,0),(0,0)],2,2);self.assertEqual(v,(1,0));self.assertEqual(at,[2,2])
        v,at,lead=S.settle([(1,0),(0,0)],2,2);self.assertIsNone(v);self.assertEqual(at,[None,2])
        v,at,_=S.settle([(1,1),(0,1),(1,1),(1,0),(1,0)],2,2);self.assertEqual(v,(1,1));self.assertEqual(at,[4,2])
        for bad in ([(1,)],[(1,2)],[(True,0)],[[0,0,0]]):
            with self.assertRaises(ValueError):S.settle(bad,2,2)

    def test_exact_stopping_sequence(self):
        c=S.Certifier20S([(0,1)]*5,3,10,read_bits=2,eps_bar=0.15,**KW)
        try:
            m=c.threshold_next();self.assertEqual(m,S.threshold(2,0.15,0.001,2))
            self.assertTrue(c.more([(1,1)]*(m-1)));self.assertFalse(c.more([(1,1)]*m))
            with self.assertRaises(ValueError):c.observe(0,[(1,1)]*(m-1))   # not settled
            with self.assertRaises(ValueError):c.observe(0,[(1,1)]*(m+1))   # over-read
            with self.assertRaises(ValueError):c.observe(0,[])
            with self.assertRaises(ValueError):c.observe(5,[(1,1)]*m)
            c.observe(0,[(1,1)]*m);self.assertEqual(list(c.ks),[5,m]);self.assertEqual(list(c.ms),[5,m]);self.assertEqual(c.t,2)
        finally:c.close()
        with self.assertRaises(ValueError):S.Certifier20S([(0,1)]*4,3,10,read_bits=2,eps_bar=0.15,**KW)
        for kw in (dict(eps_bar=0.5),dict(eps_bar=-0.1),dict(delta=0),dict(delta=1),dict(read_bits=1)):
            with self.assertRaises(ValueError,msg=str(kw)):S.Certifier20S([(0,1)]*30,3,10,**{**dict(read_bits=2,eps_bar=0.15),**kw},**KW)

    def test_read_cap(self):
        c=S.Certifier20S([(0,1)]*5,3,10,read_bits=2,eps_bar=0.15,**KW)
        try:
            with self.assertRaises(ValueError):c.more([(0,1),(1,0)]*(S.READ_CAP//2+1))
        finally:c.close()

    def test_equals_20p_at_eps_bar_zero(self):
        for sb in (2,4):
            for s in range(4):
                sd=6510+10*sb+s;n=3+s%4;T,em=_small(sd,n,sb)
                a=run(lambda i:P.Certifier20P(i,3,n+1,'a16d',read_bits=sb,**KW),T,em,sd,sb,lambda c,x:x)
                b=run(lambda i:S.Certifier20S([i],3,n+1,read_bits=sb,eps_bar=0,**KW),T,em,sd,sb,lambda c,x:[x])
                self.assertEqual(dumps(a[0]),dumps(b[0]),(sb,s));self.assertEqual(a[1],b[1])

    def test_noisy_equals_clean_and_sound(self):
        dec=0;reads=0;fixed=0
        from brute.api.certify20n import reads_for
        for eps,eb in ((0.10,0.15),(0.30,0.35)):
            for s in range(4):
                sd=6550+s;n=3+s%3;T,em=_small(sd,n,2);nz=Noisy(sd*7+int(eps*100),eps)
                a=run(lambda i:P.Certifier20P(i,3,n+1,'a16d',read_bits=2,**KW),T,em,sd,2,lambda c,x:x)
                b=run(lambda i:S.Certifier20S(nz.first(i,eb,2),3,n+1,read_bits=2,eps_bar=eb,**KW),T,em,sd,2,nz.feed)
                self.assertEqual(dumps(a[0]),dumps(b[0]),(eps,s));self.assertEqual(a[1],b[1])
                self.assertTrue(_sound(b[3]['stop'],b[3]['final'],T,em,b[2]));dec+=b[3]['stop'] in ('ID','IDF')
                self.assertLessEqual(b[3]['used'],60)
                reads+=nz.n;fixed+=sum(reads_for(t,eb,0.001,2) for t in range(1,len(b[3]['acts'])+2))
        self.assertGreater(dec,0);self.assertLess(reads,0.5*fixed)

    def test_result_fields(self):
        sd=6590;n=4;T,em=_small(sd,n,2);nz=Noisy(sd,0.2);box={}
        def mk(i):box['c']=S.Certifier20S(nz.first(i,0.25,2),3,n+1,read_bits=2,eps_bar=0.25,**KW);return box['c']
        r=random.Random(sd+1);acts=[r.randrange(3) for _ in range(30)];q=0;c=mk(_bits(em[0],2))
        try:
            for a in acts:q=T[q][a];c.observe(a,nz.feed(c,_bits(em[q],2)))
            while (x:=c.propose()) is not None:
                for a in x:q=T[q][a];c.observe(a,nz.feed(c,_bits(em[q],2)))
            r=c.result();R=c.record()
        finally:c.close()
        self.assertEqual((r['api'],r['inner_api'],r['eps_bar'],r['delta'],r['read_bits']),(S.API,P.API,0.25,0.001,2))
        self.assertEqual(r['reads_total'],nz.n);self.assertEqual(r['observations'],len(R['reads_per_obs']));self.assertEqual(r['reads_max'],max(R['reads_per_obs']))
        self.assertEqual(R['thresholds'],[S.threshold(t,0.25,0.001,2) for t in range(1,len(R['thresholds'])+1)])
        self.assertTrue(all(k>=m for k,m in zip(R['reads_per_obs'],R['thresholds'])));self.assertIn('noise',json.dumps(r['soundness']))

    def test_host_agnostic(self):
        tree=ast.parse((ROOT/'brute/api/certify20s.py').read_text());bad={'os','io','threading','subprocess','socket','multiprocessing','sys','time','pathlib','random'}
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):self.assertFalse({a.name.split('.')[0] for a in n.names}&bad)
            if isinstance(n,ast.ImportFrom):self.assertNotIn((n.module or '').split('.')[0],bad)
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):self.assertNotIn(n.func.id,('open','exec','eval','__import__'))


if __name__=='__main__':unittest.main()
