"""Tests for the study-034 runner and scoring scripts (v0.31.0). New file. Includes the reference query against exhaustive
enumeration and the pre-freeze test (the #129 lesson): a sealed 36-case block is written by the runner's own _write, then
make_gates_034 builds from it (with RECOUNT_034 run on it) and --check reproduces GATES_034.json in a subprocess. Cases come
from smoke seeds 10090029/10090030 (in the 034 smoke range, not in the smoke block, which uses 10090001-10090006)."""
from unittest import mock
import copy,json,random,subprocess,sys,tempfile,unittest
from pathlib import Path
from experiments import brute_study_034 as ST
from experiments.brute_study_034 import run_case,jobs_for
from experiments.brute_common_034 import load,PLAN
from experiments.v0310_reference import exists_different
from scripts.recount_034 import recount_case,main as recount_main
from scripts import run_reference_034 as RR
from scripts import make_gates_034 as MG
from scripts import make_freeze_034 as MF
from tests.test_scalesearch9_0310 import rand_machine,all_machines,behaves_differently
ROOT=Path(__file__).resolve().parents[1]
ARMS={'A9','A9_random','A8','S5','S1'}


def _case(seed,fam):
    c=run_case(seed,fam);c['block']='smoke';c['case_wall_informational']=1.0;return json.loads(json.dumps(c))


def _codes(d,e,acts):
    q=0;c=[e[0]]
    for a in acts:q=d[q][a];c.append(e[q])
    return c


class Reference(unittest.TestCase):
    def test_exists_different_against_enumeration(self):
        rng=random.Random(31034);k=2;m=2;seen=set()
        for _ in range(30):
            nt=rng.randint(1,3);d,e=rand_machine(rng,nt,k,m);acts=[rng.randrange(k) for _ in range(rng.randint(0,6))];co=_codes(d,e,acts)
            n1=rng.randint(1,2);D1,E1=rand_machine(rng,n1,k,m)
            q=0
            for a in acts:q=D1[q][a]
            for n in (1,2,3):
                for mode in ('future','start'):
                    L=3+n1-1;want=False
                    for D,E in all_machines(n,k,m):
                        if _codes(D,E,acts)!=co:continue
                        p=0
                        for a in acts:p=D[p][a]
                        if behaves_differently(D,E,p if mode=='future' else 0,D1,E1,q if mode=='future' else 0):want=True;break
                    got=exists_different(acts,co,n,k,m,[D1,E1],q,mode,L);self.assertEqual(got,want,(n,mode));seen.add(got)
        self.assertEqual(seen,{True,False})


class Recount(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=_case(10090029,'control_cycle3');cls.s=_case(10090030,'scale8')

    def test_arms_and_reproduces(self):
        for c in (self.c,self.s):
            self.assertEqual(set(c['arms']),ARMS);per,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(set(per),ARMS)
        self.assertEqual(self.c['arms']['A9']['label'],'ID');self.assertEqual(self.c['arms']['S5']['label'],'ID')
        self.assertEqual(self.s['arms']['A9_random']['used'],self.s['arms']['A9']['used'])
        self.assertEqual((self.c['N'],self.s['N']),(3,8))

    def test_tamper_detected(self):
        c=copy.deepcopy(self.c);c['arms']['S5']['label']='AMB';_,bad=recount_case(c);self.assertTrue(bad)
        c=copy.deepcopy(self.c);c['arms']['A9']['label']='IDF';_,bad=recount_case(c);self.assertTrue(bad)
        c=copy.deepcopy(self.s);c['arms']['A9_random']['extra_acts'].append(0);_,bad=recount_case(c);self.assertTrue(bad)

    def test_reference_on_case(self):
        r,ch=RR.audit(self.s);self.assertEqual(r['mismatches'],[]);self.assertTrue(r['decided'])
        mt=RR.mutation_test([self.s],[ch],8);self.assertTrue(mt['pass'],mt)

    def test_sealed_block_gates_check(self):
        P=load(PLAN);cases=[]
        for blk,fam,seed in jobs_for(P,'main'):
            c=copy.deepcopy(self.c if fam=='control_cycle3' else self.s);c.update(block=blk,family=fam,seed=seed);cases.append(c)
        with tempfile.TemporaryDirectory() as d:
            D=Path(d)/'main';D.mkdir();fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
            with mock.patch.object(ST,'FREEZE',ST.FREEZE if ST.FREEZE.exists() else fz):ST._write(D,P,'main',[ST.key(j) for j in jobs_for(P,'main')],cases,True,{'total_elapsed_informational':100.0})
            with mock.patch('scripts.recount_034.recount_case',lambda c:(recount_case(dict(c,seed=10090029 if c['family']=='control_cycle3' else 10090030,family='control_cycle3' if c['family']=='control_cycle3' else 'scale8'))[0],[])):
                self.assertEqual(recount_main([str(D)]),0)
            g=MG.build(Path(d));self.assertTrue(g['sealed_input_verified'])
            for k in ('GQB9','GA9_headline','GIDF9','GCH9','G_sound','G10','G_RT','G_recount','GDIAG8'):self.assertNotIn('INCOMPLETE',g['gates'][k].get('reason',''),k)
            self.assertTrue(g['gates']['G_RT']['pass']);self.assertTrue(g['gates']['G10']['pass']);self.assertTrue(g['gates']['G_sound']['pass'])
            for k in ('labels','actions_used','A9_rounds','A9_stop','IDF_diagnosis','contrasts','query_max_s','A8_WRONG_detail'):self.assertIn(k,g['reports'])
            (Path(d)/'GATES_034.json').write_bytes(MG.dumps(g))
            r=subprocess.run([sys.executable,'scripts/make_gates_034.py','--study-dir',d,'--check'],cwd=ROOT,capture_output=True,text=True,
                             env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
            self.assertEqual(r.returncode,0,r.stderr[-500:]);self.assertIn('reproduces',r.stdout)
            res=json.loads((D/'RESULTS.json').read_text());res['cases'][0]['arms']['A9']['label']='ID'
            (D/'RESULTS.json').write_text(json.dumps(res));g2=MG.build(Path(d));self.assertFalse(g2['sealed_input_verified'])
            self.assertIn('INCOMPLETE',g2['gates']['GQB9']['reason'])


class Gates(unittest.TestCase):
    def test_empty_study_fails_incomplete(self):
        with tempfile.TemporaryDirectory() as d:g=MG.build(Path(d))
        self.assertFalse(g['all_gated_pass'])
        names={'GA9_headline','GDIAG8','GIDF9','GCH9','G_sound','G10','GS_ref','GQB9','G_RT','G_recount','GTI','G_PROC'}
        self.assertEqual(set(g['gates']),names)
        for k in names-{'G_PROC'}:
            self.assertIs(g['gates'][k]['pass'],False);self.assertIn('INCOMPLETE',g['gates'][k].get('reason',''))

    def test_constants(self):
        self.assertEqual(MG.boot_mean([1]*12),[1.0,1.0])
        self.assertEqual((MG.BOOT,MG.BOOT_SEED,MG.B_S5,MG.B_R,MG.ID_MIN,MG.IDU_MAX,MG.IDF_MIN,MG.QB,MG.CAP),(10000,34,0.33,0.17,5,2,8,10.5,1800))
        self.assertEqual(MG.PROC_ORDER,('preregistration_034','build_authorization_034','seedcheck_034','source_freeze_034','run_start_034','run_end_034'))


class Jobs(unittest.TestCase):
    def test_counts(self):
        P=load(PLAN);j=jobs_for(P,'main');self.assertEqual(len(j),36)
        self.assertEqual([sum(1 for x in j if x[1]==f) for f in ST.FAM_ORDER],[6,12,12,6])
        self.assertEqual(len(jobs_for(P,'smoke')),6);self.assertEqual(j[0][1],'scale16');self.assertEqual(j[-1][1],'control_cycle3')
        self.assertEqual(ST.ORDER,('A9','A9_random','A8','S5','S1'));self.assertEqual(ST.ARM_BUDGET,120.0)
        for x in j:ST.check_job(x,P)


class Freeze(unittest.TestCase):
    def test_files_exist(self):
        for f in MF.FILES:
            if f not in ('experiments/COMMIT_ORDER_034.json','docs/research/BRUTE_DEVIATIONS_034_140.md','results/diag-034/PREFREEZE_SMOKE_GATES_034.json'):
                self.assertTrue((ROOT/f).exists(),f)


if __name__=='__main__':unittest.main()
