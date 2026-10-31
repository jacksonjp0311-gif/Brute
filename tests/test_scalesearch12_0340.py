"""v0.34.0: A12 sound noisy stop (brute.scalesearch12). doubling_candidates is lo, max(c+1, 2c), ... capped at B_max;
bmin12 (doubling then bisection) returns the same least B as bmin11 (bisection) and an exhaustive enumeration; the a11 stop
with doubling equals active11 (same stops, steps, B); every sound ID stop on small noisy traces is checked by enumeration
(no machine of <= N states fits the trace within B_max and differs from M1 in the future or from the start); the GSAFE12
replay: the B_max confirmation on the sealed 036 trace of noisy_scale8 10210002 (A11_r3, ID at B 1, truth needs 2 flips)
finds a rival that separates from the start state, so no ID is claimed; host-agnostic source."""
import gzip,json,pathlib,random,unittest
from time import perf_counter
from brute import scalesearch10 as S10
from brute import scalesearch11 as S11
from brute import scalesearch12 as S
from brute.scalesearch7 import machine_flips
from brute.scalesearch8 import run_word
from tests.test_scalesearch10_0320 import all_machines,noisy_trace,differs,Hook

FAR=lambda:perf_counter()+60
ROOT=pathlib.Path(__file__).resolve().parents[1]
SEALED=ROOT/'results/study-036/main/RESULTS.json.gz'


class T12(unittest.TestCase):
    def test_doubling_candidates(self):
        self.assertEqual(S.doubling_candidates(1,6),[1,2,4,6]);self.assertEqual(S.doubling_candidates(1,2),[1,2])
        self.assertEqual(S.doubling_candidates(3,6),[3,6]);self.assertEqual(S.doubling_candidates(0,27),[0,1,2,4,8,16,27])
        self.assertEqual(S.doubling_candidates(5,5),[5]);self.assertEqual(S.doubling_candidates(6,5),[])

    def test_doubling_equals_bisect_and_enumeration(self):
        rng=random.Random(3701);k,m,s=2,2,1;checked=0;none=0
        for _ in range(14):
            d=[[rng.randrange(3) for _ in range(k)] for _ in range(3)];e=[rng.randrange(m) for _ in range(3)]
            rd,acts=noisy_trace(rng,d,e,8,k,rng.randint(1,4));tr=S10.Trace10(rd,acts,s)
            best=min(machine_flips(D,E,acts,rd,s) for nn in (1,2) for D,E in all_machines(nn,k,m))
            if best==0:continue
            pr=[];a=S.bmin12(S10._Owner10(30),tr,k,m,2,1,6,FAR(),probes=pr);b=S11.bmin11(S10._Owner10(30),tr,k,m,2,1,6,FAR())
            self.assertEqual(a,b);self.assertEqual([p[0] for p in pr][:1],[1])
            if best<=6:self.assertEqual(a,('ok',best));checked+=1;self.assertIn([best,True],pr)
            else:self.assertEqual(a[0],'none');none+=1;self.assertEqual([p[0] for p in pr],[1,2,4,6])
        self.assertGreater(checked,3)

    def test_a11_stop_with_doubling_equals_active11(self):
        rng=random.Random(3702);k,m,s=2,2,1
        for _ in range(8):
            d=[[rng.randrange(3) for _ in range(k)] for _ in range(3)];e=[0,1,rng.randrange(2)]
            rd,acts=noisy_trace(rng,d,e,9,k,2);out={}
            for name,fn in (('a11',lambda ob,rr:S11.active11(rd,acts,k,s,3,ob,rr,FAR(),12,4,3,'bisect')),
                            ('a12',lambda ob,rr:S.active12(rd,acts,k,s,3,ob,rr,FAR(),12,4,3,'double','a11'))):
                st={'q':S10.final_state(d,acts)}
                def ob(a):st['q']=d[st['q']][a];return (e[st['q']],)
                out[name]=fn(ob,lambda:(e[st['q']],))
            for f in ('stop','used','reads','B'):self.assertEqual(out['a11'][f],out['a12'][f])
            self.assertEqual(out['a11']['trace'].readings,out['a12']['trace'].readings)

    def test_sound_ID_checked_by_enumeration(self):
        rng=random.Random(3703);k,m,s=2,2,1;N=2;BM=3;ids=0;conf=0
        for _ in range(16):
            d=[[rng.randrange(2) for _ in range(k)] for _ in range(2)];e=[0,1]
            rd,acts=noisy_trace(rng,d,e,10,k,rng.randint(0,2));st={'q':S10.final_state(d,acts)}
            def ob(a):st['q']=d[st['q']][a];return (e[st['q']],)
            x=S.active12(rd,acts,k,s,N,ob,lambda:(e[st['q']],),FAR(),12,BM,3,'double','sound',hook=Hook())
            self.assertLessEqual(x['used'],12);self.assertEqual(x['reads'],3*x['used'])
            conf+=sum(1 for y in x['rounds'] if 'confirm' in y)
            if x['stop']!='ID':continue
            ids+=1;tr=x['trace'];M1=x['final']['model'];s1=S10.final_state(M1[0],tr.acts)
            for nn in range(1,N+1):
                for D,E in all_machines(nn,k,m):
                    if machine_flips(D,E,tr.acts,tr.readings,s)>BM:continue
                    s2=S10.final_state(D,tr.acts)
                    self.assertFalse(differs(M1[0],M1[1],s1,D,E,s2));self.assertFalse(differs(M1[0],M1[1],0,D,E,0))
        self.assertGreater(ids,3);self.assertGreater(conf,0)

    def test_GSAFE12_sealed_036_trace(self):
        from experiments import worlds_026 as W
        d=json.load(gzip.open(SEALED));c=[c for c in d['cases'] if c['seed']==10210002][0];a=c['arms']['A11_r3']
        self.assertEqual((a['label'],a['stop'],a['B_final'],a['truth_flips_trace'],a['B_max']),('WRONG','ID',1,2,6))
        acts=list(W.actions(c['seed'],c['eps'],c['k']))+a['extra_acts'];rd=[tuple(x) for x in a['base_readings']+a['extra_readings']]
        self.assertEqual(len(acts),a['T_final']);tr=S10.Trace10(rd,acts,W.S_BITS);M1=a['model'];k=c['k'];m=1<<W.S_BITS
        self.assertTrue(S10.fits(M1,tr,1));s1=S10.final_state(M1[0],tr.acts);o=S10._Owner10(120.0)
        x=S10.stop_check10(tr,1,k,m,c['N'],FAR()+600,1,120.0,'g3',o);self.assertEqual(x['stop'],'ID')
        C=S.confirm12(o,tr,k,m,c['N'],M1,s1,'ID',6,FAR()+600,'g3');self.assertNotEqual(C['verdict'],'ID')
        self.assertNotEqual(C['verdict'],'unknown');self.assertTrue(C['future']['found'] or C['start']['found'])
        F=C['future'] if C['future']['found'] else C['start'];M2=F['M2'];self.assertTrue(S10.fits(M2,tr,6))
        w=F['word_sat'];pre=tr.acts+w if C['future']['found'] else w
        p1=[M1[1][0]]+run_word(M1[0],M1[1],0,pre);p2=[M2[1][0]]+run_word(M2[0],M2[1],0,pre)
        self.assertNotEqual(p1,p2)  # a start-distinct rival: no ID at B 1 under B_max 6
        print('\nGSAFE12',json.dumps({'verdict':C['verdict'],'future':C['future']['verdicts'],
                                     'start':C['start'] and C['start']['verdicts'],'rival_n':F['n']}))

    def test_host_agnostic(self):
        src=pathlib.Path(S.__file__).read_text()
        for bad in ('import os','import threading','import subprocess','open(','socket','import time\n','print('):self.assertNotIn(bad,src)


if __name__=='__main__':unittest.main()
