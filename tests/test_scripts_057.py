"""Tests for the study-057 runner and scoring scripts (v0.54.0). New file; built from tests/test_scripts_056.py (frozen).
Fresh cases use an old development seed (10051001) as a scale20 world (N 20), outside every study-057 range (plan, smoke), with the
caps lowered in-process for speed (the study caps are checked separately)."""
import copy,json,random,tempfile,unittest
from pathlib import Path
from unittest import mock
from experiments import brute_study_057 as ST
from experiments.brute_common_057 import load,PLAN,C20,B20,WORKERS,ALL_ARMS,COVER,LEN_RNG
from experiments import worlds_050 as W50
from experiments.brute_study_033 import StepWorld,passive
from scripts.recount_057 import recount_case,coverage_case,oracle
from scripts import make_gates_057 as MG
from scripts import make_freeze_057 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10051001
IN_MAIN=lambda s:12410001<=s<=12410012


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual((C20,B20,WORKERS),(50000,2000000,8));self.assertEqual(ALL_ARMS,('API16E20','COV_O','LEN_R','COV_X','COV_X_b'))
        self.assertEqual(COVER,{'h':1,'steps':120,'api':'brute.cover20/1'});self.assertEqual(LEN_RNG,'random.Random(seed*7+57).randrange(k)')

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertIn(ST.N57,(12,8))
        self.assertEqual(len(J),5*ST.N57);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        self.assertTrue(all(IN_MAIN(j[2]) for j in J))
        self.assertEqual([j[3] for j in J[:4]],['COV_O','LEN_R','API16E20','COV_X'])
        b=[j[2] for j in J if j[3]=='COV_X_b'];self.assertEqual(b,sorted(b,reverse=True))
        for j in J:ST.check_job(j,P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),10)
        self.assertTrue(all(12430001<=j[2]<=12430002 for j in J))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        for j in (('main','scale20v',12330001,'COV_X'),('smoke','scale20v',12410001,'COV_X'),('main','scale20v',12410001,'API20L'),
                  ('main','scale20t',12410001,'COV_X'),('main','scale20v',12410013,'COV_X')):
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_oracle_and_length_control(self):
        w=W50.world(DEV,'scale20');_,acts,_=passive(StepWorld(w),DEV);e=ST.oracle_walk(w,acts)
        self.assertEqual(ST.coverage(w,acts+e)[1],0);self.assertEqual(e,oracle(w,acts))
        r=random.Random(DEV*7+57);self.assertEqual(ST.len_control(DEV,len(e),3),[r.randrange(3) for _ in e])

    def test_clean_recount_small_caps(self):
        with mock.patch.object(ST,'C20',2000),mock.patch.object(ST,'B20',20000):
            c=json.loads(json.dumps(ST.run_fresh(DEV,'COV_X')));o=json.loads(json.dumps(ST.run_fresh(DEV,'COV_O')))
        c['block']='smoke';c['arms'].update(o['arms']);a=c['arms']['COV_X']
        self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],c['N'],a['ext_len']),(2000,20000,None,20,120))
        self.assertEqual(a['extra_acts'][:120],a['ext_acts']);self.assertEqual(a['hook_arms'],0);self.assertEqual(a['api']['api'],'brute.certify/16e')
        self.assertEqual(o['arms']['COV_O']['truth_pairs_unexercised_handoff_reachable'],0)
        out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertTrue(out['COV_X']['used_ok_057'])
        cv,b2=coverage_case(c);self.assertEqual(b2,[]);self.assertTrue(cv['COV_O']['ext_ok'])
        c2=copy.deepcopy(c);c2['arms']['COV_X']['label']='WRONG';self.assertNotEqual(recount_case(c2)[1],[])
        c3=copy.deepcopy(c);c3['arms']['COV_O']['ext_acts'][0]^=1;self.assertNotEqual(coverage_case(c3)[1],[])
        self.assertEqual(ST.canon57(c['arms']['COV_X']),ST.canon57(copy.deepcopy(c['arms']['COV_X'])))


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GS57_sound','GMATCH57','GPRE57','GX_gain57','GDET57','GFID57','GHOST57','GS_ref','G_sound','G_recount','GTI57','GTEST','G_RT'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('reason',G['gates'][g],g)
            self.assertFalse(G['certified_20v_N20']);self.assertFalse(G['sound_not_certified_20v'])
            self.assertTrue(G['status_phrase'].startswith('not certified, no certification status'))

    def test_mcnemar(self):
        self.assertEqual(MG.mcnemar(0,0),1.0);self.assertAlmostEqual(MG.mcnemar(3,0),0.25);self.assertAlmostEqual(MG.mcnemar(5,0),0.0625)

    def test_freeze_list(self):
        gen={'results/diag-057/PREFREEZE_SMOKE_GATES_057.json','docs/research/BRUTE_DEVIATIONS_057_188.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/cover20.py','brute/api/certify16e.py','experiments/brute_study_057.py','scripts/make_gates_057.py',
                  'experiments/BRUTE_PLAN_057.json','results/diag-057/SEEDCHECK_057.json','results/study-056/GATES_056.json',
                  'tests/test_scripts_057.py','tests/test_release_0540.py','tests/test_cover20.py'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_056',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
