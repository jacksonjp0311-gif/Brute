"""Tests for the study-039 runner and scoring scripts (v0.36.0). New file; built from tests/test_scripts_038.py (frozen).
Includes the pre-freeze test (the #129 lesson): a sealed 54-case block is written by the runner's own _write and merge, then
make_gates_039 builds from it (RECOUNT_039 run on it) and --check reproduces GATES_039.json in a subprocess. Cases come from
an old development seed (10050001, control_cycle3), outside every study-039 range (plan, smoke)."""
from unittest import mock
import copy,json,random,subprocess,sys,tempfile,unittest
from pathlib import Path
from experiments import brute_study_039 as ST
from experiments import worlds_039 as W
from experiments.brute_common_039 import load,PLAN
from scripts.recount_039 import recount_case,main as recount_main
from scripts import make_gates_039 as MG
from scripts import make_freeze_039 as MF
from scripts.check_seeds_039 import ranges_039
ROOT=Path(__file__).resolve().parents[1];DEV=10050001


def _groups(seed,pkey):
    out={}
    for g in ST.GROUPS:
        c=ST.run_group(seed,pkey,g);c['block']='smoke';c['job_wall_informational']=1.0;out[g]=json.loads(json.dumps(c))
    return out


class Runner(unittest.TestCase):
    def test_jobs_main(self):
        P=load(PLAN);J=ST.jobs_for(P,'main');G=ST.plan_groups(P)
        self.assertEqual(len(J),sum(n*len(G[k]) for k,n in MG.EXPECTED.items()));self.assertEqual(len({ST.key(j) for j in J}),len(J))
        R=ranges_039(P)
        for b,k,s,g in J:self.assertTrue(R['target/'+k][0]<=s<=R['target/'+k][1])
        for j in J[::17]:ST.check_job(j,P)
        self.assertEqual((J[0][3],J[0][1]),('A14','scale16'))
        self.assertEqual([j[3] for j in J],sorted([j[3] for j in J],key=ST.GROUPS.index))

    def test_jobs_smoke(self):
        P=load(PLAN);J=ST.jobs_for(P,'smoke');self.assertTrue(all(10590001<=j[2]<=10590012 for j in J))
        self.assertEqual(len(J),12*len(ST.GROUPS))

    def test_check_job_refuses_foreign_seed(self):
        P=load(PLAN)
        with self.assertRaises(Exception):ST.check_job(('main','scale16',10520001,'A14'),P)
        with self.assertRaises(Exception):ST.check_job(('smoke','scale16',10530001,'A14'),P)

    def test_perm_world(self):
        for s in range(3):
            w=W.world(10059001+s,'perm12');self.assertEqual((w.n,w.k),(12,3))
            for a in range(3):self.assertEqual(sorted(w.transitions[q][a] for q in range(12)),list(range(12)))
            self.assertEqual(W.minimal_states(w),12)

    def test_sizes(self):
        for f,n in (('scale12',12),('scale14',14),('scale16',16),('control_cycle3',3)):self.assertEqual(W.world(10059011,f).n,n)

    def test_random_stream_distinct_from_034(self):
        a=[random.Random(DEV*91039+39).randrange(3) for _ in range(64)];b=[random.Random(DEV*91034+34).randrange(3) for _ in range(64)]
        self.assertNotEqual(a,b)

    def test_merge_and_recount_control(self):
        g=_groups(DEV,'control');jobs=[('smoke','control',DEV,x) for x in ST.GROUPS];done={ST.key(j):g[j[3]] for j in jobs}
        c=ST.merge(jobs,done)[0];self.assertEqual(tuple(c['arms']),ST.ORDER)
        out,bad=recount_case(c);self.assertEqual(bad,[]);self.assertTrue(all(v['label']=='ID' for v in out.values()))
        c2=copy.deepcopy(c);c2['arms']['A14']['label']='IDF';self.assertNotEqual(recount_case(c2)[1],[])
        c3=copy.deepcopy(c);c3['arms']['A14_random']['extra_acts']=[0]+list(c3['arms']['A14_random']['extra_acts']);self.assertNotEqual(recount_case(c3)[1],[])


class PreFreeze(unittest.TestCase):
    def test_sealed_block_gates_reproduce(self):
        g=_groups(DEV,'control');P=load(PLAN);jobs=[];done={}
        for k,n in MG.EXPECTED.items():
            for i in range(n):
                for x in ST.plan_groups(P)[k]:
                    j=('main',k,DEV+i if k=='control' else 10059100+i,x);jobs.append(j);r=copy.deepcopy(g[x]);r['block']='main';r['key']=k;r['seed']=j[2];done[ST.key(j)]=r
        cases=ST.merge(jobs,done);self.assertEqual(len(cases),54)
        with tempfile.TemporaryDirectory() as d:
            D=Path(d);(D/'main').mkdir();fz=D/'FZ.json';fz.write_text('{}')
            with mock.patch.object(ST,'FREEZE',fz):ST._write(D/'main',P,'main',[ST.key(j) for j in jobs],cases,True,{'total_elapsed_informational':1.0})
            rc=recount_main([str(D/'main')]);self.assertEqual(rc,1)  # relabelled seeds regenerate other worlds: the recount must notice
            G=MG.build(D);self.assertTrue(G['sealed_input_verified']);(D/'GATES_039.json').write_bytes(MG.dumps(G))
            self.assertNotIn('reason',G['gates']['GC14_headline']);self.assertFalse(G['gates']['G_recount']['pass'])
            r=subprocess.run([sys.executable,'scripts/make_gates_039.py','--study-dir',str(D),'--check'],cwd=ROOT,capture_output=True,text=True,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
            self.assertEqual(r.returncode,0,r.stderr[-500:])

    def test_incomplete_input(self):
        with tempfile.TemporaryDirectory() as d:
            G=MG.build(Path(d));self.assertFalse(G['gates']['GC14_headline']['pass']);self.assertIn('INCOMPLETE',G['gates']['GC14_headline']['reason'])

    def test_freeze_list(self):
        gen={'experiments/COMMIT_ORDER_039.json','results/diag-039/PREFREEZE_SMOKE_GATES_039.json','docs/research/BRUTE_DEVIATIONS_039_150.md'}
        miss=[f for f in MF.FILES if not (ROOT/f).exists() and f not in gen];self.assertEqual(miss,[])
        for f in ('brute/scalesearch14.py','experiments/brute_study_039.py','scripts/make_gates_039.py','scripts/recount_039.py','scripts/run_reference_039.py'):self.assertIn(f,MF.FILES)


if __name__=='__main__':unittest.main()
