"""Study-024 process scripts: watchdog_024 (wrapper over the frozen watchdog_014), hbsentinel_024 / hb_attribution_024,
run_tests_0210 K rules (K_0200_113, deviation #116), launch_study_024 refusals (G_PROC a), first log line (G_PROC b), seal_024 heartbeat / reproset block, study024_storage gzip,
run_reference_024 checkpoint / PROGRESS / gated set / small-set mutation guard, run_study_024 stream table invariants (no
literal budgets), rate_math_024 projection, make_freeze_024 file list. Smoke only; every temp directory is removed."""
import json,shutil,subprocess,sys,tempfile,threading,time,unittest
from pathlib import Path
from scripts import watchdog_024 as W,run_tests_0210 as RT,seal_024 as S,study024_storage as ST,run_reference_024 as RR,run_study_024 as RS
from scripts import hbsentinel_024 as HS,hb_attribution_024 as HA,rate_math_024 as RM,make_freeze_024 as MF


class _Tmp(unittest.TestCase):
    def tmp(self):
        d=Path(tempfile.mkdtemp(prefix='brute-t024-'));self.addCleanup(shutil.rmtree,d,True);return d


class Watchdog024(_Tmp):
    def test_paths(self):self.assertTrue(str(W.STUDY).endswith('results/study-024'));self.assertEqual(W.CAP,7200)

    def test_kill_thread(self):
        d=self.tmp();(d/'RUN_T0').write_text(f'{time.time()}\n')
        p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],start_new_session=True)
        (d/'RUN_STATE_024.json').write_text(json.dumps({'running':{'x':{'pgid':p.pid}}}))
        rc=W.run(d,cap=3,period=0.5,kill_after=5,fsync_every=1);p.wait(5)
        self.assertEqual(rc,3);stop=json.loads((d/'STOP_024.json').read_text())
        self.assertEqual(stop['survivors'],[]);self.assertIn(p.pid,stop['process_groups'])
        hb=S.heartbeat(d,float((d/'RUN_T0').read_text()));self.assertGreaterEqual(hb['beats'],4);self.assertLess(hb['max_gap_s'],2)

    def test_run_done_exits(self):
        d=self.tmp();(d/'RUN_T0').write_text(f'{time.time()}\n');(d/'RUN_DONE_024.json').write_text('{}')
        self.assertEqual(W.run(d,cap=60,period=0.2),0);self.assertFalse((d/'STOP_024.json').exists())


class RunTests0210(unittest.TestCase):
    def test_k_list_and_paths(self):
        from scripts import run_tests_0200 as Z
        self.assertEqual(RT.K_ALLOWED,Z.K_ALLOWED);self.assertEqual(RT.TAGS,Z.TAGS);self.assertNotIn('0200',RT.TAGS)
        self.assertTrue(str(RT.OUT).endswith('study-024/TEST_SUITE_024.json'));self.assertTrue(str(RT.PLAN).endswith('BRUTE_PLAN_024.json'))
        self.assertTrue(all('0210' in g for g in RT.TOOLING_GLOBS))

    def test_new_tests_against_v0200(self):
        n=RT.new_tests();self.assertIn('test_stitchedregion_0210.py',n);self.assertIn('test_certify10_0210.py',n);self.assertNotIn('test_lrregion_0200.py',n)

    def _m(self,r0200,r1ok=True):
        return {'test_x.py':{'results':{'test_x.T.test_a':['ok']},'tests_run':1,'skipped':[]},
                'test_release_0200.py':{'results':{RT.K_0200_113:r0200},'tests_run':1,'skipped':[]},
                'test_release_0200_r1.py':{'results':{'test_release_0200_r1.R.test_a':['ok' if r1ok else 'fail','x']},'tests_run':1,'skipped':[]}}

    def test_k0200_113(self):
        plain={'tests_run':3,'skipped':[]};fr={'changed':[]};msg=['error','Traceback ... VerificationError: '+RT.K_0200_113_MSG+'\n']
        V=RT.verdict(self._m(msg),plain,fr,{},{},new_tests_=());self.assertTrue(V['k_rules']['0200_113']['applied']);self.assertTrue(V['clauses']['i_only_declared_failures'])
        for bad in (self._m(['error','other error']),self._m(msg,r1ok=False)):
            V=RT.verdict(bad,plain,fr,{},{},new_tests_=());self.assertFalse(V['clauses']['i_only_declared_failures'])
        m=self._m(msg);m['test_release_0200.py']['results']['test_release_0200.Release0200.test_version_consistent']=['fail','x']
        self.assertFalse(RT.verdict(m,plain,fr,{},{},new_tests_=())['clauses']['i_only_declared_failures'])

    def test_clause_vi_tooling_order(self):
        m={'test_x.py':{'results':{'test_x.T.test_a':['ok']},'tests_run':1,'skipped':[]}};plain={'tests_run':1,'skipped':[]};fr={'changed':[]}
        V=RT.verdict(m,plain,fr,{},{},new_tests_=(),tooling=('scripts/verify_release_0210.py',))
        self.assertFalse(V['clauses']['vi_tooling_order']);self.assertFalse(V['passed'])
        self.assertTrue(RT.verdict(m,plain,fr,{},{},new_tests_=(),tooling=())['clauses']['vi_tooling_order'])


class Launcher024(_Tmp):
    def test_refuses_hooks(self):
        from scripts import launch_study_024 as L
        for env in ({'SMOKE':'1'},{'BRUTE_SMOKE_DRILL':'1'},{'CAP_S':'5'},{'BUDGET_S':'1'},{'LIMIT':'1'},{'SKIP_GTI':'1'},{'STUDY_DIR_024':'/tmp/x'},{'STUDY_DIR_023':'x'},{'STUDY_DIR_':'x'}):
            self.assertEqual(L.refused(dict(env,PATH='/bin')),sorted(env));self.assertIn('refusing: dry-run hook',L.preflight(dict(env)))
        self.assertEqual(L.refused({'PATH':'/bin','SMOKEY':'1','MY_STUDY_DIR_X':'1'}),[])
        e=L.clean_env({'SMOKE':'1','STUDY_DIR_024':'x','PATH':'/bin'});self.assertNotIn('SMOKE',e);self.assertNotIn('STUDY_DIR_024',e);self.assertEqual(e['PATH'],'/bin')

    def test_preflight_dir(self):
        from scripts import launch_study_024 as L
        d=self.tmp();self.assertIn('RUN_T0 missing',L.preflight({},d));(d/'RUN_T0').write_text('1\n');self.assertIsNone(L.preflight({},d))
        (d/'RUN_STATE_024.json').write_text(json.dumps({'orchestrator_pid':__import__('os').getpid()}));self.assertIn('alive',L.preflight({},d))
        (d/'RUN_STATE_024.json').unlink();(d/'LAUNCH_024.json').write_text('{}');self.assertIn('LAUNCH_024.json exists',L.preflight({},d))

    def test_cli_refuses(self):
        import os
        env=dict(os.environ,SMOKE='1',PYTHONPATH=str(Path(__file__).resolve().parents[1]))
        p=subprocess.run([sys.executable,'scripts/launch_study_024.py','--check-only'],cwd=Path(__file__).resolve().parents[1],env=env,capture_output=True,text=True)
        self.assertEqual(p.returncode,3);self.assertIn('SMOKE',p.stdout)


class FirstLine024(unittest.TestCase):
    def test_first_line(self):
        src=Path(RS.__file__).read_text();self.assertIn('def first_line',src)
        body=src[src.index('def main'):];self.assertIn('first_line(',body.split('\n',3)[1]+body.split('\n',3)[2])


class Sentinel024(_Tmp):
    def test_sentinel_records_and_exits(self):
        d=self.tmp();(d/'RUN_T0').write_text(f'{time.time()}\n')
        p=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'],start_new_session=True)
        (d/'RUN_STATE_024.json').write_text(json.dumps({'orchestrator_pid':p.pid}))
        t=threading.Timer(5.0,lambda:(d/'RUN_DONE_024.json').write_text('{}'));t.start()
        self.assertEqual(HS.run(d,cap=60),0);p.kill();p.wait(5)
        R=[json.loads(l) for l in (d/'HB_SENTINEL_024.jsonl').read_text().splitlines()]
        self.assertGreaterEqual(len(R),2);self.assertIn('workers_cpu_s',R[0])

    def test_classes(self):
        self.assertEqual(HA.classify(30,30,30,29,0,4),'box_pause');self.assertEqual(HA.classify(60,60,60,1,200,4),'watchdog_stall')


class SealStorage024(_Tmp):
    def test_gz_and_blocks(self):
        self.assertEqual(ST._gz(b'abc'*100),ST._gz(b'abc'*100));self.assertTrue(str(ST.STUDY).endswith('study-024'))
        self.assertEqual(ST.BLOCKS,('transfer','repro/reproset'))
        d=self.tmp();(d/'x.txt').write_text('1');B=S.build(d)
        self.assertEqual(set(B['blocks']),{'transfer','repro/reproset'});self.assertEqual(B['study'],'BRUTE-0210-STITCHED-LR-024')


class Reference024(_Tmp):
    def test_checkpoint_progress_gated_and_small_mutation(self):
        d=self.tmp();ck=d/'c.jsonl'
        with open(ck,'w') as fh:RR._append(fh,{'event':'start','t':1});RR._append(fh,{'case':'a/1/0.02','ok':True,'first_difference':None,'wall_informational':0})
        cases,ev=RR.read_ck(ck);self.assertEqual(list(cases),['a/1/0.02']);self.assertEqual(list(ev),['start'])
        self.assertIsNone(RR.mutation([{'schema':'brute.case.v21_0'}]*10,{},1,{})['passed']);self.assertIn('v0210_reference',RR.R.__name__)
        self.assertTrue(RR.gated({'block':'main','eps':0.02}));self.assertFalse(RR.gated({'block':'stress','eps':0.05}))
        self.assertTrue(RR.gated({'block':'main','eps':0.01}));self.assertTrue(RR.gated({'block':'main','eps':0.0}))
        P=RR.Progress(d/'P.json',10,100,2);P.add({'wall_informational':2.0});P.write();r=json.loads((d/'P.json').read_text())
        self.assertEqual((r['cases_done'],r['cases_total'],r['mean_audit_cost_s']),(1,10,2.0));self.assertEqual(RR.PROGRESS_EVERY,60)


class Orchestrator024(unittest.TestCase):
    def test_streams(self):
        T={t['name']:t for t in RS.tasks()};self.assertEqual(set(T),{'transfer','gti','repro','g11'})
        self.assertEqual((RS.CAP,RS.MAX_WORKERS),(7200,8))
        for n,t in T.items():self.assertEqual((t['workers'],t['budget']),RS.STREAMS[n]);self.assertTrue(t['mandatory'])
        self.assertEqual(T['repro']['deps'],['transfer']);self.assertEqual(T['g11']['deps'],['transfer'])
        W_={n:t['workers'] for n,t in T.items()}
        self.assertLessEqual(W_['transfer']+W_['gti'],8);self.assertLessEqual(W_['gti']+W_['repro']+W_['g11'],8)
        self.assertIn(RS.RBLOCK,T['repro']['cmd']);self.assertIn('run_tests_0210.py',' '.join(T['gti']['cmd']))
        self.assertNotIn('SMOKE',RS.stream_env({'SMOKE':'1','X':'1'},'gti'));self.assertIn('SMOKE',RS.stream_env({'SMOKE':'1'},'transfer'))
        if not RS.SM:self.assertEqual((RS.BLOCK,RS.RBLOCK),('transfer','reproset'));self.assertNotIn('--every',T['repro']['cmd'])   # held-out layout (a SMOKE=1 dry run swaps in the smoke blocks)
        self.assertIn('--progress',T['g11']['cmd']);self.assertIn(RS.BLOCK,T['transfer']['cmd'])
        self.assertLessEqual(max(RS.STREAMS['gti'][1],RS.STREAMS['transfer'][1]+max(RS.STREAMS['repro'][1],RS.STREAMS['g11'][1])),RS.CAP)


class RateMath024(unittest.TestCase):
    def test_projection(self):
        jobs=[('main','a',i,0.0) for i in range(10)]+[('stress','b',i,0.05) for i in range(4)]
        r=RM.project(jobs,{'a/0.0':2.0,'b/0.05':5.0},2);self.assertEqual(r['raw_s'],20.0);self.assertEqual(r['projected_s'],35.0)
        with self.assertRaises(SystemExit):RM.project(jobs,{'a/0.0':2.0},2)
        self.assertEqual((RM.FACTOR,RM.FILL),(1.75,0.8))


class Freeze024(unittest.TestCase):
    def test_files(self):
        for f in ('brute/stitchedregion.py','brute/api/certify10.py','experiments/v0210_reference.py','scripts/run_tests_0210.py','tests/test_scripts_024.py',
                  'results/smoke-024/KILL_DRILL_024.json','docs/research/v0.21.0/STITCHED_LEMMA_024.md','docs/research/v0.21.0/RATE_MATH_024.json',
                  'experiments/COMMIT_ORDER_024.json','scripts/launch_study_024.py'):self.assertIn(f,MF.FILES)
        self.assertFalse(any('release_0210' in f for f in MF.FILES))
        self.assertEqual(len(MF.FILES),len(set(MF.FILES)))


if __name__=='__main__':unittest.main()
