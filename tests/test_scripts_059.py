"""Tests for the study-059 runner and scoring scripts (v0.56.0). New file; built from tests/test_scripts_058.py (frozen).
The study caps are checked as constants; fresh cases use an old development seed (10051001), outside every study-059 range, with
the caps lowered in-process for speed."""
import copy,json,tempfile,unittest
from pathlib import Path
from unittest import mock
from experiments import brute_study_059 as ST
from experiments import worlds_059 as W59
from experiments.brute_common_059 import load,PLAN,C59,B59,K59,WORKERS,ALL_ARMS,ARM_NOISE,BOUND,DELTA
from scripts.recount_059 import recount_case,k_for
from scripts import make_gates_059 as MG
from scripts import make_freeze_059 as MF
from brute.api import certify20n as N
ROOT=Path(__file__).resolve().parents[1];DEV=10051001
IN_MAIN=lambda s:12590001<=s<=12590012


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual((C59,B59,K59,WORKERS,BOUND,DELTA),(50000,2000000,400,8,20,0.001));self.assertEqual(ALL_ARMS,('C4','N4_05','N4_10','N4_10b','NEG4'))
        self.assertEqual(ARM_NOISE,{'C4':[0.0,None],'N4_05':[0.05,0.10],'N4_10':[0.10,0.15],'N4_10b':[0.10,0.15],'NEG4':[0.25,0.10]})

    def test_worlds_and_noise(self):
        w=W59.world(DEV);self.assertEqual((w.n,w.s),(20,4))
        from experiments import worlds_058 as W58
        self.assertEqual(w.emissions,W58.world(DEV,'scale20r4').emissions)
        a=W59.Noise(DEV,0.10).reads((0,1,0,1),50);b=W59.Noise(DEV,0.10).reads((0,1,0,1),50);self.assertEqual(a,b)
        self.assertNotEqual(a,[(0,1,0,1)]*50);self.assertEqual(W59.Noise(DEV,0.0).reads((1,1,0,0),3),[(1,1,0,0)]*3)

    def test_k_rule_independent(self):
        for t in (1,2,10,100,5000):
            for eb in (0.10,0.15):self.assertEqual(k_for(t,eb),N.reads_for(t,eb,0.001,4))

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertIn(ST.N59,(12,8))
        self.assertEqual(len(J),5*ST.N59);self.assertEqual(len({ST.key(j) for j in J}),len(J))
        self.assertTrue(all(IN_MAIN(j[2]) for j in J))
        self.assertEqual([j[3] for j in J[:4]],['C4','N4_05','N4_10','NEG4'])
        b=[j[2] for j in J if j[3]=='N4_10b'];self.assertEqual(b,sorted(b,reverse=True))
        for j in J:ST.check_job(j,P)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),10)
        self.assertTrue(all(12590051<=j[2]<=12590052 for j in J))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        for j in (('main','scale20n',12530001,'C4'),('smoke','scale20n',12590001,'C4'),('main','scale20n',12590001,'B4'),
                  ('main','scale20b',12590001,'C4'),('main','scale20n',12590013,'C4')):
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_truth_label(self):
        w=W59.world(DEV);m=(w.transitions,w.emissions)
        self.assertEqual(ST.truth_label('IDF',m,w.start,w,w.start),'IDF');self.assertEqual(ST.truth_label('none',None,None,w,0),'NOFIT')
        self.assertEqual(ST.truth_label('unknown',None,None,w,0),'IDU');self.assertEqual(ST.truth_label('K_spent',m,0,w,0),'AMB')
        e2=list(w.emissions);e2[0]^=1;self.assertEqual(ST.truth_label('ID',(w.transitions,e2),w.start,w,w.start),'WRONG')

    def test_record_recount_small_caps(self):
        with mock.patch.object(ST,'B59',20000),mock.patch.object(ST,'C59',2000),mock.patch.object(ST,'K59',40):
            c=json.loads(json.dumps(ST.run_fresh(DEV,'N4_10')))
        c['block']='smoke';a=c['arms']['N4_10']
        self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],c['N'],a['read_bits'],a['eps']),(2000,20000,None,20,4,0.10))
        self.assertEqual(a['api']['api'],'brute.certify/20n');self.assertGreater(a['reads_total'],len(a['reads_per_obs']))
        out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(out['N4_10']['label'],a['label'])
        self.assertEqual(out['N4_10']['maj_errors'],a['maj_errors'])
        c2=copy.deepcopy(c);c2['arms']['N4_10']['extra_masks'].append(1);self.assertNotEqual(recount_case(c2)[1],[])
        c3=copy.deepcopy(c);c3['arms']['N4_10']['maj_errors']+=1;self.assertNotEqual(recount_case(c3)[1],[])
        c4=copy.deepcopy(c);c4['arms']['N4_10']['reads_per_obs'][0]+=2;self.assertNotEqual(recount_case(c4)[1],[])
        self.assertEqual(ST.canon59(a),ST.canon59(copy.deepcopy(a)))


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GS59_sound','GN_keep59','GN05_59','GMAJ59','GDET59','GFID59','GHOST59','GS_ref','G_recount','GTEST'):
                self.assertFalse(G['gates'][g]['pass'],g);self.assertIn('reason',G['gates'][g],g)
            self.assertFalse(G['certified_noisy_readbits4_N20']);self.assertFalse(G['sound_not_certified_noisy'])
            self.assertTrue(G['status_phrase'].startswith('not certified, no certification status'))
            self.assertIn('2-bit readings at 20 states stay Open',G['framing'])

    def test_proc_order(self):
        self.assertEqual(MG.PROC_ORDER,('preregistration_059','build_authorization_059','seedcheck_059','prefreeze_smoke_059','deviation_192',
                                        'freeze_059','main_run_059'))

    def test_freeze_list(self):
        gen={'results/diag-059/PREFREEZE_SMOKE_GATES_059.json','docs/research/BRUTE_DEVIATIONS_059_192.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify20n.py','brute/api/certify20b.py','experiments/brute_study_059.py','scripts/make_gates_059.py',
                  'experiments/BRUTE_PLAN_059.json','results/diag-059/SEEDCHECK_059.json','results/study-058/GATES_058.json',
                  'tests/test_scripts_059.py','tests/test_release_0560.py','tests/test_certify20n.py','experiments/worlds_059.py'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_058',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)


if __name__=='__main__':unittest.main()
