"""Study-018 process scripts: watchdog_018 (wrapper over the frozen watchdog_014), hbsentinel_018 / hb_attribution_018,
run_tests_0160 K rules and parallel children, seal_018 heartbeat, study018_storage gzip, run_reference_018 checkpoint /
PROGRESS / small-set mutation guard, run_study_018 stream table invariants (no literal budgets: deviation #96 lesson),
rate_math_018 projection. Smoke only, temp directories."""
import json,subprocess,sys,tempfile,threading,time,unittest
from pathlib import Path
from scripts import watchdog_018 as W,run_tests_0160 as RT,seal_018 as S,study018_storage as ST,run_reference_018 as RR,run_study_018 as RS
from scripts import hbsentinel_018 as HS,hb_attribution_018 as HA,rate_math_018 as RM


class Watchdog018(unittest.TestCase):
    def test_paths(self):self.assertTrue(str(W.STUDY).endswith('results/study-018'));self.assertEqual(W.CAP,7200)

    def test_kill_thread(self):
        d=Path(tempfile.mkdtemp());(d/'RUN_T0').write_text(f'{time.time()}\n')
        p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
        (d/'RUN_STATE_018.json').write_text(json.dumps({'running':{'x':{'pgid':p.pid}}}))
        rc=W.run(d,cap=3,period=0.5,kill_after=5,fsync_every=1);p.wait(5)
        self.assertEqual(rc,3);stop=json.loads((d/'STOP_018.json').read_text())
        self.assertEqual(stop['survivors'],[]);self.assertIn(p.pid,stop['process_groups'])
        hb=S.heartbeat(d,float((d/'RUN_T0').read_text()));self.assertGreaterEqual(hb['beats'],4);self.assertLess(hb['max_gap_s'],2)

    def test_run_done_exits(self):
        d=Path(tempfile.mkdtemp());(d/'RUN_T0').write_text(f'{time.time()}\n');(d/'RUN_DONE_018.json').write_text('{}')
        self.assertEqual(W.run(d,cap=60,period=0.2),0);self.assertFalse((d/'STOP_018.json').exists())


class RunTests0160(unittest.TestCase):
    def test_k0150_needs_clean_pass(self):
        f={sorted(RT.K_ALLOWED['0150'])[0]}
        m={'test_release_0150.py':{'results':{t:(['fail'] if t in f else ['ok']) for t in RT.K_ALLOWED['0150']},'tests_run':4,'skipped':[]}}
        plain={'tests_run':4,'skipped':[]};fr={'changed':[]};ok={'results':{t:['ok'] for t in f}}
        self.assertTrue(RT.verdict(m,plain,fr,{},{'0150':ok},new_tests=())['clauses']['i_only_declared_failures'])
        self.assertFalse(RT.verdict(m,plain,fr,{},{'0150':None},new_tests=())['clauses']['i_only_declared_failures'])
        self.assertEqual(RT.TAGS['0150'],'v0.15.0');self.assertEqual(len(RT.K_ALLOWED['0150']),4)

    def test_k096(self):
        t='test_scripts_017.Orchestrator017.test_streams'
        m={'test_scripts_017.py':{'results':{t:['fail']},'tests_run':1,'skipped':[]}}
        V=RT.verdict(m,{'tests_run':1,'skipped':[]},{'changed':[]},{},{},new_tests=())
        self.assertTrue(V['clauses']['i_only_declared_failures']);self.assertTrue(V['k_rules']['096']['applied'])
        m2={'test_scripts_017.py':{'results':{'test_scripts_017.Sentinel017.test_classes':['fail']},'tests_run':1,'skipped':[]}}
        self.assertFalse(RT.verdict(m2,{'tests_run':1,'skipped':[]},{'changed':[]},{},{},new_tests=())['clauses']['i_only_declared_failures'])

    def test_new_tests_against_v0150(self):self.assertIn('test_noisyregion_0160.py',RT.NEW_TESTS);self.assertNotIn('test_api_certify5_0150.py',RT.NEW_TESTS)


class Sentinel018(unittest.TestCase):
    def test_sentinel_records_and_exits(self):
        d=Path(tempfile.mkdtemp());(d/'RUN_T0').write_text(f'{time.time()}\n')
        p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
        (d/'RUN_STATE_018.json').write_text(json.dumps({'orchestrator_pid':p.pid}))
        t=threading.Timer(5.0,lambda:(d/'RUN_DONE_018.json').write_text('{}'));t.start()
        self.assertEqual(HS.run(d,cap=60),0);p.kill();p.wait(5)
        R=[json.loads(l) for l in (d/'HB_SENTINEL_018.jsonl').read_text().splitlines()]
        self.assertGreaterEqual(len(R),2);self.assertIn('workers_cpu_s',R[0])

    def test_classes(self):
        self.assertEqual(HA.classify(30,30,30,29,0,4),'box_pause');self.assertEqual(HA.classify(60,60,60,1,200,4),'watchdog_stall')


class Storage018(unittest.TestCase):
    def test_gz(self):
        self.assertEqual(ST._gz(b'abc'*100),ST._gz(b'abc'*100));self.assertTrue(str(ST.STUDY).endswith('study-018'))
        self.assertEqual(ST.BLOCKS,('transfer','repro/main'))


class Reference018(unittest.TestCase):
    def test_checkpoint_progress_and_small_mutation(self):
        d=Path(tempfile.mkdtemp());ck=d/'c.jsonl'
        with open(ck,'w') as fh:RR._append(fh,{'event':'start','t':1});RR._append(fh,{'case':'a/1/0.02','ok':True,'first_difference':None,'wall_informational':0})
        cases,ev=RR.read_ck(ck);self.assertEqual(list(cases),['a/1/0.02']);self.assertEqual(list(ev),['start'])
        self.assertIsNone(RR.mutation([{}]*3,{},1,{})['passed']);self.assertIn('v0160_reference',RR.R.__name__)
        self.assertEqual(RR.ckey({'family':'a','seed':1,'eps':0.02}),'a/1/0.02')
        self.assertTrue(RR.gated({'block':'main','eps':0.02}));self.assertFalse(RR.gated({'block':'stress','eps':0.05}));self.assertFalse(RR.gated({'block':'main','eps':0.01}))
        P=RR.Progress(d/'P.json',10,100,2);P.add({'wall_informational':2.0});P.write();r=json.loads((d/'P.json').read_text())
        self.assertEqual((r['cases_done'],r['cases_total'],r['mean_audit_cost_s']),(1,10,2.0));self.assertEqual(RR.PROGRESS_EVERY,60)


class Orchestrator018(unittest.TestCase):
    def test_streams(self):
        T={t['name']:t for t in RS.tasks()};self.assertEqual(set(T),{'transfer','gti','repro','g11'})
        self.assertEqual((RS.CAP,RS.MAX_WORKERS),(7200,8))
        for n,t in T.items():self.assertEqual((t['workers'],t['budget']),RS.STREAMS[n]);self.assertTrue(t['mandatory'])
        self.assertEqual(T['repro']['deps'],['transfer']);self.assertEqual(T['g11']['deps'],['transfer'])
        W={n:t['workers'] for n,t in T.items()}
        self.assertLessEqual(W['transfer']+W['gti'],8);self.assertLessEqual(W['gti']+W['repro']+W['g11'],8)
        self.assertIn('main',T['repro']['cmd']);self.assertIn('run_tests_0160.py',' '.join(T['gti']['cmd']))
        self.assertIn('--progress',T['g11']['cmd'])


class RateMath018(unittest.TestCase):
    def test_projection(self):
        jobs=[('main','a',i,0.0) for i in range(10)]+[('main','b',i,0.02) for i in range(4)]
        r=RM.project(jobs,{'a/0.0':2.0,'b/0.02':5.0},2);self.assertEqual(r['raw_s'],20.0);self.assertEqual(r['projected_s'],35.0)
        with self.assertRaises(SystemExit):RM.project(jobs,{'a/0.0':2.0},2)
        self.assertEqual((RM.FACTOR,RM.FILL),(1.75,0.8))


if __name__=='__main__':unittest.main()
