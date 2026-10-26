"""Watchdog (plan process_controls.watchdog): heartbeat, deadline kill of the orchestrator and stream process groups,
STOP_010.json with latency, early exit on RUN_DONE. Uses a temporary directory and a 4 s cap (drill only)."""
import json,os,signal,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from scripts import watchdog_010 as W
ROOT=Path(__file__).resolve().parents[1]


class Watchdog010(unittest.TestCase):
    def _dir(self):
        d=Path(tempfile.mkdtemp());(d/'RUN_T0').write_text(f'{time.time()}\n');return d

    def test_kill_at_deadline(self):
        d=self._dir()
        orch=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
        # a stream that ignores SIGTERM forces the SIGKILL path
        s=subprocess.Popen([sys.executable,'-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)'],start_new_session=True)
        (d/'RUN_STATE_010.json').write_text(json.dumps({'orchestrator_pid':orch.pid,'running':{'x':{'pgid':s.pid}}}))
        try:
            rc=W.run(d,cap=4,period=0.5,kill_after=2)
            self.assertEqual(rc,3);orch.wait(5);s.wait(5)
            S=json.loads((d/'STOP_010.json').read_text())
            self.assertTrue(S['sigkill_used']);self.assertEqual(S['survivors'],[]);self.assertLess(S['kill_latency_s'],15)
            self.assertEqual(S['process_groups'],[s.pid]);self.assertEqual(S['orchestrator_pids'],[orch.pid])
            H=[json.loads(l) for l in (d/'HEARTBEAT_010.jsonl').read_text().splitlines()]
            self.assertGreaterEqual(len(H),6);self.assertTrue(all('monotonic' in h for h in H))
        finally:
            for p in (orch,s):
                if p.poll() is None:p.kill()

    def test_untracked_child_stream_is_killed(self):
        d=self._dir()
        code=('import subprocess,sys,time;p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"],start_new_session=True);'
              'open(sys.argv[1],"w").write(str(p.pid));time.sleep(60)')
        cp=d/'child.pid';orch=subprocess.Popen([sys.executable,'-c',code,str(cp)],start_new_session=True)
        (d/'RUN_STATE_010.json').write_text(json.dumps({'orchestrator_pid':orch.pid,'running':{}}))
        try:
            for _ in range(50):
                if cp.exists() and cp.read_text():break
                time.sleep(0.1)
            child=int(cp.read_text())
            self.assertEqual(W.run(d,cap=3,period=0.5,kill_after=2),3);orch.wait(5)
            S=json.loads((d/'STOP_010.json').read_text());self.assertIn(child,S['process_groups']);self.assertEqual(S['survivors'],[])
            self.assertFalse(W.pid_alive(child))
        finally:
            if orch.poll() is None:orch.kill()

    def test_exit_on_run_done(self):
        d=self._dir();(d/'RUN_DONE_010.json').write_text('{}')
        self.assertEqual(W.run(d,cap=30,period=0.2),0);self.assertFalse((d/'STOP_010.json').exists())

    def test_cap_override_refused_in_study_dir(self):
        r=subprocess.run([sys.executable,'scripts/watchdog_010.py','--cap','5'],cwd=ROOT,capture_output=True,text=True,
                         env=dict(os.environ,PYTHONPATH=str(ROOT)))
        self.assertNotEqual(r.returncode,0);self.assertIn('outside',r.stderr)


if __name__=='__main__':unittest.main()
