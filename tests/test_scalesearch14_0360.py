"""v0.36.0: A14 incremental sound active identification (brute.scalesearch14). Inc14 synced as the trace grows gives the
same least n as the frozen least9 and an exhaustive enumeration; the guarded rival check gives the same verdict as the
frozen differ9 on small traces; every A14 ID stop on small traces is checked by enumeration; a prefix change is refused;
GINC14: on every sealed study-034 A9 trace, for every round, the pooled incremental least n equals the stored n_min and every
decided stored rival verdict (SAT/UNSAT per size n, future and start) is reproduced exactly by differ14, rounds replayed in
order on one pool per case (so the instance carries the earlier rounds' retired guards and learned clauses); host-agnostic."""
import gzip,itertools,json,pathlib,random,unittest
from time import perf_counter
from brute import scalesearch9 as S9
from brute import scalesearch14 as S
from brute.region import codes_mask
from brute.scalesearch import simulate
from brute.scalesearch8 import _Owner8
from brute.scalesearch10 import _Owner10

FAR=lambda:perf_counter()+120
ROOT=pathlib.Path(__file__).resolve().parents[1]
SEALED034=ROOT/'results/study-034/main/RESULTS.json.gz'


def machines(n,k,m):
    for d in itertools.product(range(n),repeat=n*k):
        D=[list(d[q*k:(q+1)*k]) for q in range(n)]
        for E in itertools.product(range(m),repeat=n):yield D,list(E)


def differs(d1,e1,s1,d2,e2,s2):
    k=len(d1[0]);seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return True
        for a in range(k):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return False


def trace(rng,d,e,T,k):
    q=0;acts=[];masks=[1<<e[0]]
    for _ in range(T):a=rng.randrange(k);q=d[q][a];acts.append(a);masks.append(1<<e[q])
    return masks,acts


def replay034(case):
    """GINC14 items for one sealed study-034 case: [seed, round, kind, stored, A14]."""
    from experiments import worlds_026 as W
    a=case['arms']['A9'];k=case['k'];m=1<<W.S_BITS;N=case['N']
    tr=W.trajectory(W.world(case['seed'],case['family']),case['seed'],0.0)
    acts=list(tr['actions'])+list(a['extra_acts']);masks=[codes_mask(tuple(r),W.S_BITS) for r in tr['readings']]+list(a['extra_masks'])
    P=S.Pool14(k,m);out=[]
    try:
        for i,r in enumerate(a['rounds']):
            T=r['T'];ac=acts[:T];mk=masks[:T+1];o=_Owner10(600.0)
            if r['n_min'] is not None:
                st,n,M1=S.least14(o,P,mk,ac,N,FAR()+600,1);out.append([case['seed'],i,'n_min',r['n_min'],n if st=='ok' else st])
            if r['M1'] is None:continue
            M1=r['M1'];s1=r['s1'];L=S.word_len9(N,len(M1[0]))
            for mode in ('future','start'):
                V=r.get(mode)
                if V is None:continue
                for n,v in V['verdicts']:
                    if v=='UNKNOWN':continue
                    f=S.differ14(o,P,mk,ac,n,M1,s1,mode,L,FAR()+600)[0]
                    out.append([case['seed'],i,f'{mode}:{n}',v,{True:'SAT',False:'UNSAT',None:'UNKNOWN'}[f]])
    finally:P.close()
    return out


class T14(unittest.TestCase):
    def test_least_incremental_equals_fresh_and_enumeration(self):
        rng=random.Random(3901);k,m=2,2;checked=0
        for _ in range(12):
            nt=rng.randint(1,3);d=[[rng.randrange(nt) for _ in range(k)] for _ in range(nt)];e=[rng.randrange(m) for _ in range(nt)]
            masks,acts=trace(rng,d,e,12,k);P=S.Pool14(k,m)
            try:
                for T in (3,6,9,12):
                    mk,ac=masks[:T+1],acts[:T];o=_Owner10(30)
                    a=S.least14(o,P,mk,ac,3,FAR());b=S9.least9(_Owner8(30),mk,ac,k,m,3,FAR())
                    best=min(n for n in (1,2,3) if any(simulate(D,E,ac,mk)[0] for D,E in machines(n,k,m)))
                    self.assertEqual(a[:2],b[:2]);self.assertEqual(a[:2],('ok',best));self.assertTrue(simulate(a[2][0],a[2][1],ac,mk)[0]);checked+=1
            finally:P.close()
        self.assertGreater(checked,40)

    def test_differ14_equals_differ9(self):
        rng=random.Random(3902);k,m=2,2;N=3;n_=0;seen=set()
        for _ in range(16):
            d=[[rng.randrange(3) for _ in range(k)] for _ in range(3)];e=[rng.randrange(m) for _ in range(3)]
            masks,acts=trace(rng,d,e,rng.randint(2,9),k);P=S.Pool14(k,m)
            try:
                st,n0,M1=S9.least9(_Owner8(30),masks,acts,k,m,N,FAR());s1=simulate(M1[0],M1[1],acts,masks)[1];L=S.word_len9(N,len(M1[0]))
                for mode in ('future','start'):
                    for n in range(n0,N+1):
                        a=S.differ14(_Owner10(30),P,masks,acts,n,M1,s1,mode,L,FAR())[0];b=S9.differ9(_Owner8(30),masks,acts,k,m,n,M1,s1,mode,L,FAR())[0]
                        self.assertEqual(a,b);n_+=1;seen.add(a)
            finally:P.close()
        self.assertGreater(n_,30);self.assertEqual(seen,{True,False})

    def test_ID_stop_checked_by_enumeration(self):
        rng=random.Random(3903);k,m=2,2;N=3;ids=0;words=0
        for _ in range(40):
            nt=rng.randint(2,3);d=[[rng.randrange(nt) for _ in range(k)] for _ in range(nt)];e=[rng.randrange(m) for _ in range(nt)]
            masks,acts=trace(rng,d,e,4,k);st={'q':0}
            for a in acts:st['q']=d[st['q']][a]
            def ob(a):st['q']=d[st['q']][a];return 1<<e[st['q']]
            x=S.active14(masks,acts,k,m,N,ob,FAR(),16);self.assertLessEqual(x['used'],16)
            words+=sum(1 for r in x['rounds'] if 'obs' in r)
            if x['stop']!='ID':continue
            ids+=1;M1=x['final']['model'];s1=x['final']['s1']
            for nn in range(1,N+1):
                for D,E in machines(nn,k,m):
                    ok,s2,_=simulate(D,E,x['acts'],x['masks'])
                    if not ok:continue
                    self.assertFalse(differs(M1[0],M1[1],s1,D,E,s2));self.assertFalse(differs(M1[0],M1[1],0,D,E,0))
            self.assertFalse(differs(M1[0],M1[1],0,d,e,0))
        self.assertGreater(ids,5);self.assertGreater(words,0)

    def test_stop_check14_equals_stop_check9(self):
        rng=random.Random(3904);k,m=2,2;N=3;n_=0
        for _ in range(16):
            d=[[rng.randrange(3) for _ in range(k)] for _ in range(3)];e=[rng.randrange(m) for _ in range(3)]
            masks,acts=trace(rng,d,e,rng.randint(3,12),k)
            a=S.stop_check14(masks,acts,k,m,N,FAR(),1,30.0);b=S9.stop_check9(masks,acts,k,m,N,FAR(),1,30.0)
            self.assertEqual((a['stop'],a['n_min']),(b['stop'],b['n_min']));n_+=1
        self.assertEqual(n_,16)

    def test_prefix_change_refused(self):
        I=S.Inc14(2,2,2);I.sync([1,2],[0])
        with self.assertRaises(ValueError):I.sync([1,1,2],[0,1])
        I.close()

    def test_GINC14_sealed_034_traces(self):
        d=json.load(gzip.open(SEALED034));items=[];t=perf_counter()
        for c in d['cases']:items+=replay034(c)
        bad=[x for x in items if x[3]!=x[4]]
        self.assertEqual(bad,[]);self.assertGreater(len([x for x in items if x[2]!='n_min']),100)
        print('\nGINC14',json.dumps({'cases':len(d['cases']),'n_min_checked':sum(1 for x in items if x[2]=='n_min'),
            'verdicts_checked':sum(1 for x in items if x[2]!='n_min'),'SAT':sum(1 for x in items if x[3]=='SAT'),
            'UNSAT':sum(1 for x in items if x[3]=='UNSAT'),'mismatches':len(bad),'wall_informational':round(perf_counter()-t,1)}))

    def test_constants_and_host_agnostic(self):
        self.assertEqual((S.QUERY_S14,S.K14,S.BUDGET14,S.K14_64,S.BUDGET14_64),(9.0,128,240.0,64,120.0))
        src=pathlib.Path(S.__file__).read_text()
        for bad in ('import os','import threading','import subprocess','open(','socket','import time\n','print('):self.assertNotIn(bad,src)


if __name__=='__main__':unittest.main()
