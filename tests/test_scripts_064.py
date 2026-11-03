"""Tests for the study-064 runner and scoring scripts (v0.61.0). New file; built from tests/test_scripts_063.py (frozen).
The study caps are checked as constants; fresh cases use an old development seed (10051001), outside every study-064 range, with
the caps lowered in-process for speed."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest import mock
from experiments import brute_study_064 as ST
from experiments.brute_common_064 import load,PLAN,C64,B64,K64,WORKERS,ALL_ARMS,ARM_SPEC,READ_BITS,NODE_CAP,HARD_KILL_S,MAIN_CAP_S
from scripts.recount_064 import recount_case
from scripts import make_gates_064 as MG
from scripts import make_freeze_064 as MF
from scripts import prefreeze_smoke_064 as PS
ROOT=Path(__file__).resolve().parents[1];DEV=10051001
IN20=lambda s:12640101<=s<=12640106
IN24=lambda s:12640201<=s<=12640206


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual((C64,B64,K64,WORKERS,READ_BITS,NODE_CAP,HARD_KILL_S,MAIN_CAP_S),(50000,8000000,400,6,2,200000,1800.0,2400.0))
        self.assertEqual(ALL_ARMS,('P24','B24','P20','P20b'))
        self.assertEqual(ARM_SPEC,{'P24':['scale24p','scale24',24,'certify32p'],'B24':['scale24p','scale24',24,'certify32b'],
                                   'P20':['scale20p','scale20',20,'certify20p'],'P20b':['scale20p','scale20',20,'certify20p']})

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertIn((ST.N_P20B,ST.N_B24),PS.STEPS);self.assertEqual(ST.N_SEEDS,6)
        self.assertEqual(len(J),2*ST.N_SEEDS+ST.N_B24+ST.N_P20B);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        for j in J:
            self.assertTrue(IN24(j[2]) if j[1]=='scale24p' else IN20(j[2]),j);ST.check_job(j,P)
        self.assertEqual([j[3] for j in J[:ST.N_B24]],['B24']*ST.N_B24)
        b=[j[2] for j in J if j[3]=='P20b'];self.assertEqual(b,sorted(b,reverse=True));self.assertEqual(sorted(b),list(range(12640101,12640101+ST.N_P20B)))
        self.assertEqual([j[2] for j in J if j[3]=='B24'],list(range(12640201,12640201+ST.N_B24)))
        for g,s0 in (('P24',12640201),('P20',12640101)):
            self.assertEqual([j[2] for j in J if j[3]==g],list(range(s0,s0+ST.N_SEEDS)))

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),4)
        self.assertTrue(all(12640301<=j[2]<=12640306 for j in J))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        bad=[('main','scale20p',12630101,'P20'),('smoke','scale20p',12640101,'P20'),('main','scale24p',12640101,'P24'),
             ('main','scale20p',12640107,'P20'),('main','scale24p',12640207,'P24'),('main','scale20p',12640101,'W2'),
             ('main','scale20p',12640301,'P20'),('main','scale24p',12610101,'P24'),('main','scale20p',12640201,'B24')]
        if ST.N_P20B<6:bad.append(('main','scale20p',12640101+ST.N_P20B,'P20b'))
        if ST.N_B24<6:bad.append(('main','scale24p',12640201+ST.N_B24,'B24'))
        for j in bad:
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_record_recount_small_caps(self):
        with mock.patch.object(ST,'C64',2000),mock.patch.object(ST,'K64',40):
            cs={g:json.loads(json.dumps(ST.run_fresh(DEV,g,budget=20000))) for g in ('P20','P24','B24')}
        for g,c in cs.items():
            c['block']='smoke';a=c['arms'][g];N=ARM_SPEC[g][2]
            self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],c['N'],a['read_bits'],a['bound']),(2000,20000,None,N,2,N))
            self.assertEqual(a['api']['family_bound'],N)
            self.assertEqual(a['used'],len(a['extra_acts']));self.assertLessEqual(a['used'],40)
            with mock.patch('scripts.recount_064.K',40):out,bad=recount_case(c)
            self.assertEqual(bad,[]);self.assertEqual(out[g]['label'],a['label'])
            c2=copy.deepcopy(c);c2['arms'][g]['extra_masks'].append(1)
            with mock.patch('scripts.recount_064.K',40):self.assertNotEqual(recount_case(c2)[1],[])
            self.assertEqual(ST.canon64(a),ST.canon64(copy.deepcopy(a)))
        for g in ('P20','P24'):
            a=cs[g]['arms'][g];self.assertEqual(a['node_cap'],NODE_CAP);self.assertGreaterEqual(len(a['repins']),1);self.assertIsNone(a['repins'][0][1])
            self.assertEqual(a['clique_size'],len(a['final_clique']));self.assertEqual(a['final_clique'],sorted(a['final_clique']))
            self.assertLessEqual(a['clique_prefix'],a['clique_final'])
        self.assertIsNone(cs['B24']['arms']['B24']['node_cap'])


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GS64_sound','GP24_64','GP20_64','GDET64','GFID64','GHOST64','GS_ref64','G_recount64','GTEST64'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('reason',G['gates'][g],g)
            self.assertFalse(G['certified_readbits2_N24_clique']);self.assertFalse(G['certified_readbits2_N20_clique'])
            self.assertTrue(G['status_phrase'].startswith('not certified, no certification status'))
            self.assertIn('SIZE TEST',G['framing'])

    def test_proc_order_and_rules(self):
        self.assertEqual(MG.PROC_ORDER,('preregistration_064','build_authorization_064','seedcheck_064','prefreeze_smoke_064',
                                        'deviation_202','freeze_064','main_run_064'))
        self.assertEqual((MG.min24(6),MG.min20(6),MG.min24(5),MG.min20(5)),(2,3,2,3))
        self.assertEqual((MG.REF_BUDGET,MG.REF_WORKERS,MG.SOFT),(1800.0,6,('GP24_64',)))
        self.assertEqual(MG.status_phrase(True,True,[]),'certified (read_bits 2, N <= 24, clique-anchored)')
        self.assertTrue(MG.status_phrase(False,True,['GP24_64']).endswith('24 states at 2 bits stay Open'))

    def test_cut_projection(self):
        self.assertEqual(PS.STEPS,((2,3),(1,3),(1,2)));self.assertEqual((PS.CAP,PS.SAFETY),(2400.0,1.25))
        self.assertEqual(PS._lpt([3,3,2,2,2],2),7.0)

    def test_freeze_list(self):
        gen={'results/diag-064/PREFREEZE_SMOKE_GATES_064.json','docs/research/BRUTE_DEVIATIONS_064_202.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify32p.py','tests/test_certify32p.py','brute/api/certify20p.py','experiments/brute_study_064.py','scripts/make_gates_064.py',
                  'experiments/BRUTE_PLAN_064.json','results/diag-064/SEEDCHECK_064.json','results/study-063/GATES_063.json','tests/test_scripts_064.py',
                  'results/diag-064/CAPABILITY_PROBE_064.json','results/diag-064/REF_PIN_DIAG_064.json','experiments/v0610_reference.py',
                  'experiments/BRUTE_SOURCE_FREEZE_063.json','tests/test_release_0610.py'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_063',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
