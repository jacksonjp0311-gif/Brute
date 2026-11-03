"""Tests for the study-063 runner and scoring scripts (v0.60.0). New file; built from tests/test_scripts_062.py (frozen).
The study caps are checked as constants; fresh cases use an old development seed (10051001), outside every study-063 range, with
the caps lowered in-process for speed."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest import mock
from experiments import brute_study_063 as ST
from experiments.brute_common_063 import load,PLAN,C63,B63,K63,WORKERS,ALL_ARMS,ARM_SPEC,READ_BITS,BOUND,NODE_CAP,HARD_KILL_S
from scripts.recount_063 import recount_case
from scripts import make_gates_063 as MG
from scripts import make_freeze_063 as MF
from scripts import prefreeze_smoke_063 as PS
ROOT=Path(__file__).resolve().parents[1];DEV=10051001
IN=lambda s:12630101<=s<=12630108


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual((C63,B63,K63,WORKERS,READ_BITS,BOUND,NODE_CAP,HARD_KILL_S),(50000,8000000,400,6,2,20,200000,2400.0))
        self.assertEqual(ALL_ARMS,('B2','P2','P2b'))
        self.assertEqual(ARM_SPEC,{'B2':['scale20p2','scale20',20,'certify20b'],'P2':['scale20p2','scale20',20,'certify20p'],'P2b':['scale20p2','scale20',20,'certify20p']})

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertIn((ST.N_P2B,ST.N_SEEDS),PS.STEPS)
        self.assertEqual(len(J),2*ST.N_SEEDS+ST.N_P2B);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        for j in J:self.assertTrue(IN(j[2]),j);self.assertEqual(j[1],'scale20p2')
        self.assertEqual([j[3] for j in J[:ST.N_SEEDS]],['P2']*ST.N_SEEDS)
        b=[j[2] for j in J if j[3]=='P2b'];self.assertEqual(b,sorted(b,reverse=True));self.assertEqual(sorted(b),list(range(12630101,12630101+ST.N_P2B)))
        for g in ('P2','B2'):
            a=[j[2] for j in J if j[3]==g];self.assertEqual(a,list(range(12630101,12630101+ST.N_SEEDS)))
        for j in J:ST.check_job(j,P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),6)
        self.assertTrue(all(12630301<=j[2]<=12630302 for j in J))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        bad=[('main','scale20p2',12620101,'P2'),('smoke','scale20p2',12630101,'P2'),('main','scale24w',12630101,'P2'),
             ('main','scale20p2',12630109,'B2'),('main','scale20p2',12630101,'W2'),('main','scale20p2',12630301,'P2')]
        if ST.N_P2B<8:bad.append(('main','scale20p2',12630101+ST.N_P2B,'P2b'))
        if ST.N_SEEDS<8:bad.append(('main','scale20p2',12630101+ST.N_SEEDS,'P2'))
        for j in bad:
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_record_recount_small_caps(self):
        with mock.patch.object(ST,'C63',2000),mock.patch.object(ST,'K63',40):
            cp=json.loads(json.dumps(ST.run_fresh(DEV,'P2',budget=20000)));cb=json.loads(json.dumps(ST.run_fresh(DEV,'B2',budget=20000)))
        for c,arm,api in ((cp,'P2','brute.certify/20p'),(cb,'B2','brute.certify/20b')):
            c['block']='smoke';a=c['arms'][arm]
            self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],c['N'],a['read_bits'],a['bound']),(2000,20000,None,20,2,20))
            self.assertEqual(a['api']['api'],api);self.assertEqual(a['api']['family_bound'],20)
            self.assertEqual(a['used'],len(a['extra_acts']));self.assertLessEqual(a['used'],40)
            self.assertLessEqual(a['clique_prefix'],a['clique_final'])
            with mock.patch('scripts.recount_063.K',40):out,bad=recount_case(c)
            self.assertEqual(bad,[]);self.assertEqual(out[arm]['label'],a['label'])
            c2=copy.deepcopy(c);c2['arms'][arm]['extra_masks'].append(1)
            with mock.patch('scripts.recount_063.K',40):self.assertNotEqual(recount_case(c2)[1],[])
            self.assertEqual(ST.canon63(a),ST.canon63(copy.deepcopy(a)))
        a=cp['arms']['P2'];self.assertEqual(a['node_cap'],NODE_CAP);self.assertGreaterEqual(len(a['repins']),1);self.assertIsNone(a['repins'][0][1])
        self.assertEqual(a['clique_size'],len(a['final_clique']));self.assertEqual(a['final_clique'],sorted(a['final_clique']))
        self.assertIsNone(cb['arms']['B2']['node_cap'])


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GS63_sound','GP63','GDET63','GFID63','GHOST63','GS_ref63','G_recount63','GTEST63'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('reason',G['gates'][g],g)
            self.assertFalse(G['certified_readbits2_N20_clique']);self.assertFalse(G['sound_no_2bit_gain'])
            self.assertTrue(G['status_phrase'].startswith('not certified, no certification status'))
            self.assertIn('2-bit readings at 20 states',G['framing']);self.assertIn('pool change',G['framing'])

    def test_proc_order_and_rules(self):
        self.assertEqual(MG.PROC_ORDER,('preregistration_063','build_authorization_063','seedcheck_063','prefreeze_smoke_063',
                                        'deviation_200','freeze_063','main_run_063'))
        self.assertEqual((MG.min_w(8),MG.min_d(8),MG.min_w(6),MG.min_d(6)),(3,2,3,2))
        self.assertEqual(MG.status_phrase(True,False,[]),'certified (read_bits 2, N <= 20, clique-anchored)')
        self.assertEqual(MG.status_phrase(False,True,['GP63']),'sound but no 2-bit gain')

    def test_mcnemar(self):
        self.assertEqual(MG.mcnemar_exact(0,0),1.0);self.assertAlmostEqual(MG.mcnemar_exact(3,0),0.25)
        self.assertEqual(MG.mcnemar_exact(1,4),MG.mcnemar_exact(4,1))

    def test_cut_projection(self):
        self.assertEqual(PS.STEPS,((3,8),(2,8),(2,6)));self.assertEqual((PS.CAP,PS.SAFETY),(3300.0,1.25))
        self.assertEqual(PS._lpt([3,3,2,2,2],2),7.0)

    def test_freeze_list(self):
        gen={'results/diag-063/PREFREEZE_SMOKE_GATES_063.json','docs/research/BRUTE_DEVIATIONS_063_200.md','tests/test_release_0600.py'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify20p.py','tests/test_certify20p.py','brute/api/certify20b.py','experiments/brute_study_063.py','scripts/make_gates_063.py',
                  'experiments/BRUTE_PLAN_063.json','results/diag-063/SEEDCHECK_063.json','results/diag-063/SEEDCHECK_063_ATTEMPT1_FAIL.json',
                  'results/study-062/GATES_062.json','tests/test_scripts_063.py','results/diag-063/CAPABILITY_PROBE_063.json',
                  'experiments/BRUTE_SOURCE_FREEZE_062.json','scripts/check_seeds_063_m.py'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_062',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
