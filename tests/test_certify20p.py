"""Tests for brute/api/certify20p.py (v0.60.0, BRUTE_PLAN_063). New file. Small random worlds only (fast); 20-state behaviour is
the study's job. certify/20p must agree with the frozen certify/20b on n_min whenever both decide, never give a wrong ID/IDF on
small worlds (checked against the true machine), pin the exact max clique (brute force on small matrices), keep K accounting,
refuse malformed input and stay host-agnostic (AST)."""
import ast,itertools,random,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys;sys.path.insert(0,str(ROOT))
from brute.api import certify20b as B
from brute.api import certify20p as P
KW=dict(conflict_cap=5000,budget_conflicts=200000)


def world(seed,n,sb):
    r=random.Random(seed);return [[r.randrange(n) for _ in range(3)] for _ in range(n)],[r.randrange(1<<sb) for _ in range(n)]


def drive(make,T,em,seed,sb,K=60):
    r=random.Random(seed+1);acts=[r.randrange(3) for _ in range(40)];q=0;words=[]
    c=make(B.reading_of(em[q],sb),K)
    try:
        for a in acts:q=T[q][a];c.observe(a,B.reading_of(em[q],sb))
        while True:
            x=c.propose()
            if x is None:break
            words.append(list(x))
            for a in x:q=T[q][a];c.observe(a,B.reading_of(em[q],sb))
        R=c.record();res=dict(c.result())
    finally:c.close()
    return R,res,q,words


def beq(d1,e1,s1,d2,e2,s2):
    seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return False
        for a in range(3):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return True


class T20P(unittest.TestCase):
    def test_agrees_with_20b_and_sound(self):
        dec=0
        for sb in (2,4):
            for s in range(6):
                sd=6300+10*sb+s;n=3+s%4;T,em=world(sd,n,sb)
                a=drive(lambda i,K:B.Certifier20B(i,3,n+1,'a16d',read_bits=sb,K=K,**KW),T,em,sd,sb)
                b=drive(lambda i,K:P.Certifier20P(i,3,n+1,'a16d',read_bits=sb,K=K,**KW),T,em,sd,sb)
                R,res,q,words=b;self.assertEqual(res['api'],P.API)
                if a[1]['stop'] in ('ID','IDF') and res['stop'] in ('ID','IDF'):self.assertEqual(a[1]['n_min'],res['n_min'],(sb,s))
                if R['stop']=='ID':self.assertTrue(beq(R['final']['model'][0],R['final']['model'][1],0,T,em,0));dec+=1
                if R['stop']=='IDF':self.assertTrue(beq(R['final']['model'][0],R['final']['model'][1],R['final']['s1'],T,em,q));dec+=1
                self.assertGreaterEqual(len(R['repins']),1);self.assertIsNone(R['repins'][0][1])
                self.assertEqual(R['used'],sum(len(w) for w in words));self.assertLessEqual(R['used'],60)
                fc=R['final_clique'];self.assertEqual(sorted(fc),fc);self.assertEqual(fc[0],0);self.assertEqual(R['clique'],len(fc));self.assertEqual(len(fc),R['repins'][-1][2])
        self.assertGreater(dec,0)

    def test_max_clique_exact(self):
        for s in range(30):
            r=random.Random(9000+s);n=4+s%7;A=[[r.random()<0.5 for _ in range(n)] for _ in range(n)]
            ap=lambda t,u:A[t][u] if t<u else A[u][t]
            best=0
            for k in range(n,0,-1):
                for S in itertools.combinations(range(1,n),k-1):
                    S=(0,)+S
                    if all(ap(x,y) for x,y in itertools.combinations(S,2)):best=k;break
                if best:break
            mc,exact=P.max_clique0(A,[0]);self.assertTrue(exact);self.assertEqual(len(mc),best,s)
            self.assertTrue(all(ap(x,y) for x,y in itertools.combinations(mc,2)));self.assertIn(0,mc)

    def test_node_cap_keeps_floor(self):
        r=random.Random(5);n=12;A=[[r.random()<0.7 for _ in range(n)] for _ in range(n)]
        mc,exact=P.max_clique0(A,[0],cap=1);self.assertFalse(exact);self.assertGreaterEqual(len(mc),1);self.assertIn(0,mc)

    def test_lower_bound_is_clique(self):
        sd=6400;n=5;T,em=world(sd,n,2);R,res,q,words=drive(lambda i,K:P.Certifier20P(i,3,n+1,'a16d',read_bits=2,K=K,**KW),T,em,sd,2)
        for x in R['rounds']:self.assertGreaterEqual(x['n_min'] if x['n_min'] is not None else 99,R['repins'][0][2])

    def test_k_accounting(self):
        for s in range(4):
            sd=6500+s;n=4+s%3;T,em=world(sd,n,2)
            for K in (1,3,5):
                R,res,q,words=drive(lambda i,KK:P.Certifier20P(i,3,n+1,'a16d',read_bits=2,K=KK,**KW),T,em,sd,2,K=K)
                self.assertLessEqual(R['used'],K)

    def test_refusals(self):
        for nc in (0,-1,True,1.5,'3'):
            with self.assertRaises((ValueError,TypeError),msg=repr(nc)):P.Certifier20P((0,1),3,20,read_bits=2,node_cap=nc,**KW)
        with self.assertRaises(ValueError):P.Certifier20P((0,1),3,20,read_bits=5,**KW)
        with self.assertRaises(ValueError):P.Certifier20P((0,1),3,21,read_bits=2,**KW)
        with self.assertRaises(ValueError):P.Pool63(3,4,None,None,[1,2])
        c=P.Certifier20P((0,1),3,20,read_bits=2,**KW);c.close();self.assertEqual(c.node_cap,P.NODE_CAP)

    def test_oneshot(self):
        sd=6600;n=4;T,em=world(sd,n,2);r=random.Random(sd);acts=[r.randrange(3) for _ in range(30)];q=0;obs=[]
        for a in acts:q=T[q][a];obs.append(B.reading_of(em[q],2))
        o1=B.certify20b(B.reading_of(em[0],2),acts,obs,3,n+1,read_bits=2,**KW);o2=P.certify20p(B.reading_of(em[0],2),acts,obs,3,n+1,read_bits=2,**KW)
        self.assertEqual(o2['api'],P.API)
        if o1['stop'] in ('ID','IDF','AMB') and o2['stop'] in ('ID','IDF','AMB'):self.assertEqual(o1['n_min'],o2['n_min'])

    def test_host_agnostic(self):
        tree=ast.parse((ROOT/'brute/api/certify20p.py').read_text());bad={'os','io','threading','subprocess','socket','multiprocessing','sys','time','pathlib'}
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):self.assertFalse({a.name.split('.')[0] for a in n.names}&bad)
            if isinstance(n,ast.ImportFrom):self.assertNotIn((n.module or '').split('.')[0],bad)
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):self.assertNotIn(n.func.id,('open','exec','eval','__import__'))


if __name__=='__main__':unittest.main()
