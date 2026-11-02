"""Tests for the study-060 runner and scoring scripts (v0.57.0). New file; built from tests/test_scripts_059.py (frozen).
The study caps are checked as constants; fresh cases use an old development seed (10051001), outside every study-060 range, with
the caps lowered in-process for speed."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest import mock
from experiments import brute_study_060 as ST
from experiments import worlds_060 as W60
from experiments.brute_common_060 import load,PLAN,C60,B60,K60,WORKERS,ALL_ARMS,ARM_SPEC,READ_BITS,HARD_KILL_S
from scripts.recount_060 import recount_case
from scripts import make_gates_060 as MG
from scripts import make_freeze_060 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10051001
IN24=lambda s:12600101<=s<=12600112;IN32=lambda s:12600201<=s<=12600212


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual((C60,B60,K60,WORKERS,READ_BITS,HARD_KILL_S),(50000,8000000,400,8,4,3600));self.assertEqual(ALL_ARMS,('S24','S24b','S32'))
        self.assertEqual(ARM_SPEC,{'S24':['scale24w','scale24r4',24],'S24b':['scale24w','scale24r4',24],'S32':['scale32w','scale32r4',32]})

    def test_worlds(self):
        from experiments import worlds_026 as W26
        from experiments import worlds_058 as W58
        for fam,n in (('scale24r4',24),('scale32r4',32)):
            w=W60.world(DEV,fam);b=W26.scale_world(DEV,n);self.assertEqual((w.n,w.s,w.k),(n,4,3))
            self.assertEqual(w.transitions,tuple(tuple(r) for r in b.transitions));self.assertEqual(w.start,b.start)
            self.assertEqual(w.emissions,W58.emissions(DEV,4,n));self.assertLessEqual(W60.true_size(w),n);self.assertGreaterEqual(W60.true_size(w),1)
        with self.assertRaises(ValueError):W60.world(DEV,'scale20r4')

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertEqual(ST.N24,12);self.assertIn(ST.N32,(6,0))
        self.assertEqual(len(J),2*ST.N24+ST.N32);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        for j in J:self.assertTrue(IN24(j[2]) if j[1]=='scale24w' else IN32(j[2]),j)
        self.assertEqual([j[3] for j in J[:ST.N32]],['S32']*ST.N32)
        b=[j[2] for j in J if j[3]=='S24b'];self.assertEqual(b,sorted(b,reverse=True))
        a=[j[2] for j in J if j[3]=='S24'];self.assertEqual(a,sorted(a))
        for j in J:ST.check_job(j,P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),6)
        self.assertTrue(all(12600301<=j[2]<=12600302 for j in J))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        for j in (('main','scale24w',12590001,'S24'),('smoke','scale24w',12600101,'S24'),('main','scale24w',12600101,'S32'),
                  ('main','scale32w',12600101,'S32'),('main','scale24w',12600113,'S24'),('main','scale24w',12600101,'C4')):
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_truth_label(self):
        w=W60.world(DEV,'scale24r4');m=(w.transitions,w.emissions)
        self.assertEqual(ST.truth_label('IDF',m,w.start,w,w.start),'IDF');self.assertEqual(ST.truth_label('none',None,None,w,0),'NOFIT')
        self.assertEqual(ST.truth_label('unknown',None,None,w,0),'IDU');self.assertEqual(ST.truth_label('K_spent',m,0,w,0),'AMB')
        e2=list(w.emissions);e2[0]^=1;self.assertEqual(ST.truth_label('ID',(w.transitions,e2),w.start,w,w.start),'WRONG')

    def test_record_recount_small_caps(self):
        with mock.patch.object(ST,'B60',20000),mock.patch.object(ST,'C60',2000),mock.patch.object(ST,'K60',40):
            c=json.loads(json.dumps(ST.run_fresh(DEV,'S24')))
        c['block']='smoke';a=c['arms']['S24']
        self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],c['N'],a['read_bits'],a['bound']),(2000,20000,None,24,4,24))
        self.assertEqual(a['api']['api'],'brute.certify/32b');self.assertEqual(a['api']['family_bound'],24)
        out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(out['S24']['label'],a['label'])
        c2=copy.deepcopy(c);c2['arms']['S24']['extra_masks'].append(1);self.assertNotEqual(recount_case(c2)[1],[])
        c3=copy.deepcopy(c);c3['arms']['S24']['bound']=20;self.assertNotEqual(recount_case(c3)[1],[])
        self.assertEqual(ST.canon60(a),ST.canon60(copy.deepcopy(a)))


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GS60_sound','GN24_60','GDET60','GFID60','GHOST60','GS_ref','G_recount','GTEST'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('reason',G['gates'][g],g)
            self.assertFalse(G['certified_readbits4_N24']);self.assertFalse(G['sound_not_certified_N24'])
            self.assertTrue(G['status_phrase'].startswith('not certified, no certification status'))
            self.assertIn('2-bit readings at 20 states stay Open',G['framing']);self.assertIn('TARGET CHANGE',G['framing'])

    def test_proc_order(self):
        self.assertEqual(MG.PROC_ORDER,('preregistration_060','build_authorization_060','seedcheck_060','prefreeze_smoke_060','deviation_194',
                                        'freeze_060','main_run_060'))

    def test_freeze_list(self):
        gen={'results/diag-060/PREFREEZE_SMOKE_GATES_060.json','docs/research/BRUTE_DEVIATIONS_060_194.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify32b.py','brute/api/certify20b.py','experiments/brute_study_060.py','scripts/make_gates_060.py',
                  'experiments/BRUTE_PLAN_060.json','results/diag-060/SEEDCHECK_060.json','results/study-059/GATES_059.json',
                  'tests/test_scripts_060.py','tests/test_release_0570.py','tests/test_certify32b.py','experiments/worlds_060.py',
                  'results/diag-060/BUDGET_PROBE_060.json'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_059',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
