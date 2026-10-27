import unittest
import numpy as np
from experiments import v0160_reference as R
from experiments.brute_common import load


def naive_support(init,acts,obss,m,b,T):
    """Explicit (table, emission) enumeration over 4-state machines on the first T steps (vectorised over emissions)."""
    D=R.tables();E=np.array([[(e>>(2*q))&3 for q in range(4)] for e in range(256)]);mm=[R.mism(init)]+[R.mism(o) for o in obss[:T]]
    out=set();feas=False
    for lo in range(0,len(D),8192):
        Dc=D[lo:lo+8192];ar=np.arange(len(Dc));st=np.zeros(len(Dc),dtype=np.int64);cost=np.zeros((len(Dc),256),dtype=np.int64)
        for t in range(T+1):
            cost+=mm[t][E[:,st].T]
            if t<T:st=Dc[ar,st,acts[t]]
        nx=Dc[ar,st,b];ok=cost<=m;feas|=bool(ok.any())
        codes=E[:,nx].T
        for c in range(4):
            if (ok&(codes==c)).any():out.add(c)
    return sorted(out) if feas else None


class Reference0160(unittest.TestCase):
    def test_m_table(self):
        for B,m in {20:2,40:3,58:4,60:4,70:5,80:5,90:5}.items():self.assertEqual(R.ref_m(B),m,B)
        self.assertEqual({k:v for k,v in load(R.PLAN)['tolerant_region']['m_table_examples_Exact'].items()},
                         {str(B):R.ref_m(B) for B in (20,40,58,60,70,80,90)})
        self.assertEqual(R.ref_m(0),0)

    def test_flip_array(self):
        F=R.flip_array(8490001,0.02);self.assertEqual(F.shape,(45,2));self.assertFalse(R.flip_array(8490001,0.0).any())
        self.assertTrue((F==R.flip_array(8490001,0.02)).all())

    def test_costs_against_naive(self):
        rng=np.random.default_rng(5)
        for trial in range(3):
            T=5;acts=[int(x) for x in rng.integers(0,2,T)]
            obs=[tuple(None if rng.random()<0.3 else int(rng.integers(0,2)) for _ in range(2)) for _ in range(T+1)]
            init,obss=obs[0],obs[1:];costs=R.ref_costs(init,acts+[0],obss+[(None,None)])
            for m in (0,1,2):
                for b in (0,1):self.assertEqual(R.support_at(costs,T,b,m),naive_support(init,acts,obss,m,b,T),(trial,m,b))

    def test_rgn_rule(self):
        S=[{'t':t,'a':0,'cert':[None,None],'supp':[None,None],'obs':(0,0),'act':[1,2]} for t in (8,9,10)]
        sup=[[[1],[2]],[[1],[0,2]],[[3],None]];e=R.ref_rgn(S,sup,2,8)
        self.assertEqual([r['certificate'] for r in e['trace']],[[None,None],[1,None],[3,None]])
        self.assertEqual(e['false_certificates'],1);self.assertEqual(e['first_cert_step'],9);self.assertEqual(e['certificates'],2)

    def test_kinds(self):self.assertEqual(len(R.KINDS),20)





class NoBruteImport0160(unittest.TestCase):
    def test_no_brute_import(self):
        import ast
        for f in ('experiments/v0160_reference.py',):
            tree=ast.parse(open(f).read())
            for n in ast.walk(tree):
                mods=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or ''] if isinstance(n,ast.ImportFrom) else []
                for m in mods:self.assertFalse(m=='brute' or m.startswith('brute.'),m)


if __name__=='__main__':unittest.main()
