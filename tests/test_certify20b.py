"""Tests for brute/api/certify20b.py (v0.55.0, BRUTE_PLAN_058). New file. Small random worlds only (fast); 20-state behaviour is
the study's job. read_bits 2 must equal certify/16e; wider readings must decide small worlds soundly; malformed input is refused;
the module is host-agnostic (AST: no I/O, threads, subprocess, os or socket)."""
import ast,random,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys;sys.path.insert(0,str(ROOT))
from brute.api import certify20b as B
from brute.api import certify16e as E
from experiments.brute_common import dumps
WALL=('query_walls','chunk_walls')


def world(seed,n,sb):
    r=random.Random(seed);return [[r.randrange(n) for _ in range(3)] for _ in range(n)],[r.randrange(1<<sb) for _ in range(n)]


def drive(cls,T,em,seed,n,sb,**kw):
    r=random.Random(seed+1);acts=[r.randrange(3) for _ in range(40)];q=0;rd=[B.reading_of(em[q],sb)]
    for a in acts:q=T[q][a];rd.append(B.reading_of(em[q],sb))
    c=cls(rd[0],3,n+1,'a16d',K=60,conflict_cap=5000,budget_conflicts=200000,**kw)
    try:
        for a,o in zip(acts,rd[1:]):c.observe(a,o)
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


class TestCertify20B(unittest.TestCase):
    def test_bits2_equals_16e(self):
        for s in range(3):
            n=3+s;T,em=world(9100+s,n,2)
            R1,r1,_=drive(E.Certifier16E,T,em,9100+s,n,2);R2,r2,_=drive(B.Certifier20B,T,em,9100+s,n,2,read_bits=2)
            for r in (r1,r2):
                for k in ('api','soundness','read_bits'):r.pop(k,None)
            self.assertEqual(dumps(r1),dumps(r2));self.assertEqual(R1['masks'],R2['masks']);self.assertEqual(R1['acts'],R2['acts'])
            strip=lambda R:[{k:v for k,v in x.items() if k not in WALL} for x in R['rounds']]
            self.assertEqual(dumps(strip(R1)),dumps(strip(R2)))

    def test_wide_sound(self):
        for sb in (3,4):
            for s in range(3):
                n=3+s;T,em=world(9200+10*sb+s,n,sb);R,r,q=drive(B.Certifier20B,T,em,9200+10*sb+s,n,sb,read_bits=sb)
                self.assertEqual(r['api'],'brute.certify/20b');self.assertEqual(r['read_bits'],sb)
                f=R['final']
                if R['stop']=='ID':self.assertTrue(beq(f['model'][0],f['model'][1],0,T,em,0))
                if R['stop']=='IDF':self.assertTrue(beq(f['model'][0],f['model'][1],f['s1'],T,em,q))

    def test_reading_of(self):
        self.assertEqual(B.reading_of(5,3),(1,0,1));self.assertEqual(B.reading_of(1,4),(0,0,0,1));self.assertEqual(B.reading_of(2,2),(1,0))

    def test_refusals(self):
        for ini,kw in (((0,0,0),{'read_bits':2}),((0,1),{'read_bits':3}),((0,2,0),{'read_bits':3}),((True,0),{'read_bits':2}),
                       ((0,0),{'read_bits':5}),((0,0),{'read_bits':1}),((0,0),{'read_bits':True}),([0,0,0,0,0],{'read_bits':4})):
            with self.assertRaises(ValueError,msg=str((ini,kw))):B.Certifier20B(ini,3,4,'a16d',conflict_cap=10,budget_conflicts=10,**kw)
        c=B.Certifier20B((0,1,0),3,4,'a16d',read_bits=3,conflict_cap=10,budget_conflicts=10)
        try:
            for o in ((0,1),(0,1,2),(0,1,0,1),(0,False,1)):
                with self.assertRaises(ValueError,msg=str(o)):c.observe(0,o)
            with self.assertRaises(ValueError):c.observe(3,(0,0,0))
        finally:c.close()

    def test_one_shot(self):
        T,em=world(9300,3,3);acts=[random.Random(1).randrange(3) for _ in range(30)];q=0;obs=[]
        ini=B.reading_of(em[0],3)
        for a in acts:q=T[q][a];obs.append(B.reading_of(em[q],3))
        r=B.certify20b(ini,acts,obs,num_actions=3,family_bound=4,read_bits=3,conflict_cap=5000,budget_conflicts=100000)
        self.assertEqual(r['api'],'brute.certify/20b');self.assertIn(r['label'],('ID','IDF','AMB','IDU'))
        with self.assertRaises(ValueError):B.certify20b(ini,acts,obs[:-1],num_actions=3,family_bound=4,read_bits=3)

    def test_host_agnostic(self):
        tree=ast.parse((ROOT/'brute/api/certify20b.py').read_text());bad={'os','io','threading','subprocess','socket','multiprocessing','sys','pathlib'}
        for nd in ast.walk(tree):
            if isinstance(nd,ast.Import):self.assertFalse({a.name.split('.')[0] for a in nd.names}&bad)
            if isinstance(nd,ast.ImportFrom):self.assertNotIn((nd.module or '').split('.')[0],bad)
            if isinstance(nd,ast.Call) and isinstance(nd.func,ast.Name):self.assertNotIn(nd.func.id,('open','exec','eval','__import__'))


if __name__=='__main__':unittest.main()
