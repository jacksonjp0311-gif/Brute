"""v0.35.0: A13 incremental least-B and B_max confirmation (brute.scalesearch13). bmin13 on one Inc13 instance, synced as
the trace grows, returns the same least B as bmin12 (fresh per-B chain) and an exhaustive enumeration; confirm13 gives the
same verdict as confirm12 on small noisy traces; every A13 sound ID stop on small noisy traces is checked by enumeration;
GSAFE13: the A13 confirmation on the sealed 036 trace of noisy_scale8 10210002 finds a start-state-distinct rival at B_max
(no ID at B 1) and gives the same verdict as the frozen A12 confirm12; GINC13: on every sealed 037 A12_r3 noisy_scale8
trace (the REFERENCE_037 audit set) the incremental least B equals the A12 least B wherever A12 decided; host-agnostic."""
import gzip,json,pathlib,random,unittest
from time import perf_counter
from brute import scalesearch10 as S10
from brute import scalesearch12 as S12
from brute import scalesearch13 as S
from brute.scalesearch7 import machine_flips
from brute.scalesearch8 import run_word
from tests.test_scalesearch10_0320 import all_machines,noisy_trace,differs,Hook

FAR=lambda:perf_counter()+60
ROOT=pathlib.Path(__file__).resolve().parents[1]
SEALED036=ROOT/'results/study-036/main/RESULTS.json.gz'
SEALED037=ROOT/'results/study-037/main/RESULTS.json.gz'


def _trace(c,a,W):
    acts=list(W.actions(c['seed'],c['eps'],c['k']))+a['extra_acts'];rd=[tuple(x) for x in a['base_readings']+a['extra_readings']]
    return acts,rd


class T13(unittest.TestCase):
    def test_incremental_equals_fresh_and_enumeration(self):
        rng=random.Random(3801);k,m,s=2,2,1;checked=0;none=0
        for _ in range(12):
            d=[[rng.randrange(3) for _ in range(k)] for _ in range(3)];e=[rng.randrange(m) for _ in range(3)]
            rd,acts=noisy_trace(rng,d,e,10,k,rng.randint(1,4));inc=S.Inc13(2,k,m,s,6)
            try:
                for T in (5,7,10):
                    tr=S10.Trace10(rd[:T+1],acts[:T],s)
                    best=min(machine_flips(D,E,tr.acts,tr.readings,s) for nn in (1,2) for D,E in all_machines(nn,k,m))
                    if best==0:continue
                    pr=[];a=S.bmin13(S10._Owner10(30),inc,tr,1,6,FAR(),pr);b=S12.bmin12(S10._Owner10(30),tr,k,m,2,1,6,FAR())
                    self.assertEqual(a,b)
                    if best<=6:self.assertEqual(a,('ok',best));checked+=1;self.assertEqual(pr[-1],[best,True])
                    else:self.assertEqual(a[0],'none');none+=1
            finally:inc.close()
        self.assertGreater(checked,5)

    def test_prefix_change_refused(self):
        inc=S.Inc13(2,2,2,1,3);inc.sync(S10.Trace10([(0,),(1,)],[0],1))
        with self.assertRaises(ValueError):inc.sync(S10.Trace10([(0,),(0,),(1,)],[0,1],1))
        inc.close()

    def test_confirm13_equals_confirm12(self):
        rng=random.Random(3802);k,m,s=2,2,1;N=2;BM=3;n=0;seen=set()
        for _ in range(20):
            d=[[rng.randrange(2) for _ in range(k)] for _ in range(2)];e=[0,1]
            rd,acts=noisy_trace(rng,d,e,8,k,rng.randint(0,2));tr=S10.Trace10(rd,acts,s);o=S10._Owner10(30)
            B=min(machine_flips(D,E,acts,rd,s) for nn in (1,2) for D,E in all_machines(nn,k,m))
            if B>=BM:continue
            x=S10.stop_check10(tr,B,k,m,N,FAR(),1,30.0,'g3',o)
            if x['stop'] not in ('ID','IDF'):continue
            inc=S.Inc13(N,k,m,s,BM)
            try:
                a=S.confirm13(o,inc,tr,x['model'],x['s1'],x['stop'],BM,FAR());b=S12.confirm12(o,tr,k,m,N,x['model'],x['s1'],x['stop'],BM,FAR())
            finally:inc.close()
            self.assertEqual(a['verdict'],b['verdict']);n+=1;seen.add(a['verdict'])
        self.assertGreater(n,5)

    def test_sound_ID_checked_by_enumeration(self):
        rng=random.Random(3803);k,m,s=2,2,1;N=2;BM=3;ids=0;conf=0
        for _ in range(16):
            d=[[rng.randrange(2) for _ in range(k)] for _ in range(2)];e=[0,1]
            rd,acts=noisy_trace(rng,d,e,10,k,rng.randint(0,2));st={'q':S10.final_state(d,acts)}
            def ob(a):st['q']=d[st['q']][a];return (e[st['q']],)
            x=S.active13(rd,acts,k,s,N,ob,lambda:(e[st['q']],),FAR(),12,BM,3,hook=Hook())
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

    def test_GSAFE13_sealed_036_trace(self):
        from experiments import worlds_026 as W
        d=json.load(gzip.open(SEALED036));c=[c for c in d['cases'] if c['seed']==10210002][0];a=c['arms']['A11_r3']
        self.assertEqual((a['label'],a['stop'],a['B_final'],a['truth_flips_trace'],a['B_max']),('WRONG','ID',1,2,6))
        acts,rd=_trace(c,a,W);self.assertEqual(len(acts),a['T_final']);tr=S10.Trace10(rd,acts,W.S_BITS);M1=a['model'];k=c['k'];m=1<<W.S_BITS
        self.assertTrue(S10.fits(M1,tr,1));s1=S10.final_state(M1[0],tr.acts);o=S10._Owner10(120.0)
        x=S10.stop_check10(tr,1,k,m,c['N'],FAR()+600,1,120.0,'g3',o);self.assertEqual(x['stop'],'ID')
        inc=S.Inc13(c['N'],k,m,W.S_BITS,6,'g3')
        try:C=S.confirm13(o,inc,tr,M1,s1,'ID',6,FAR()+600)
        finally:inc.close()
        C12=S12.confirm12(o,tr,k,m,c['N'],M1,s1,'ID',6,FAR()+600,'g3')
        self.assertNotEqual(C['verdict'],'ID');self.assertNotEqual(C['verdict'],'unknown');self.assertEqual(C['verdict'],C12['verdict'])
        F=C['future'] if C['future']['found'] else C['start'];M2=F['M2'];self.assertTrue(S10.fits(M2,tr,6))
        w=F['word_sat'];pre=tr.acts+w if C['future']['found'] else w
        p1=[M1[1][0]]+run_word(M1[0],M1[1],0,pre);p2=[M2[1][0]]+run_word(M2[0],M2[1],0,pre)
        self.assertNotEqual(p1,p2)
        print('\nGSAFE13',json.dumps({'verdict':C['verdict'],'verdict_A12':C12['verdict'],'future':C['future']['verdicts'],
                                     'start':C['start'] and C['start']['verdicts'],'rival_n':F['n'],'query_walls':o.query_walls[-3:]}))

    def test_GINC13_sealed_037_reference_set(self):
        from experiments import worlds_026 as W
        d=json.load(gzip.open(SEALED037));items=[];m=1<<W.S_BITS
        for c in d['cases']:
            if c['key']!='noisy_scale8':continue
            a=c['arms']['A12_r3'];acts,rd=_trace(c,a,W);inc=S.Inc13(c['N'],c['k'],m,W.S_BITS,a['B_max'],'g3')
            try:
                for r in a['rounds']:
                    if r.get('raise_status') is None:continue
                    T=r['T'];tr=S10.Trace10(rd[:T+1],acts[:T],W.S_BITS)
                    if r['raise_status']=='unknown':items.append([c['seed'],T,r['B'],'A12 capped',None]);continue
                    want=('ok',r['raise_to']) if r['raise_status']=='ok' else ('none',None)
                    got=S.bmin13(S10._Owner10(120.0),inc,tr,r['B']+1,a['B_max'],FAR()+600)
                    items.append([c['seed'],T,r['B'],list(want),list(got)]);self.assertEqual(got,want,(c['seed'],T))
            finally:inc.close()
        dec=[x for x in items if x[3]!='A12 capped']
        self.assertGreater(len(dec),10)
        print('\nGINC13',json.dumps({'decided':len(dec),'A12_capped_skipped':len(items)-len(dec),'mismatches':0,
                                    'raised':sum(1 for x in dec if x[3][0]=='ok')}))

    def test_host_agnostic(self):
        src=pathlib.Path(S.__file__).read_text()
        for bad in ('import os','import threading','import subprocess','open(','socket','import time\n','print('):self.assertNotIn(bad,src)


if __name__=='__main__':unittest.main()
