"""Tests for the study-058 runner and scoring scripts (v0.55.0). New file; built from tests/test_scripts_057.py (frozen).
The study caps are checked as constants; fresh cases use an old development seed (10051001), outside every study-058 range, with
the caps lowered in-process for speed and the bound check bypassed only through the small-world helper in tests/test_certify20b."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest import mock
from experiments import brute_study_058 as ST
from experiments import worlds_058 as W58
from experiments.brute_common_058 import load,PLAN,C58,B58,K58,WORKERS,ALL_ARMS,ARM_FAMILY,BOUND
from scripts.recount_058 import recount_case
from scripts import make_gates_058 as MG
from scripts import make_freeze_058 as MF
ROOT=Path(__file__).resolve().parents[1];DEV=10051001
IN_MAIN=lambda s:12530001<=s<=12530012


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual((C58,B58,K58,WORKERS,BOUND),(50000,2000000,400,8,20));self.assertEqual(ALL_ARMS,('B2','B2R','B3','B4','B4_b'))
        self.assertEqual(ARM_FAMILY,{'B2':'scale20','B2R':'scale20r2','B3':'scale20r3','B4':'scale20r4','B4_b':'scale20r4'})

    def test_worlds(self):
        for fam,b in W58.BITS.items():
            w=W58.world(DEV,fam);self.assertEqual((w.n,w.s),(20,b));self.assertTrue(all(0<=e<(1<<b) for e in w.emissions))
        a=W58.world(DEV,'scale20r4');b=W58.world(DEV,'scale20r4');self.assertEqual(a.emissions,b.emissions)
        self.assertEqual(W58.world(DEV,'scale20r2').transitions,W58.world(DEV,'scale20').transitions)

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertIn(ST.N58,(12,8))
        self.assertEqual(len(J),5*ST.N58);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        self.assertTrue(all(IN_MAIN(j[2]) for j in J))
        self.assertEqual([j[3] for j in J[:4]],['B4','B3','B2R','B2'])
        b=[j[2] for j in J if j[3]=='B4_b'];self.assertEqual(b,sorted(b,reverse=True))
        for j in J:ST.check_job(j,P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),10)
        self.assertTrue(all(12550001<=j[2]<=12550002 for j in J))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        for j in (('main','scale20b',12410001,'B4'),('smoke','scale20b',12530001,'B4'),('main','scale20b',12530001,'COV_X'),
                  ('main','scale20v',12530001,'B4'),('main','scale20b',12530013,'B4')):
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_truth_label(self):
        w=W58.world(DEV,'scale20r4');m=(w.transitions,w.emissions)
        self.assertEqual(ST.truth_label('IDF',m,w.start,w,w.start),'IDF')
        self.assertEqual(ST.truth_label('unknown',None,None,w,0),'IDU');self.assertEqual(ST.truth_label('K_spent',m,0,w,0),'AMB')
        e2=list(w.emissions);e2[0]^=1;self.assertEqual(ST.truth_label('ID',(w.transitions,e2),w.start,w,w.start),'WRONG')
        self.assertEqual(ST.truth_label('IDF',m,3,w,3),'IDF')

    def test_record_recount_small_caps(self):
        with mock.patch.object(ST,'B58',20000),mock.patch.object(ST,'C58',2000),mock.patch.object(ST,'K58',40):
            c=json.loads(json.dumps(ST.run_fresh(DEV,'B4')))
        c['block']='smoke';a=c['arms']['B4']
        self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],c['N'],a['read_bits']),(2000,20000,None,20,4))
        self.assertEqual(a['api']['api'],'brute.certify/20b')
        out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(out['B4']['label'],a['label'])
        c2=copy.deepcopy(c);c2['arms']['B4']['extra_masks'].append(1);self.assertNotEqual(recount_case(c2)[1],[])
        c3=copy.deepcopy(c);c3['arms']['B4']['prefix_masks'][0]=1<<15 if c3['arms']['B4']['prefix_masks'][0]!=1<<15 else 1;self.assertNotEqual(recount_case(c3)[1],[])
        self.assertEqual(ST.canon58(a),ST.canon58(copy.deepcopy(a)))


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GS58_sound','GB_gain58','GB3_58','GDET58','GFID58','GHOST58','GS_ref','G_recount','GTEST'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('reason',G['gates'][g],g)
            self.assertFalse(G['certified_readbits_N20']);self.assertFalse(G['sound_not_certified_readbits'])
            self.assertTrue(G['status_phrase'].startswith('not certified, no certification status'))
            self.assertIn('2-bit readings at 20 states stay Open',G['framing'])

    def test_proc_order(self):
        self.assertEqual(MG.PROC_ORDER,('preregistration_058','build_authorization_058','seedcheck_058','prefreeze_smoke_058','deviation_190',
                                        'freeze_058','main_run_058'))

    def test_freeze_list(self):
        gen={'results/diag-058/PREFREEZE_SMOKE_GATES_058.json','docs/research/BRUTE_DEVIATIONS_058_190.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify20b.py','brute/api/certify16e.py','experiments/brute_study_058.py','scripts/make_gates_058.py',
                  'experiments/BRUTE_PLAN_058.json','results/diag-058/SEEDCHECK_058.json','results/study-057/GATES_057.json',
                  'tests/test_scripts_058.py','tests/test_release_0550.py','tests/test_certify20b.py','experiments/worlds_058.py'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_057',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
