"""Tests for brute/api/certify20w.py (v0.59.0, BRUTE_PLAN_062). New file. Small random worlds only (fast); 20-state behaviour is
the study's job. probe_word=() must equal certify/20b record-for-record; the default window must append the probe word after every
separating word, count it in K and stay sound on small worlds; malformed input is refused; the module is host-agnostic (AST)."""
import ast,random,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys;sys.path.insert(0,str(ROOT))
from brute.api import certify20b as B
from brute.api import certify20w as W
from experiments.brute_common import dumps
WALL=('query_walls','chunk_walls')


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


DROP=('wall','query_walls','chunk_walls','case_wall','chunk_wall_max')


def strip(R):
    """Drop wall-clock fields at every depth (timing is not part of the canonical record)."""
    if isinstance(R,dict):return {k:strip(v) for k,v in R.items() if k not in DROP}
    if isinstance(R,list):return [strip(v) for v in R]
    return R


def beq(d1,e1,s1,d2,e2,s2):
    seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return False
        for a in range(3):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return True


KW=dict(conflict_cap=5000,budget_conflicts=200000)


class T20W(unittest.TestCase):
    def test_empty_probe_equals_20b(self):
        for sb in (2,4):
            for s in range(4):
                sd=7000+10*sb+s;n=3+s%3;T,em=world(sd,n,sb)
                a=drive(lambda i,K:B.Certifier20B(i,3,n+1,'a16d',read_bits=sb,K=K,**KW),T,em,sd,sb)
                b=drive(lambda i,K:W.Certifier20W(i,3,n+1,'a16d',read_bits=sb,K=K,probe_word=(),**KW),T,em,sd,sb)
                self.assertEqual(dumps(strip(a[0])),dumps(strip(b[0])),(sb,s));self.assertEqual(a[3],b[3])
                ra={k:v for k,v in a[1].items() if k not in ('api','soundness','probe_word','case_wall','chunk_wall_max')}
                rb={k:v for k,v in b[1].items() if k not in ('api','soundness','probe_word','case_wall','chunk_wall_max')}
                self.assertEqual(dumps(strip(ra)),dumps(strip(rb)))

    def test_window_appended_and_sound(self):
        seen=0
        for s in range(6):
            sd=7100+s;n=3+s%4;T,em=world(sd,n,2)
            R,res,q,words=drive(lambda i,K:W.Certifier20W(i,3,n+1,'a16d',read_bits=2,K=K,**KW),T,em,sd,2)
            self.assertEqual(res['api'],W.API);self.assertEqual(res['probe_word'],[0,1])
            ws=[x for x in R['rounds'] if x.get('obs') is not None]
            self.assertEqual(len(ws),len(words))
            for x,wd in zip(ws,words):
                self.assertEqual(wd,list(x['word'])+list(x.get('probe',[])));self.assertEqual(len(x['obs']),len(wd));self.assertEqual(len(x['pred1']),len(x['word']))
                seen+=bool(x.get('probe'))
            self.assertEqual(R['used'],sum(len(w) for w in words));self.assertLessEqual(R['used'],60)
            if R['stop']=='ID':self.assertTrue(beq(R['final']['model'][0],R['final']['model'][1],0,T,em,0))
            if R['stop']=='IDF':self.assertTrue(beq(R['final']['model'][0],R['final']['model'][1],R['final']['s1'],T,em,q))
        self.assertGreater(seen,0)

    def test_k_counts_probe(self):
        for s in range(6):
            sd=7200+s;n=4+s%3;T,em=world(sd,n,2)
            for K in (1,2,3,5):
                R,res,q,words=drive(lambda i,KK:W.Certifier20W(i,3,n+1,'a16d',read_bits=2,K=KK,**KW),T,em,sd,2,K=K)
                self.assertLessEqual(R['used'],K);self.assertLessEqual(sum(len(w) for w in words),K)

    def test_refusals(self):
        for p in ((3,),(0,-1),('0',),(True,),'01',None,0,(0.0,)):
            with self.assertRaises((ValueError,TypeError),msg=repr(p)):W.Certifier20W((0,1),3,20,read_bits=2,probe_word=p,**KW)
        with self.assertRaises(ValueError):W.Certifier20W((0,1),3,20,read_bits=5,**KW)
        with self.assertRaises(ValueError):W.Certifier20W((0,1),3,21,read_bits=2,**KW)
        c=W.Certifier20W((0,1),3,20,read_bits=2,**KW);c.close()
        self.assertEqual(c.probe_word,(0,1));self.assertEqual(W.PROBE_WORD,(0,1))

    def test_oneshot(self):
        sd=7300;n=4;T,em=world(sd,n,2);r=random.Random(sd);acts=[r.randrange(3) for _ in range(30)];q=0;obs=[]
        for a in acts:q=T[q][a];obs.append(B.reading_of(em[q],2))
        o1=B.certify20b(B.reading_of(em[0],2),acts,obs,3,n+1,read_bits=2,**KW);o2=W.certify20w(B.reading_of(em[0],2),acts,obs,3,n+1,read_bits=2,**KW)
        self.assertEqual(o2['api'],W.API);self.assertEqual(o1['label'],o2['label']);self.assertEqual(o1['n_min'],o2['n_min'])

    def test_host_agnostic(self):
        tree=ast.parse((ROOT/'brute/api/certify20w.py').read_text());bad={'os','io','threading','subprocess','socket','multiprocessing','sys','time','pathlib'}
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):self.assertFalse({a.name.split('.')[0] for a in n.names}&bad)
            if isinstance(n,ast.ImportFrom):self.assertNotIn((n.module or '').split('.')[0],bad)
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):self.assertNotIn(n.func.id,('open','exec','eval','__import__'))


if __name__=='__main__':unittest.main()
