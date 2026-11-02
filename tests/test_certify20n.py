"""Tests for brute/api/certify20n.py (v0.56.0, BRUTE_PLAN_059). New file. Small random worlds only (fast); 20-state behaviour is the
study's job. reads=1 on noise-free readings must equal certify/20b; read_bits 2 must equal certify/16n on the same noisy reads; the
k rule and majority are checked; noisy small worlds must decide soundly; malformed input is refused; host-agnostic (AST)."""
import ast,math,random,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys;sys.path.insert(0,str(ROOT))
from brute.api import certify20n as N
from brute.api import certify20b as B
from brute.api import certify16n as N16
from experiments.brute_common import dumps
from experiments.worlds_059 import Noise
WALL=('query_walls','chunk_walls');KW=dict(K=60,conflict_cap=5000,budget_conflicts=200000)
ONLY=('api','inner_api','soundness','read_bits','eps_bar','delta','reads','observations','reads_total','reads_max')


def world(seed,n,sb):
    r=random.Random(seed);return [[r.randrange(n) for _ in range(3)] for _ in range(n)],[r.randrange(1<<sb) for _ in range(n)]


def drive(make,feed,T,em,seed,sb):
    r=random.Random(seed+1);acts=[r.randrange(3) for _ in range(40)];q=0;c=make(B.reading_of(em[q],sb))
    try:
        for a in acts:q=T[q][a];c.observe(a,feed(c,B.reading_of(em[q],sb)))
        while True:
            x=c.propose()
            if x is None:break
            for a in x:q=T[q][a];c.observe(a,feed(c,B.reading_of(em[q],sb)))
        R=c.record();res=dict(c.result())
    finally:c.close()
    for k in ONLY:res.pop(k,None)
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


class TestCertify20N(unittest.TestCase):
    def test_reads1_equals_20b(self):
        for sb in (3,4):
            for s in range(2):
                n=3+s;sd=9400+10*sb+s;T,em=world(sd,n,sb)
                R1,r1,_=drive(lambda i:B.Certifier20B(i,3,n+1,'a16d',read_bits=sb,**KW),lambda c,x:x,T,em,sd,sb)
                R2,r2,_=drive(lambda i:N.Certifier20N([i],3,n+1,read_bits=sb,reads=1,**KW),lambda c,x:[x],T,em,sd,sb)
                self.assertEqual(dumps(r1),dumps(r2));self.assertEqual(R1['masks'],R2['masks']);self.assertEqual(dumps(strip(R1)),dumps(strip(R2)))

    def test_bits2_equals_16n(self):
        for s in range(2):
            n=3+s;sd=9500+s;T,em=world(sd,n,2);out=[]
            for mk in ('16n','20n'):
                nz=Noise(sd,0.05);feed=lambda c,x,nz=nz:nz.reads(x,c.reads_needed())
                if mk=='16n':m=lambda i,nz=nz:N16.Certifier16N(nz.reads(i,N16.reads_for(1,0.10,0.001)),3,n+1,eps_bar=0.10,delta=0.001,**KW)
                else:m=lambda i,nz=nz:N.Certifier20N(nz.reads(i,N.reads_for(1,0.10,0.001,2)),3,n+1,read_bits=2,eps_bar=0.10,delta=0.001,**KW)
                out.append(drive(m,feed,T,em,sd,2))
            (R1,r1,_),(R2,r2,_)=out
            self.assertEqual(dumps(r1),dumps(r2));self.assertEqual(R1['masks'],R2['masks']);self.assertEqual(R1['reads_per_obs'],R2['reads_per_obs'])
            self.assertEqual(dumps(strip(R1)),dumps(strip(R2)))

    def test_k_rule(self):
        for t in (1,7,300):
            for eb,sb in ((0.10,4),(0.15,4),(0.15,3)):
                k=N.reads_for(t,eb,0.001,sb);self.assertEqual(k%2,1)
                self.assertLessEqual(sb*math.exp(-2*k*(0.5-eb)**2),0.001*6/(math.pi**2*t*t)*(1+1e-9))
                if k>2:self.assertGreater(sb*math.exp(-2*(k-2)*(0.5-eb)**2),0.001*6/(math.pi**2*t*t))
        self.assertGreaterEqual(N.reads_for(5,0.15,0.001,4),N.reads_for(5,0.15,0.001,2))

    def test_majority(self):
        self.assertEqual(N.majority([(0,1,1,0),(1,1,0,0),(0,1,1,1)],4),((0,1,1,0),[1,3,2,1]))
        with self.assertRaises(ValueError):N.majority([(0,1,1,0)]*2,4)
        with self.assertRaises(ValueError):N.majority([(0,1,1)],4)

    def test_noisy_sound(self):
        for s in range(3):
            n=3+s;sd=9600+s;T,em=world(sd,n,4);nz=Noise(sd,0.10)
            R,r,q=drive(lambda i:N.Certifier20N(nz.reads(i,N.reads_for(1,0.15,0.001,4)),3,n+1,read_bits=4,eps_bar=0.15,delta=0.001,**KW),
                        lambda c,x:nz.reads(x,c.reads_needed()),T,em,sd,4)
            f=R['final']
            if R['stop']=='ID':self.assertTrue(beq(f['model'][0],f['model'][1],0,T,em,0))
            if R['stop']=='IDF':self.assertTrue(beq(f['model'][0],f['model'][1],f['s1'],T,em,q))

    def test_result_fields(self):
        c=N.Certifier20N([(0,1,0,1)],3,4,read_bits=4,eps_bar=0.15,reads=1,conflict_cap=10,budget_conflicts=10)
        try:
            r=c.current();self.assertEqual((r['api'],r['inner_api'],r['read_bits'],r['eps_bar'],r['delta'],r['reads']),('brute.certify/20n','brute.certify/20b',4,0.15,0.001,1))
        finally:c.close()

    def test_refusals(self):
        for ini,kw in (([(0,0,0,0)]*2,{}),([(0,0,0)]*37,{}),([(0,2,0,0)]*37,{}),([(True,0,0,0)]*37,{}),
                       ([(0,0,0,0)],{'read_bits':5,'reads':1}),([(0,0,0,0)],{'eps_bar':0.0,'reads':1}),([(0,0,0,0)],{'eps_bar':0.5,'reads':1}),
                       ([(0,0,0,0)],{'eps_bar':True,'reads':1}),([(0,0,0,0)]*2,{'reads':2}),([(0,0,0,0)],{'delta':0,'reads':1})):
            k={'read_bits':4,'eps_bar':0.15,**kw}
            with self.assertRaises(ValueError,msg=str(kw)):N.Certifier20N(ini,3,4,conflict_cap=10,budget_conflicts=10,**k)
        c=N.Certifier20N([(0,1,0,1)],3,4,read_bits=4,eps_bar=0.15,reads=1,conflict_cap=10,budget_conflicts=10)
        try:
            for o in ([(0,1)],[(0,1,0,2)],[(0,1,0,1)]*3,(0,1,0,1)):
                with self.assertRaises(ValueError,msg=str(o)):c.observe(0,o)
            with self.assertRaises(ValueError):c.observe(3,[(0,0,0,0)])
        finally:c.close()

    def test_host_agnostic(self):
        tree=ast.parse((ROOT/'brute/api/certify20n.py').read_text());bad={'os','io','threading','subprocess','socket','multiprocessing','sys','pathlib'}
        for nd in ast.walk(tree):
            if isinstance(nd,ast.Import):self.assertFalse({a.name.split('.')[0] for a in nd.names}&bad)
            if isinstance(nd,ast.ImportFrom):self.assertNotIn((nd.module or '').split('.')[0],bad)
            if isinstance(nd,ast.Call) and isinstance(nd.func,ast.Name):self.assertNotIn(nd.func.id,('open','exec','eval','__import__'))


if __name__=='__main__':unittest.main()
