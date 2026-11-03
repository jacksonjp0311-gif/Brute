"""Tests for brute/api/certify32p.py (v0.61.0, BRUTE_PLAN_064). New file. Small random worlds only (fast); 24-state behaviour is
the study's job. certify/32p must be certify/20p exactly at bound <= 20 (identical records), stay sound against the true machine
at a loose bound (n+5), own its bound (0 and 33 refused, 21..32 accepted, self.N set), keep K accounting and
stay host-agnostic (AST)."""
import ast,json,random,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys;sys.path.insert(0,str(ROOT))
from brute.api import certify20b as B
from brute.api import certify20p as P
from brute.api import certify32p as Q
from tests.test_certify20p import world,drive,beq,KW
from scripts.api_checks_059 import _small
from scripts.api_checks_063 import _run_small,_sound
from experiments.brute_common import dumps
KW60=dict(K=60,**KW)


def strip(d):return json.dumps({k:v for k,v in d.items() if k not in ('api','soundness')},sort_keys=True,default=str)


class T32P(unittest.TestCase):
    def test_equals_20p_at_small_bound(self):
        for sb in (2,4):
            for s in range(5):
                sd=6410+10*sb+s;n=3+s%4;T,em=_small(sd,n,sb)
                a=_run_small(lambda i:P.Certifier20P(i,3,n+1,'a16d',read_bits=sb,**KW60),T,em,sd,sb)
                b=_run_small(lambda i:Q.Certifier32P(i,3,n+1,'a16d',read_bits=sb,**KW60),T,em,sd,sb)
                self.assertEqual(a[1:],b[1:]);self.assertEqual(dumps(a[0]),dumps(b[0]),(sb,s))

    def test_sound_at_loose_bound(self):
        dec=0
        for sb in (3,4):
            for s in range(6):
                sd=6430+10*sb+s;n=3+s%3;T,em=_small(sd,n,sb)
                e,we,qe=_run_small(lambda i:Q.Certifier32P(i,3,n+5,'a16d',read_bits=sb,**KW60),T,em,sd,sb)
                self.assertTrue(_sound(e['stop'],e['final'],T,em,qe),(sb,s));dec+=e['stop'] in ('ID','IDF')
                self.assertEqual(e['used'],sum(len(w) for w in we));self.assertLessEqual(e['used'],60)
                e,we,qe=_run_small(lambda i:Q.Certifier32P(i,3,n+1,'a16d',read_bits=sb,**KW60),T,em,sd,sb)
                self.assertTrue(_sound(e['stop'],e['final'],T,em,qe),(sb,s,'n+1'));dec+=e['stop'] in ('ID','IDF')
        self.assertGreater(dec,0)  # loose bounds rarely decide on these budgets; the n+1 runs must decide some

    def test_bounds(self):
        for fb in (0,33,-1):
            with self.assertRaises(ValueError,msg=fb):Q.Certifier32P((0,1),3,fb,read_bits=2,**KW)
        for fb in (21,24,32):
            c=Q.Certifier32P((0,1),3,fb,read_bits=2,**KW);self.assertEqual(c.N,fb);c.close()
        with self.assertRaises(ValueError):P.Certifier20P((0,1),3,21,read_bits=2,**KW)

    def test_k_accounting(self):
        for s in range(3):
            sd=6450+s;n=4+s%2;T,em=world(sd,n,2)
            for K in (1,4):
                R,res,q,words=drive(lambda i,KK:Q.Certifier32P(i,3,24,'a16d',read_bits=2,K=KK,**KW),T,em,sd,2,K=K)
                self.assertLessEqual(R['used'],K)

    def test_oneshot(self):
        sd=6460;n=4;T,em=world(sd,n,2);r=random.Random(sd);acts=[r.randrange(3) for _ in range(30)];q=0;obs=[]
        for a in acts:q=T[q][a];obs.append(B.reading_of(em[q],2))
        o1=P.certify20p(B.reading_of(em[0],2),acts,obs,3,n+1,read_bits=2,**KW);o2=Q.certify32p(B.reading_of(em[0],2),acts,obs,3,n+1,read_bits=2,**KW)
        self.assertEqual(o2['api'],Q.API);self.assertEqual(o1['stop'],o2['stop']);self.assertEqual(o1.get('n_min'),o2.get('n_min'))

    def test_host_agnostic(self):
        tree=ast.parse((ROOT/'brute/api/certify32p.py').read_text());bad={'os','io','threading','subprocess','socket','multiprocessing','sys','time','pathlib'}
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):self.assertFalse({a.name.split('.')[0] for a in n.names}&bad)
            if isinstance(n,ast.ImportFrom):self.assertNotIn((n.module or '').split('.')[0],bad)
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):self.assertNotIn(n.func.id,('open','exec','eval','__import__'))


if __name__=='__main__':unittest.main()
