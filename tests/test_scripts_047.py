"""Tests for the study-047 runner and scoring scripts (v0.44.0). New file; built from tests/test_scripts_046.py (frozen).
Fresh cases use an old development seed (10050003, control_cycle3), outside every study-047 range (plan, smoke)."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest import mock
from experiments import brute_study_047 as ST
from experiments.brute_common_047 import load,PLAN,caps
from scripts.recount_047 import recount_case
from scripts import make_gates_047 as MG
from scripts import make_freeze_047 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10050003
IN_FRESH=lambda s:11430001<=s<=11430012 or 11470001<=s<=11470006
IN_SEALED=lambda s:11130001<=s<=11130012 or 11190001<=s<=11190006 or 11230001<=s<=11230012 or 11270001<=s<=11270006


class Runner(unittest.TestCase):
    def test_jobs_main_cut(self):
        # #167: the declared cut rule fired (worst case 4836 s > 3600 s), so part d (scale20) is not in the job list
        P=load(PLAN);self.assertTrue(ST.CUT_D);J=ST.jobs_for(P,'main');self.assertEqual(len(J),126);self.assertEqual(len({ST.key(j) for j in J}),126)
        R=[j for j in J if j[0] in ST.REPLAY_PARTS];F=[j for j in J if j[0]=='main']
        self.assertEqual(J[:72],R);self.assertTrue(all(IN_SEALED(j[2]) and j[3]==ST.REPLAY_PARTS[j[0]][1] for j in R))
        self.assertEqual(len(F),54);self.assertTrue(all(IN_FRESH(j[2]) for j in F));self.assertNotIn('scale20',{j[1] for j in J})
        b=[j for j in F if j[3]=='API16D_b'];self.assertEqual(len(b),18);self.assertEqual([j[2] for j in b if j[1]=='scale16'],list(range(11430012,11430000,-1)))
        for j in J[::7]:ST.check_job(j,P)
        with self.assertRaises(Exception):ST.check_job(('main','scale20',11490001,'API16D'),P)

    def test_jobs_main_uncut(self):
        P=load(PLAN)
        with mock.patch.object(ST,'CUT_D',False):J=ST.jobs_for(P,'main')
        self.assertEqual(len(J),138);self.assertEqual(sum(j[1]=='scale20' for j in J),12)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),26)
        self.assertTrue(all(11570001<=j[2]<=11570006 for j in J if j[0] in ('smoke','probe')))
        for j in J:ST.check_job(j,P)

    def test_arm_settings(self):
        self.assertEqual(ST.ARMS,('API16D','API16D_b','A16_N','API16'));self.assertEqual(ST.D_ARMS,('API16D','API16D_b'))
        self.assertEqual((ST.CAP_S,ST.BUDGET_S,ST.GUARD_CASE_S,ST.GUARD_CALL_S),(9.0,240.0,600.0,30.0));self.assertEqual(caps(),(294000,7840000))

    def test_check_job_refuses_foreign_seed(self):
        P=load(PLAN)
        with self.assertRaises(Exception):ST.check_job(('main','scale16',11130001,'API16D'),P)
        with self.assertRaises(Exception):ST.check_job(('smoke','scale16',11430001,'API16D'),P)
        with self.assertRaises(Exception):ST.check_job(('main','scale16',11430001,'A16_nf2'),P)

    def test_fresh_recount_and_canon(self):
        for arm in ('API16D','A16_N'):
            c=json.loads(json.dumps(ST.run_fresh(DEV,'control',arm)));c['block']='smoke';a=c['arms'][arm]
            out,bad=recount_case(c);self.assertEqual(bad,[],arm);self.assertEqual(out[arm]['label'],'ID');self.assertEqual(a['label'],'ID')
            c2=copy.deepcopy(c);c2['arms'][arm]['label']='WRONG';self.assertNotEqual(recount_case(c2)[1],[])
            if arm=='API16D':d=a
        a=d;x=copy.deepcopy(a);x['arm_wall_informational']=99.0
        for r in x['rounds']:r['query_walls']=[1.0]
        self.assertEqual(ST.canon16d(a),ST.canon16d(x));x['conflicts_spent']+=1;self.assertNotEqual(ST.canon16d(a),ST.canon16d(x))

    def test_classify(self):
        cap=lambda n:{'capped':n};same={'same':True,'words_equal':True}
        self.assertEqual(ST.classify(same,cap(1),cap(0)),'none')
        self.assertEqual(ST.classify({'same':False,'words_equal':True},cap(0),cap(0)),'infidelity')
        self.assertEqual(ST.classify({'same':True,'words_equal':False},cap(0),cap(0)),'infidelity')
        self.assertEqual(ST.classify({'same':False,'words_equal':True},cap(2),cap(0)),'cap-timing')
        self.assertEqual(ST.classify({'same':False,'words_equal':False},cap(0),cap(1)),'word-divergence')


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GDET','GFID16D','GFID_wall','GAPI16D_fresh','GAPI16_compat','GHOST16D','G10','GQB22','GS_ref','G_sound','G_recount','GTI','G_RT'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('INCOMPLETE',G['gates'][g]['reason'])

    def test_freeze_list(self):
        gen={'experiments/COMMIT_ORDER_047.json','results/diag-047/PREFREEZE_SMOKE_GATES_047.json','docs/research/BRUTE_DEVIATIONS_047_167.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify16d.py','brute/api/certify16.py','experiments/brute_study_047.py','experiments/host_hook_047.py','scripts/make_gates_047.py',
                  'scripts/recount_047.py','scripts/run_reference_047.py','scripts/api_checks_047.py','scripts/verify_release_0440.py',
                  'results/diag-047/CAP_CALIBRATION_047.json','results/diag-047/SEEDCHECK_047.json','results/study-046/main/SEAL.json',
                  'experiments/BRUTE_SOURCE_FREEZE_046.json','experiments/BRUTE_PLAN_046.json'):self.assertIn(f,MF.FILES)
        self.assertEqual(len(MF.FILES),len(set(MF.FILES)))
        old=__import__('scripts.make_freeze_046',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
