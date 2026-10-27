"""Study-014 process scripts: watchdog_014 (heartbeat fields, kill thread), run_tests_0120 K rules, seal_014 heartbeat,
study014_storage gzip, run_reference_014 checkpoint / small-set mutation guard. Smoke only, temp directories."""
import json,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from scripts import watchdog_014 as W,run_tests_0120 as RT,seal_014 as S,study014_storage as ST,run_reference_014 as RR


class Watchdog014(unittest.TestCase):
    def test_beat_fields(self):
        w,r=W.beat(None);self.assertIsNone(r['gap_s'])
        for k in ('wall','monotonic','boottime','cpu_s','psi_io_some_us','psi_io_full_us'):self.assertIn(k,r)
        w2,r2=W.beat(w);self.assertGreaterEqual(r2['gap_s'],0)

    def test_kill_thread(self):
        d=Path(tempfile.mkdtemp());(d/'RUN_T0').write_text(f'{time.time()}\n')
        p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
        (d/'RUN_STATE_014.json').write_text(json.dumps({'running':{'x':{'pgid':p.pid}}}))
        rc=W.run(d,cap=3,period=0.5,kill_after=5,fsync_every=1);p.wait(5)
        self.assertEqual(rc,3);stop=json.loads((d/'STOP_014.json').read_text())
        self.assertEqual(stop['survivors'],[]);self.assertIn(p.pid,stop['process_groups']);self.assertLess(stop['kill_latency_s'],15)
        beats=[json.loads(l) for l in (d/'HEARTBEAT_014.jsonl').read_text().splitlines()];self.assertGreaterEqual(len(beats),4)
        hb=S.heartbeat(d,float((d/'RUN_T0').read_text()));self.assertLess(hb['max_gap_s'],2)

    def test_run_done_exits(self):
        d=Path(tempfile.mkdtemp());(d/'RUN_T0').write_text(f'{time.time()}\n');(d/'RUN_DONE_014.json').write_text('{}')
        self.assertEqual(W.run(d,cap=60,period=0.2),0);self.assertFalse((d/'STOP_014.json').exists())


class RunTests0120(unittest.TestCase):
    def _mods(self,fail):
        return {'test_release_0110.py':{'results':{t:(['fail'] if t in fail else ['ok']) for t in RT.K_ALLOWED['0110']},'tests_run':3,'skipped':[]}}

    def test_k0110_needs_clean_pass(self):
        f={sorted(RT.K_ALLOWED['0110'])[0]};m=self._mods(f);plain={'tests_run':3,'skipped':[]};fr={'changed':[]}
        ok={'results':{t:['ok'] for t in f}}
        self.assertTrue(RT.verdict(m,plain,fr,{},{'0110':ok},new_tests=())['clauses']['i_only_declared_failures'])
        self.assertFalse(RT.verdict(m,plain,fr,{},{'0110':None},new_tests=())['clauses']['i_only_declared_failures'])
        self.assertEqual(RT.TAGS['0100'],'v0.10.0');self.assertEqual(RT.TAGS['0110'],'v0.11.0')

    def test_new_tests_against_v0110(self):self.assertIn('test_api_certify2_0120.py',RT.NEW_TESTS);self.assertIn('test_scripts_014.py',RT.NEW_TESTS)


class Storage014(unittest.TestCase):
    def test_gz_deterministic(self):self.assertEqual(ST._gz(b'abc'*100),ST._gz(b'abc'*100));self.assertEqual(ST.BLOCKS,('transfer','repro/transfer'))


class Reference014(unittest.TestCase):
    def test_checkpoint_and_small_mutation(self):
        d=Path(tempfile.mkdtemp());ck=d/'c.jsonl'
        with open(ck,'w') as fh:RR._append(fh,{'event':'start','t':1});RR._append(fh,{'case':'a/1/0.1','ok':True,'first_difference':None,'wall_informational':0})
        cases,ev=RR.read_ck(ck);self.assertEqual(list(cases),['a/1/0.1']);self.assertEqual(list(ev),['start'])
        self.assertIsNone(RR.mutation([{}]*3,{},1,{})['passed'])


if __name__=='__main__':unittest.main()
