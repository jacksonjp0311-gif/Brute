"""Tests for brute/api/certify32s.py (v0.63.0, BRUTE_PLAN_066). New file. Small random worlds only (fast); 24-state behaviour is the
study's job. certify/32s must: reuse the certify/20s threshold and settle unchanged; equal certify/32p exactly at eps_bar 0 (one
reading per observation); equal certify/20s exactly (record and result minus api names) at the same bound on the same noisy reads;
accept a bound above 20 (certify/20s refuses it); stay sound; keep K accounting; stay host-agnostic."""
import ast,random,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
import sys;sys.path.insert(0,str(ROOT))
from brute.api import certify32p as Q
from brute.api import certify20s as S
from brute.api import certify32s as X
from scripts.api_checks_059 import _small,_bits
from scripts.api_checks_063 import _sound
from experiments.brute_common import dumps
from tests.test_certify20s import run,Noisy,KW


class T32S(unittest.TestCase):
    def test_reuses_20s_rules(self):
        self.assertIs(X.threshold,S.threshold);self.assertIs(X.settle,S.settle);self.assertEqual(X.READ_CAP,S.READ_CAP)
        self.assertTrue(issubclass(X.Certifier32S,S.Certifier20S));self.assertEqual(X.API,'brute.certify/32s')
        s=X.soundness(0.35,0.001,2);self.assertEqual(s['family_bound'],Q.soundness()['family_bound'])

    def test_equals_32p_at_eps_bar_zero(self):
        for sb in (2,4):
            for s in range(3):
                sd=6610+10*sb+s;n=3+s%4;T,em=_small(sd,n,sb)
                for N in (n+1,n+5):
                    a=run(lambda i:Q.Certifier32P(i,3,N,'a16d',read_bits=sb,**KW),T,em,sd,sb,lambda c,x:x)
                    b=run(lambda i:X.Certifier32S([i],3,N,read_bits=sb,eps_bar=0,**KW),T,em,sd,sb,lambda c,x:[x])
                    self.assertEqual(dumps(a[0]),dumps(b[0]),(sb,s,N));self.assertEqual(a[1],b[1])

    def test_equals_20s_on_noisy_reads_and_sound(self):
        dec=0
        for eps,eb in ((0.10,0.15),(0.30,0.35)):
            for s in range(4):
                sd=6550+s;n=3+s%3;T,em=_small(sd,n,2)
                n1=Noisy(sd*7+int(eps*100),eps);n2=Noisy(sd*7+int(eps*100),eps)
                a=run(lambda i:S.Certifier20S(n1.first(i,eb,2),3,n+1,read_bits=2,eps_bar=eb,**KW),T,em,sd,2,n1.feed)
                b=run(lambda i:X.Certifier32S(n2.first(i,eb,2),3,n+1,read_bits=2,eps_bar=eb,**KW),T,em,sd,2,n2.feed)
                self.assertEqual(dumps(a[0]),dumps(b[0]),(eps,s));self.assertEqual(a[1],b[1]);self.assertEqual(n1.n,n2.n)
                self.assertTrue(_sound(b[3]['stop'],b[3]['final'],T,em,b[2]));dec+=b[3]['stop'] in ('ID','IDF');self.assertLessEqual(b[3]['used'],60)
        self.assertGreater(dec,0)

    def test_bound_above_20(self):
        with self.assertRaises(ValueError):S.Certifier20S([(0,1)]*5,3,24,read_bits=2,eps_bar=0.15,**KW)
        c=X.Certifier32S([(0,1)]*5,3,24,read_bits=2,eps_bar=0.15,**KW)
        try:
            self.assertEqual(c.inner.N if hasattr(c.inner,'N') else 24,24);d=c._extra({});self.assertEqual((d['api'],d['inner_api'],d['eps_bar']),(X.API,Q.API,0.15))
        finally:c.close()
        for kw in (dict(eps_bar=0.5),dict(delta=0),dict(read_bits=1)):
            with self.assertRaises(ValueError,msg=str(kw)):X.Certifier32S([(0,1)]*30,3,24,**{**dict(read_bits=2,eps_bar=0.15),**kw},**KW)

    def test_host_agnostic(self):
        tree=ast.parse((ROOT/'brute/api/certify32s.py').read_text());bad={'os','io','threading','subprocess','socket','multiprocessing','sys','time','pathlib','random'}
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):self.assertFalse({a.name.split('.')[0] for a in n.names}&bad)
            if isinstance(n,ast.ImportFrom):self.assertNotIn((n.module or '').split('.')[0],bad)
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):self.assertNotIn(n.func.id,('open','exec','eval','__import__'))


if __name__=='__main__':unittest.main()
