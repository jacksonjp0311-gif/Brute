"""Tests for the study-035 runner and scoring scripts (v0.32.0). New file; built from tests/test_scripts_034.py (frozen).
Includes the reference against exhaustive enumeration and the pre-freeze test (the #129 lesson): a sealed 48-case block is
written by the runner's own _write, then make_gates_035 builds from it (RECOUNT_035 run on it) and --check reproduces
GATES_035.json in a subprocess. Cases come from old development seeds (10050001 control, 10090005 noisy_scale8), which are
outside every study-035 range (plan, smoke)."""
from unittest import mock
import copy,itertools,json,random,subprocess,sys,tempfile,unittest
from pathlib import Path
from experiments import brute_study_035 as ST
from experiments.brute_study_035 import run_case,jobs_for
from experiments.brute_common_035 import load,PLAN
from experiments.v0320_reference import exists_machine,exists_different
from scripts.recount_035 import recount_case,main as recount_main
from scripts import run_reference_035 as RR
from scripts import make_gates_035 as MG
from scripts import make_freeze_035 as MF
ROOT=Path(__file__).resolve().parents[1]
ARMS={'A10','A10_fixed','A9','S7','S5'};DEV={'control':10050001,'noisy_scale8':10090005}


def _case(seed,pkey):
    c=run_case(seed,pkey);c['block']='smoke';c['case_wall_informational']=1.0;return json.loads(json.dumps(c))


def _flips(d,e,acts,rd):
    b=lambda c:((c>>1)&1,c&1);q=0;f=sum(x!=y for x,y in zip(b(e[0]),rd[0]))
    for a,o in zip(acts,rd[1:]):q=d[q][a];f+=sum(x!=y for x,y in zip(b(e[q]),o))
    return f


class Reference(unittest.TestCase):
    def test_exists_machine_against_enumeration(self):
        rng=random.Random(32035);seen=set();k=2;m=4
        for _ in range(12):
            T=rng.randint(0,5);acts=[rng.randrange(k) for _ in range(T)];rd=[(rng.randrange(2),rng.randrange(2)) for _ in range(T+1)]
            for n in (1,2):
                best=min(_flips(d,e,acts,rd) for d in itertools.product(itertools.product(range(n),repeat=k),repeat=n) for e in itertools.product(range(m),repeat=n))
                for B in range(0,4):
                    got=exists_machine(acts,rd,n,k,m,B,10.0);self.assertEqual(got,best<=B,(n,B));seen.add(got)
        self.assertEqual(seen,{True,False})

    def test_exists_different_two_bit_against_enumeration(self):
        rng=random.Random(32036);seen=set();k=2;m=4
        def fin(d,acts,q=0):
            for a in acts:q=d[q][a]
            return q
        def differs(d1,e1,s1,d2,e2,s2):
            st=[(s1,s2)];vis={(s1,s2)}
            while st:
                p,q=st.pop()
                if e1[p]!=e2[q]:return True
                for a in range(k):
                    x=(d1[p][a],d2[q][a])
                    if x not in vis:vis.add(x);st.append(x)
            return False
        for _ in range(6):
            T=rng.randint(1,4);acts=[rng.randrange(k) for _ in range(T)];rd=[(rng.randrange(2),rng.randrange(2)) for _ in range(T+1)]
            M1=([[0,0]],[rng.randrange(m)]);B=rng.randint(0,3)
            for n in (1,2):
                for mode in ('future','start'):
                    want=any(_flips(d,e,acts,rd)<=B and differs(M1[0],M1[1],0,d,e,fin(d,acts) if mode=='future' else 0)
                             for d in itertools.product(itertools.product(range(n),repeat=k),repeat=n) for e in itertools.product(range(m),repeat=n))
                    got=exists_different(acts,rd,n,k,m,B,M1,0,mode,n+1,10.0);self.assertEqual(got,want,(n,mode,B));seen.add(got)
        self.assertEqual(seen,{True,False})


class Recount(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.c=_case(DEV['control'],'control');cls.s=_case(DEV['noisy_scale8'],'noisy_scale8')

    def test_arms_and_reproduces(self):
        for c in (self.c,self.s):
            self.assertEqual(set(c['arms']),ARMS);per,bad=recount_case(c);self.assertEqual(bad,[]);self.assertEqual(set(per),ARMS)
        self.assertEqual(self.c['arms']['A10']['label'],'ID');self.assertEqual(self.c['arms']['S5']['label'],'ID')
        self.assertEqual(self.c['arms']['A10']['B_final'],0);self.assertEqual((self.c['N'],self.s['N']),(3,8))

    def test_tamper_detected(self):
        c=copy.deepcopy(self.c);c['arms']['S5']['label']='AMB';_,bad=recount_case(c);self.assertTrue(bad)
        c=copy.deepcopy(self.c);c['arms']['A10']['label']='IDF';_,bad=recount_case(c);self.assertTrue(bad)
        c=copy.deepcopy(self.s);c['arms']['A10']['extra_acts'].append(0);_,bad=recount_case(c);self.assertTrue(bad)

    def test_reference_on_case(self):
        r,ch=RR.audit(self.s);self.assertEqual(r['mismatches'],[]);self.assertGreater(r['decided']+r['undecided'],0)
        mt=RR.mutation_test([self.s],[ch],8);self.assertTrue(mt['pass'],mt)

    def test_sealed_block_gates_check(self):
        P=load(PLAN);cases=[];src={}
        for blk,k,seed in jobs_for(P,'main'):
            base=self.c if k in ('control','clean_scale12','scale16_clean') else self.s
            c=copy.deepcopy(base);c.update(block=blk,key=k,seed=seed);cases.append(c);src[(k,seed)]=base
        with tempfile.TemporaryDirectory() as d:
            D=Path(d)/'main';D.mkdir();fz=Path(d)/'FREEZE_STANDIN.json';fz.write_text('{}')
            with mock.patch.object(ST,'FREEZE',ST.FREEZE if ST.FREEZE.exists() else fz):ST._write(D,P,'main',[ST.key(j) for j in jobs_for(P,'main')],cases,True,{'total_elapsed_informational':100.0})
            with mock.patch('scripts.recount_035.recount_case',lambda c:(recount_case(dict(src[(c['key'],c['seed'])],block=c['block']))[0],[])):
                self.assertEqual(recount_main([str(D)]),0)
            g=MG.build(Path(d));self.assertTrue(g['sealed_input_verified'])
            for k in ('GQB10','GA10_headline','GNR10','GAD10','G_sound','G10','G_RT','G_recount'):self.assertNotIn('INCOMPLETE',g['gates'][k].get('reason',''),k)
            self.assertTrue(g['gates']['G_RT']['pass']);self.assertTrue(g['gates']['G10']['pass']);self.assertIn('G16',g['secondary'])
            for k in ('labels','budget_used','A10_B_final','within_budget','contrasts','query_max_s','stops'):self.assertIn(k,g['reports'])
            (Path(d)/'GATES_035.json').write_bytes(MG.dumps(g))
            r=subprocess.run([sys.executable,'scripts/make_gates_035.py','--study-dir',d,'--check'],cwd=ROOT,capture_output=True,text=True,
                             env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
            self.assertEqual(r.returncode,0,r.stderr[-500:]);self.assertIn('reproduces',r.stdout)
            res=json.loads((D/'RESULTS.json').read_text());res['cases'][0]['arms']['A10']['label']='ID'
            (D/'RESULTS.json').write_text(json.dumps(res));g2=MG.build(Path(d));self.assertFalse(g2['sealed_input_verified'])
            self.assertIn('INCOMPLETE',g2['gates']['GQB10']['reason'])


class Gates(unittest.TestCase):
    def test_empty_study_fails_incomplete(self):
        with tempfile.TemporaryDirectory() as d:g=MG.build(Path(d))
        self.assertFalse(g['all_gated_pass'])
        names={'GA10_headline','GNR10','GAD10','GQB10','G_sound','G10','GS_ref','G_RT','G_recount','GTI','G_PROC'}
        self.assertEqual(set(g['gates']),names);self.assertEqual(set(g['secondary']),{'G16'})
        for k in names-{'G_PROC'}:
            self.assertIs(g['gates'][k]['pass'],False);self.assertIn('INCOMPLETE',g['gates'][k].get('reason',''))

    def test_constants(self):
        self.assertEqual((MG.B_S7,MG.B_FIX,MG.IDF_MIN,MG.IDU_MAX,MG.ID16,MG.QB,MG.CAP,MG.B_MAX),(0.25,0.17,4,3,2,10.5,1800,27))
        self.assertEqual(MG.PROC_ORDER,('preregistration_035','build_authorization_035','seedcheck_035','source_freeze_035','run_start_035','run_end_035'))
        self.assertEqual(MG.EXPECTED,{'noisy_scale8':12,'noisy_scale12':12,'clean_scale12':12,'scale16_clean':6,'control':6})


class Jobs(unittest.TestCase):
    def test_counts(self):
        P=load(PLAN);j=jobs_for(P,'main');self.assertEqual(len(j),48)
        self.assertEqual([sum(1 for x in j if x[1]==k) for k in ST.KEY_ORDER],[6,12,12,12,6])
        self.assertEqual(len(jobs_for(P,'smoke')),8);self.assertEqual(j[0][1],'scale16_clean');self.assertEqual(j[-1][1],'control')
        self.assertEqual(ST.ORDER,('A10','A10_fixed','A9','S7','S5'));self.assertEqual(ST.B_MAX,27);self.assertEqual(ST.QUERY_S,10)
        for x in j:ST.check_job(x,P)


class Freeze(unittest.TestCase):
    def test_files_exist(self):
        for f in MF.FILES:
            if f not in ('experiments/COMMIT_ORDER_035.json','docs/research/BRUTE_DEVIATIONS_035_142.md','results/diag-035/PREFREEZE_SMOKE_GATES_035.json'):
                self.assertTrue((ROOT/f).exists(),f)


if __name__=='__main__':unittest.main()
