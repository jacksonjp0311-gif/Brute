"""Tests for the study-030 runner and scoring scripts (v0.27.0). New file. Includes the pre-freeze test (the #129 lesson):
a sealed 51-case block is written by the runner's own _write, then make_gates_030 builds from it and --check reproduces
GATES_030.json in a subprocess."""
from unittest import mock
import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from experiments import brute_study_030 as ST
from experiments.brute_study_030 import run_case,jobs_for
from experiments.brute_common_030 import load,PLAN
from scripts.recount_030 import recount_case
from scripts import make_gates_030 as MG
from scripts import make_freeze_030 as MF
from scripts import run_reference_030 as RR
ROOT=Path(__file__).resolve().parents[1]
ARMS={'S5','S5_softcap','S4','S1'}


class Recount(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        c=run_case(9690029,'control_cycle3',0.0);c['block']='smoke';c['case_wall_informational']=1.0;cls.c=json.loads(json.dumps(c))

    def test_arms_and_reproduces(self):
        self.assertEqual(set(self.c['arms']),ARMS)
        per,bad=recount_case(self.c);self.assertEqual(bad,[]);self.assertEqual(set(per),ARMS)
        for a in ('S5','S5_softcap','S4'):
            for k in ('timing_informational','solves','builds','queries_by_witness','exact_answers'):self.assertIn(k,self.c['arms'][a])
        for a in ('S5','S5_softcap'):
            for k in ('cap_stops','build_skips','max_chunk_s_informational'):self.assertIn(k,self.c['arms'][a])
        self.assertTrue(all(self.c['arms'][a]['identify']['ran'] for a in ARMS))

    def test_tamper_detected(self):
        c=copy.deepcopy(self.c);a=c['arms']['S5'];i=next(i for i in range(176) if a['unk'][i][0]==0)
        a['cert'][i][0]=(a['cert'][i][0] or 0)+1;_,bad=recount_case(c);self.assertTrue(bad)
        c=copy.deepcopy(self.c);c['arms']['S1']['F']+=1;_,bad=recount_case(c);self.assertTrue(bad)

    def test_clause_a(self):
        for o in ('S1','S4'):
            cmpd,mis,exc=MG.clause_a(self.c,o);self.assertEqual(mis,0);self.assertGreater(cmpd,0)
        self.assertEqual(MG.truth_missing(self.c)[1],0)
        c=copy.deepcopy(self.c);i=next(i for i in range(176) if c['arms']['S5']['unk'][i][1]==0 and c['arms']['S1']['unk'][i][1]==0)
        c['arms']['S5']['sup'][i][1]=[9];self.assertEqual(MG.clause_a(c,'S1')[1],1)
        self.assertEqual(self.c['clause_a']['vs_S1']['mismatches'],0);self.assertEqual(self.c['clause_a']['vs_S4']['mismatches'],0)

    def test_reference_slot(self):
        r=RR._s5_as_s2(self.c);self.assertEqual(set(r['arms']),{'S2'});self.assertIs(r['arms']['S2'],self.c['arms']['S5'])

    def test_sealed_block_gates_check(self):
        """Pre-freeze: seal a full-shape block with the runner's _write, run make_gates_030 on it, then --check."""
        P=load(PLAN);cases=[]
        for blk,fam,seed,eps in jobs_for(P,'main'):
            c=copy.deepcopy(self.c);c.update(block=blk,family=fam,seed=seed,eps=eps)
            if blk=='stress':c['arms']={a:c['arms'][a] for a in ST.ORDER['noisy']}
            cases.append(c)
        with tempfile.TemporaryDirectory() as d:
            D=Path(d)/'main';D.mkdir();fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
            with mock.patch.object(ST,'FREEZE',ST.FREEZE if ST.FREEZE.exists() else fz):ST._write(D,P,'main',[ST.key(j) for j in jobs_for(P,'main')],cases,True,{'total_elapsed_informational':100.0})
            g=MG.build(Path(d));self.assertTrue(g['sealed_input_verified'])
            for k in ('GQB5','GSC5_headline','G10','G_RT'):self.assertNotIn('INCOMPLETE',g['gates'][k].get('reason',''),k)
            self.assertTrue(g['gates']['GQB5']['pass']);self.assertTrue(g['gates']['G_RT']['pass']);self.assertTrue(g['gates']['G10']['pass'])
            self.assertTrue(g['gates']['GSC5_headline']['observed']['a']['pass'])
            for k in ('TP_ratio','U_contrasts','ID','X','U','S5_counters_mean'):self.assertIn(k,g['reports'])
            (Path(d)/'GATES_030.json').write_bytes(MG.dumps(g))
            r=subprocess.run([sys.executable,'scripts/make_gates_030.py','--study-dir',d,'--check'],cwd=ROOT,capture_output=True,text=True,
                             env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
            self.assertEqual(r.returncode,0,r.stderr[-500:]);self.assertIn('reproduces',r.stdout)
            res=json.loads((D/'RESULTS.json').read_text());res['cases'][0]['arms']['S5']['U_count']+=1
            (D/'RESULTS.json').write_text(json.dumps(res));g2=MG.build(Path(d));self.assertFalse(g2['sealed_input_verified'])
            self.assertIn('INCOMPLETE',g2['gates']['GQB5']['reason'])


class Gates(unittest.TestCase):
    def test_empty_study_fails_incomplete(self):
        with tempfile.TemporaryDirectory() as d:g=MG.build(Path(d))
        self.assertFalse(g['all_gated_pass'])
        self.assertEqual(set(g['gates']),{'GQB5','GSC5_headline','G10','GS_ref','GTI','G_PROC','G_RT','G_recount'})
        for k in ('GQB5','GSC5_headline','G10','GS_ref','GTI','G_RT','G_recount'):
            self.assertFalse(g['gates'][k]['pass']);self.assertIn('INCOMPLETE',g['gates'][k].get('reason',''))

    def test_constants(self):
        self.assertEqual(MG.boot_mean([0.5]*12),[0.5,0.5]);lo,hi=MG.boot_mean([-0.2,-0.1,-0.3,0.0]*3);self.assertLess(lo,hi);self.assertLess(hi,0.0)
        self.assertEqual(MG.median([4,1,2,3]),2.5)
        self.assertEqual((MG.BOOT,MG.BOOT_SEED,MG.B_DELTA,MG.X_MIN,MG.QB,MG.CAP),(10000,30,0.08,5,10.5,1800))


class Jobs(unittest.TestCase):
    def test_counts(self):
        P=load(PLAN);j=jobs_for(P,'main');self.assertEqual(len(j),51)
        self.assertEqual(sum(1 for x in j if x[0]=='stress'),9);self.assertEqual(len(jobs_for(P,'smoke')),7)
        self.assertEqual(ST.ORDER[0],('S5','S5_softcap','S4','S1'));self.assertEqual(ST.ORDER['noisy'],('S5','S4','S1'))
        self.assertEqual(ST.BUDGET[0],{'S5':55.0,'S5_softcap':55.0,'S4':55.0,'S1':55.0});self.assertEqual(ST.SOLVER4,'g3')
        self.assertTrue(all(9610001<=x[2]<=9640006 for x in j))


class Freeze(unittest.TestCase):
    def test_files_exist(self):
        for f in MF.FILES:
            if f not in ('experiments/COMMIT_ORDER_030.json','docs/research/BRUTE_DEVIATIONS_030_132.md','results/diag-030/PREFREEZE_SMOKE_GATES_030.json'):
                self.assertTrue((ROOT/f).exists(),f)


if __name__=='__main__':unittest.main()
