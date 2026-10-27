"""brute.certify/6 tests (plan 018 GAPI6): stateless answers equal the study runner's RGN4 supports / certificates and m;
host-agnostic import check; ValueError on bad input (incl. eps_bar outside [0, 0.5), delta outside (0, 1)); soundness dict."""
import ast,unittest
from pathlib import Path
from brute.api.certify6 import certify6,API
from experiments.brute_study_018 import run_job,load,PLAN

ROOT=Path(__file__).resolve().parents[1]


class Certify6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        plan=load(PLAN);cls.cases=[run_job(('smoke-api',f,s,0.02),plan)[1] for f,s in (('cycle3',8490009),('ood4',8490012))]

    def test_matches_runner(self):
        for c in self.cases:
            tr=c['arms']['SP8']['trace'];acts=[r['action'] for r in tr];obs=[tuple(r['observed']) for r in tr]
            r=certify6(tuple(c['initial_visible']),acts,obs,c['B'])
            self.assertEqual((r['api'],r['m'],r['observed_bits'],r['steps']),(API,c['m'],c['B'],len(acts)))
            self.assertEqual(r['supports'][:-1],c['noisy']['RGN4']['support'])
            self.assertEqual(r['certificates'][:-1],[x['certificate'] for x in c['certifiers']['RGN4']['trace']])
            k=20;p=certify6(tuple(c['initial_visible']),acts[:k],obs[:k],c['B'])
            self.assertEqual(p['supports'],c['noisy']['RGN4']['support'][:k+1])

    def test_soundness(self):
        r=certify6((0,1),[],[],10,delta=0.05)
        self.assertEqual(r['soundness'],{'kind':'probabilistic','delta':0.05,'conditional_on':'flips <= m and n* <= family_bound'})
        self.assertEqual(len(r['supports']),1);self.assertEqual(r['certificates'],[[None,None]])

    def test_bad_input(self):
        ok=((0,1),[0],[(1,None)],10)
        for kw in ({'eps_bar':0.5},{'eps_bar':-0.01},{'eps_bar':True},{'delta':0},{'delta':1},{'delta':1.5},{'family_bound':5},
                   {'family_bound':True},{'burn_in':-1}):
            with self.assertRaises(ValueError,msg=str(kw)):certify6(*ok,**kw)
        for args in (((0,1),[0],[],10),((0,2),[],[],10),((0,1),[2],[(0,0)],10),((0,1),[0],[(0,0)],3),((0,1),[],[],-1),((0,1),[],[],True)):
            with self.assertRaises(ValueError,msg=str(args)):certify6(*args)

    def test_host_agnostic(self):
        for f in ('brute/api/certify6.py',):
            mods=set()
            for n in ast.walk(ast.parse((ROOT/f).read_text())):
                if isinstance(n,ast.Import):mods|={a.name.split('.')[0] for a in n.names}
                elif isinstance(n,ast.ImportFrom):mods.add((n.module or '').split('.')[0])
            self.assertLessEqual(mods,{'__future__','brute','fractions'},f)
        src=(ROOT/'brute/noisyregion.py').read_text()
        for bad in ('import os','import socket','subprocess','threading','open('):self.assertNotIn(bad,src)


if __name__=='__main__':unittest.main()
