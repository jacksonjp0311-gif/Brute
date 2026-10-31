"""Tests for the study-050 runner and scoring scripts (v0.47.0). New file; built from tests/test_scripts_049.py (frozen).
Fresh cases use an old development seed (10050003) as a clean or noisy scale12 world, outside every study-050 range (plan, smoke)."""
import copy,json,tempfile,unittest
from pathlib import Path
from experiments import brute_study_050 as ST
from experiments.brute_common_050 import load,PLAN,C50,B20,B12,budget_for,NOISE_OF
from scripts.recount_050 import recount_case,noise_check,k_rule
from scripts import make_gates_050 as MG
from scripts import make_freeze_050 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10050003
IN_MAIN=lambda s:11730001<=s<=11730024 or 11750001<=s<=11750006 or 11790001<=s<=11790012


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual((C50,B20,B12),(50000,4000000,1500000));self.assertEqual(budget_for('scale20'),B20);self.assertEqual(budget_for('noise12'),B12)
        self.assertEqual(NOISE_OF,{'API16N':(0.05,None),'API16N_b':(0.05,None),'API16N_c':(0.0,1)})
        from experiments import brute_study_047 as S47;self.assertEqual(S47.caps(),(50000,1500000));self.assertIs(S47._api16d,ST._api)

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertIn((ST.N12B,ST.N20B),((12,12),(6,12),(6,6)))
        self.assertEqual(len(J),24+ST.N20B+12+ST.N12B+12+6);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        self.assertTrue(all(IN_MAIN(j[2]) for j in J));self.assertEqual(sum(j[0]=='c' for j in J),6)
        self.assertEqual(sorted(j[2] for j in J if j[3]=='API16E_b' and j[1]=='scale20'),list(range(11730001,11730001+ST.N20B)))
        for j in J:ST.check_job(j,P)
        with self.assertRaises(Exception):ST.check_job(('main','noise12',11790001+ST.N12B,'API16N_b'),P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),14)
        self.assertTrue(all(11810001<=j[2]<=11810006 for j in J))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        for j in (('main','scale20',11670001,'API16E'),('smoke','scale20',11730001,'API16E'),('main','scale20',11730001,'API16N'),
                  ('main','noise12',11790001,'API16E'),('c','scale20',11730001,'API16N_c'),('main','control',11750001,'API16N_c')):
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_clean_recount_and_canon(self):
        c=json.loads(json.dumps(ST.run_fresh(DEV,'control','API16E')));c['block']='smoke';a=c['arms']['API16E']
        self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],c['N']),(C50,B12,None,12))
        out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(out['API16E']['label'],a['label'])
        c2=copy.deepcopy(c);c2['arms']['API16E']['label']='WRONG';self.assertNotEqual(recount_case(c2)[1],[])
        x=copy.deepcopy(a);x['arm_wall_informational']=99.0;x['rounds'][0]['chunk_walls_informational']=[[9.0]]
        self.assertEqual(ST.canon16e(a),ST.canon16e(x));x['rounds'][0]['chunk_conflicts']=[[1,2]];self.assertNotEqual(ST.canon16e(a),ST.canon16e(x))

    def test_noise_record_and_compat(self):
        n=json.loads(json.dumps(ST.run_fresh(DEV,'noise12','API16N')));a=n['arms']['API16N']
        self.assertEqual(a['majority_errors'],0);self.assertGreater(a['bits_flipped'],0);self.assertEqual(a['reads_per_obs'][0],27)
        out,bad=recount_case(n);self.assertEqual(bad,[]);x,b2=noise_check(n,'API16N',a);self.assertEqual((b2,x['majority_errors']),([],0))
        y=copy.deepcopy(a);y['votes'][3]=[0,0];self.assertNotEqual(noise_check(n,'API16N',y)[1],[])
        y=copy.deepcopy(a);y['votes'][1]=[1,1];self.assertEqual(ST.canon16e(a),ST.canon16e(y));self.assertNotEqual(ST.canon16n(a),ST.canon16n(y))
        e=ST.run_fresh(DEV,'control','API16E')['arms']['API16E'];c=ST.run_fresh(DEV,'control','API16N_c')['arms']['API16N_c']
        self.assertEqual(ST.canon16e(e),ST.canon16e(c));self.assertEqual(k_rule(1000,None),69);self.assertEqual(k_rule(5,1),1)


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GDET50','GFID50','GS20_sound50','GN12_sound','GCOMPAT16N','GHOST50','G10','GQB25','GS_ref','G_sound','G_recount','GTEST','G_RT'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('reason',G['gates'][g],g)

    def test_freeze_list(self):
        gen={'results/diag-050/PREFREEZE_SMOKE_GATES_050.json','docs/research/BRUTE_DEVIATIONS_050_173.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify16n.py','brute/api/certify16e.py','experiments/worlds_050.py','experiments/brute_study_049.py','scripts/make_gates_050.py',
                  'experiments/BRUTE_PLAN_049.json','results/study-049/main/SEAL.json','results/diag-050/SEEDCHECK_050.json'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_049',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
