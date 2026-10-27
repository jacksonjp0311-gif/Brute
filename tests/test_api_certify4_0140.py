"""brute.certify/4 tests (plan 016 api_definition): (i) query equals certify/3 (api name aside); (ii) suggest_action
equals the study RSXL action at every step; (iii) ValueError on bad input; (iv) host-agnostic import check."""
import ast,unittest
from pathlib import Path
from brute.api.certify3 import Certifier3,certify3
from brute.api.certify4 import Certifier4,certify4,suggest4,API
from experiments.brute_study_016 import run_job,load,PLAN

ROOT=Path(__file__).resolve().parents[1]


class Certify4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        plan=load(PLAN);cls.cases=[run_job(('smoke-api',f,s,0.35),plan)[1] for f,s in (('cycle3',8290009),('ood4',8290012))]

    def test_query_and_suggest(self):
        for c in self.cases:
            tr=c['rsxl']['trace'];init=tuple(c['initial_visible'])
            c4=Certifier4().initialize(init);c3=Certifier3().initialize(init)
            try:
                for r in tr:
                    s=c4.suggest_action(r['passive_action'])
                    self.assertEqual((s['api'],s['action'],s['rule'],s['bounded_sizes'],s['deferred']),
                                     (API,r['action'],r['rsxl_rule'],r['bounded_sizes'],r['deferred']),r['step'])
                    for b in (0,1):
                        q4=c4.query(b);q3=c3.query(b);self.assertEqual(q4['api'],API);q4['api']=q3['api'];self.assertEqual(q4,q3)
                        self.assertEqual(q4['answer'],c['transfer']['RSXL4']['trace'][r['step']-1]['certificate'][b])
                    o=tuple(r['observed']);c4.observe(r['action'],o);c3.observe(r['action'],o)
            finally:c4.close();c3.close()

    def test_stateless(self):
        c=self.cases[0];tr=c['rsxl']['trace'][:30];obs=[tuple(c['initial_visible'])]+[tuple(r['observed']) for r in tr];acts=[r['action'] for r in tr]
        q=certify4(obs,acts,0);q3=certify3(obs,acts,0);q['api']=q3['api'];self.assertEqual(q,q3)
        s=suggest4(obs[:-1],acts[:-1],None,tr[-1]['passive_action']);self.assertEqual((s['action'],s['deferred']),(tr[-1]['action'],tr[-1]['deferred']))
        self.assertEqual(suggest4(obs[:-1],acts[:-1],False,tr[-1]['passive_action'])['rule'],'sp8')

    def test_bad_input(self):
        c=Certifier4()
        with self.assertRaises(ValueError):c.suggest_action()
        c.initialize((0,1))
        for bad in (2,True,None):
            with self.assertRaises(ValueError):c.suggest_action(bad)
        with self.assertRaises(ValueError):c.suggest_action(0,deferred=1)
        with self.assertRaises(ValueError):c.observe(0,(2,0))
        with self.assertRaises(ValueError):Certifier4(margin=0)
        with self.assertRaises(ValueError):certify4([(0,1)],[0],0)
        with self.assertRaises(ValueError):suggest4([(0,1)],[],certified_before=1)
        c.close()

    def test_host_agnostic(self):
        for f in ('brute/api/certify4.py','brute/deferredsplit.py'):
            mods=set()
            for n in ast.walk(ast.parse((ROOT/f).read_text())):
                if isinstance(n,ast.Import):mods|={a.name.split('.')[0] for a in n.names}
                elif isinstance(n,ast.ImportFrom):mods.add((n.module or '').split('.')[0])
            self.assertLessEqual(mods,{'__future__','brute'},f)


if __name__=='__main__':unittest.main()
