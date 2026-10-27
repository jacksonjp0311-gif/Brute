"""brute.certify/5 tests (plan 017 api_definition, GAPI5): (i) stateless certify5 / suggest5 agree with the stateful
object; (ii) host-agnostic import check; (iii) ValueError on bad input; (iv) suggest_action(rule='rglx') equals the
study RGLX action / rule / lookahead at every step of fixed smoke traces, and query equals certify/4."""
import ast,unittest
from fractions import Fraction
from pathlib import Path
from brute.api.certify4 import Certifier4,certify4
from brute.api.certify5 import Certifier5,certify5,suggest5,API
from experiments.brute_study_017 import run_job,load,PLAN

ROOT=Path(__file__).resolve().parents[1]


class Certify5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        plan=load(PLAN);cls.cases=[run_job(('smoke-api',f,s,0.35),plan)[1] for f,s in (('cycle3',8390009),('ood4',8390012))]

    def test_suggest_matches_runner(self):
        for c in self.cases:
            for mode in ('rglx','rgl'):
                tr=c[mode]['trace'];init=tuple(c['initial_visible'])
                c5=Certifier5().initialize(init);c4=Certifier4().initialize(init)
                try:
                    for r in tr:
                        s=c5.suggest_action(r['passive_action'],mode)
                        self.assertEqual((s['api'],s['action'],s['rule'],s['bounded_sizes'],s['lookahead']),
                                         (API,r['action'],r['rule'],r['bounded_sizes'],r['lookahead']),(mode,r['step']))
                        if r['lookahead'] is not None:
                            L=r['lookahead'];a=r['action']
                            self.assertEqual(s['lookahead_score'],float(Fraction(L['num'][a],L['den'][a])) if L['den'][a] else 0.0)
                        else:self.assertIsNone(s['lookahead_score'])
                        for b in (0,1):
                            q5=c5.query(b);q4=c4.query(b);self.assertEqual(q5['api'],API);q5['api']=q4['api'];self.assertEqual(q5,q4)
                            self.assertEqual(q5['answer'],c['transfer'][mode.upper()+'4']['trace'][r['step']-1]['certificate'][b])
                        o=tuple(r['observed']);c5.observe(r['action'],o);c4.observe(r['action'],o)
                finally:c5.close();c4.close()

    def test_stateless(self):
        c=self.cases[0];tr=c['rglx']['trace'][:30];obs=[tuple(c['initial_visible'])]+[tuple(r['observed']) for r in tr];acts=[r['action'] for r in tr]
        q=certify5(obs,acts,0);q4=certify4(obs,acts,0);q['api']=q4['api'];self.assertEqual(q,q4)
        s=suggest5(obs[:-1],acts[:-1],'rglx',None,tr[-1]['passive_action'])
        self.assertEqual((s['action'],s['rule'],s['lookahead']),(tr[-1]['action'],tr[-1]['rule'],tr[-1]['lookahead']))
        self.assertIn(suggest5(obs[:-1],acts[:-1],'rglx',True,tr[-1]['passive_action'])['rule'],('rsx','sp8'))

    def test_bad_input(self):
        c=Certifier5()
        with self.assertRaises(ValueError):c.suggest_action()
        c.initialize((0,1))
        for bad in (2,True,None):
            with self.assertRaises(ValueError):c.suggest_action(bad)
        with self.assertRaises(ValueError):c.suggest_action(0,rule='greedy')
        with self.assertRaises(ValueError):c.observe(0,(2,0))
        with self.assertRaises(ValueError):Certifier5(margin=0)
        with self.assertRaises(ValueError):Certifier5(family_bound=5)
        with self.assertRaises(ValueError):certify5([(0,1)],[0],0)
        with self.assertRaises(ValueError):suggest5([(0,1)],[],certified_before=1)
        c.close()

    def test_host_agnostic(self):
        for f in ('brute/api/certify5.py','brute/boundedlookahead.py'):
            mods=set()
            for n in ast.walk(ast.parse((ROOT/f).read_text())):
                if isinstance(n,ast.Import):mods|={a.name.split('.')[0] for a in n.names}
                elif isinstance(n,ast.ImportFrom):mods.add((n.module or '').split('.')[0])
            self.assertLessEqual(mods,{'__future__','brute','fractions'},f)


if __name__=='__main__':unittest.main()
