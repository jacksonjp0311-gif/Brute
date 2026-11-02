"""Tests for brute/api/certify32b.py (v0.57.0, BRUTE_PLAN_060). New file. Small random worlds only (fast); 24- and 32-state behaviour
is the study's job. At family_bound <= 20 certify/32b must equal certify/20b (rounds without wall fields, masks, result without
api/soundness); bounds 21..32 are accepted and applied as the declared N; bad bounds are refused; small worlds declared at N > 20
must decide soundly; certify16d's own bound is not patched; host-agnostic (AST)."""
import ast,random,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys;sys.path.insert(0,str(ROOT))
from brute.api import certify32b as X
from brute.api import certify20b as B
from brute.api import certify16d as D16
from experiments.brute_common import dumps
WALL=('query_walls','chunk_walls');KW=dict(K=60,conflict_cap=5000,budget_conflicts=200000)


def world(seed,n,sb):
    r=random.Random(seed);return [[r.randrange(n) for _ in range(3)] for _ in range(n)],[r.randrange(1<<sb) for _ in range(n)]


def drive(make,T,em,seed,sb):
    r=random.Random(seed+1);acts=[r.randrange(3) for _ in range(40)];q=0;c=make(B.reading_of(em[q],sb))
    try:
        for a in acts:q=T[q][a];c.observe(a,B.reading_of(em[q],sb))
        while True:
            x=c.propose()
            if x is None:break
            for a in x:q=T[q][a];c.observe(a,B.reading_of(em[q],sb))
        R=c.record();res=dict(c.result())
    finally:c.close()
    return R,res,q


def beq(d1,e1,s1,d2,e2,s2):
    seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return False
        for a in range(3):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return True


strip=lambda R:[{k:v for k,v in x.items() if k not in WALL} for x in R['rounds']]
core=lambda r:{k:v for k,v in r.items() if k not in ('api','soundness')}


class TestCertify32B(unittest.TestCase):
    def test_equals_20b_at_small_bounds(self):
        for sb in (2,4):
            for s in range(3):
                n=3+s;sd=9700+10*sb+s;T,em=world(sd,n,sb)
                R1,r1,_=drive(lambda i:B.Certifier20B(i,3,n+1,'a16d',read_bits=sb,**KW),T,em,sd,sb)
                R2,r2,_=drive(lambda i:X.Certifier32B(i,3,n+1,'a16d',read_bits=sb,**KW),T,em,sd,sb)
                self.assertEqual(dumps(core(r1)),dumps(core(r2)));self.assertEqual(R1['masks'],R2['masks']);self.assertEqual(dumps(strip(R1)),dumps(strip(R2)))
                self.assertEqual(r2['api'],'brute.certify/32b')

    def test_large_bound_applied_and_sound(self):
        for s in range(2):
            n=3+s;sd=9800+s;T,em=world(sd,n,4)
            for fb in (21,24):
                R,r,q=drive(lambda i:X.Certifier32B(i,3,fb,'a16d',read_bits=4,**KW),T,em,sd,4)
                self.assertEqual(r['family_bound'],fb);f=R['final']
                if R['stop']=='ID':self.assertTrue(beq(f['model'][0],f['model'][1],0,T,em,0))
                if R['stop']=='IDF':self.assertTrue(beq(f['model'][0],f['model'][1],f['s1'],T,em,q))

    def test_bounds(self):
        for fb in range(21,33):
            c=X.Certifier32B((0,1,0,1),3,fb,read_bits=4,conflict_cap=10,budget_conflicts=10)
            try:self.assertEqual(c.current()['family_bound'],fb)
            finally:c.close()
        for fb in (0,33,-1,True,24.0,'24'):
            with self.assertRaises((ValueError,TypeError),msg=repr(fb)):X.Certifier32B((0,1,0,1),3,fb,read_bits=4,conflict_cap=10,budget_conflicts=10)
        for rb in (5,True):
            with self.assertRaises((ValueError,TypeError),msg=repr(rb)):X.Certifier32B((0,1,0,1),3,24,read_bits=rb,conflict_cap=10,budget_conflicts=10)
        self.assertEqual(D16.A16D_MAX_BOUND,20)
        with self.assertRaises(ValueError):B.Certifier20B((0,1,0,1),3,21,read_bits=4,conflict_cap=10,budget_conflicts=10)

    def test_one_shot(self):
        T,em=world(9900,3,4);r=random.Random(9901);acts=[r.randrange(3) for _ in range(30)];q=0;obs=[]
        for a in acts:q=T[q][a];obs.append(B.reading_of(em[q],4))
        a=X.certify32b(B.reading_of(em[0],4),acts,obs,3,4,read_bits=4,conflict_cap=5000,budget_conflicts=200000)
        b=B.certify20b(B.reading_of(em[0],4),acts,obs,3,4,read_bits=4,conflict_cap=5000,budget_conflicts=200000)
        self.assertEqual(dumps(core(a)),dumps(core(b)));self.assertEqual(a['api'],'brute.certify/32b')
        self.assertIn('family_bound',a['soundness'])

    def test_host_agnostic(self):
        tree=ast.parse((ROOT/'brute/api/certify32b.py').read_text());bad={'os','io','threading','subprocess','socket','multiprocessing','sys','pathlib'}
        for nd in ast.walk(tree):
            if isinstance(nd,ast.Import):self.assertFalse({a.name.split('.')[0] for a in nd.names}&bad)
            if isinstance(nd,ast.ImportFrom):self.assertNotIn((nd.module or '').split('.')[0],bad)
            if isinstance(nd,ast.Call) and isinstance(nd.func,ast.Name):self.assertNotIn(nd.func.id,('open','exec','eval','__import__'))


if __name__=='__main__':unittest.main()
