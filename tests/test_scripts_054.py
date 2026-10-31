"""Tests for the study-054 runner and scoring scripts (v0.51.0). New file; built from tests/test_scripts_053.py (frozen).
Fresh cases use an old development seed (10050001) as a clean scale16 world (N 16), outside every study-054 range (plan, smoke)."""
import copy,json,tempfile,unittest
from pathlib import Path
from experiments import brute_study_054 as ST
from experiments.brute_common_054 import load,PLAN,caps_for,WORKERS_S,WORKERS_C,ALL_ARMS
from scripts.recount_054 import recount_case,compat_rule
from scripts import make_gates_054 as MG
from scripts import make_freeze_054 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10050001
IN_MAIN=lambda s:12170001<=s<=12170006 or 12190001<=s<=12190006


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual([caps_for(k) for k in ('scale20t','compat20t')],[(50000,2000000),(50000,3000000)])
        self.assertEqual((WORKERS_S,WORKERS_C),(4,4));self.assertEqual(ALL_ARMS,('API20T','API20T_b','API16E20','API16E'))

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertIn(ST.N20T,(6,4));self.assertIn(ST.NC20T,(6,4))
        self.assertEqual(len(J),3*ST.N20T+2*ST.NC20T);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        self.assertTrue(all(IN_MAIN(j[2]) for j in J))
        for j in J:ST.check_job(j,P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),10)
        self.assertTrue(all(12210001<=j[2]<=12210004 for j in J))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        for j in (('main','scale20t',12110001,'API20T'),('smoke','scale20t',12170001,'API20T'),('main','scale20t',12170001,'API16E'),
                  ('main','compat20t',12190001,'API20T_b'),('main','compat20t',12170001,'API20T')):
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_clean_recount_and_compat(self):
        c=json.loads(json.dumps(ST.run_fresh(DEV,'compat20t','API20T')));c['block']='smoke'
        e=json.loads(json.dumps(ST.run_fresh(DEV,'compat20t','API16E')));c['arms'].update(e['arms']);a=c['arms']['API20T']
        self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],c['N']),(50000,3000000,None,16))
        out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(out['API20T']['label'],a['label'])
        c2=copy.deepcopy(c);c2['arms']['API20T']['label']='WRONG';self.assertNotEqual(recount_case(c2)[1],[])
        b=c['arms']['API16E'];r=compat_rule(a,b,a['label'],b['label']);self.assertEqual(r['label_equal'],a['label']==b['label'])
        self.assertEqual(a['hook_arms'],0)


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GDET54','GFID54','GS20T_sound54','GS20T_gain54','GCOMPAT20T54','GHOST54','GS_ref','G_sound','G_recount','GTEST','G_RT'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('reason',G['gates'][g],g)
            self.assertFalse(G['certified_20t_N20'])

    def test_freeze_list(self):
        gen={'results/diag-054/PREFREEZE_SMOKE_GATES_054.json','docs/research/BRUTE_DEVIATIONS_054_181.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify20t.py','brute/api/certify16e.py','experiments/brute_study_054.py','scripts/make_gates_054.py',
                  'experiments/BRUTE_PLAN_054.json','experiments/BRUTE_PLAN_054a.json','results/diag-054/SEEDCHECK_054.json',
                  'tests/test_scripts_054.py','tests/test_release_0510.py','tests/test_certify20t.py'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_053',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
