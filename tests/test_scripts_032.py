"""Tests for the study-032 runner and scoring scripts (v0.29.0). New file. Includes the pre-freeze test (the #129 lesson):
a sealed 48-case block is written by the runner's own _write, then make_gates_032 builds from it and --check reproduces
GATES_032.json in a subprocess. Cases run with a reduced per-arm budget (test only) on smoke seeds 9890029/9890030."""
from unittest import mock
import copy,functools,json,subprocess,sys,tempfile,unittest
from pathlib import Path
from experiments import brute_study_032 as ST
from experiments.brute_study_032 import run_case,jobs_for
from experiments.brute_common_032 import load,PLAN
from experiments import v0290_reference as REF
from scripts.recount_032 import recount_case,flip_profile as rc_flip
from scripts import make_gates_032 as MG
from scripts import make_freeze_032 as MF
ROOT=Path(__file__).resolve().parents[1]
ARMS={'S7','S7_contra','S5','S1'}


def _case(seed,fam,eps,budget):
    with mock.patch.object(ST,'run_arm',functools.partial(ST.run_arm,budget=budget)):c=run_case(seed,fam,eps)
    c['block']='smoke';c['case_wall_informational']=1.0;return json.loads(json.dumps(c))


class Recount(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=_case(9890030,'control_cycle3',0.0,8.0);cls.n=_case(9890029,'noisy_scale8',0.05,6.0)

    def test_arms_and_reproduces(self):
        for c in (self.c,self.n):
            self.assertEqual(set(c['arms']),ARMS);per,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(set(per),ARMS)
            for a in ARMS:
                for k in ('U_inf_count','F_truth','F_truth_checked','grammar_contradicted','status_end'):self.assertIn(k,c['arms'][a])
        self.assertIn('flip_budget_end',self.n['arms']['S7']);self.assertIn('contra_checks',self.n['arms']['S7_contra'])
        self.assertEqual(self.n['noise']['B_end'],27);self.assertEqual(self.n['noise'],rc_flip(9890029,0.05,ST.STEPS))
        self.assertEqual(self.c['noise']['realised_flips'],0);self.assertEqual(self.c['S5_in_S7']['mismatches'],0)
        self.assertEqual(self.c['arms']['S7']['F_truth'],0)

    def test_tamper_detected(self):
        c=copy.deepcopy(self.c);a=c['arms']['S7'];i=next(i for i in range(ST.STEPS) if a['unk'][i][0]==0)
        a['cert'][i][0]=(a['cert'][i][0] or 0)+1;_,bad=recount_case(c);self.assertTrue(bad)
        c=copy.deepcopy(self.c);c['arms']['S1']['F_truth']+=1;_,bad=recount_case(c);self.assertTrue(bad)
        c=copy.deepcopy(self.n);c['noise']['realised_flips']+=1;_,bad=recount_case(c);self.assertTrue(bad)
        c=copy.deepcopy(self.c);c['arms']['S5']['status_end']='grammar_contradicted';_,bad=recount_case(c);self.assertTrue(bad)

    def test_s5_in_s7(self):
        c=copy.deepcopy(self.c);i=next(i for i in range(ST.STEPS) if c['arms']['S7']['unk'][i][1]==0 and c['arms']['S5']['unk'][i][1]==0
                                      and c['arms']['S5']['sup'][i][1])
        c['arms']['S7']['sup'][i][1]=[9];self.assertEqual(ST.s5_in_s7(c['arms'])['mismatches'],1)

    def test_reference_on_case(self):
        from experiments import worlds_026 as W
        w=W.world(9890029,'scale8');tr=W.trajectory(w,9890029,0.05)
        r=REF.audit_case(self.n,tr['readings'],tr['actions'],'S7',2000,None,[(i,b) for i in range(0,40,3) for b in range(3)])
        self.assertEqual(r['mismatches'],[]);self.assertGreater(r['decided'],0)
        self.assertEqual(REF.ref_bound(176),27);self.assertEqual(REF.ref_bound(0),1)

    def test_sealed_block_gates_check(self):
        """Pre-freeze: seal a full-shape block with the runner's _write, run make_gates_032 on it, then --check."""
        P=load(PLAN);cases=[]
        for blk,fam,seed,eps in jobs_for(P,'main'):
            c=copy.deepcopy(self.n if eps>0 else self.c);c.update(block=blk,family=fam,seed=seed,eps=eps);cases.append(c)
        with tempfile.TemporaryDirectory() as d:
            D=Path(d)/'main';D.mkdir();fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
            with mock.patch.object(ST,'FREEZE',ST.FREEZE if ST.FREEZE.exists() else fz):ST._write(D,P,'main',[ST.key(j) for j in jobs_for(P,'main')],cases,True,{'total_elapsed_informational':100.0})
            g=MG.build(Path(d));self.assertTrue(g['sealed_input_verified'])
            for k in ('GQB7','GRP7_headline','GNR7','G_RT'):self.assertNotIn('INCOMPLETE',g['gates'][k].get('reason',''),k)
            self.assertTrue(g['gates']['G_RT']['pass']);self.assertEqual(g['gates']['GNR7']['observed']['S5_in_S7_eps0']['mismatches'],0)
            for k in ('coverage_within_B','U_inf','X_inf','U','X','contrasts','grammar_contradicted','F_truth_recount','S5_in_S7','TP_ratio','counters_mean'):self.assertIn(k,g['reports'])
            (Path(d)/'GATES_032.json').write_bytes(MG.dumps(g))
            r=subprocess.run([sys.executable,'scripts/make_gates_032.py','--study-dir',d,'--check'],cwd=ROOT,capture_output=True,text=True,
                             env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
            self.assertEqual(r.returncode,0,r.stderr[-500:]);self.assertIn('reproduces',r.stdout)
            res=json.loads((D/'RESULTS.json').read_text());res['cases'][0]['arms']['S7']['U_count']+=1
            (D/'RESULTS.json').write_text(json.dumps(res));g2=MG.build(Path(d));self.assertFalse(g2['sealed_input_verified'])
            self.assertIn('INCOMPLETE',g2['gates']['GQB7']['reason'])


class Gates(unittest.TestCase):
    def test_empty_study_fails_incomplete(self):
        with tempfile.TemporaryDirectory() as d:g=MG.build(Path(d))
        self.assertFalse(g['all_gated_pass'])
        self.assertEqual(set(g['gates']),{'GRP7_headline','GNR7','GQB7','G10','GS_ref','GTI','G_PROC','G_RT','G_recount'})
        for k in ('GQB7','GRP7_headline','GNR7','G10','GS_ref','GTI','G_RT','G_recount'):
            self.assertFalse(g['gates'][k]['pass']);self.assertIn('INCOMPLETE',g['gates'][k].get('reason',''))

    def test_constants(self):
        self.assertEqual(MG.boot_mean([0.5]*12),[0.5,0.5]);self.assertEqual(MG.median([4,1,2,3]),2.5)
        self.assertEqual((MG.BOOT,MG.BOOT_SEED,MG.B_S5,MG.B_S1,MG.X_MIN,MG.NR_D,MG.NR_CI,MG.QB,MG.CAP),(10000,32,-0.10,-0.05,3,0.05,0.08,10.5,1800))
        self.assertEqual(MG.PROC_ORDER,('preregistration_032','build_authorization_032','seedcheck_032','source_freeze_032','run_start_032'))


class Jobs(unittest.TestCase):
    def test_counts(self):
        P=load(PLAN);j=jobs_for(P,'main');self.assertEqual(len(j),48)
        self.assertEqual(sum(1 for x in j if x[0]=='noisy'),30);self.assertEqual(sum(1 for x in j if x[0]=='clean'),12)
        self.assertEqual(sum(1 for x in j if x[0]=='control'),6);self.assertEqual(len(jobs_for(P,'smoke')),6)
        self.assertEqual(j[0][:2],('noisy','noisy_scale16'));self.assertEqual(j[-1][1],'control_cycle3')
        self.assertEqual(ST.ORDER,('S7','S7_contra','S5','S1'));self.assertEqual(ST.ARM_BUDGET,55.0)
        self.assertTrue(all(9810001<=x[2]<=9840006 for x in j))
        for x in j:ST.check_job(x,P)


class Freeze(unittest.TestCase):
    def test_files_exist(self):
        for f in MF.FILES:
            if f not in ('experiments/COMMIT_ORDER_032.json','docs/research/BRUTE_DEVIATIONS_032_136.md','results/diag-032/PREFREEZE_SMOKE_GATES_032.json'):
                self.assertTrue((ROOT/f).exists(),f)


if __name__=='__main__':unittest.main()
