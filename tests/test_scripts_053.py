"""Tests for the study-053 runner and scoring scripts (v0.50.0). New file; built from tests/test_scripts_052.py (frozen).
Fresh cases use an old development seed (10050001) as a clean scale16 world (N 16), outside every study-053 range (plan, smoke)."""
import copy,json,tempfile,unittest
from pathlib import Path
from experiments import brute_study_053 as ST
from experiments.brute_common_053 import load,PLAN,C50,B16,B16N,C20,B20,caps_for,NOISE_OF,WORKERS,WORKERS_A,WORKERS_B,ALL_ARMS
from scripts.recount_053 import recount_case,bfs_form,rooted,compat_rule
from scripts import make_gates_053 as MG
from scripts import make_freeze_053 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10050001
IN_MAIN=lambda s:12050001<=s<=12050012 or 12070001<=s<=12070006 or 12090001<=s<=12090006 or 12110001<=s<=12110006


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual((C50,B16,B16N,C20,B20),(50000,3000000,1500000,50000,2000000))
        self.assertEqual([caps_for(k) for k in ('noise16','noise16_bar','compat16','scale20c')],[(C50,B16N),(C50,B16N),(C50,B16),(C20,B20)])
        self.assertEqual(NOISE_OF,{'API16N16':(0.05,None),'API16N16_b':(0.05,None),'API16N16_bar':(0.10,None),'API16N16_c':(0.0,1)})
        self.assertEqual((WORKERS,WORKERS_A,WORKERS_B),(8,7,1));self.assertEqual(len(ALL_ARMS),7)
        from experiments import brute_study_047 as S47;self.assertIs(S47._api16d,ST._api)

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertIn(ST.N16BAR,(6,3));self.assertIn(ST.N20C,(6,3))
        self.assertEqual(len(J),2*ST.N20C+12+24+ST.N16BAR);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        self.assertTrue(all(IN_MAIN(j[2]) for j in J));self.assertEqual([j[1] for j in J[:2*ST.N20C]],['scale20c']*(2*ST.N20C))
        self.assertEqual(sorted(j[2] for j in J if j[3]=='API16N16_bar'),list(range(12070001,12070001+ST.N16BAR)))
        self.assertEqual(sorted(j[2] for j in J if j[3]=='API16E20'),list(range(12110001,12110001+ST.N20C)))
        for j in J:ST.check_job(j,P)
        if ST.N20C<6:
            with self.assertRaises(Exception):ST.check_job(('main','scale20c',12110001+ST.N20C,'API16E20'),P)
        if ST.N16BAR<6:
            with self.assertRaises(Exception):ST.check_job(('main','noise16_bar',12070001+ST.N16BAR,'API16N16_bar'),P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),10)
        self.assertTrue(all(12130001<=j[2]<=12130006 for j in J))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        for j in (('main','noise16',11930001,'API16N16'),('smoke','noise16',12050001,'API16N16'),('main','noise16',12050001,'API16E'),
                  ('main','noise16_bar',12070001,'API16N16'),('main','compat16',12090001,'API16N16_bar'),('main','scale20c',12050001,'API16E20'),
                  ('main','scale20c',12110001,'API16E'),('main','compat16',12110001,'API16E')):
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_clean_recount_and_compat(self):
        c=json.loads(json.dumps(ST.run_fresh(DEV,'compat16','API16E')));c['block']='smoke';a=c['arms']['API16E']
        self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],c['N']),(C50,B16,None,16))
        out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(out['API16E']['label'],a['label'])
        c2=copy.deepcopy(c);c2['arms']['API16E']['label']='WRONG';self.assertNotEqual(recount_case(c2)[1],[])
        n=json.loads(json.dumps(ST.run_fresh(DEV,'compat16','API16N16_c')))['arms']['API16N16_c']
        self.assertEqual((n['eps'] if 'eps' in n else 0.0,n['reads']),(0.0,1))
        r=compat_rule(n,a,n['label'],a['label']);self.assertEqual(r['label_equal'],n['label']==a['label'])
        if a['label']==n['label'] in ('ID','IDF'):self.assertTrue(r['equal'],r)

    def test_rooted_renaming_free(self):
        d=[[1,2],[0,2],[2,1]];e=[0,1,1];p=[0,2,1]   # swap states 1 and 2
        d2=[[0]*2 for _ in d];e2=[0]*3
        for q in range(3):
            e2[p[q]]=e[q]
            for a in range(2):d2[p[q]][a]=p[d[q][a]]
        self.assertEqual(bfs_form([d,e]),bfs_form([d2,e2]));self.assertNotEqual(bfs_form([d,e]),bfs_form([d,[0,1,0]]))
        self.assertEqual(rooted([d,e],1),rooted([d2,e2],2));self.assertNotEqual(rooted([d,e],1),rooted([d,e],0))

    def test_compat_rule_cases(self):
        from unittest import mock
        from experiments import brute_study_051 as S51
        self.enterContext(mock.patch.object(S51,'canon16e',lambda r:None))   # H4 canon16e equality is informational; synthetic records lack rounds
        m=[[[1,0],[0,1]],[0,1]];m2=[[[1,0],[0,1]],[1,0]]
        R=lambda mod,s,fm:{'model':mod,'s1':s,'future_match':fm}
        self.assertTrue(compat_rule(R(m,0,True),R(m,0,True),'ID','ID')['equal'])
        self.assertFalse(compat_rule(R(m,0,True),R(m2,0,True),'ID','ID')['equal'])
        self.assertTrue(compat_rule(R(m,1,True),R(m2,0,True),'IDF','IDF')['equal'])
        self.assertFalse(compat_rule(R(m,1,True),R(m2,0,False),'IDF','IDF')['equal'])
        self.assertFalse(compat_rule(R(m,0,True),R(m,0,True),'ID','IDF')['equal'])
        self.assertTrue(compat_rule(R(None,None,None),R(None,None,None),'AMB','AMB')['equal'])


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GDET53','GFID53','GN16_sound53','GCOMPAT16N53','GHOST53','GQB27','GS_ref','G_sound','G_recount','GTEST','G_RT'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('reason',G['gates'][g],g)
            self.assertFalse(G['certified_16n_N16'])
            for g in ('GS20C_det53','GS20C_sound53'):self.assertIn(g,G['nonblocking']);self.assertNotIn(g,G['gates'])

    def test_arm_order_insensitive(self):
        import inspect
        src=inspect.getsource(MG.build);self.assertNotIn("list(c['arms'])==",src);self.assertIn("sorted(c['arms'])==sorted(CP)",src)

    def test_freeze_list(self):
        gen={'results/diag-053/PREFREEZE_SMOKE_GATES_053.json','docs/research/BRUTE_DEVIATIONS_053_179.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify16n.py','brute/api/certify16e.py','experiments/brute_study_052.py','scripts/make_gates_053.py',
                  'experiments/BRUTE_PLAN_052.json','experiments/BRUTE_PLAN_053.json','results/study-052/main/SEAL.json','results/diag-053/SEEDCHECK_053.json',
                  'tests/test_scripts_053.py','tests/test_release_0500.py'):
            self.assertIn(f,MF.FILES)
        self.assertEqual(len(set(MF.FILES)),395)   # inherited repeats; the freeze hashes sorted(set(FILES))
        old=__import__('scripts.make_freeze_052',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
