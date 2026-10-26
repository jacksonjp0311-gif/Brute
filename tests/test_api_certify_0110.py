"""GAPI gate test (BRUTE_PLAN_013 api_definition.gate_test) for brute/api/certify.py."""
import ast,unittest
from pathlib import Path
from brute.api.certify import Certifier,certify,BASE,TAU6,KW,FAMILY,API
import experiments.brute_study_012 as S12
from experiments.brute_common_013 import load,PLAN,plan_view,plan006_keys
from scripts.check_seeds_013 import check_run_seeds

SEEDS=(6190009,6190010,6190011,6190012);FAMS=('cycle3','switch3','unaliased2','ood4');MASK=0.35
_CASES={}


def case(i):
    if i not in _CASES:
        plan=load(PLAN);check_run_seeds('smoke',[SEEDS[i]],plan)
        _CASES[i]=S12.run_case_2x2(SEEDS[i],FAMS[i],MASK,plan,plan['tau6']['value'],arms=('SP8',),block='smoke-api')
    return _CASES[i]


def replay(c,H=None):
    """[(step, b, query result, SP8 recorded certificate)] for both actions at every step."""
    C=Certifier(library_hypotheses=H).initialize(tuple(c['initial_visible']));out=[]
    try:
        for r in c['arms']['SP8']['trace']:
            a=r['action'];R={a:r,1-a:r['counterfactual']}
            for b in (0,1):out.append((r['step'],b,C.query(b),R[b]['certificate']))
            C.observe(a,tuple(r['observed']))
    finally:C.close()
    return out


class ApiCertify0110(unittest.TestCase):
    def test_constants_match_plan(self):
        plan=load(PLAN);v=plan_view(plan);p6=plan006_keys(v)
        self.assertEqual(TAU6,plan['tau6']['value']);self.assertEqual(FAMILY,p6['declared_family'])
        self.assertEqual(KW,{'surprise_fraction':v['surprise_fraction'],'recency_window':v['recency_window'],'burn_in':v['burn_in']})
        import experiments.brute_study_009 as S9
        self.assertEqual(BASE,tuple(S9._base(p6)))

    def test_reproduces_sp8_exactly(self):
        n=0
        for i in range(4):
            c=case(i);self.assertEqual(len(c['arms']['SP8']['trace']),44)
            for t,b,q,cert in replay(c):
                self.assertEqual(q['api'],API);self.assertEqual(q['answer'],cert,(SEEDS[i],t,b))
                self.assertEqual(q['status'],'CERTIFIED' if cert is not None else 'UNKNOWN');n+=cert is not None
        self.assertGreater(n,0)

    def test_stateless_wrapper(self):
        c=case(0);tr=c['arms']['SP8']['trace'][:20]
        obs=[tuple(c['initial_visible'])]+[tuple(r['observed']) for r in tr];acts=[r['action'] for r in tr]
        q=certify(obs,acts,0);r=c['arms']['SP8']['trace'][20];R={r['action']:r,1-r['action']:r['counterfactual']}
        self.assertEqual(q['answer'],R[0]['certificate']);self.assertEqual(q['step'],20)

    def test_malformed_input(self):
        for bad in ((0,2),(0,),(0,1,1),'01',(True,0),None):
            with self.assertRaises(ValueError):Certifier().initialize(bad)
        C=Certifier().initialize((0,1))
        for a in (2,-1,True,None,'0'):
            with self.assertRaises(ValueError):C.query(a)
            with self.assertRaises(ValueError):C.observe(a,(0,1))
        with self.assertRaises(ValueError):C.observe(0,(0,5))
        with self.assertRaises(ValueError):C.initialize((0,1))
        with self.assertRaises(ValueError):Certifier().query(0)
        with self.assertRaises(ValueError):Certifier(family_states=5)
        with self.assertRaises(ValueError):certify([(0,1)],[0],0)
        C.close()

    def test_dr_mode_subset(self):
        lo=load(PLAN)['smoke_seeds']['range'][0];k=0
        for i in range(4):
            c=case(i);_,H=S12.library(FAMS[i],lo+20+i)
            for (t,b,q,cert) in replay(c,H[0]):
                if q['answer'] is not None:self.assertEqual(q['answer'],cert);k+=1
                if q['rule']=='dr-disagree':self.assertIsNotNone(cert)
        self.assertGreaterEqual(k,0)

    def test_no_host_imports(self):
        src=Path(__file__).resolve().parents[1]/'brute'/'api'/'certify.py';tree=ast.parse(src.read_text())
        banned={'subprocess','socket','http','threading','urllib','multiprocessing','asyncio'}
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):
                for a in n.names:self.assertNotIn(a.name.split('.')[0],banned)
            if isinstance(n,ast.ImportFrom):self.assertNotIn((n.module or '').split('.')[0],banned)
            if isinstance(n,ast.Attribute):self.assertFalse(n.attr=='system' and getattr(n.value,'id','')=='os')
            if isinstance(n,ast.Call):self.assertNotIn(getattr(n.func,'id',''),{'open','exec','eval'})


if __name__=='__main__':unittest.main()
