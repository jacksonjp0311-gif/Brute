"""Tests for the study-033 runner and scoring scripts (v0.30.0). New file. Includes the pre-freeze test (the #129 lesson):
a sealed 36-case block is written by the runner's own _write, then make_gates_033 builds from it (with RECOUNT_033 run on
it) and --check reproduces GATES_033.json in a subprocess. Cases come from smoke seeds 9990029/9990030 (not in the smoke
block, which uses 9990001-9990006)."""
from unittest import mock
import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from experiments import brute_study_033 as ST
from experiments.brute_study_033 import run_case,jobs_for
from experiments.brute_common_033 import load,PLAN,write_new
from scripts.recount_033 import recount_case,main as recount_main
from scripts import run_reference_033 as RR
from scripts import make_gates_033 as MG
from scripts import make_freeze_033 as MF
ROOT=Path(__file__).resolve().parents[1]
ARMS={'A8','A8_random','S5','S1'}


def _case(seed,fam):
    c=run_case(seed,fam);c['block']='smoke';c['case_wall_informational']=1.0;return json.loads(json.dumps(c))


class Recount(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=_case(9990030,'control_cycle3');cls.s=_case(9990029,'scale8')

    def test_arms_and_reproduces(self):
        for c in (self.c,self.s):
            self.assertEqual(set(c['arms']),ARMS);per,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(set(per),ARMS)
            for a in ARMS:
                for k in ('label','n_min','unique','unknown','second_found','used','model','truth_consistent_final'):self.assertIn(k,c['arms'][a])
        self.assertEqual(self.c['arms']['A8']['label'],'ID');self.assertEqual(self.c['arms']['S5']['label'],'ID')
        self.assertEqual(self.s['arms']['A8_random']['used'],self.s['arms']['A8']['used'])

    def test_tamper_detected(self):
        c=copy.deepcopy(self.c);c['arms']['S5']['label']='AMB';_,bad=recount_case(c);self.assertTrue(bad)
        c=copy.deepcopy(self.c);c['arms']['A8']['model'][1][0]^=1;_,bad=recount_case(c);self.assertTrue(bad)
        c=copy.deepcopy(self.s);c['arms']['A8_random']['extra_acts'].append(0);_,bad=recount_case(c);self.assertTrue(bad)
        a=self.s['arms']['A8']
        if a['extra_acts']:
            c=copy.deepcopy(self.s);c['arms']['A8']['extra_masks'][0]^=0b1111;_,bad=recount_case(c);self.assertTrue(bad)

    def test_reference_on_case(self):
        r,ref=RR.audit(self.s);self.assertEqual(r['mismatches'],[]);self.assertTrue(r['decided'])
        mt=RR.mutation_test([self.s],[ref],8);self.assertTrue(mt['pass'],mt)

    def test_sealed_block_gates_check(self):
        """Pre-freeze: seal a full-shape block with the runner's _write, recount it, run make_gates_033, then --check."""
        P=load(PLAN);cases=[]
        for blk,fam,seed in jobs_for(P,'main'):
            c=copy.deepcopy(self.c if fam=='control_cycle3' else self.s);c.update(block=blk,family=fam,seed=seed);cases.append(c)
        with tempfile.TemporaryDirectory() as d:
            D=Path(d)/'main';D.mkdir();fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
            with mock.patch.object(ST,'FREEZE',ST.FREEZE if ST.FREEZE.exists() else fz):ST._write(D,P,'main',[ST.key(j) for j in jobs_for(P,'main')],cases,True,{'total_elapsed_informational':100.0})
            with mock.patch('scripts.recount_033.recount_case',lambda c:(recount_case(dict(c,seed=9990030 if c['family']=='control_cycle3' else 9990029,family='control_cycle3' if c['family']=='control_cycle3' else 'scale8'))[0],[])):
                self.assertEqual(recount_main([str(D)]),0)
            g=MG.build(Path(d));self.assertTrue(g['sealed_input_verified'])
            for k in ('GQB8','GAE8_headline','GCH8','G_sound','G10','G_RT','G_recount'):self.assertNotIn('INCOMPLETE',g['gates'][k].get('reason',''),k)
            self.assertTrue(g['gates']['G_RT']['pass']);self.assertTrue(g['gates']['G10']['pass']);self.assertTrue(g['gates']['G_sound']['pass'])
            for k in ('labels','actions_used','A8_rounds','A8_stop','indistinguishable_diagnosis','contrasts','query_max_s'):self.assertIn(k,g['reports'])
            (Path(d)/'GATES_033.json').write_bytes(MG.dumps(g))
            r=subprocess.run([sys.executable,'scripts/make_gates_033.py','--study-dir',d,'--check'],cwd=ROOT,capture_output=True,text=True,
                             env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
            self.assertEqual(r.returncode,0,r.stderr[-500:]);self.assertIn('reproduces',r.stdout)
            res=json.loads((D/'RESULTS.json').read_text());res['cases'][0]['arms']['A8']['label']='ID'
            (D/'RESULTS.json').write_text(json.dumps(res));g2=MG.build(Path(d));self.assertFalse(g2['sealed_input_verified'])
            self.assertIn('INCOMPLETE',g2['gates']['GQB8']['reason'])


class Gates(unittest.TestCase):
    def test_empty_study_fails_incomplete(self):
        with tempfile.TemporaryDirectory() as d:g=MG.build(Path(d))
        self.assertFalse(g['all_gated_pass'])
        self.assertEqual(set(g['gates']),{'GAE8_headline','GCH8','G_sound','G10','GS_ref','GQB8','G_RT','G_recount','GTI','G_PROC'})
        for k in ('GAE8_headline','GCH8','G_sound','G10','GS_ref','GQB8','GTI','G_RT','G_recount'):
            self.assertFalse(g['gates'][k]['pass']);self.assertIn('INCOMPLETE',g['gates'][k].get('reason',''))

    def test_constants(self):
        self.assertEqual(MG.boot_mean([1]*12),[1.0,1.0])
        self.assertEqual((MG.BOOT,MG.BOOT_SEED,MG.B_S5,MG.B_R,MG.ID_MIN,MG.IDU_MAX,MG.QB,MG.CAP),(10000,33,0.33,0.17,6,2,10.5,1800))
        self.assertEqual(MG.PROC_ORDER,('preregistration_033','build_authorization_033','seedcheck_033','source_freeze_033','run_start_033','run_end_033'))
        self.assertGreaterEqual(4/12,MG.B_S5);self.assertLess(3/12,MG.B_S5);self.assertGreaterEqual(3/12,MG.B_R);self.assertLess(2/12,MG.B_R)


class Jobs(unittest.TestCase):
    def test_counts(self):
        P=load(PLAN);j=jobs_for(P,'main');self.assertEqual(len(j),36)
        self.assertEqual([sum(1 for x in j if x[1]==f) for f in ST.FAM_ORDER],[6,12,12,6])
        self.assertEqual(len(jobs_for(P,'smoke')),6);self.assertEqual(j[0][1],'scale16');self.assertEqual(j[-1][1],'control_cycle3')
        self.assertEqual(ST.ORDER,('A8','A8_random','S5','S1'));self.assertEqual(ST.ARM_BUDGET,120.0)
        for x in j:ST.check_job(x,P)


class Freeze(unittest.TestCase):
    def test_files_exist(self):
        for f in MF.FILES:
            if f not in ('experiments/COMMIT_ORDER_033.json','docs/research/BRUTE_DEVIATIONS_033_138.md','results/diag-033/PREFREEZE_SMOKE_GATES_033.json'):
                self.assertTrue((ROOT/f).exists(),f)


if __name__=='__main__':unittest.main()
