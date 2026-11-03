"""Tests for the study-065 runner and scoring scripts (v0.62.0). New file; built from tests/test_scripts_064.py (frozen).
The study caps are checked as constants; fresh cases use an old development seed (10051001), outside every study-065 range, with
the caps lowered in-process for speed."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest import mock
from experiments import brute_study_065 as ST
from experiments.brute_common_065 import (load,PLAN,C65,B65,K65,WORKERS,ALL_ARMS,NOISY,ARM_NOISE,READ_BITS,NODE_CAP,BOUND,DELTA,
                                          HARD_KILL_S,MAIN_CAP_S)
from scripts.recount_065 import recount_case,m_exact
from scripts import make_gates_065 as MG
from scripts import make_freeze_065 as MF
from scripts import prefreeze_smoke_065 as PS
from brute.api import certify20s as S
ROOT=Path(__file__).resolve().parents[1];DEV=10051001
IN20=lambda s:12650101<=s<=12650106


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual((C65,B65,K65,WORKERS,READ_BITS,NODE_CAP,BOUND,DELTA,HARD_KILL_S,MAIN_CAP_S),(50000,8000000,400,6,2,200000,20,0.001,1800.0,2400.0))
        self.assertEqual(ALL_ARMS,('C20','S10','S20','S30','S30b'));self.assertEqual(NOISY,('S10','S20','S30','S30b'))
        self.assertEqual({k:list(v) for k,v in ARM_NOISE.items()},{'C20':[0,None],'S10':[.10,.15],'S20':[.20,.25],'S30':[.30,.35],'S30b':[.30,.35]})

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertIn((ST.N_S20,ST.N_S10),PS.STEPS);self.assertEqual((ST.N_SEEDS,ST.N_S30B),(6,1))
        self.assertEqual(len(J),2*ST.N_SEEDS+ST.N_S20+ST.N_S10+ST.N_S30B);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        for j in J:self.assertTrue(IN20(j[2]),j);ST.check_job(j,P)
        self.assertEqual([j[3] for j in J[:ST.N_SEEDS]],['C20']*ST.N_SEEDS)
        for g,n in (('C20',ST.N_SEEDS),('S30',ST.N_SEEDS),('S20',ST.N_S20),('S10',ST.N_S10),('S30b',ST.N_S30B)):
            self.assertEqual([j[2] for j in J if j[3]==g],list(range(12650101,12650101+n)),g)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),5)
        self.assertTrue(all(j[2]==12650301 for j in J));self.assertEqual(sorted(j[3] for j in J),sorted(ALL_ARMS))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        bad=[('main','scale20',12640101,'C20'),('smoke','scale20',12650101,'C20'),('main','scale20',12650107,'S30'),('main','scale24',12650101,'C20'),
             ('main','scale20',12650301,'S10'),('main','scale20',12650101,'P20'),('main','scale20',12650102,'S30b')]
        if ST.N_S20<6:bad.append(('main','scale20',12650101+ST.N_S20,'S20'))
        if ST.N_S10<6:bad.append(('main','scale20',12650101+ST.N_S10,'S10'))
        for j in bad:
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_thresholds_match_recount(self):
        for eb in (0.15,0.25,0.35):
            for t in (1,2,7,50,400,1000):self.assertEqual(S.threshold(t,eb,DELTA,2),m_exact(t,eb),(eb,t))

    def test_record_recount_small_caps(self):
        with mock.patch.object(ST,'C65',2000),mock.patch.object(ST,'K65',40):
            cs={g:json.loads(json.dumps(ST.run_fresh(DEV,g,budget=20000))) for g in ('C20','S30','S10')}
        for g,c in cs.items():
            c['block']='smoke';a=c['arms'][g]
            self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],c['N'],a['read_bits']),(2000,20000,None,20,2))
            self.assertEqual(a['used'],len(a['extra_acts']));self.assertLessEqual(a['used'],40)
            with mock.patch('scripts.recount_065.K',40):out,bad=recount_case(c)
            self.assertEqual(bad,[]);self.assertEqual(out[g]['label'],a['label'])
            c2=copy.deepcopy(c);c2['arms'][g]['extra_masks'].append(1)
            with mock.patch('scripts.recount_065.K',40):self.assertNotEqual(recount_case(c2)[1],[])
            self.assertEqual(ST.canon65(a),ST.canon65(copy.deepcopy(a)))
        for g in ('S30','S10'):
            a=cs[g]['arms'][g];self.assertEqual(ST.canon_inner(a),ST.canon_inner(cs['C20']['arms']['C20']),g)
            self.assertEqual(a['settled_bit_errors'],0);self.assertLess(a['reads_total'],a['fixed_reads_total'])
            self.assertEqual(a['reads_total'],sum(a['reads_per_obs']));self.assertEqual(a['observations'],len(a['reads_per_obs']))
            c2=copy.deepcopy(cs[g]);c2['arms'][g]['reads_total']+=1
            with mock.patch('scripts.recount_065.K',40):self.assertNotEqual(recount_case(c2)[1],[])
            c3=copy.deepcopy(cs[g]);c3['arms'][g]['readings_sha256']='0'*64
            with mock.patch('scripts.recount_065.K',40):self.assertNotEqual(recount_case(c3)[1],[])


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GS65_sound','GMAJ65','GEQ65','GN65','GN_low65','GREAD65','GDET65','GFID65','GHOST65','GS_ref65','G_recount65','GTEST65'):
                self.assertFalse(G['gates'][g]['pass'],g)
            self.assertFalse(G['certified_readbits2_N20_eps030_seq']);self.assertFalse(G['certified_readbits2_N20_eps020_seq'])
            self.assertTrue(G['status_phrase'].startswith('not certified, no certification status'))

    def test_proc_order_and_rules(self):
        self.assertEqual(MG.PROC_ORDER,('preregistration_065','build_authorization_065','seedcheck_065','prefreeze_smoke_065',
                                        'deviation_204','freeze_065','main_run_065'))
        self.assertEqual((MG.min30(6),MG.min30(3),MG.READ_RATIO),(3,2,0.35))
        self.assertEqual((MG.REF_BUDGET,MG.REF_WORKERS,MG.SOFT),(1800.0,6,('GN65',)))
        self.assertEqual(MG.status_phrase(True,True,[]),MG.PHRASE30)
        self.assertTrue(MG.status_phrase(False,True,['GN65']).endswith('eps 0.30 stays Open'))

    def test_cut_projection(self):
        self.assertEqual(PS.STEPS,((6,6),(3,6),(3,3)));self.assertEqual((PS.CUT_AT,PS.SAFETY),(2000.0,1.25))
        self.assertEqual(PS._lpt([3,3,2,2,2],2),7.0)

    def test_freeze_list(self):
        gen={'results/diag-065/PREFREEZE_SMOKE_GATES_065.json','docs/research/BRUTE_DEVIATIONS_065_204.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify20s.py','tests/test_certify20s.py','brute/api/certify20p.py','brute/api/certify32p.py','experiments/brute_study_065.py',
                  'scripts/make_gates_065.py','experiments/BRUTE_PLAN_065.json','results/diag-065/SEEDCHECK_065.json','results/study-064/GATES_064.json',
                  'tests/test_scripts_065.py','experiments/BRUTE_SOURCE_FREEZE_064.json','tests/test_release_0620.py','experiments/worlds_065.py'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_064',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)

    def test_entries_exclude_previous_release(self):
        ev=[e['event'] for e in MF.entries()];self.assertEqual(ev[0],'preregistration_065')
        for x in ('release_0610','fresh_clone_verify_064','handoff_released_064'):self.assertNotIn(x,ev)


if __name__=='__main__':unittest.main()
