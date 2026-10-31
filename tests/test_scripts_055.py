"""Tests for the study-055 runner and scoring scripts (v0.52.0). New file; built from tests/test_scripts_054.py (frozen).
Fresh cases use an old development seed (10051001) as a clean scale16 world (N 16), outside every study-055 range (plan, smoke)."""
import copy,json,tempfile,unittest
from pathlib import Path
from experiments import brute_study_055 as ST
from experiments.brute_common_055 import load,PLAN,caps_for,WORKERS_S,WORKERS_C,ALL_ARMS
from scripts.recount_055 import recount_case,compat_rule
from scripts import make_gates_055 as MG
from scripts import make_freeze_055 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10051001
IN_MAIN=lambda s:12250001<=s<=12250006 or 12270001<=s<=12270006


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual([caps_for(k) for k in ('scale20t','compat20t')],[(50000,2000000),(50000,3000000)])
        self.assertEqual((WORKERS_S,WORKERS_C),(4,4));self.assertEqual(ALL_ARMS,('API20C','API20C_b','API16E20','API16E'))

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertIn(ST.N20C,(6,4));self.assertIn(ST.NC20C,(6,4))
        self.assertEqual(len(J),3*ST.N20C+2*ST.NC20C);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        self.assertTrue(all(IN_MAIN(j[2]) for j in J))
        for j in J:ST.check_job(j,P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),10)
        self.assertTrue(all(12290001<=j[2]<=12290004 for j in J))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        for j in (('main','scale20t',12110001,'API20C'),('smoke','scale20t',12250001,'API20C'),('main','scale20t',12250001,'API16E'),
                  ('main','compat20t',12270001,'API20C_b'),('main','compat20t',12250001,'API20C')):
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_clean_recount_and_compat(self):
        c=json.loads(json.dumps(ST.run_fresh(DEV,'compat20t','API20C')));c['block']='smoke'
        e=json.loads(json.dumps(ST.run_fresh(DEV,'compat20t','API16E')));c['arms'].update(e['arms']);a=c['arms']['API20C']
        self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],c['N']),(50000,3000000,None,16))
        out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(out['API20C']['label'],a['label'])
        c2=copy.deepcopy(c);c2['arms']['API20C']['label']='WRONG';self.assertNotEqual(recount_case(c2)[1],[])
        b=c['arms']['API16E'];r=compat_rule(a,b,a['label'],b['label']);self.assertEqual(r['label_equal'],a['label']==b['label'])
        self.assertEqual(a['hook_arms'],0)
        self.assertIn('cube',a);self.assertEqual(a['cube']['depth'],5)
        self.assertEqual(a['api']['api'],'brute.certify/20c');self.assertEqual(a['api']['label'],a['label'])   # full api_result kept for GFID55 replay (#183)



class CubeAudit(unittest.TestCase):
    def test_plan_matches_api_on_random_traces(self):
        # the independent recomputation (scripts/cube_audit_055) equals certify20c.cube_plan fed with Pool15-style future_pairs
        import random
        from scripts import cube_audit_055 as CA
        from brute.api.certify20c import cube_plan
        from brute.scalesearch15 import apart_matrix
        rng=random.Random(55)
        for _ in range(300):
            T=rng.randrange(0,9);acts=[rng.randrange(2) for _ in range(T)];masks=[1<<rng.randrange(2) for _ in range(T+1)];n=rng.randrange(1,6)
            A=apart_matrix(masks,acts);fp={(t,u) for t in range(T+1) for u in range(t+1,T+1) if A[t][u] and masks[t]&masks[u]}
            pos,live,pr=cube_plan(n,T,fp);p2,l2,pr2,_=CA.plan(n,T,masks,acts)
            self.assertEqual((pos,[list(x) for x in live],[[list(c),list(q)] for c,q in pr]),(p2,l2,pr2))

    def test_apart_word(self):
        from scripts import cube_audit_055 as CA
        self.assertEqual(CA.apart_word([1,2],[0],1,0,1),(0,[]))
        self.assertEqual(CA.apart_word([1,1,1,2],[0,0,0],3,1,2),(1,[0]))
        self.assertIsNone(CA.apart_word([1,1,1],[0,1],2,0,1))

    def test_audit_fresh_record(self):
        from scripts import cube_audit_055 as CA
        c=json.loads(json.dumps(ST.run_fresh(DEV,'compat20t','API20C')));c['block']='smoke';x=CA.audit_arm(c,'API20C')
        self.assertTrue(x['pass'],x['mismatches']);self.assertTrue(x['conflict_sum_ok'])
        c2=copy.deepcopy(c);c2['arms']['API20C']['conflicts_spent']+=1;self.assertFalse(CA.audit_arm(c2,'API20C')['pass'])


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GDET55','GFID55','GCUBE55','GS20C_sound55','GS20C_gain55','GCOMPAT20C55','GHOST55','GS_ref','G_sound','G_recount','GTEST','G_RT'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('reason',G['gates'][g],g)
            self.assertFalse(G['certified_20c_N20'])

    def test_freeze_list(self):
        gen={'results/diag-055/PREFREEZE_SMOKE_GATES_055.json','docs/research/BRUTE_DEVIATIONS_055_183.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify20c.py','brute/api/certify16e.py','experiments/brute_study_055.py','scripts/make_gates_055.py',
                  'experiments/BRUTE_PLAN_055.json','results/diag-055/SEEDCHECK_055.json',
                  'tests/test_scripts_055.py','tests/test_release_0520.py','tests/test_certify20c.py','scripts/cube_audit_055.py'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_054',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
