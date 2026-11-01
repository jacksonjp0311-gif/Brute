"""Tests for the study-056 runner and scoring scripts (v0.53.0). New file; built from tests/test_scripts_055.py (frozen).
Fresh cases use an old development seed (10051001) as a clean scale16 world (N 16), outside every study-056 range (plan, smoke)."""
import copy,json,tempfile,unittest
from pathlib import Path
from experiments import brute_study_056 as ST
from experiments.brute_common_056 import load,PLAN,caps_for,WORKERS_S,WORKERS_C,ALL_ARMS
from scripts.recount_056 import recount_case,compat_rule_056,minimise,unpointed_iso
from scripts import make_gates_056 as MG
from scripts import make_freeze_056 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10051001
IN_MAIN=lambda s:12330001<=s<=12330006 or 12350001<=s<=12350006


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual([caps_for(k) for k in ('scale20t','compat20t')],[(50000,2000000),(50000,3000000)])
        self.assertEqual((WORKERS_S,WORKERS_C),(4,4));self.assertEqual(ALL_ARMS,('API20L','API20L_b','API16E20','API16E'))

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertIn(ST.N20L,(6,4));self.assertIn(ST.NC20L,(6,4))
        self.assertEqual(len(J),3*ST.N20L+2*ST.NC20L);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        self.assertTrue(all(IN_MAIN(j[2]) for j in J))
        for j in J:ST.check_job(j,P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),10)
        self.assertTrue(all(12370001<=j[2]<=12370004 for j in J))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        for j in (('main','scale20t',12250001,'API20L'),('smoke','scale20t',12330001,'API20L'),('main','scale20t',12330001,'API16E'),
                  ('main','compat20t',12350001,'API20L_b'),('main','compat20t',12330001,'API20L')):
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_clean_recount_compat_and_table(self):
        c=json.loads(json.dumps(ST.run_fresh(DEV,'compat20t','API20L')));c['block']='smoke'
        e=json.loads(json.dumps(ST.run_fresh(DEV,'compat20t','API16E')));c['arms'].update(e['arms']);a=c['arms']['API20L']
        self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],c['N']),(50000,3000000,None,16))
        out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(out['API20L']['label'],a['label'])
        c2=copy.deepcopy(c);c2['arms']['API20L']['label']='WRONG';self.assertNotEqual(recount_case(c2)[1],[])
        b=c['arms']['API16E'];r=compat_rule_056(a,b,out['API20L']['label'],out['API16E']['label'],out['API20L'].get('future_match'),out['API16E'].get('future_match'))
        self.assertEqual(r['label_equal'],out['API20L']['label']==out['API16E']['label']);self.assertEqual(r['rule_name'],'compat_rule_056')
        self.assertEqual(a['hook_arms'],0);self.assertIn('table',a)
        self.assertEqual(a['api']['api'],'brute.certify/20l');self.assertEqual(a['api']['label'],a['label'])   # full api_result kept for GFID56 replay
        from scripts import table_audit_056 as TA
        x=TA.audit_arm(c,'API20L');self.assertTrue(x['pass'],x['mismatches'])
        from scripts import run_reference_056  # noqa: F401  (binds the 056 names)
        from scripts import run_reference_047 as R47
        self.assertEqual(R47._audit(R47.view(c,'API20L'))[0]['mismatches'],[])   # #185: n_min is the least consistent size (GS_ref)
        c3=copy.deepcopy(c);t=c3['arms']['API20L']['table'];t['hypotheses']=(t.get('hypotheses') or 0)+1;self.assertFalse(TA.audit_arm(c3,'API20L')['pass'])


class CompatRule(unittest.TestCase):
    def test_unpointed_iso(self):
        # 2-state toggle on input 0 (outputs 1,2): any start state gives the same unpointed machine; a different output does not
        m=[[[1],[0]],[1,2]]
        self.assertTrue(unpointed_iso(m,0,m,1))
        n=[[[1],[0]],[1,4]];self.assertFalse(unpointed_iso(m,0,n,0))
        self.assertIsNotNone(minimise(m,0))

    def test_rule_labels(self):
        m=[[[1],[0]],[1,2]];x={'model':m,'s1':0};y={'model':m,'s1':1}
        self.assertTrue(compat_rule_056(x,y,'IDF','IDF',True,True)['equal'])
        self.assertFalse(compat_rule_056(x,y,'IDF','IDF',True,False)['equal'])
        self.assertFalse(compat_rule_056(x,y,'IDF','AMB',True,True)['equal'])
        self.assertTrue(compat_rule_056(x,x,'ID','ID',None,None)['equal'])


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GDET56','GFID56','GTABLE56','GS20L_sound56','GS20L_gain56','GCOMPAT20L56','GHOST56','GS_ref','G_sound','G_recount','GTEST','G_RT'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('reason',G['gates'][g],g)
            self.assertFalse(G['certified_20l_N20']);self.assertTrue(G['status_phrase'].startswith('not certified, no certification status'))
            self.assertIn('RECHECK_055',G['secondary']);self.assertIsNone(G['secondary']['RECHECK_055']['pass'])

    def test_freeze_list(self):
        gen={'results/diag-056/PREFREEZE_SMOKE_GATES_056.json','docs/research/BRUTE_DEVIATIONS_056_185.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify20l.py','brute/api/certify20c.py','experiments/brute_study_056.py','scripts/make_gates_056.py',
                  'experiments/BRUTE_PLAN_056.json','results/diag-056/SEEDCHECK_056.json','results/study-055/GATES_055.json',
                  'tests/test_scripts_056.py','tests/test_release_0530.py','tests/test_certify20l.py','scripts/table_audit_056.py'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_055',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
