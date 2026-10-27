"""GAPI2 (BRUTE_PLAN_014 api_definition.gate_test) for brute.certify/2 on the api_test smoke trajectories 7190009-7190012."""
import ast,unittest
from pathlib import Path
from brute.api.certify import Certifier
from brute.api.certify2 import Certifier2,certify2,REASONS,API
from experiments.brute_study_014 import run_job,jobs_for,library,load,PLAN
from scripts.check_seeds_014 import smoke_source

ROOT=Path(__file__).resolve().parents[1]
_CASES={}


def cases():
    if not _CASES:
        plan=load(PLAN)
        for j in jobs_for(plan,'smoke-api'):_CASES[j[2]]=run_job(j,plan)[1]
    return _CASES


def replay(c,lib=None):
    """[(t, [query(0), query(1)], [certify/1 query(0), query(1)])] along the case's SP8 trajectory."""
    tr=c['arms']['SP8']['trace'];C=Certifier2(library=lib).initialize(c['initial_visible']);C1=Certifier().initialize(c['initial_visible']);out=[]
    try:
        for r in tr:
            out.append((r['step'],[C.query(0),C.query(1)],[C1.query(0),C1.query(1)]))
            C.observe(r['action'],r['observed']);C1.observe(r['action'],r['observed'])
    finally:C.close();C1.close()
    return out


class Certify2(unittest.TestCase):
    def test_i_no_library_equals_rg4_and_contains_certify1(self):
        for seed,c in cases().items():
            rg=c['transfer']['RG4']['trace']
            for (t,q,q1),row in zip(replay(c),rg):
                self.assertEqual(t,row['step'])
                for b in (0,1):
                    self.assertEqual(q[b]['answer'],row['certificate'][b],f'{seed} t={t} b={b}')
                    self.assertEqual(q[b]['status']=='CERTIFIED',row['certificate'][b] is not None)
                    if q1[b]['answer'] is not None:self.assertEqual(q[b]['answer'],q1[b]['answer'])
                    self.assertEqual(q[b]['api'],API)

    def test_ii_library_equals_study_dlf(self):
        for seed,c in cases().items():
            lib,hyp=library(*smoke_source(seed));L={'hypotheses':hyp[0],'min_n':lib['min_n']}
            dlf=c['transfer']['DLFp']['trace']
            for (t,q,_),row in zip(replay(c,L),dlf):
                for b in (0,1):
                    self.assertEqual((q[b]['status']=='CERTIFIED',q[b]['answer'],q[b]['rule']),
                                     (row['certificate'][b] is not None,row['certificate'][b],row['rule'][b]),f'{seed} t={t} b={b}')

    def test_iii_reasons(self):
        seen=set()
        for seed,c in cases().items():
            lib,hyp=library(*smoke_source(seed))
            for L in (None,{'hypotheses':hyp[0],'min_n':lib['min_n']}):
                for t,q,_ in replay(c,L):
                    for x in q:
                        if x['status']=='UNKNOWN':self.assertIn(x['reason'],REASONS);seen.add(x['reason'])
                        else:self.assertIsNone(x['reason']);self.assertIn(x['rule'],('sp8','rg','license'))
        self.assertIn('burn-in',seen)

    def test_iv_value_errors(self):
        for m in (0,2,True):
            with self.assertRaises(ValueError):Certifier2(margin=m)
        with self.assertRaises(ValueError):Certifier2(library={'hypotheses':[]})
        C=Certifier2()
        with self.assertRaises(ValueError):C.query(0)
        C.initialize((0,1))
        for bad in ((2,0),(0,),'01',(True,0)):
            with self.assertRaises(ValueError):C.observe(0,bad)
        with self.assertRaises(ValueError):C.query(2)
        with self.assertRaises(ValueError):C.initialize((0,1))
        C.close()
        with self.assertRaises(ValueError):certify2([(0,1)],[0],0)
        r=certify2([(0,1),(1,None)],[1],0);self.assertEqual(r['status'],'UNKNOWN');self.assertEqual(r['reason'],'burn-in')

    def test_v_host_agnostic(self):
        for f in ('brute/api/certify2.py','brute/boundedtransfer.py'):
            tree=ast.parse((ROOT/f).read_text());mods=set()
            for n in ast.walk(tree):
                if isinstance(n,ast.Import):mods|={a.name.split('.')[0] for a in n.names}
                elif isinstance(n,ast.ImportFrom):mods.add((n.module or '').split('.')[0])
                elif isinstance(n,ast.Call) and isinstance(n.func,ast.Name):self.assertNotEqual(n.func.id,'open',f)
            self.assertFalse(mods&{'os','subprocess','socket','http','threading'},f)


if __name__=='__main__':unittest.main()
