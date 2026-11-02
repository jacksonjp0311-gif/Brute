"""Tests for the study-062 runner and scoring scripts (v0.59.0). New file; built from tests/test_scripts_061.py (frozen).
The study caps are checked as constants; fresh cases use an old development seed (10051001), outside every study-062 range, with
the caps lowered in-process for speed."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest import mock
from experiments import brute_study_062 as ST
from experiments import worlds_058 as W58
from experiments.brute_common_062 import load,PLAN,C62,B62,K62,WORKERS,ALL_ARMS,ARM_SPEC,READ_BITS,BOUND,PROBE_WORD,HARD_KILL_S
from scripts.recount_062 import recount_case
from scripts import make_gates_062 as MG
from scripts import make_freeze_062 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10051001
IN=lambda s:12620101<=s<=12620112


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual((C62,B62,K62,WORKERS,READ_BITS,BOUND,PROBE_WORD),(50000,load(ROOT/'results/diag-062/BUDGET_PROBE_062.json')['B62'],400,8,2,20,(0,1)))
        self.assertIn(B62,(2000000,8000000));self.assertEqual(ALL_ARMS,('B2','W2','W2b'));self.assertIsInstance(HARD_KILL_S,float)
        self.assertEqual(ARM_SPEC,{'B2':['scale20w2','scale20',20,'certify20b'],'W2':['scale20w2','scale20',20,'certify20w'],'W2b':['scale20w2','scale20',20,'certify20w']})

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertIn((ST.N_W2B,ST.N_SEEDS),((6,12),(2,12),(2,8),(2,3)))
        self.assertEqual(len(J),2*ST.N_SEEDS+ST.N_W2B);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        for j in J:self.assertTrue(IN(j[2]),j);self.assertEqual(j[1],'scale20w2')
        self.assertEqual([j[3] for j in J[:ST.N_SEEDS]],['W2']*ST.N_SEEDS)
        b=[j[2] for j in J if j[3]=='W2b'];self.assertEqual(b,sorted(b,reverse=True));self.assertEqual(sorted(b),list(range(12620101,12620101+ST.N_W2B)))
        for g in ('W2','B2'):
            a=[j[2] for j in J if j[3]==g];self.assertEqual(a,list(range(12620101,12620101+ST.N_SEEDS)))
        for j in J:ST.check_job(j,P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),6)
        self.assertTrue(all(12620301<=j[2]<=12620302 for j in J))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        bad=[('main','scale20w2',12610101,'W2'),('smoke','scale20w2',12620101,'W2'),('main','scale24w',12620101,'W2'),
             ('main','scale20w2',12620113,'B2'),('main','scale20w2',12620101,'S24'),('main','scale20w2',12620301,'W2')]
        if ST.N_W2B<12:bad.append(('main','scale20w2',12620101+ST.N_W2B,'W2b'))
        if ST.N_SEEDS<12:bad.append(('main','scale20w2',12620101+ST.N_SEEDS,'W2'))
        for j in bad:
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_record_recount_small_caps(self):
        with mock.patch.object(ST,'C62',2000),mock.patch.object(ST,'K62',40):
            cw=json.loads(json.dumps(ST.run_fresh(DEV,'W2',budget=20000)));cb=json.loads(json.dumps(ST.run_fresh(DEV,'B2',budget=20000)))
        for c,arm,api in ((cw,'W2','brute.certify/20w'),(cb,'B2','brute.certify/20b')):
            c['block']='smoke';a=c['arms'][arm]
            self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],c['N'],a['read_bits'],a['bound']),(2000,20000,None,20,2,20))
            self.assertEqual(a['api']['api'],api);self.assertEqual(a['api']['family_bound'],20)
            self.assertEqual(a['used'],len(a['extra_acts']));self.assertLessEqual(a['used'],40)
            self.assertLessEqual(a['clique_prefix'],a['clique_final'])
            with mock.patch('scripts.recount_062.K',40):out,bad=recount_case(c)
            self.assertEqual(bad,[]);self.assertEqual(out[arm]['label'],a['label'])
            c2=copy.deepcopy(c);c2['arms'][arm]['extra_masks'].append(1)
            with mock.patch('scripts.recount_062.K',40):self.assertNotEqual(recount_case(c2)[1],[])
            self.assertEqual(ST.canon62(a),ST.canon62(copy.deepcopy(a)))
        self.assertEqual(cw['arms']['W2']['probe_word'],[0,1]);self.assertEqual(cb['arms']['B2']['probe_word'],[])
        c3=copy.deepcopy(cw);c3['arms']['W2']['probe_word']=[]
        with mock.patch('scripts.recount_062.K',40):self.assertNotEqual(recount_case(c3)[1],[])


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GS62_sound','GW62','GDET62','GFID62','GHOST62','GS_ref','G_recount','GTEST'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('reason',G['gates'][g],g)
            self.assertFalse(G['certified_readbits2_N20_windows']);self.assertFalse(G['sound_no_2bit_gain'])
            self.assertTrue(G['status_phrase'].startswith('not certified, no certification status'))
            self.assertIn('2-bit readings at 20 states',G['framing']);self.assertIn('policy change',G['framing'])

    def test_proc_order_and_rules(self):
        self.assertEqual(MG.PROC_ORDER,('preregistration_062','budget_probe_062','build_authorization_062','seedcheck_062','prefreeze_smoke_062',
                                        'deviation_198','freeze_062','main_run_062'))
        self.assertEqual((MG.min_w(12),MG.min_d(12),MG.min_w(8),MG.min_d(8)),(4,3,3,2))
        self.assertEqual(MG.status_phrase(True,False,[]),'certified (read_bits 2, N <= 20, windows)')
        self.assertEqual(MG.status_phrase(False,True,['GW62']),'sound but no 2-bit gain')

    def test_mcnemar(self):
        self.assertEqual(MG.mcnemar_exact(0,0),1.0);self.assertAlmostEqual(MG.mcnemar_exact(3,0),0.25);self.assertAlmostEqual(MG.mcnemar_exact(4,0),0.125)
        self.assertAlmostEqual(MG.mcnemar_exact(5,1),2*7/64);self.assertEqual(MG.mcnemar_exact(2,2),1.0);self.assertEqual(MG.mcnemar_exact(1,4),MG.mcnemar_exact(4,1))

    def test_freeze_list(self):
        gen={'results/diag-062/PREFREEZE_SMOKE_GATES_062.json','docs/research/BRUTE_DEVIATIONS_062_198.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify20w.py','tests/test_certify20w.py','brute/api/certify20b.py','experiments/brute_study_062.py','scripts/make_gates_062.py',
                  'experiments/BRUTE_PLAN_062.json','results/diag-062/SEEDCHECK_062.json','results/study-061/GATES_061.json',
                  'tests/test_scripts_062.py','tests/test_release_0590.py','results/diag-062/BUDGET_PROBE_062.json','experiments/BRUTE_SOURCE_FREEZE_061.json'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_061',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
