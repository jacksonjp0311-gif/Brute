"""Tests for brute/api/certify16.py (certify/16, v0.43.0; BRUTE_PLAN_046). New file. Worlds use an old development seed
(10050003, control_cycle3), outside every study-046 range; the certify14 fixture is results/diag-046/CERTIFY14_SAMPLE_046.json."""
import ast,json,unittest
from pathlib import Path
from brute.api import certify16 as C
from brute.api.certify14 import Certifier14
from experiments import worlds_043 as W
from experiments.brute_study_033 import StepWorld,passive
from scripts.make_certify14_sample_046 import canon
ROOT=Path(__file__).resolve().parents[1];DEV=10050003


def world():
    w=W.world(DEV,'control_cycle3');sw=StepWorld(w);_,acts,rd=passive(sw,DEV);return w,sw,acts,rd


class API(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(C.API,'brute.certify/16');self.assertEqual(C.SEARCHES[0],'a16');self.assertEqual(C.A16_MAX_BOUND,16)
        self.assertEqual(C.LABEL_OF_STOP,{'ID':'ID','IDF':'IDF','AMB':'AMB','K_spent':'AMB','unknown':'IDU'})

    def test_soundness_is_conditional_on_N(self):
        s=json.dumps(C.soundness()).lower();self.assertIn('family_bound',s);self.assertIn('inferred',s)

    def test_loop_control_ID(self):
        w,sw,acts,rd=world()
        with C.Certifier16(rd[0],w.k,3,budget_s=60.0) as c:
            for a,o in zip(acts,rd[1:]):c.observe(a,o)
            while (x:=c.propose()) is not None:
                for a in x:c.observe(a,sw.step(a))
            r=c.result()
        self.assertEqual((r['api'],r['label'],r['n_min'],r['family_bound']),('brute.certify/16','ID',3,3))
        for k in ('model','calls','unknown','soundness','used','rounds'):self.assertIn(k,r)

    def test_one_shot_matches_loop_on_passive(self):
        w,sw,acts,rd=world();r=C.certify16(rd[0],acts,rd[1:],w.k,3);self.assertEqual(r['api'],'brute.certify/16');self.assertIn(r['label'],('ID','AMB'))

    def test_one_shot_ambiguous_is_AMB(self):
        w,sw,acts,rd=world();r=C.certify16(rd[0],acts[:2],rd[1:3],w.k,3);self.assertEqual(r['label'],'AMB')

    def test_observe_rules(self):
        w,sw,acts,rd=world();c=C.Certifier16(rd[0],w.k,3,budget_s=60.0)
        with self.assertRaises(ValueError):c.observe(w.k,rd[1])
        for a,o in zip(acts,rd[1:]):c.observe(a,o)
        x=c.propose()
        if x is not None:
            with self.assertRaises(RuntimeError):c.propose()
            with self.assertRaises(ValueError):c.observe((x[0]+1)%w.k,(0,0))
        c.close()

    def test_argument_checks(self):
        for kw in ({'family_bound':17},{'family_bound':0},{'num_actions':5},{'K':-1},{'budget_s':0}):
            with self.assertRaises(ValueError,msg=str(kw)):C.Certifier16((0,1),**{'num_actions':3,'family_bound':3,**kw})
        with self.assertRaises(ValueError):C.Certifier16((0,1),search='nope')

    def test_delegation_is_certify14(self):
        self.assertIsInstance(C.Certifier16((0,1),search='s4',family_bound=3),Certifier14)

    def test_certify14_sample_byte_equal(self):
        S=json.loads((ROOT/'results/diag-046/CERTIFY14_SAMPLE_046.json').read_text())
        for c in S['cases']:
            a=c['args'];kw=dict(c['kwargs']);kw.setdefault('search','region')
            self.assertEqual(canon(C.certify16(tuple(a[0]),a[1],[tuple(o) for o in a[2]],**kw)),c['output'],c['name'])

    def test_host_agnostic_static(self):
        t=ast.parse((ROOT/'brute/api/certify16.py').read_text());bad=('os','subprocess','threading','multiprocessing','socket','io','pathlib','shutil','tempfile')
        for n in ast.walk(t):
            if isinstance(n,ast.Import):self.assertFalse([a.name for a in n.names if a.name.split('.')[0] in bad])
            if isinstance(n,ast.ImportFrom) and n.module:self.assertNotIn(n.module.split('.')[0],bad)
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Name):self.assertNotIn(n.func.id,('open','exec','eval','__import__'))

    def test_api_checks_closure(self):
        from scripts.api_checks_046 import closure
        c16=closure('brute.api.certify16');c14=closure('brute.api.certify14')
        self.assertTrue(set(c14)<=set(c16));self.assertIn('brute.scalesearch16',set(c16)-set(c14))
        self.assertEqual({m:v for m,v in c16.items() if m not in c14 and (v['bad_imports'] or v['bad_calls'])},{})


if __name__=='__main__':unittest.main()
