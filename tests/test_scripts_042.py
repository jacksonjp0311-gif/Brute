"""Tests for the study-042 runner and scoring scripts (v0.39.0). New file; built from tests/test_scripts_041.py (frozen).
Fresh cases use an old development seed (10050001, control_cycle3), outside every study-042 range (plan, smoke); the replay
recount test reads one sealed study-041 replay record (results/study-041/main/RESULTS.json.gz, read only)."""
import copy,gzip,json,tempfile,unittest
from pathlib import Path
from experiments import brute_study_042 as ST
from experiments.brute_common_042 import load,PLAN
from scripts.recount_042 import recount_replay042,recount_case,amb_ok
from scripts import make_gates_042 as MG
from scripts import make_freeze_042 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10050001


class Runner(unittest.TestCase):
    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertEqual(len(J),60);self.assertEqual(len({ST.key(j) for j in J}),60)
        self.assertEqual([j[1] for j in J[:24]],['scale16']*24)
        self.assertEqual({k:sum(j[1]==k for j in J) for k in MG.EXP_CASES},{k:2*v for k,v in MG.EXP_CASES.items()})
        self.assertTrue(all(10810001<=j[2]<=10810012 or 10820001<=j[2]<=10820012 or 10860001<=j[2]<=10860006 for j in J))
        for j in J[::7]:ST.check_job(j,P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),24)
        self.assertTrue(all(10880001<=j[2]<=10880006 for j in J if j[0] in ('smoke','probe')))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign_seed(self):
        P=load(PLAN)
        with self.assertRaises(Exception):ST.check_job(('main','perm12',10710001,'A16'),P)
        with self.assertRaises(Exception):ST.check_job(('smoke','perm12',10810001,'A16'),P)
        with self.assertRaises(Exception):ST.check_job(('main','scale16',10810001,'A15'),P)

    def test_replay_recount_041_record(self):
        res=json.load(gzip.open(ROOT/'results/study-041/main/RESULTS.json.gz'))
        r=next(x for x in res['replays'] if x['key']=='control' and x['stop']=='ID')
        out,bad=recount_replay042(r);self.assertEqual(bad,[]);self.assertEqual(out['label'],'ID')
        r2=copy.deepcopy(r);r2['n_min']=(r2['n_min'] or 0)-1;self.assertNotEqual(recount_replay042(r2)[1],[])

    def test_fresh_and_recount(self):
        for arm in ST.ARMS:
            c=json.loads(json.dumps(ST.run_fresh(DEV,'control',arm)));c['block']='smoke'
            out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(out[arm]['label'],'ID')
            c2=copy.deepcopy(c);c2['arms'][arm]['label']='IDF';self.assertNotEqual(recount_case(c2)[1],[])

    def test_amb_rule_refuses_missing_future(self):
        self.assertEqual(amb_ok([0],[0,0],2,3,None,0,None),(False,'future_not_ending_SAT'))
        self.assertFalse(amb_ok([0],[0,0],2,3,([[0,0]],[0]),0,{'verdicts':[[2,'UNSAT']]})[0])


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('G16','G16_sem','GPERM17','GQB17','G_sound','G10','GS_ref','G_recount'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('INCOMPLETE',G['gates'][g]['reason'])

    def test_boot_seeded(self):
        self.assertEqual(MG.boot([1.0,2.0,3.0]),MG.boot([1.0,2.0,3.0]));self.assertIsNone(MG.boot([]))
        self.assertEqual(list(MG.boot([1.5]*5)),[1.5,1.5])

    def test_freeze_list(self):
        gen={'experiments/COMMIT_ORDER_042.json','results/diag-042/PREFREEZE_SMOKE_GATES_042.json','docs/research/BRUTE_DEVIATIONS_042_157.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/scalesearch16.py','brute/encaudit16.py','experiments/brute_study_042.py','experiments/solver_proxy_041.py',
                  'scripts/make_gates_042.py','scripts/recount_042.py','scripts/run_reference_042.py','scripts/verify_release_0390.py'):self.assertIn(f,MF.FILES)
        self.assertEqual(len(MF.FILES),len(set(MF.FILES)))


if __name__=='__main__':unittest.main()
