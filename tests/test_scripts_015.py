"""Study-015 process scripts: watchdog_015 (wrapper over the frozen watchdog_014; heartbeat fields, kill thread),
run_tests_0130 K rules, seal_015 heartbeat, study015_storage gzip, run_reference_015 checkpoint / small-set mutation
guard, run_study_015 stream table. Smoke only, temp directories."""
import json,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from scripts import watchdog_015 as W,run_tests_0130 as RT,seal_015 as S,study015_storage as ST,run_reference_015 as RR,run_study_015 as RS


class Watchdog015(unittest.TestCase):
    def test_paths(self):self.assertTrue(str(W.STUDY).endswith('results/study-015'));self.assertEqual(W.CAP,7200)

    def test_kill_thread(self):
        d=Path(tempfile.mkdtemp());(d/'RUN_T0').write_text(f'{time.time()}\n')
        p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
        (d/'RUN_STATE_015.json').write_text(json.dumps({'running':{'x':{'pgid':p.pid}}}))
        rc=W.run(d,cap=3,period=0.5,kill_after=5,fsync_every=1);p.wait(5)
        self.assertEqual(rc,3);stop=json.loads((d/'STOP_015.json').read_text())
        self.assertEqual(stop['survivors'],[]);self.assertIn(p.pid,stop['process_groups']);self.assertLess(stop['kill_latency_s'],15)
        hb=S.heartbeat(d,float((d/'RUN_T0').read_text()));self.assertGreaterEqual(hb['beats'],4);self.assertLess(hb['max_gap_s'],2)

    def test_run_done_exits(self):
        d=Path(tempfile.mkdtemp());(d/'RUN_T0').write_text(f'{time.time()}\n');(d/'RUN_DONE_015.json').write_text('{}')
        self.assertEqual(W.run(d,cap=60,period=0.2),0);self.assertFalse((d/'STOP_015.json').exists())


class RunTests0130(unittest.TestCase):
    def test_k0120_needs_clean_pass(self):
        f={sorted(RT.K_ALLOWED['0120'])[0]}
        m={'test_release_0120.py':{'results':{t:(['fail'] if t in f else ['ok']) for t in RT.K_ALLOWED['0120']},'tests_run':4,'skipped':[]}}
        plain={'tests_run':4,'skipped':[]};fr={'changed':[]};ok={'results':{t:['ok'] for t in f}}
        self.assertTrue(RT.verdict(m,plain,fr,{},{'0120':ok},new_tests=())['clauses']['i_only_declared_failures'])
        self.assertFalse(RT.verdict(m,plain,fr,{},{'0120':None},new_tests=())['clauses']['i_only_declared_failures'])
        self.assertEqual(RT.TAGS['0120'],'v0.12.0');self.assertIn('test_release_0110.Release0110.test_embeddable_api_answers',RT.K_ALLOWED['0110'])

    def test_new_tests_against_v0120(self):self.assertIn('test_api_certify3_0130.py',RT.NEW_TESTS);self.assertNotIn('test_api_certify2_0120.py',RT.NEW_TESTS)


class Storage015(unittest.TestCase):
    def test_gz(self):self.assertEqual(ST._gz(b'abc'*100),ST._gz(b'abc'*100));self.assertTrue(str(ST.STUDY).endswith('study-015'))


class Reference015(unittest.TestCase):
    def test_checkpoint_and_small_mutation(self):
        d=Path(tempfile.mkdtemp());ck=d/'c.jsonl'
        with open(ck,'w') as fh:RR._append(fh,{'event':'start','t':1});RR._append(fh,{'case':'a/1/0.1','ok':True,'first_difference':None,'wall_informational':0})
        cases,ev=RR.read_ck(ck);self.assertEqual(list(cases),['a/1/0.1']);self.assertEqual(list(ev),['start'])
        self.assertIsNone(RR.mutation([{}]*3,{},1,{})['passed']);self.assertIn('v0130_reference',RR.R.__name__)


class Orchestrator015(unittest.TestCase):
    def test_streams(self):
        T={t['name']:(t['workers'],t['budget'],t['deps']) for t in RS.tasks()}
        self.assertEqual(T,{'transfer':(4,3000,[]),'gti':(2,3600,[]),'repro':(2,1500,['transfer']),'g11':(2,2400,['transfer'])})
        self.assertEqual((RS.CAP,RS.MAX_WORKERS),(7200,8))


if __name__=='__main__':unittest.main()
