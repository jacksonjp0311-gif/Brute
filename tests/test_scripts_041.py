"""Tests for the study-041 runner and scoring scripts (v0.38.0). New file; built from tests/test_scripts_040.py (frozen).
Replays use a sealed study-039 control trace (part a); fresh cases use an old development seed (10050001, control_cycle3),
outside every study-041 range (plan, smoke)."""
import copy,json,tempfile,unittest
from pathlib import Path
from experiments import brute_study_041 as ST
from experiments.brute_common_041 import load,PLAN
from scripts.recount_041 import recount_replay,recount_case
from scripts import make_gates_041 as MG
from scripts import make_freeze_041 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10050001


class Runner(unittest.TestCase):
    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertEqual(len(J),294);self.assertEqual(len({ST.key(j) for j in J}),294)
        parts=[j[1] for j in J if j[0]=='replay'];self.assertEqual({p:parts.count(p) for p in 'abc'},MG.EXP_REPLAYS)
        self.assertEqual(parts[0],'c');self.assertEqual(parts[-1],'a')
        fr=[j for j in J if j[0]=='main'];self.assertEqual(len(fr),54)
        self.assertTrue(all(10710001<=j[2]<=10710012 or 10760001<=j[2]<=10760006 for j in fr))
        for j in J[::23]:ST.check_job(j,P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),28)
        self.assertTrue(all(10780001<=j[2]<=10780006 for j in J if j[0]=='smoke'))

    def test_check_job_refuses_foreign_seed(self):
        P=load(PLAN)
        with self.assertRaises(Exception):ST.check_job(('main','perm12',10540007,'A15'),P)
        with self.assertRaises(Exception):ST.check_job(('smoke','perm12',10710001,'A15'),P)
        with self.assertRaises(Exception):ST.check_job(('replay','a','039','perm12',10710001,'E1',0),P)

    def test_replay_and_recount(self):
        st,k,s=[x for x in ST.part_a() if x[1]=='control'][0];r=json.loads(json.dumps(ST.replay(st,k,s,'E1',0)));r['part']='a'
        self.assertEqual(r['sealed'][0],r['stop']);out,bad=recount_replay(r);self.assertEqual(bad,[]);self.assertEqual(out['label'],'ID')
        r2=copy.deepcopy(r);r2['n_min']=(r2['n_min'] or 0)-1;self.assertNotEqual(recount_replay(r2)[1],[])
        r3=copy.deepcopy(r);r3['calls']=r3['calls'][1:];self.assertNotEqual(recount_replay(r3)[1],[])

    def test_fresh_and_recount(self):
        c=json.loads(json.dumps(ST.run_fresh(DEV,'control','A15')));c['block']='smoke'
        out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(out['A15']['label'],'ID')
        c2=copy.deepcopy(c);c2['arms']['A15']['label']='IDF';self.assertNotEqual(recount_case(c2)[1],[])


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GAUD_sem','GAUD_loc','GAUD_time','GAUD_stab','GPERM16','GQB16'):
                self.assertFalse(G['gates'][g]['pass']);self.assertIn('INCOMPLETE',G['gates'][g]['reason'])

    def test_boot_seeded(self):
        self.assertEqual(MG.boot([1.0,2.0,3.0]),MG.boot([1.0,2.0,3.0]));self.assertIsNone(MG.boot([]))
        lo,hi=MG.boot([1.5]*5);self.assertEqual((lo,hi),(1.5,1.5))

    def test_freeze_list(self):
        gen={'experiments/COMMIT_ORDER_041.json','results/diag-041/PREFREEZE_SMOKE_GATES_041.json','docs/research/BRUTE_DEVIATIONS_041_154.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/encaudit16.py','brute/scalesearch15.py','experiments/brute_study_041.py','experiments/solver_proxy_041.py',
                  'scripts/make_gates_041.py','scripts/recount_041.py','scripts/run_reference_041.py'):self.assertIn(f,MF.FILES)


if __name__=='__main__':unittest.main()
