"""Tests for the study-052 runner and scoring scripts (v0.49.0). New file; built from tests/test_scripts_051.py (frozen).
Fresh cases use an old development seed (10050003) as a clean scale12 world, outside every study-052 range (plan, smoke)."""
import copy,json,tempfile,unittest
from pathlib import Path
from experiments import brute_study_052 as ST
from experiments.brute_common_052 import load,PLAN,C50,B12,B12N,caps_for,NOISE_OF,WORKERS,ALL_ARMS
from scripts.recount_052 import recount_case,bfs_form,rooted,compat_rule
from scripts import make_gates_052 as MG
from scripts import make_freeze_052 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10050003
IN_MAIN=lambda s:11930001<=s<=11930024 or 11950001<=s<=11950012 or 11970001<=s<=11970006


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual((C50,B12,B12N),(50000,3000000,1500000))
        self.assertEqual([caps_for(k) for k in ('noise12','noise12_bar','compat')],[(C50,B12N),(C50,B12N),(C50,B12)])
        self.assertEqual(NOISE_OF,{'API16N':(0.05,None),'API16N_b':(0.05,None),'API16N_bar':(0.10,None),'API16N_c':(0.0,1)});self.assertEqual(WORKERS,8)
        from experiments import brute_study_047 as S47;self.assertIs(S47._api16d,ST._api)

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertIn(ST.N12BAR,(12,6))
        self.assertEqual(len(J),48+ST.N12BAR+12);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        self.assertTrue(all(IN_MAIN(j[2]) for j in J));self.assertEqual([j[1] for j in J[:12]],['compat']*12)
        self.assertEqual(sorted(j[2] for j in J if j[3]=='API16N_bar'),list(range(11950001,11950001+ST.N12BAR)))
        for j in J:ST.check_job(j,P)
        if ST.N12BAR<12:
            with self.assertRaises(Exception):ST.check_job(('main','noise12_bar',11950001+ST.N12BAR,'API16N_bar'),P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),10)
        self.assertTrue(all(12030001<=j[2]<=12030006 for j in J))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        for j in (('main','noise12',11870001,'API16N'),('smoke','noise12',11930001,'API16N'),('main','noise12',11930001,'API16E'),
                  ('main','noise12_bar',11950001,'API16N'),('main','compat',11970001,'API16N_bar'),('main','scale20',11930001,'API16N')):
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_clean_recount_and_compat(self):
        c=json.loads(json.dumps(ST.run_fresh(DEV,'compat','API16E')));c['block']='smoke';a=c['arms']['API16E']
        self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],c['N']),(C50,B12,None,12))
        out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(out['API16E']['label'],a['label'])
        c2=copy.deepcopy(c);c2['arms']['API16E']['label']='WRONG';self.assertNotEqual(recount_case(c2)[1],[])
        n=json.loads(json.dumps(ST.run_fresh(DEV,'compat','API16N_c')))['arms']['API16N_c']
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
        self.assertTrue(compat_rule(R(m,1,True),R(m2,0,True),'IDF','IDF')['equal'])   # same machine from each current state
        self.assertFalse(compat_rule(R(m,1,True),R(m2,0,False),'IDF','IDF')['equal'])
        self.assertFalse(compat_rule(R(m,0,True),R(m,0,True),'ID','IDF')['equal'])
        self.assertTrue(compat_rule(R(None,None,None),R(None,None,None),'AMB','AMB')['equal'])


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GDET52','GFID52','GN12_sound52','GCOMPAT16N52','GHOST52','GQB26','GS_ref','G_sound','G_recount','GTEST','G_RT'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('reason',G['gates'][g],g)

    def test_freeze_list(self):
        gen={'results/diag-052/PREFREEZE_SMOKE_GATES_052.json','docs/research/BRUTE_DEVIATIONS_052_177.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify16n.py','brute/api/certify16s.py','experiments/brute_study_051.py','scripts/make_gates_052.py',
                  'experiments/BRUTE_PLAN_051.json','experiments/BRUTE_PLAN_052.json','results/study-051/main/SEAL.json','results/diag-052/SEEDCHECK_052.json'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_051',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
