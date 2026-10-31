"""Tests for the study-051 runner and scoring scripts (v0.48.0). New file; built from tests/test_scripts_050.py (frozen).
Fresh cases use an old development seed (10050003) as a clean scale12 world, outside every study-051 range (plan, smoke)."""
import copy,json,tempfile,unittest
from pathlib import Path
from experiments import brute_study_051 as ST
from experiments.brute_common_051 import load,PLAN,C20,B20,C50,B12,B12N,caps_for,NOISE_OF,WORKERS_A,WORKERS_B
from scripts.recount_051 import recount_case,bfs_form
from scripts import make_gates_051 as MG
from scripts import make_freeze_051 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10050003
IN_MAIN=lambda s:11830001<=s<=11830012 or 11850001<=s<=11850006 or 11870001<=s<=11870012


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual((C20,B20,C50,B12,B12N),(12000,2000000,50000,3000000,1500000))
        self.assertEqual([caps_for(k) for k in ('scale20','control','noise12')],[(C20,B20),(C50,B12),(C50,B12N)])
        self.assertEqual(NOISE_OF,{'API16N':(0.05,None),'API16N_b':(0.05,None)});self.assertEqual((WORKERS_A,WORKERS_B),(4,8))
        from experiments import brute_study_047 as S47;self.assertIs(S47._api16d,ST._api)

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertIn((ST.N12B,ST.NCOMPAT),((12,6),(6,6),(6,3)))
        self.assertEqual(len(J),24+12+ST.NCOMPAT+12+ST.N12B);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        self.assertTrue(all(IN_MAIN(j[2]) for j in J));self.assertEqual(sum(j[0]=='c' for j in J),ST.NCOMPAT)
        self.assertEqual(sum(ST.phase_of(j)=='A' for j in J),24);self.assertTrue(all(j[1]=='scale20' for j in J if ST.phase_of(j)=='A'))
        self.assertEqual(sorted(j[2] for j in J if j[3]=='API16N_b'),list(range(11870001,11870001+ST.N12B)))
        for j in J:ST.check_job(j,P)
        if ST.N12B<12:
            with self.assertRaises(Exception):ST.check_job(('main','noise12',11870001+ST.N12B,'API16N_b'),P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),14)
        self.assertTrue(all(11890001<=j[2]<=11890006 for j in J))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        for j in (('main','scale20',11730001,'API16S'),('smoke','scale20',11830001,'API16S'),('main','scale20',11830001,'API16E'),
                  ('main','noise12',11870001,'API16S'),('c','scale20',11830001,'API16S_c'),('main','control',11850001,'API16S_c')):
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_clean_recount_canon_and_compat(self):
        c=json.loads(json.dumps(ST.run_fresh(DEV,'control','API16E')));c['block']='smoke';a=c['arms']['API16E']
        self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],c['N']),(C50,B12,None,12))
        out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(out['API16E']['label'],a['label'])
        c2=copy.deepcopy(c);c2['arms']['API16E']['label']='WRONG';self.assertNotEqual(recount_case(c2)[1],[])
        s=json.loads(json.dumps(ST.run_fresh(DEV,'control','API16S_c')));b=s['arms']['API16S_c']
        self.assertEqual(b['encoding'],'a16d+unvisited_bfs_v1');self.assertGreaterEqual(b['sym_clauses'],0);self.assertEqual(b['label'],a['label'])
        if a['label'] in ('ID','IDF'):self.assertEqual(bfs_form(a['model']),bfs_form(b['model']))
        x=copy.deepcopy(b);x['arm_wall_informational']=99.0;self.assertEqual(ST.canon16s(b),ST.canon16s(x))
        x['sym_clauses']=b['sym_clauses']+1;self.assertNotEqual(ST.canon16s(b),ST.canon16s(x))

    def test_bfs_form_renaming_free(self):
        d=[[1,2],[0,2],[2,1]];e=[0,1,1];p=[0,2,1]   # swap states 1 and 2
        d2=[[0]*2 for _ in d];e2=[0]*3
        for q in range(3):
            e2[p[q]]=e[q]
            for a in range(2):d2[p[q]][a]=p[d[q][a]]
        self.assertEqual(bfs_form([d,e]),bfs_form([d2,e2]));self.assertNotEqual(bfs_form([d,e]),bfs_form([d,[0,1,0]]))


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GDET51','GFID51','GS20_sound51','GN12_sound51','GCOMPAT16S','GHOST51','G10','GQB25','GS_ref','G_sound','G_recount','GTEST','G_RT'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('reason',G['gates'][g],g)

    def test_freeze_list(self):
        gen={'results/diag-051/PREFREEZE_SMOKE_GATES_051.json','docs/research/BRUTE_DEVIATIONS_051_175.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify16s.py','brute/api/certify16n.py','experiments/brute_study_050.py','scripts/make_gates_051.py',
                  'experiments/BRUTE_PLAN_050.json','results/study-050/main/SEAL.json','results/diag-051/SEEDCHECK_051.json'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_050',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
