"""Tests for the study-044 runner and scoring scripts (v0.41.0). New file; built from tests/test_scripts_043.py (frozen).
Fresh cases use an old development seed (10050003, control_cycle3), outside every study-044 range (plan, smoke); the replay
recount test reads one sealed study-041 replay record (results/study-041/main/RESULTS.json.gz, read only)."""
import copy,gzip,json,tempfile,unittest
from pathlib import Path
from unittest import mock
from experiments import brute_study_044 as ST
from experiments.brute_common_044 import load,PLAN
from scripts.recount_044 import recount_replay043,recount_case,schedule
from scripts import make_gates_044 as MG
from scripts import make_freeze_044 as MF
from brute.lowobspolicy17 import xf_schedule
ROOT=Path(__file__).resolve().parents[1];DEV=10050003
IN_RANGE=lambda s:10930001<=s<=10930012 or 10970001<=s<=10970006


class Runner(unittest.TestCase):
    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertEqual(len(J),54);self.assertEqual(len({ST.key(j) for j in J}),54)
        self.assertEqual([j[1] for j in J[:36]],['lowobs12']*36);self.assertEqual([j[3] for j in J[:12]],['A16_c30']*12)
        self.assertEqual({k:sum(j[1]==k for j in J) for k in MG.EXP_CASES},{k:3*v for k,v in MG.EXP_CASES.items()})
        self.assertTrue(all(IN_RANGE(j[2]) for j in J))
        for j in J[::5]:ST.check_job(j,P)

    def test_jobs_main_cut(self):
        P=load(PLAN)
        with mock.patch.object(ST,'CUT_C30',True):J=ST.jobs_for(P,'main')
        c30=[j[2] for j in J if j[3]=='A16_c30' and j[1]=='lowobs12'];self.assertEqual(c30,list(range(10930001,10930009)))
        self.assertEqual(len(J),50);self.assertEqual(sum(j[3]=='A16_c30' and j[1]=='control' for j in J),6)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),24)
        self.assertTrue(all(10990001<=j[2]<=10990006 for j in J if j[0] in ('smoke','probe')))
        for j in J:ST.check_job(j,P)

    def test_arm_settings(self):
        self.assertEqual(ST.ARMS,('A16_c9','A16_c30','A16_xf'))
        self.assertEqual([ST.CAP[a] for a in ST.ARMS],[9,30,9]);self.assertEqual([ST.ARM_BUDGET[a] for a in ST.ARMS],[240,600,240])

    def test_check_job_refuses_foreign_seed(self):
        P=load(PLAN)
        with self.assertRaises(Exception):ST.check_job(('main','lowobs12',10910001,'A16_c9'),P)
        with self.assertRaises(Exception):ST.check_job(('smoke','lowobs12',10930001,'A16_c9'),P)
        with self.assertRaises(Exception):ST.check_job(('main','lowobs12',10930001,'A16'),P)

    def test_recount_schedule_independent(self):
        for k in (2,3):
            for s in (1,DEV):self.assertEqual(schedule(k,s),xf_schedule(k,32,s))

    def test_replay_recount_041_record(self):
        res=json.load(gzip.open(ROOT/'results/study-041/main/RESULTS.json.gz'))
        r=next(x for x in res['replays'] if x['key']=='control' and x['stop']=='ID')
        out,bad=recount_replay043(r);self.assertEqual(bad,[]);self.assertEqual(out['label'],'ID')

    def test_fresh_and_recount(self):
        c=None
        for arm in ST.ARMS:
            c=json.loads(json.dumps(ST.run_fresh(DEV,'control',arm)));c['block']='smoke'
            out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(out[arm]['label'],'ID')
            c2=copy.deepcopy(c);c2['arms'][arm]['label']='IDF';self.assertNotEqual(recount_case(c2)[1],[])
        x=c['arms']['A16_xf'];self.assertEqual(x['xf_used'],32);self.assertEqual(x['xf_actions'],schedule(c['k'],DEV))
        c3=copy.deepcopy(c);c3['arms']['A16_xf']['xf_used']=31;self.assertIn(('A16_xf','xf_short',31),recount_case(c3)[1])
        c4=copy.deepcopy(c);e=c4['arms']['A16_xf']['extra_acts'];e[0]=(e[0]+1)%c['k'];self.assertIn(('A16_xf','xf_schedule'),recount_case(c4)[1])


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GLO_cap','GLO_pol','GLO_sem','GQB19','G_sound','G10','G_recount'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('INCOMPLETE',G['gates'][g]['reason'])

    def test_freeze_list(self):
        gen={'experiments/COMMIT_ORDER_044.json','results/diag-044/PREFREEZE_SMOKE_GATES_044.json','docs/research/BRUTE_DEVIATIONS_044_161.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/lowobspolicy17.py','brute/scalesearch16.py','experiments/brute_study_044.py','scripts/make_gates_044.py','scripts/recount_044.py',
                  'scripts/run_reference_044.py','scripts/verify_release_0410.py','scripts/check_seeds_044b.py','results/diag-044/SEEDCHECK_044B.json',
                  'results/diag-044/SEEDCHECK_044.json','experiments/BRUTE_SOURCE_FREEZE_043.json'):self.assertIn(f,MF.FILES)
        self.assertEqual(len(MF.FILES),len(set(MF.FILES)))


if __name__=='__main__':unittest.main()
