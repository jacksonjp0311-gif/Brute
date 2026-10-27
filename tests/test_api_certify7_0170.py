"""brute.certify/7 tests (plan 019 GAPI7): stateless answers equal the study runner's RGNB4 / RGNB4_3 supports,
certificates and boundary; host-agnostic import check; ValueError on bad input (incl. eps_bar outside [0, 0.5), delta
outside (0, 1), num_actions outside {2, 3}); exact soundness dict."""
import ast,unittest
from pathlib import Path
from brute.api.certify7 import certify7,API
from experiments.brute_study_019 import run_job,load,PLAN

ROOT=Path(__file__).resolve().parents[1]


class Certify7(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        plan=load(PLAN)
        cls.cases=[run_job(('smoke-api',f,s,0.02),plan)[1] for f,s in (('cycle3',8590009),('ood4',8590012))]
        cls.a3=run_job(('smoke-a3','rand4a3',8590017,0.02),plan)[1]

    def test_matches_runner_two_actions(self):
        for c in self.cases:
            tr=c['arms']['SP8']['trace'];acts=[r['action'] for r in tr];obs=[tuple(r['observed']) for r in tr]
            r=certify7(tuple(c['initial_visible']),acts,obs,c['B'])
            self.assertEqual((r['api'],r['boundary'],r['observed_bits'],r['steps'],r['num_actions']),(API,c['boundary'],c['B'],len(acts),2))
            self.assertEqual(r['supports'][:-1],c['noisy']['RGNB4']['support']);self.assertEqual(r['m'][:-1],c['noisy']['RGNB4']['m'])
            self.assertEqual(r['certificates'][:-1],[x['certificate'] for x in c['certifiers']['RGNB4']['trace']])
            k=20;p=certify7(tuple(c['initial_visible']),acts[:k],obs[:k],c['B'])
            self.assertEqual(p['supports'],c['noisy']['RGNB4']['support'][:k+1])

    def test_matches_runner_three_actions(self):
        c=self.a3;rd=[tuple(o) for o in c['readings']]
        r=certify7(rd[0],c['actions'],rd[1:],c['B'],num_actions=3)
        self.assertEqual(r['supports'][:-1],c['regions']['RGNB4_3']['support']);self.assertEqual(r['m'][:-1],c['regions']['RGNB4_3']['m'])
        self.assertEqual(r['certificates'][:-1],[x['certificate'] for x in c['certifiers']['RGNB4_3']['trace']])

    def test_soundness(self):
        r=certify7((0,1),[],[],10,delta=0.05)
        self.assertEqual(r['soundness'],{'kind':'probabilistic','delta':0.05,'conditional_on':'running flips <= m(b) and n* <= family_bound'})
        self.assertEqual(len(r['supports']),1);self.assertEqual(r['certificates'],[[None,None]])
        self.assertEqual(certify7((0,1),[],[],10,num_actions=3)['certificates'],[[None,None,None]])

    def test_bad_input(self):
        ok=((0,1),[0],[(1,None)],10)
        for kw in ({'eps_bar':0.5},{'eps_bar':-0.01},{'eps_bar':True},{'delta':0},{'delta':1},{'delta':1.5},{'family_bound':5},
                   {'family_bound':True},{'burn_in':-1},{'num_actions':1},{'num_actions':4},{'num_actions':True},{'num_actions':2.0}):
            with self.assertRaises(ValueError,msg=str(kw)):certify7(*ok,**kw)
        for args in (((0,1),[0],[],10),((0,2),[],[],10),((0,1),[2],[(0,0)],10),((0,1),[True],[(0,0)],10),((0,1),[0],[(0,0)],3),
                     ((0,1),[],[],-1),((0,1),[],[],True)):
            with self.assertRaises(ValueError,msg=str(args)):certify7(*args)
        with self.assertRaises(ValueError):certify7((0,1),[3],[(0,0)],10,num_actions=3)
        self.assertEqual(certify7((0,1),[2],[(0,0)],10,num_actions=3)['steps'],1)

    def test_host_agnostic(self):
        allowed={'__future__','brute','fractions'}
        for f in ('brute/api/certify7.py','brute/seqmargin.py','brute/region3.py'):
            mods=set()
            for n in ast.walk(ast.parse((ROOT/f).read_text())):
                if isinstance(n,ast.Import):mods|={a.name.split('.')[0] for a in n.names}
                elif isinstance(n,ast.ImportFrom):mods.add((n.module or '').split('.')[0])
            self.assertLessEqual(mods,allowed,f)
            src=(ROOT/f).read_text()
            for bad in ('import os','import socket','subprocess','threading','open('):self.assertNotIn(bad,src,f)


if __name__=='__main__':unittest.main()
