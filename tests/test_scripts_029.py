"""Tests for the study-029 runner and scoring scripts (v0.26.0). New file. Includes the pre-freeze test required by plan
029 A1 GTI (the #129 lesson): a sealed 51-case block is written by the runner's own _write, then make_gates_029 builds
from it and --check reproduces GATES_029.json in a subprocess."""
from unittest import mock
import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from experiments import brute_study_029 as ST
from experiments.brute_study_029 import run_case,jobs_for
from experiments.brute_common_029 import load,PLAN
from scripts.recount_029 import recount_case
from scripts import make_gates_029 as MG
from scripts import make_freeze_029 as MF
from scripts import run_reference_029 as RR
ROOT=Path(__file__).resolve().parents[1]
ARMS={'S4','S4_nowit','S4_nosym','S1','S3'}


class Recount(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        c=run_case(9590001,'control_cycle3',0.0);c['block']='smoke';c['case_wall_informational']=1.0;cls.c=json.loads(json.dumps(c))

    def test_arms_and_reproduces(self):
        self.assertEqual(set(self.c['arms']),ARMS)
        per,bad=recount_case(self.c);self.assertEqual(bad,[]);self.assertEqual(set(per),ARMS)
        for a in ('S4','S4_nowit','S4_nosym'):
            for k in ('timing_informational','solves','builds','queries_by_witness','exact_answers'):self.assertIn(k,self.c['arms'][a])
        self.assertTrue(all(self.c['arms'][a]['identify']['ran'] for a in ARMS))

    def test_tamper_detected(self):
        c=copy.deepcopy(self.c);a=c['arms']['S4'];i=next(i for i in range(176) if a['unk'][i][0]==0)
        a['cert'][i][0]=(a['cert'][i][0] or 0)+1;_,bad=recount_case(c);self.assertTrue(bad)
        c=copy.deepcopy(self.c);c['arms']['S1']['F']+=1;_,bad=recount_case(c);self.assertTrue(bad)

    def test_clause_a(self):
        for o in ('S1','S3'):
            cmpd,mis,exc=MG.clause_a(self.c,o);self.assertEqual(mis,0);self.assertGreater(cmpd,0)
        self.assertEqual(MG.truth_missing(self.c)[1],0)
        c=copy.deepcopy(self.c);i=next(i for i in range(176) if c['arms']['S4']['unk'][i][1]==0 and c['arms']['S1']['unk'][i][1]==0)
        c['arms']['S4']['sup'][i][1]=[9];self.assertEqual(MG.clause_a(c,'S1')[1],1)

    def test_reference_slot(self):
        r=RR._s4_as_s2(self.c);self.assertEqual(set(r['arms']),{'S2'});self.assertIs(r['arms']['S2'],self.c['arms']['S4'])

    def test_throughput(self):
        t=MG.tp(self.c,'S4');self.assertGreater(t,0)
        a=self.c['arms']['S4'];self.assertAlmostEqual(t,a['exact_answers']/a['arm_wall_informational'])

    def test_sealed_block_gates_check(self):
        """Pre-freeze: seal a full-shape block with the runner's _write, run make_gates_029 on it, then --check."""
        P=load(PLAN);cases=[]
        for blk,fam,seed,eps in jobs_for(P,'main'):
            c=copy.deepcopy(self.c);c.update(block=blk,family=fam,seed=seed,eps=eps)
            if blk=='stress':c['arms']={a:c['arms'][a] for a in ST.ORDER['noisy']}
            cases.append(c)
        with tempfile.TemporaryDirectory() as d:
            D=Path(d)/'main';D.mkdir();fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
            with mock.patch.object(ST,'FREEZE',ST.FREEZE if ST.FREEZE.exists() else fz):ST._write(D,P,'main',[ST.key(j) for j in jobs_for(P,'main')],cases,True,{'total_elapsed_informational':100.0})
            g=MG.build(Path(d));self.assertTrue(g['sealed_input_verified'])
            for k in ('GQB','GSC4_headline','GTP','G10','G_RT'):self.assertNotIn('INCOMPLETE',g['gates'][k].get('reason',''),k)
            self.assertTrue(g['gates']['GQB']['pass']);self.assertTrue(g['gates']['G_RT']['pass'])
            self.assertIn('TP_ratio',g['reports']);self.assertIn('U_contrasts',g['reports'])
            (Path(d)/'GATES_029.json').write_bytes(MG.dumps(g))
            r=subprocess.run([sys.executable,'scripts/make_gates_029.py','--study-dir',d,'--check'],cwd=ROOT,capture_output=True,text=True,
                             env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
            self.assertEqual(r.returncode,0,r.stderr[-500:]);self.assertIn('reproduces',r.stdout)
            res=json.loads((D/'RESULTS.json').read_text());res['cases'][0]['arms']['S4']['U_count']+=1
            (D/'RESULTS.json').write_text(json.dumps(res));g2=MG.build(Path(d));self.assertFalse(g2['sealed_input_verified'])
            self.assertIn('INCOMPLETE',g2['gates']['GQB']['reason'])


class Gates(unittest.TestCase):
    def test_empty_study_fails_incomplete(self):
        with tempfile.TemporaryDirectory() as d:g=MG.build(Path(d))
        self.assertFalse(g['all_gated_pass'])
        for k in ('GQB','GSC4_headline','GTP','G10','GS_ref14','GTI','G_RT','G_recount','GAPI14'):
            self.assertFalse(g['gates'][k]['pass']);self.assertIn('INCOMPLETE',g['gates'][k].get('reason',''))

    def test_api_probe(self):
        p=MG.api_probe();self.assertIsNone(p['error']);self.assertEqual(p['searches'],['region','s2','s3','s4'])
        self.assertTrue(p['region_equals_certify13']);self.assertTrue(p['s3_equals_certify13']);self.assertTrue(p['s4_equals_s3_small'])

    def test_bootstrap_and_median(self):
        self.assertEqual(MG.boot_mean([0.5]*12),[0.5,0.5]);lo,hi=MG.boot_mean([-0.2,-0.1,-0.3,0.0]*3);self.assertLess(lo,hi);self.assertLess(hi,0.0)
        self.assertEqual(MG.median([3,1,2]),2);self.assertEqual(MG.median([4,1,2,3]),2.5);self.assertIsNone(MG.median([]))
        self.assertEqual(MG.BOOT_SEED,29);self.assertEqual(MG.B_DELTA,0.08);self.assertEqual(MG.X_MIN,5)


class Jobs(unittest.TestCase):
    def test_counts(self):
        P=load(PLAN);j=jobs_for(P,'main');self.assertEqual(len(j),51)
        self.assertEqual(sum(1 for x in j if x[0]=='stress'),9);self.assertEqual(len(jobs_for(P,'smoke')),7)
        self.assertEqual(ST.ORDER[0],('S4','S4_nowit','S4_nosym','S1','S3'));self.assertEqual(ST.ORDER['noisy'],('S4','S1','S3'))
        self.assertEqual(ST.SOLVER4,'g3')


class Freeze(unittest.TestCase):
    def test_files_exist(self):
        for f in MF.FILES:
            if f not in ('experiments/COMMIT_ORDER_029.json','docs/research/BRUTE_DEVIATIONS_029_130.md','results/diag-029/PREFREEZE_SMOKE_GATES_029.json'):
                self.assertTrue((ROOT/f).exists(),f)


if __name__=='__main__':unittest.main()
