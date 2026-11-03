"""Tests for the study-066 runner and scoring scripts (v0.63.0). New file; built from tests/test_scripts_065.py (frozen).
The study caps are checked as constants; fresh cases use an old development seed (10051001), outside every study-066 range, with
the caps lowered in-process for speed. The runner's process kill is exercised with a stand-in job that sleeps (synthetic only)."""
import copy,json,tempfile,time,unittest
from pathlib import Path
from unittest import mock
from experiments import brute_study_066 as ST
from experiments.brute_common_066 import (load,PLAN,C66,B66,K66,WORKERS,ALL_ARMS,NOISY,ARM_NOISE,ARM_KEY,ARM_BOUND,READ_BITS,NODE_CAP,DELTA,
                                          HARD_KILL_S,JOB_KILL_S,MAIN_CAP_S,CONTROL)
from experiments.brute_common_009 import Checkpoint
from scripts.recount_066 import recount_case,m_exact
from scripts import make_gates_066 as MG
from scripts import make_freeze_066 as MF
from brute.api import certify20s as S
ROOT=Path(__file__).resolve().parents[1];DEV=10051001
IN20=lambda s:12660101<=s<=12660106;IN24=lambda s:12660201<=s<=12660204


class Runner(unittest.TestCase):
    def test_caps_fixed(self):
        self.assertEqual((C66,B66,K66,WORKERS,READ_BITS,NODE_CAP,DELTA,HARD_KILL_S,JOB_KILL_S,MAIN_CAP_S),(50000,8000000,400,7,2,200000,0.001,1800.0,600.0,2400.0))
        self.assertEqual(ALL_ARMS,('C24','S24','C20','S30','S30b'));self.assertEqual(NOISY,('S30','S24','S30b'))
        self.assertEqual(CONTROL,{'S30':'C20','S30b':'C20','S24':'C24'})
        self.assertEqual(ARM_BOUND,{'C20':20,'S30':20,'S30b':20,'C24':24,'S24':24})
        self.assertEqual({k:list(v) for k,v in ARM_NOISE.items()},{'C20':[0,None],'S30':[.30,.35],'C24':[0,None],'S24':[.30,.35],'S30b':[.30,.35]})

    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');self.assertEqual((ST.N20,ST.N24,ST.N_S30B),(6,4,1))
        self.assertEqual(len(J),21);self.assertEqual(len({ST.key(j) for j in J}),21)
        for j in J:self.assertTrue(IN20(j[2]) if j[1]=='scale20' else IN24(j[2]),j);self.assertEqual(j[1],ARM_KEY[j[3]]);ST.check_job(j,P)
        for g,n,s0 in (('C20',6,12660101),('S30',6,12660101),('C24',4,12660201),('S24',4,12660201),('S30b',1,12660101)):
            self.assertEqual([j[2] for j in J if j[3]==g],list(range(s0,s0+n)),g)

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertEqual(len(J),5)
        self.assertTrue(all(j[2]==12660301 for j in J));self.assertEqual(sorted(j[3] for j in J),sorted(ALL_ARMS))
        for j in J:ST.check_job(j,P)

    def test_check_job_refuses_foreign(self):
        P=load(PLAN)
        bad=[('main','scale20',12650101,'C20'),('smoke','scale20',12660101,'C20'),('main','scale20',12660107,'S30'),('main','scale24',12660101,'C20'),
             ('main','scale20',12660201,'C24'),('main','scale24',12660205,'S24'),('main','scale20',12660102,'S30b'),('main','scale20',12660101,'S10')]
        for j in bad:
            with self.assertRaises(Exception,msg=str(j)):ST.check_job(j,P)

    def test_thresholds_match_recount(self):
        for t in (1,2,7,50,400,1000):self.assertEqual(S.threshold(t,0.35,DELTA,2),m_exact(t,0.35),t)

    def test_kill_path(self):
        # synthetic: a stand-in job that sleeps past kill_s is SIGKILLed and becomes a KILL record; a fast job finishes normally
        P=load(PLAN);J=ST.jobs_for(P,'smoke')[:2]
        def fake(job,plan):
            if job[3]==J[0][3]:time.sleep(60)
            w=ST.W66.world(job[2],job[1])
            return ST.key(job),{'schema':ST.SCHEMA_CASE,'key':job[1],'seed':job[2],'n':w.n,'k':w.k,'eps':0.0,'block':job[0],'killed':False,
                                'job_wall_informational':0.0,'arms':{job[3]:{'label':'IDU','stop':'IDU','n_min':None,'conflicts_spent':0,'used':0}}}
        with tempfile.TemporaryDirectory() as d,mock.patch.object(ST,'run_job',fake):
            ck=Checkpoint(Path(d)/'CK.jsonl');t0=time.perf_counter();ST.run_jobs(J,P,ck,log=lambda *a,**k:None,kill_s=3)
            self.assertLess(time.perf_counter()-t0,30)
            k0=ck.done[ST.key(J[0])];self.assertTrue(k0['killed']);a=k0['arms'][J[0][3]]
            self.assertEqual((a['label'],a['stop'],a['model'],a['bound']),('KILL','KILL',None,ARM_BOUND[J[0][3]]))
            self.assertFalse(ck.done[ST.key(J[1])]['killed'])
            cs=ST.merge(J,ck.done);self.assertEqual(cs[0]['killed_arms'],[J[0][3]])
            c=copy.deepcopy(cs[0]);c['arms']={J[0][3]:c['arms'][J[0][3]]};out,bad=recount_case(c)
            self.assertEqual(bad,[]);self.assertEqual(out[J[0][3]]['label'],'KILL')
            c['killed_arms']=[];self.assertNotEqual(recount_case(c)[1],[])

    def test_record_recount_small_caps(self):
        with mock.patch.object(ST,'C66',2000),mock.patch.object(ST,'K66',40):
            cs={g:json.loads(json.dumps(ST.run_fresh(DEV,g,budget=20000))) for g in ('C20','S30')}
        for g,c in cs.items():
            c['block']='smoke';c['killed_arms']=[];a=c['arms'][g]
            self.assertEqual((a['conflict_cap'],a['budget_conflicts'],a['max_chunks'],a['bound'],a['read_bits']),(2000,20000,None,20,2))
            self.assertEqual(a['used'],len(a['extra_acts']));self.assertLessEqual(a['used'],40)
            with mock.patch('scripts.recount_066.K',40):out,bad=recount_case(c)
            self.assertEqual(bad,[]);self.assertEqual(out[g]['label'],a['label'])
            c2=copy.deepcopy(c);c2['arms'][g]['extra_masks'].append(1)
            with mock.patch('scripts.recount_066.K',40):self.assertNotEqual(recount_case(c2)[1],[])
            self.assertEqual(ST.canon66(a),ST.canon66(copy.deepcopy(a)))
        a=cs['S30']['arms']['S30'];self.assertEqual(ST.canon_inner(a),ST.canon_inner(cs['C20']['arms']['C20']))
        self.assertEqual(a['settled_bit_errors'],0);self.assertLess(a['reads_total'],a['fixed_reads_total'])
        c3=copy.deepcopy(cs['S30']);c3['arms']['S30']['readings_sha256']='0'*64
        with mock.patch('scripts.recount_066.K',40):self.assertNotEqual(recount_case(c3)[1],[])


class Gates(unittest.TestCase):
    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d))
            for g in ('GS66_sound','GLIVE66','GMAJ66','GEQ66','GN66','GN24_66','GREAD66','GDET66','GFID66','GHOST66','GS_ref66','G_recount66','GTEST66'):
                self.assertFalse(G['gates'][g]['pass'],g)
            self.assertFalse(G['certified_readbits2_N24_eps030_seq']);self.assertFalse(G['certified_readbits2_N20_eps030_seq'])
            self.assertTrue(G['status_phrase'].startswith('not certified, no certification status'))

    def test_proc_order_and_rules(self):
        self.assertEqual(MG.PROC_ORDER,('preregistration_066','build_authorization_066','seedcheck_066','prefreeze_smoke_066',
                                        'deviation_206','freeze_066','main_run_066'))
        self.assertEqual((MG.min30(6),MG.READ_RATIO,MG.MAIN_CAP_S),(3,0.35,2400.0))
        self.assertEqual((MG.REF_BUDGET,MG.REF_WORKERS,MG.SOFT),(1800.0,6,('GN24_66',)))
        self.assertEqual(MG.status_phrase(True,True,[]),MG.PHRASE24)
        self.assertTrue(MG.status_phrase(False,True,['GN24_66']).endswith('noise at 24 states stays Open'))

    def test_freeze_list(self):
        gen={'results/diag-066/PREFREEZE_SMOKE_GATES_066.json','docs/research/BRUTE_DEVIATIONS_066_206.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/api/certify32s.py','tests/test_certify32s.py','brute/api/certify20s.py','brute/api/certify32p.py','experiments/brute_study_066.py',
                  'scripts/make_gates_066.py','experiments/BRUTE_PLAN_066.json','results/diag-066/SEEDCHECK_066.json','results/study-065/GATES_065.json',
                  'tests/test_scripts_066.py','experiments/BRUTE_SOURCE_FREEZE_065.json','tests/test_release_0630.py','experiments/worlds_066.py'):
            self.assertIn(f,MF.FILES)
        old=__import__('scripts.make_freeze_065',fromlist=['FILES']).FILES;self.assertEqual(MF.FILES[:len(old)],old)

    def test_entries_start_at_prereg(self):
        ev=[e['event'] for e in MF.entries()];self.assertEqual(ev[0],'preregistration_066')
        for x in ('release_0620','fresh_clone_verify_065','handoff_released_065'):self.assertNotIn(x,ev)


if __name__=='__main__':unittest.main()
