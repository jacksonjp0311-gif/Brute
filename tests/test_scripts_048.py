"""Tests for the study-048 runner and scoring scripts (v0.45.0). New file; built from tests/test_scripts_047.py (frozen).
Fresh cases use an old development seed (10050003, control_cycle3), outside every study-048 range (plan, smoke)."""
import copy,json,tempfile,unittest
from pathlib import Path
from experiments import brute_study_048 as ST
from experiments.brute_common_048 import load,PLAN,C48,B16,B20,budget_for
from scripts.recount_047 import recount_case
from scripts import make_gates_048 as MG
from scripts import make_freeze_048 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10050003
IN_FRESH=lambda s:11510001<=s<=11510012 or 11530001<=s<=11530006 or 11610001<=s<=11610008
IN_SEALED=lambda s:11230001<=s<=11230012 or 11270001<=s<=11270006


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual((C48,B16,B20),(50000,1500000,1000000));self.assertEqual(budget_for('scale20'),B20);self.assertEqual(budget_for('control'),B16)
        from experiments import brute_study_047 as S47;self.assertEqual(S47.caps(),(50000,1500000))

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main')
        self.assertIn(ST.N20,(8,6,4,0));self.assertEqual(len(J),36+18+2*ST.N20);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        R=[j for j in J if j[0]=='r'];F=[j for j in J if j[0]=='main']
        self.assertEqual(len(R),18);self.assertTrue(all(IN_SEALED(j[2]) and j[3]=='API16D' for j in R))
        self.assertTrue(all(IN_FRESH(j[2]) for j in F));self.assertEqual(sum(j[1]=='scale20' for j in F),2*ST.N20)
        b=[j for j in F if j[3]=='API16D_b'];self.assertEqual(len(b),18+ST.N20)
        self.assertEqual([j[2] for j in b if j[1]=='scale16'],list(range(11510012,11510000,-1)))
        first_b=J.index(b[0]);self.assertTrue(all(j[3]=='API16D' for j in J[:first_b]))
        for j in J:ST.check_job(j,P)
        with self.assertRaises(Exception):ST.check_job(('main','scale20',11610001+ST.N20,'API16D'),P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),13)
        self.assertTrue(all(11590001<=j[2]<=11590006 for j in J if j[0]=='smoke'))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        for j in (('main','scale16',11130001,'API16D'),('smoke','scale16',11510001,'API16D'),('main','scale16',11510001,'A16_N'),
                  ('r','scale16',11230004,'API16D_b'),('r','scale20',11230004,'API16D')):
            with self.assertRaises(Exception):ST.check_job(j,P)

    def test_fresh_recount_and_canon(self):
        c=json.loads(json.dumps(ST.run_fresh(DEV,'control','API16D')));c['block']='smoke';a=c['arms']['API16D']
        self.assertEqual((a['conflict_cap'],a['budget_conflicts']),(C48,B16))
        out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(out['API16D']['label'],'ID');self.assertEqual(a['label'],'ID')
        c2=copy.deepcopy(c);c2['arms']['API16D']['label']='WRONG';self.assertNotEqual(recount_case(c2)[1],[])
        x=copy.deepcopy(a);x['arm_wall_informational']=99.0
        self.assertEqual(ST.canon16d(a),ST.canon16d(x));x['conflicts_spent']+=1;self.assertNotEqual(ST.canon16d(a),ST.canon16d(x))


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GDET48','GWALL_r','GFID48','GAPI16D_fresh48','GHOST48','G10','GQB23','GS_ref','G_sound','G_recount','GTI','G_RT'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('INCOMPLETE',G['gates'][g]['reason'])

    def test_freeze_list(self):
        gen={'results/diag-048/PREFREEZE_SMOKE_GATES_048.json'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify16d.py','experiments/brute_study_047.py','experiments/brute_study_048.py','scripts/make_gates_048.py',
                  'experiments/BRUTE_PLAN_047.json','results/study-047/main/SEAL.json','results/diag-048/SEEDCHECK_048.json'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_047',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
