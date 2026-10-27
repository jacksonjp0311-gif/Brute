"""brute.certify/3 tests (plan 015 api_definition): (i) query equals certify/2; (ii) suggest_action equals the study RSX
action; (iii) ValueError on bad input; (iv) host-agnostic import check."""
import ast,unittest
from pathlib import Path
from brute.api.certify2 import Certifier2,certify2
from brute.api.certify3 import Certifier3,certify3,suggest3,API
from experiments.brute_study_015 import run_job,load,PLAN

ROOT=Path(__file__).resolve().parents[1]


class Certify3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        plan=load(PLAN);cls.cases=[run_job(('smoke-api',f,s,0.35),plan)[1] for f,s in (('cycle3',8190009),('ood4',8190012))]

    def test_query_and_suggest(self):
        for c in self.cases:
            tr=c['rsx']['trace'];init=tuple(c['initial_visible'])
            c3=Certifier3().initialize(init);c2=Certifier2().initialize(init)
            try:
                for r in tr:
                    s=c3.suggest_action(r['passive_action'])
                    self.assertEqual((s['api'],s['action'],s['rule'],s['bounded_sizes']),(API,r['action'],r['rsx_rule'],r['bounded_sizes']))
                    for b in (0,1):
                        q3=c3.query(b);q2=c2.query(b);self.assertEqual(q3['api'],API);q3['api']=q2['api'];self.assertEqual(q3,q2)
                        self.assertEqual(q3['answer'],c['transfer']['RSX4']['trace'][r['step']-1]['certificate'][b])
                    o=tuple(r['observed']);c3.observe(r['action'],o);c2.observe(r['action'],o)
            finally:c3.close();c2.close()

    def test_stateless(self):
        c=self.cases[0];tr=c['rsx']['trace'][:12];obs=[tuple(c['initial_visible'])]+[tuple(r['observed']) for r in tr];acts=[r['action'] for r in tr]
        q=certify3(obs,acts,0);q2=certify2(obs,acts,0);q['api']=q2['api'];self.assertEqual(q,q2)
        s=suggest3(obs[:-1],acts[:-1],tr[-1]['passive_action']);self.assertEqual(s['action'],tr[-1]['action'])

    def test_bad_input(self):
        c=Certifier3()
        with self.assertRaises(ValueError):c.suggest_action()
        c.initialize((0,1))
        for bad in (2,True,None):
            with self.assertRaises(ValueError):c.suggest_action(bad)
        with self.assertRaises(ValueError):c.observe(0,(2,0))
        with self.assertRaises(ValueError):Certifier3(margin=0)
        with self.assertRaises(ValueError):certify3([(0,1)],[0],0)
        c.close()

    def test_host_agnostic(self):
        for f in ('brute/api/certify3.py','brute/regionsplit.py'):
            mods=set()
            for n in ast.walk(ast.parse((ROOT/f).read_text())):
                if isinstance(n,ast.Import):mods|={a.name.split('.')[0] for a in n.names}
                elif isinstance(n,ast.ImportFrom):mods.add((n.module or '').split('.')[0])
            self.assertLessEqual(mods,{'__future__','brute'},f)


if __name__=='__main__':unittest.main()
