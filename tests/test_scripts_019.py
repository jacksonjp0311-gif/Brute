"""Study-019 process scripts: watchdog_019 (wrapper over the frozen watchdog_014), hbsentinel_019 / hb_attribution_019,
run_tests_0170 K rules (K_0160 added) and the D100 porcelain fix, seal_019 heartbeat / reproset block, study019_storage gzip,
run_reference_019 checkpoint / PROGRESS / gated set / small-set mutation guard, run_study_019 stream table invariants (no
literal budgets), rate_math_019 projection, make_freeze_019 file list. Smoke only; every temp directory is removed."""
import json,shutil,subprocess,sys,tempfile,threading,time,unittest
from pathlib import Path
from scripts import watchdog_019 as W,run_tests_0170 as RT,seal_019 as S,study019_storage as ST,run_reference_019 as RR,run_study_019 as RS
from scripts import hbsentinel_019 as HS,hb_attribution_019 as HA,rate_math_019 as RM,make_freeze_019 as MF


class _Tmp(unittest.TestCase):
    def tmp(self):
        d=Path(tempfile.mkdtemp(prefix='brute-t019-'));self.addCleanup(shutil.rmtree,d,True);return d


class Watchdog019(_Tmp):
    def test_paths(self):self.assertTrue(str(W.STUDY).endswith('results/study-019'));self.assertEqual(W.CAP,7200)

    def test_kill_thread(self):
        d=self.tmp();(d/'RUN_T0').write_text(f'{time.time()}\n')
        p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
        (d/'RUN_STATE_019.json').write_text(json.dumps({'running':{'x':{'pgid':p.pid}}}))
        rc=W.run(d,cap=3,period=0.5,kill_after=5,fsync_every=1);p.wait(5)
        self.assertEqual(rc,3);stop=json.loads((d/'STOP_019.json').read_text())
        self.assertEqual(stop['survivors'],[]);self.assertIn(p.pid,stop['process_groups'])
        hb=S.heartbeat(d,float((d/'RUN_T0').read_text()));self.assertGreaterEqual(hb['beats'],4);self.assertLess(hb['max_gap_s'],2)

    def test_run_done_exits(self):
        d=self.tmp();(d/'RUN_T0').write_text(f'{time.time()}\n');(d/'RUN_DONE_019.json').write_text('{}')
        self.assertEqual(W.run(d,cap=60,period=0.2),0);self.assertFalse((d/'STOP_019.json').exists())


class RunTests0170(unittest.TestCase):
    def test_k0160_needs_clean_pass(self):
        f={sorted(RT.K_ALLOWED['0160'])[0]}
        m={'test_release_0160.py':{'results':{t:(['fail'] if t in f else ['ok']) for t in RT.K_ALLOWED['0160']},'tests_run':4,'skipped':[]}}
        plain={'tests_run':4,'skipped':[]};fr={'changed':[]};ok={'results':{t:['ok'] for t in f}}
        self.assertTrue(RT.verdict(m,plain,fr,{},{'0160':ok},new_tests=())['clauses']['i_only_declared_failures'])
        self.assertFalse(RT.verdict(m,plain,fr,{},{'0160':None},new_tests=())['clauses']['i_only_declared_failures'])
        self.assertEqual((RT.TAGS['0160'],RT.TAGS['0150']),('v0.16.0','v0.15.0'));self.assertEqual(len(RT.K_ALLOWED['0160']),4)
        self.assertTrue(str(RT.OUT).endswith('study-019/TEST_SUITE_019.json'))

    def test_k096(self):
        t='test_scripts_017.Orchestrator017.test_streams'
        m={'test_scripts_017.py':{'results':{t:['fail']},'tests_run':1,'skipped':[]}}
        V=RT.verdict(m,{'tests_run':1,'skipped':[]},{'changed':[]},{},{},new_tests=())
        self.assertTrue(V['clauses']['i_only_declared_failures']);self.assertTrue(V['k_rules']['096']['applied'])

    def test_new_tests_against_v0160(self):self.assertIn('test_seqmargin_0170.py',RT.NEW_TESTS);self.assertNotIn('test_noisyregion_0160.py',RT.NEW_TESTS)

    def test_d100_porcelain_not_stripped(self):
        src=Path(RT.__file__).read_text();self.assertIn("[l[3:] for l in porc.splitlines() if l.strip()]",src)
        porc=' M brute/x.py\n M README.md\n';self.assertEqual([l[3:] for l in porc.splitlines() if l.strip()],['brute/x.py','README.md'])


class Sentinel019(_Tmp):
    def test_sentinel_records_and_exits(self):
        d=self.tmp();(d/'RUN_T0').write_text(f'{time.time()}\n')
        p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
        (d/'RUN_STATE_019.json').write_text(json.dumps({'orchestrator_pid':p.pid}))
        t=threading.Timer(5.0,lambda:(d/'RUN_DONE_019.json').write_text('{}'));t.start()
        self.assertEqual(HS.run(d,cap=60),0);p.kill();p.wait(5)
        R=[json.loads(l) for l in (d/'HB_SENTINEL_019.jsonl').read_text().splitlines()]
        self.assertGreaterEqual(len(R),2);self.assertIn('workers_cpu_s',R[0])

    def test_classes(self):
        self.assertEqual(HA.classify(30,30,30,29,0,4),'box_pause');self.assertEqual(HA.classify(60,60,60,1,200,4),'watchdog_stall')


class SealStorage019(_Tmp):
    def test_gz_and_blocks(self):
        self.assertEqual(ST._gz(b'abc'*100),ST._gz(b'abc'*100));self.assertTrue(str(ST.STUDY).endswith('study-019'))
        self.assertEqual(ST.BLOCKS,('transfer','repro/reproset'))
        d=self.tmp();(d/'x.txt').write_text('1');B=S.build(d)
        self.assertEqual(set(B['blocks']),{'transfer','repro/reproset'});self.assertEqual(B['study'],'BRUTE-0170-SEQUENTIAL-MARGIN-019')


class Reference019(_Tmp):
    def test_checkpoint_progress_gated_and_small_mutation(self):
        d=self.tmp();ck=d/'c.jsonl'
        with open(ck,'w') as fh:RR._append(fh,{'event':'start','t':1});RR._append(fh,{'case':'a/1/0.02','ok':True,'first_difference':None,'wall_informational':0})
        cases,ev=RR.read_ck(ck);self.assertEqual(list(cases),['a/1/0.02']);self.assertEqual(list(ev),['start'])
        self.assertIsNone(RR.mutation([{'schema':'brute.case.v17_0'}]*30,{},1,{})['passed']);self.assertIn('v0170_reference',RR.R.__name__)
        self.assertTrue(RR.gated({'block':'main','eps':0.02}));self.assertFalse(RR.gated({'block':'stress','eps':0.05}))
        self.assertFalse(RR.gated({'block':'main','eps':0.01}));self.assertTrue(RR.gated({'schema':'brute.case3.v17_0','block':'alphabet3','eps':0.0}))
        P=RR.Progress(d/'P.json',10,100,2);P.add({'wall_informational':2.0});P.write();r=json.loads((d/'P.json').read_text())
        self.assertEqual((r['cases_done'],r['cases_total'],r['mean_audit_cost_s']),(1,10,2.0));self.assertEqual(RR.PROGRESS_EVERY,60)


class Orchestrator019(unittest.TestCase):
    def test_streams(self):
        T={t['name']:t for t in RS.tasks()};self.assertEqual(set(T),{'transfer','gti','repro','g11'})
        self.assertEqual((RS.CAP,RS.MAX_WORKERS),(7200,8))
        for n,t in T.items():self.assertEqual((t['workers'],t['budget']),RS.STREAMS[n]);self.assertTrue(t['mandatory'])
        self.assertEqual(T['repro']['deps'],['transfer']);self.assertEqual(T['g11']['deps'],['transfer'])
        W_={n:t['workers'] for n,t in T.items()}
        self.assertLessEqual(W_['transfer']+W_['gti'],8);self.assertLessEqual(W_['gti']+W_['repro']+W_['g11'],8)
        self.assertIn('reproset',T['repro']['cmd']);self.assertNotIn('--every',T['repro']['cmd']);self.assertIn('run_tests_0170.py',' '.join(T['gti']['cmd']))
        self.assertIn('--progress',T['g11']['cmd']);self.assertIn('transfer',T['transfer']['cmd'])
        self.assertLessEqual(max(RS.STREAMS['gti'][1],RS.STREAMS['transfer'][1]+max(RS.STREAMS['repro'][1],RS.STREAMS['g11'][1])),RS.CAP)


class RateMath019(unittest.TestCase):
    def test_projection(self):
        jobs=[('main','a',i,0.0) for i in range(10)]+[('alphabet3','rand4a3',i,0.02) for i in range(4)]
        r=RM.project(jobs,{'a/0.0':2.0,'rand4a3/0.02':5.0},2);self.assertEqual(r['raw_s'],20.0);self.assertEqual(r['projected_s'],35.0)
        with self.assertRaises(SystemExit):RM.project(jobs,{'a/0.0':2.0},2)
        self.assertEqual((RM.FACTOR,RM.FILL),(1.75,0.8))


class Freeze019(unittest.TestCase):
    def test_files(self):
        for f in ('brute/seqmargin.py','brute/region3.py','brute/api/certify7.py','scripts/run_tests_0170.py','tests/test_scripts_019.py',
                  'results/smoke-019/KILL_DRILL_019.json','docs/research/v0.17.0/RATE_MATH_019.json'):self.assertIn(f,MF.FILES)
        self.assertEqual(len(MF.FILES),len(set(MF.FILES)))


if __name__=='__main__':unittest.main()
