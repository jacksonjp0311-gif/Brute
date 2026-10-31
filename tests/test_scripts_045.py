"""Tests for the study-045 runner and scoring scripts (v0.42.0). New file; built from tests/test_scripts_044.py (frozen).
Fresh cases use an old development seed (10050003, control_cycle3), outside every study-045 range (plan, smoke); the replay
recount test reads one sealed study-041 replay record (results/study-041/main/RESULTS.json.gz, read only)."""
import copy,gzip,json,tempfile,unittest
from pathlib import Path
from experiments import brute_study_045 as ST
from experiments.brute_common_045 import load,PLAN
from scripts.recount_045 import recount_replay043,recount_case,fut_equal,n_eff
from scripts import make_gates_045 as MG
from scripts import make_freeze_045 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10050003
IN_RANGE=lambda s:11130001<=s<=11130012 or 11190001<=s<=11190006


class Runner(unittest.TestCase):
    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertEqual(len(J),54);self.assertEqual(len({ST.key(j) for j in J}),54)
        self.assertEqual([j[1] for j in J[:36]],['scale16']*36);self.assertEqual([j[3] for j in J[:12]],['A16_nf2']*12)
        self.assertEqual({k:sum(j[1]==k for j in J) for k in MG.EXP_CASES},{k:3*v for k,v in MG.EXP_CASES.items()})
        self.assertTrue(all(IN_RANGE(j[2]) for j in J))
        for j in J[::5]:ST.check_job(j,P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),24)
        self.assertTrue(all(11290001<=j[2]<=11290006 for j in J if j[0] in ('smoke','probe')))
        self.assertTrue(all(j[3]=='A16_N' for j in J if j[0]=='replay'))
        for j in J:ST.check_job(j,P)

    def test_arm_settings(self):
        self.assertEqual(ST.ARMS,('A16_N','A16_nf1','A16_nf2'));self.assertEqual(ST.DELTA,{'A16_N':None,'A16_nf1':1,'A16_nf2':2})
        self.assertEqual([ST.CAP[a] for a in ST.ARMS],[9,9,9]);self.assertEqual([ST.ARM_BUDGET[a] for a in ST.ARMS],[240,240,240])

    def test_check_job_refuses_foreign_seed(self):
        P=load(PLAN)
        with self.assertRaises(Exception):ST.check_job(('main','scale16',10930001,'A16_N'),P)
        with self.assertRaises(Exception):ST.check_job(('smoke','scale16',11130001,'A16_N'),P)
        with self.assertRaises(Exception):ST.check_job(('main','scale16',11130001,'A16'),P)

    def test_fut_equal_and_n_eff(self):
        d=[[1],[0]];self.assertTrue(fut_equal(d,[0,1],0,d,[0,1],0,1));self.assertFalse(fut_equal(d,[0,1],0,d,[0,1],1,1))
        self.assertTrue(fut_equal([[0]],[0],0,[[1],[0]],[0,0],1,1))
        self.assertEqual(n_eff('A16_N',{'n_min':3},8),8);self.assertEqual(n_eff('A16_nf2',{'n_min':3},8),5);self.assertIsNone(n_eff('A16_nf1',{'n_min':None},8))

    def test_replay_recount_041_record(self):
        res=json.load(gzip.open(ROOT/'results/study-041/main/RESULTS.json.gz'))
        r=next(x for x in res['replays'] if x['key']=='control' and x['stop']=='ID')
        out,bad=recount_replay043(r);self.assertEqual(bad,[]);self.assertEqual(out['label'],'ID')

    def test_fresh_and_recount(self):
        for arm in ST.ARMS:
            c=json.loads(json.dumps(ST.run_fresh(DEV,'control',arm)));c['block']='smoke';a=c['arms'][arm]
            out,bad=recount_case(c);self.assertEqual(bad,[],arm);self.assertEqual(out[arm]['label'],a['label'])
            if arm=='A16_N':self.assertEqual(out[arm]['label'],'ID');self.assertEqual(a['bound'],c['N'])
            else:self.assertEqual(a['bound'],a['n_min']+ST.DELTA[arm]);self.assertEqual(a['ceil'],16)
            c2=copy.deepcopy(c);c2['arms'][arm]['label']='WRONG' if a['label']!='WRONG' else 'ID';self.assertNotEqual(recount_case(c2)[1],[])
            c3=copy.deepcopy(c);c3['arms'][arm]['future_match']=not a['future_match'];self.assertNotEqual(recount_case(c3)[1],[])
            c4=copy.deepcopy(c);c4['arms'][arm]['delta']=7;self.assertIn((arm,'delta',7),recount_case(c4)[1])
            c5=copy.deepcopy(c);c5['arms'][arm]['bound']=(a['bound'] or 0)+1;self.assertNotEqual(recount_case(c5)[1],[])


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GNF_bound','GNF_agree','GNF_misfire','GLO_sem','G_sound','G10','G_recount'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('INCOMPLETE',G['gates'][g]['reason'])

    def test_freeze_list(self):
        gen={'experiments/COMMIT_ORDER_045.json','results/diag-045/PREFREEZE_SMOKE_GATES_045.json','docs/research/BRUTE_DEVIATIONS_045_163.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/nfstop18.py','brute/scalesearch16.py','experiments/brute_study_045.py','scripts/make_gates_045.py','scripts/recount_045.py',
                  'scripts/run_reference_045.py','scripts/verify_release_0420.py','scripts/check_seeds_045.py','results/diag-045/SEEDCHECK_045.json',
                  'experiments/BRUTE_SOURCE_FREEZE_044.json','experiments/BRUTE_PLAN_044.json'):self.assertIn(f,MF.FILES)
        self.assertEqual(len(MF.FILES),len(set(MF.FILES)))


if __name__=='__main__':unittest.main()
