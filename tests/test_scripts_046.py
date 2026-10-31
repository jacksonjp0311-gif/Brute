"""Tests for the study-046 runner and scoring scripts (v0.43.0). New file; built from tests/test_scripts_045.py (frozen).
Fresh cases use an old development seed (10050003, control_cycle3), outside every study-046 range (plan, smoke)."""
import copy,json,tempfile,unittest
from pathlib import Path
from experiments import brute_study_046 as ST
from experiments.brute_common_046 import load,PLAN
from scripts.recount_046 import recount_case
from scripts import make_gates_046 as MG
from scripts import make_freeze_046 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10050003
IN_FRESH=lambda s:11230001<=s<=11230012 or 11270001<=s<=11270006
IN_REPLAY=lambda s:11130001<=s<=11130012 or 11190001<=s<=11190006


class Runner(unittest.TestCase):
    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertEqual(len(J),54);self.assertEqual(len({ST.key(j) for j in J}),54)
        R=[j for j in J if j[0]=='replay'];F=[j for j in J if j[0]=='main']
        self.assertEqual(J[:18],R);self.assertEqual(len(R),18);self.assertTrue(all(j[3]=='API16' and IN_REPLAY(j[2]) for j in R))
        self.assertEqual(len(F),36);self.assertTrue(all(IN_FRESH(j[2]) for j in F))
        self.assertEqual([j[1] for j in F[:24]],['scale16']*24);self.assertEqual([j[3] for j in F[:12]],['API16']*12)
        for j in J[::5]:ST.check_job(j,P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),16)
        self.assertTrue(all(11370001<=j[2]<=11370006 for j in J if j[0] in ('smoke','probe')))
        self.assertEqual([(j[1],j[2]) for j in J if j[0]=='sreplay'],[('scale16',11130005),('control',11190001)])
        for j in J:ST.check_job(j,P)

    def test_arm_settings(self):
        self.assertEqual(ST.ARMS,('API16','A16_N'));self.assertEqual(ST.DELTA,{'API16':None,'A16_N':None})
        self.assertEqual([ST.CAP[a] for a in ST.ARMS],[9,9]);self.assertEqual([ST.ARM_BUDGET[a] for a in ST.ARMS],[240,240])

    def test_check_job_refuses_foreign_seed(self):
        P=load(PLAN)
        with self.assertRaises(Exception):ST.check_job(('main','scale16',11130001,'API16'),P)
        with self.assertRaises(Exception):ST.check_job(('smoke','scale16',11230001,'API16'),P)
        with self.assertRaises(Exception):ST.check_job(('main','scale16',11230001,'A16_nf2'),P)

    def test_fresh_and_recount(self):
        for arm in ST.ARMS:
            c=json.loads(json.dumps(ST.run_fresh(DEV,'control',arm)));c['block']='smoke';a=c['arms'][arm]
            out,bad=recount_case(c);self.assertEqual(bad,[],arm);self.assertEqual(out[arm]['label'],'ID');self.assertEqual(a['label'],'ID')
            if arm=='API16':self.assertEqual(a['api']['api'],'brute.certify/16')
            c2=copy.deepcopy(c);c2['arms'][arm]['label']='WRONG';self.assertNotEqual(recount_case(c2)[1],[])
            c3=copy.deepcopy(c);c3['arms'][arm]['future_match']=not a['future_match'];self.assertNotEqual(recount_case(c3)[1],[])

    def test_compare_sealed(self):
        a={'label':'ID','stop':'ID','n_min':3,'model':[[[0,1,2],[1,2,0],[2,0,1]],[0,1,2]],'T_final':40,'rounds':[{'word':[0,1]}],'capped':0}
        s=copy.deepcopy(a);x=ST.compare_sealed(a,s);self.assertTrue(x['same']);self.assertTrue(x['same_step']);self.assertIsNone(x['first_word_divergence'])
        s2=copy.deepcopy(a);s2['T_final']=41;x=ST.compare_sealed(a,s2);self.assertTrue(x['same']);self.assertFalse(x['same_step'])
        s3=copy.deepcopy(a);s3['n_min']=4;self.assertFalse(ST.compare_sealed(a,s3)['same'])
        s4=copy.deepcopy(a);s4['rounds']=[{'word':[1,1]}];x=ST.compare_sealed(a,s4);self.assertTrue(x['same']);self.assertEqual(x['first_word_divergence'],0)


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GAPI16_replay','GAPI16_fresh','GAPI14_compat','GHOST16','G10','GQB21','GS_ref','G_sound','G_recount','GTI','G_RT'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('INCOMPLETE',G['gates'][g]['reason'])
            self.assertEqual(sorted(G['secondary']),['GAPI_cost','GREP16c'])

    def test_freeze_list(self):
        gen={'experiments/COMMIT_ORDER_046.json','results/diag-046/PREFREEZE_SMOKE_GATES_046.json','docs/research/BRUTE_DEVIATIONS_046_165.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify16.py','brute/api/certify14.py','brute/scalesearch16.py','experiments/brute_study_046.py','scripts/make_gates_046.py',
                  'scripts/recount_046.py','scripts/run_reference_046.py','scripts/api_checks_046.py','scripts/verify_release_0430.py',
                  'results/diag-046/CERTIFY14_SAMPLE_046.json','results/diag-046/SEEDCHECK_046.json','results/study-045/main/SEAL.json',
                  'experiments/BRUTE_SOURCE_FREEZE_045.json','experiments/BRUTE_PLAN_045.json'):self.assertIn(f,MF.FILES)
        self.assertEqual(len(MF.FILES),len(set(MF.FILES)))
        old=MF.FILES[:len(__import__('scripts.make_freeze_045',fromlist=['FILES']).FILES)]
        self.assertEqual(old,__import__('scripts.make_freeze_045',fromlist=['FILES']).FILES)


if __name__=='__main__':unittest.main()
