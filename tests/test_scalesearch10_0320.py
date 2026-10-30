"""v0.32.0: A10 noisy sound active identification (brute.scalesearch10). Under a flip budget B > 0, least10 equals
exhaustive enumeration of every complete machine with <= n states (n <= 3, 2 actions, 1 sensor bit) on n_min, differ10 is
SAT exactly when an enumerated machine with <= B flips differs from M1 (future and start modes), bmin10 returns the least
B; at B = 0 the region is A9's (active10 equals active9 on clean traces); majority re-reads; the host hook is armed and
disarmed once per solved query; the A10 loop never exceeds K and the fixed arm never raises B; host-agnostic source."""
import itertools,random,unittest,pathlib
from time import perf_counter
from brute import scalesearch10 as S
from brute import scalesearch9 as S9
from brute.scalesearch7 import machine_flips
from brute.scalesearch8 import run_word


def all_machines(n,k,m):
    for d in itertools.product(range(n),repeat=n*k):
        D=[list(d[q*k:(q+1)*k]) for q in range(n)]
        for e in itertools.product(range(m),repeat=n):yield D,list(e)


def differs(d1,e1,s1,d2,e2,s2):
    k=len(d1[0]);seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return True
        for a in range(k):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return False


def noisy_trace(rng,d,e,T,k,flips):
    acts=[rng.randrange(k) for _ in range(T)];q=0;rd=[(e[0],)]
    for a in acts:q=d[q][a];rd.append((e[q],))
    for t in rng.sample(range(T+1),flips):rd[t]=(1-rd[t][0],)
    return rd,acts


class Hook:
    def __init__(self):self.armed=0;self.disarmed=0;self.open=set()
    def arm(self,fn,s):self.armed+=1;tok=object();self.open.add(tok);assert callable(fn) and s>=0;return tok
    def disarm(self,tok):self.disarmed+=1;self.open.discard(tok)


FAR=lambda:perf_counter()+60


class T10(unittest.TestCase):
    def test_least_and_differ_equal_enumeration_under_B(self):
        rng=random.Random(35);k,m,s=2,2,1;cases=0
        for _ in range(14):
            n0=rng.randint(1,3);d=[[rng.randrange(n0) for _ in range(k)] for _ in range(n0)];e=[rng.randrange(m) for _ in range(n0)]
            rd,acts=noisy_trace(rng,d,e,rng.randint(3,7),k,rng.randint(0,2));tr=S.Trace10(rd,acts,s)
            for B in (1,2):
                o=S._Owner10(30);st,n,M1=S.least10(o,tr,B,k,m,3,FAR())
                enum=[nn for nn in (1,2,3) if any(machine_flips(D,E,acts,rd,s)<=B for D,E in all_machines(nn,k,m))]
                if st=='none':self.assertEqual(enum,[]);continue
                self.assertEqual(st,'ok');self.assertEqual(n,enum[0]);self.assertLessEqual(machine_flips(M1[0],M1[1],acts,rd,s),B)
                s1=S.final_state(M1[0],acts)
                for mode in ('future','start'):
                    for nn in range(n,4):
                        L=S9.word_len9(3,len(M1[0]));f,M2,s2,w=S.differ10(o,tr,B,k,m,nn,M1,s1,mode,L,FAR())
                        want=any(machine_flips(D,E,acts,rd,s)<=B and differs(M1[0],M1[1],s1 if mode=='future' else 0,D,E,S.final_state(D,acts) if mode=='future' else 0)
                                 for D,E in all_machines(nn,k,m))
                        self.assertEqual(f,want,(mode,nn,B));cases+=1
                        if f:self.assertLessEqual(machine_flips(M2[0],M2[1],acts,rd,s),B)
        self.assertGreater(cases,20)

    def test_bmin_is_least(self):
        rng=random.Random(3501);k,m,s=2,2,1;checked=0
        for _ in range(10):
            d=[[rng.randrange(3) for _ in range(k)] for _ in range(3)];e=[rng.randrange(m) for _ in range(3)]
            rd,acts=noisy_trace(rng,d,e,8,k,3);tr=S.Trace10(rd,acts,s);o=S._Owner10(30)
            best=min(machine_flips(D,E,acts,rd,s) for nn in (1,2) for D,E in all_machines(nn,k,m))
            st,B=S.bmin10(o,tr,k,m,2,1,6,FAR())
            if best==0:continue
            if best<=6:self.assertEqual((st,B),('ok',best));checked+=1
            else:self.assertEqual(st,'none')
        self.assertGreater(checked,3)

    def test_B0_equals_A9_on_clean_traces(self):
        rng=random.Random(3502);k,m,s=2,4,2
        for _ in range(6):
            n=3;d=[[rng.randrange(n) for _ in range(k)] for _ in range(n)];e=[rng.randrange(m) for _ in range(n)]
            acts=[rng.randrange(k) for _ in range(10)];q=0;rd=[(e[0]>>1,e[0]&1)]
            for a in acts:q=d[q][a];rd.append((e[q]>>1,e[q]&1))
            def mk():
                st={'q':q}
                def ob(a):st['q']=d[st['q']][a];c=e[st['q']];return (c>>1,c&1)
                return ob,(lambda:(e[st['q']]>>1,e[st['q']]&1))
            ob,rr=mk();h=Hook();r10=S.active10(rd,acts,k,s,n,ob,rr,FAR(),16,5,hook=h)
            ob2,_=mk();r9=S9.active9([1<<(a*2+b) for a,b in rd],acts,k,m,n,lambda a:(lambda o:1<<(o[0]*2+o[1]))(ob2(a)),FAR(),16)
            self.assertEqual(r10['stop'],r9['stop']);self.assertEqual(r10['used'],r9['used']);self.assertEqual(r10['B'],0)
            self.assertEqual(h.armed,h.disarmed);self.assertFalse(h.open);self.assertGreater(h.armed,0)

    def test_fixed_never_raises_and_K_respected(self):
        rng=random.Random(3503);k,m,s=2,2,1
        for _ in range(6):
            d=[[rng.randrange(3) for _ in range(k)] for _ in range(3)];e=[0,1,rng.randrange(2)]
            rd,acts=noisy_trace(rng,d,e,9,k,2);st={'q':S.final_state(d,acts)}
            def ob(a):st['q']=d[st['q']][a];return (e[st['q']],)
            rr=lambda:(e[st['q']],)
            for adaptive,B0 in ((True,0),(False,3)):
                r=S.active10(rd,acts,k,s,3,ob,rr,FAR(),12,4,B0=B0,adaptive=adaptive)
                self.assertLessEqual(r['used'],12)
                if not adaptive:self.assertEqual(r['B'],3);self.assertEqual(len(r['B_history']),1)
                else:self.assertEqual([b for _,b,_ in r['B_history']],sorted(b for _,b,_ in r['B_history']))
                for x in r['rounds']:
                    if 'obs' in x:self.assertEqual(x['reps'],3 if x['B']>0 else 1)

    def test_majority_and_cap(self):
        self.assertEqual(S.majority([(1,0),(1,1),(0,0)]),(1,0))
        rng=random.Random(9);d=[[rng.randrange(8) for _ in range(3)] for _ in range(8)];e=[rng.randrange(4) for _ in range(8)]
        acts=[rng.randrange(3) for _ in range(150)];q=0;rd=[(e[0]>>1,e[0]&1)]
        for a in acts:q=d[q][a];rd.append((e[q]>>1,e[q]&1))
        for t in rng.sample(range(151),12):rd[t]=(1-rd[t][0],rd[t][1])
        tr=S.Trace10(rd,acts,2);o=S._Owner10(0.2);t0=perf_counter();st,B=S.bmin10(o,tr,3,4,8,1,27,FAR())
        self.assertLess(perf_counter()-t0,30);self.assertTrue(all(w<5 for w in o.query_walls))

    def test_host_agnostic(self):
        src=pathlib.Path(S.__file__).read_text()
        for bad in ('import os','import threading','import subprocess','open(','socket','import time\n','print('):self.assertNotIn(bad,src)


if __name__=='__main__':unittest.main()
