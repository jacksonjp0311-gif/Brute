"""Tests for the study-049 runner and scoring scripts (v0.46.0). New file; built from tests/test_scripts_048.py (frozen).
Fresh cases use an old development seed (10050003, control_cycle3), outside every study-049 range (plan, smoke)."""
import copy,json,tempfile,unittest
from pathlib import Path
from experiments import brute_study_049 as ST
from experiments.brute_common_049 import load,PLAN,C49,B16,B20,budget_for,MAX_CHUNKS
from scripts.recount_049 import recount_case
from scripts import make_gates_049 as MG
from scripts import make_freeze_049 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10050003
IN_FRESH=lambda s:11630001<=s<=11630012 or 11650001<=s<=11650006 or 11670001<=s<=11670008
IN_SEALED=lambda s:11510001<=s<=11510012 or 11530001<=s<=11530006 or 11610001<=s<=11610008


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual((C49,B16,B20),(50000,1500000,1000000));self.assertEqual(budget_for('scale20'),B20);self.assertEqual(budget_for('control'),B16)
        self.assertEqual(MAX_CHUNKS,{'API16E':None,'API16E_b':None,'API16E_c1':1})
        from experiments import brute_study_047 as S47;self.assertEqual(S47.caps(),(50000,1500000));self.assertIs(S47._api16d,ST._api16e)

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertIn((ST.R20,ST.N20),((True,8),(False,8),(False,6),(False,4),(False,0)))
        nr=26 if ST.R20 else 18;self.assertEqual(len(J),36+2*ST.N20+nr+26);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        R=[j for j in J if j[0]=='r'];Cc=[j for j in J if j[0]=='c'];F=[j for j in J if j[0]=='main']
        self.assertEqual(len(R),nr);self.assertTrue(all(IN_SEALED(j[2]) and j[3]=='API16E' for j in R))
        self.assertEqual(len(Cc),26);self.assertTrue(all(IN_SEALED(j[2]) and j[3]=='API16E_c1' for j in Cc))
        self.assertTrue(all(IN_FRESH(j[2]) for j in F));self.assertEqual(sum(j[1]=='scale20' for j in F),2*ST.N20)
        b=[j for j in F if j[3]=='API16E_b'];self.assertEqual(len(b),18+ST.N20)
        self.assertEqual([j[2] for j in b if j[1]=='scale16'],list(range(11630012,11630000,-1)))
        for j in J:ST.check_job(j,P)
        with self.assertRaises(Exception):ST.check_job(('main','scale20',11670001+ST.N20,'API16E'),P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),16)
        self.assertTrue(all(11690001<=j[2]<=11690006 for j in J if j[0]=='smoke'))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        for j in (('main','scale16',11510001,'API16E'),('smoke','scale16',11630001,'API16E'),('main','scale16',11630001,'API16D'),
                  ('r','scale16',11510002,'API16E_b'),('c','scale16',11510002,'API16E'),('r','scale16',11230004,'API16E'),('main','scale16',11630001,'API16E_c1')):
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_fresh_recount_and_canon(self):
        c=json.loads(json.dumps(ST.run_arm(DEV,'control','API16E')));c['block']='smoke';a=c['arms']['API16E']
        self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks']),(C49,B16,None))
        for k in ('chunks_total','chunk_wall_max','case_wall_informational','calls_total'):self.assertIn(k,a)
        out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(out['API16E']['label'],'ID');self.assertEqual(a['label'],'ID')
        c2=copy.deepcopy(c);c2['arms']['API16E']['label']='WRONG';self.assertNotEqual(recount_case(c2)[1],[])
        x=copy.deepcopy(a);x['arm_wall_informational']=99.0;x['rounds'][0]['chunk_walls_informational']=[[9.0]]
        self.assertEqual(ST.canon16e(a),ST.canon16e(x));x['rounds'][0]['chunk_conflicts']=[[1,2]];self.assertNotEqual(ST.canon16e(a),ST.canon16e(x))
        self.assertEqual(ST.canon16d(a),ST.canon16d(x))


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GDET49','GFID49','GCOMPAT16D','GAPI16E_fresh49','GR49_sound','GHOST49','G10','GQB24','GS_ref','G_sound','G_recount','GTI','G_RT'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('reason',G['gates'][g],g)

    def test_freeze_list(self):
        gen={'results/diag-049/PREFREEZE_SMOKE_GATES_049.json','docs/research/BRUTE_DEVIATIONS_049_171.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify16e.py','brute/api/certify16d.py','experiments/brute_study_048.py','experiments/brute_study_049.py','scripts/make_gates_049.py',
                  'experiments/BRUTE_PLAN_048.json','results/study-048/main/SEAL.json','results/diag-049/SEEDCHECK_049.json'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_048',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
