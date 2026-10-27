"""Study-017 process scripts: watchdog_017 (wrapper over the frozen watchdog_014; heartbeat fields, kill thread),
hbsentinel_017 / hb_attribution_017 (deviation #90, ungated diagnostic),
run_tests_0150 K rules, seal_017 heartbeat, study017_storage gzip, run_reference_017 checkpoint / small-set mutation
guard, run_study_017 stream table. Smoke only, temp directories."""
import json,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from scripts import watchdog_017 as W,run_tests_0150 as RT,seal_017 as S,study017_storage as ST,run_reference_017 as RR,run_study_017 as RS
from scripts import hbsentinel_017 as HS,hb_attribution_017 as HA


class Watchdog017(unittest.TestCase):
    def test_paths(self):self.assertTrue(str(W.STUDY).endswith('results/study-017'));self.assertEqual(W.CAP,7200)

    def test_kill_thread(self):
        d=Path(tempfile.mkdtemp());(d/'RUN_T0').write_text(f'{time.time()}\n')
        p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
        (d/'RUN_STATE_017.json').write_text(json.dumps({'running':{'x':{'pgid':p.pid}}}))
        rc=W.run(d,cap=3,period=0.5,kill_after=5,fsync_every=1);p.wait(5)
        self.assertEqual(rc,3);stop=json.loads((d/'STOP_017.json').read_text())
        self.assertEqual(stop['survivors'],[]);self.assertIn(p.pid,stop['process_groups']);self.assertLess(stop['kill_latency_s'],15)
        hb=S.heartbeat(d,float((d/'RUN_T0').read_text()));self.assertGreaterEqual(hb['beats'],4);self.assertLess(hb['max_gap_s'],2)

    def test_run_done_exits(self):
        d=Path(tempfile.mkdtemp());(d/'RUN_T0').write_text(f'{time.time()}\n');(d/'RUN_DONE_017.json').write_text('{}')
        self.assertEqual(W.run(d,cap=60,period=0.2),0);self.assertFalse((d/'STOP_017.json').exists())


class RunTests0150(unittest.TestCase):
    def test_k0120_needs_clean_pass(self):
        f={sorted(RT.K_ALLOWED['0120'])[0]}
        m={'test_release_0120.py':{'results':{t:(['fail'] if t in f else ['ok']) for t in RT.K_ALLOWED['0120']},'tests_run':4,'skipped':[]}}
        plain={'tests_run':4,'skipped':[]};fr={'changed':[]};ok={'results':{t:['ok'] for t in f}}
        self.assertTrue(RT.verdict(m,plain,fr,{},{'0120':ok},new_tests=())['clauses']['i_only_declared_failures'])
        self.assertFalse(RT.verdict(m,plain,fr,{},{'0120':None},new_tests=())['clauses']['i_only_declared_failures'])
        self.assertEqual(RT.TAGS['0120'],'v0.12.0');self.assertIn('test_release_0110.Release0110.test_embeddable_api_answers',RT.K_ALLOWED['0110'])

    def test_k0130_declared(self):
        self.assertEqual(RT.TAGS['0130'],'v0.13.0');self.assertEqual(len(RT.K_ALLOWED['0130']),4)
        self.assertIn('test_release_0130.Release0130.test_embeddable_api_answers',RT.K_ALLOWED['0130'])

    def test_k0140_declared(self):
        self.assertEqual(RT.TAGS['0140'],'v0.14.0');self.assertEqual(len(RT.K_ALLOWED['0140']),4)
        self.assertIn('test_release_0140.Release0140.test_embeddable_api_answers',RT.K_ALLOWED['0140'])

    def test_new_tests_against_v0140(self):self.assertIn('test_api_certify5_0150.py',RT.NEW_TESTS);self.assertNotIn('test_api_certify4_0140.py',RT.NEW_TESTS)


class Sentinel017(unittest.TestCase):
    def test_sentinel_records_and_exits(self):
        d=Path(tempfile.mkdtemp());(d/'RUN_T0').write_text(f'{time.time()}\n')
        p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
        (d/'RUN_STATE_017.json').write_text(json.dumps({'orchestrator_pid':p.pid}))
        import threading
        t=threading.Timer(5.0,lambda:(d/'RUN_DONE_017.json').write_text('{}'));t.start()
        self.assertEqual(HS.run(d,cap=60),0);p.kill();p.wait(5)
        R=[json.loads(l) for l in (d/'HB_SENTINEL_017.jsonl').read_text().splitlines()]
        self.assertGreaterEqual(len(R),2)
        for k in ('wall','monotonic','boottime','max_tick_gap_mono','workers_cpu_s','n_desc','cpu_jiffies','ckpt_bytes'):self.assertIn(k,R[0])
        self.assertLess(max(r['max_tick_gap_mono'] for r in R),2.0);self.assertIsNotNone(R[0]['workers_cpu_s'])

    def test_classes(self):
        self.assertEqual(HA.classify(60,30,30,29,0,4),'clock_step');self.assertEqual(HA.classify(30,30,30,29,0,4),'box_pause')
        self.assertEqual(HA.classify(60,30,60,29,0,4),'suspend')
        self.assertEqual(HA.classify(60,60,60,58,1,4),'box_pause')
        self.assertEqual(HA.classify(60,60,60,1,200,4),'watchdog_stall')
        self.assertEqual(HA.classify(60,60,60,58,200,4),'unattributed')

    def test_attribution_file(self):
        d=Path(tempfile.mkdtemp())
        H=[{'wall':100.0,'monotonic':10.0,'boottime':10.0},{'wall':102.0,'monotonic':12.0,'boottime':12.0},{'wall':160.0,'monotonic':70.0,'boottime':70.0}]
        S_=[{'wall':101.0,'monotonic':11.0,'max_tick_gap_mono':0.3,'workers_cpu_s':5.0,'n_desc':4,'cpu_jiffies':None,'ckpt_bytes':0},
            {'wall':159.5,'monotonic':69.5,'max_tick_gap_mono':58.0,'workers_cpu_s':5.5,'n_desc':4,'cpu_jiffies':None,'ckpt_bytes':0}]
        (d/'HEARTBEAT_017.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in H));(d/'HB_SENTINEL_017.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in S_))
        r=HA.attribute(d);self.assertFalse(r['gated']);self.assertEqual(len(r['gaps_over_10s']),1);self.assertEqual(r['gaps_over_10s'][0]['class'],'box_pause')
        self.assertEqual(r['max_watchdog_gap_s'],58.0)


class Storage017(unittest.TestCase):
    def test_gz(self):self.assertEqual(ST._gz(b'abc'*100),ST._gz(b'abc'*100));self.assertTrue(str(ST.STUDY).endswith('study-017'))


class Reference017(unittest.TestCase):
    def test_checkpoint_and_small_mutation(self):
        d=Path(tempfile.mkdtemp());ck=d/'c.jsonl'
        with open(ck,'w') as fh:RR._append(fh,{'event':'start','t':1});RR._append(fh,{'case':'a/1/0.1','ok':True,'first_difference':None,'wall_informational':0})
        cases,ev=RR.read_ck(ck);self.assertEqual(list(cases),['a/1/0.1']);self.assertEqual(list(ev),['start'])
        self.assertIsNone(RR.mutation([{}]*3,{},1,{})['passed']);self.assertIn('v0150_reference',RR.R.__name__)


class Orchestrator017(unittest.TestCase):
    def test_streams(self):
        T={t['name']:(t['workers'],t['budget'],t['deps']) for t in RS.tasks()}
        self.assertEqual(T,{'transfer':(4,3000,[]),'gti':(2,3600,[]),'repro':(2,1500,['transfer']),'g11':(4,2400,['transfer'])})
        self.assertEqual((RS.CAP,RS.MAX_WORKERS),(7200,8))
        self.assertEqual(RS.G11_WORKERS,6)   # deviation #92
        self.assertLessEqual(2+RS.G11_WORKERS,RS.MAX_WORKERS);self.assertGreater(2+2+RS.G11_WORKERS,RS.MAX_WORKERS)   # g11 waits for repro


if __name__=='__main__':unittest.main()
