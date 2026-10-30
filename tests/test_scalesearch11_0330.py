"""v0.33.0: A11 repeated-read sound active identification (brute.scalesearch11). majority_rate is the exact binomial tail;
b_max11 applies flip_budget to it (r = 1 gives the 035 B_end); bmin11 (bisection) returns the same least B as bmin10 (upward)
and an exhaustive enumeration; active11 on clean traces equals active10 (same stops, steps, B 0) while taking r reads per
word reading; K is counted in steps; the bisect and up searches agree on small noisy traces; host-agnostic source."""
import random,unittest,pathlib
from math import comb
from time import perf_counter
from brute import scalesearch10 as S10
from brute import scalesearch11 as S
from brute.scalesearch7 import machine_flips,flip_budget
from tests.test_scalesearch10_0320 import all_machines,noisy_trace,Hook

FAR=lambda:perf_counter()+60


class T11(unittest.TestCase):
    def test_majority_rate_and_bmax(self):
        self.assertAlmostEqual(S.majority_rate(0.05,1),0.05)
        self.assertAlmostEqual(S.majority_rate(0.05,3),3*0.05**2*0.95+0.05**3)
        self.assertAlmostEqual(S.majority_rate(0.05,5),sum(comb(5,i)*0.05**i*0.95**(5-i) for i in (3,4,5)))
        self.assertEqual(S.b_max11(354,0.05,1),flip_budget(354,0.05));self.assertEqual(S.b_max11(354,0.05,1),27)
        self.assertEqual((S.b_max11(354,0.05,3),S.b_max11(354,0.05,5)),(6,2))
        with self.assertRaises(ValueError):S.majority_rate(0.05,2)

    def test_bisect_equals_upward_and_enumeration(self):
        rng=random.Random(3601);k,m,s=2,2,1;checked=0
        for _ in range(12):
            d=[[rng.randrange(3) for _ in range(k)] for _ in range(3)];e=[rng.randrange(m) for _ in range(3)]
            rd,acts=noisy_trace(rng,d,e,8,k,rng.randint(1,4));tr=S10.Trace10(rd,acts,s)
            best=min(machine_flips(D,E,acts,rd,s) for nn in (1,2) for D,E in all_machines(nn,k,m))
            if best==0:continue
            pr=[];a=S.bmin11(S10._Owner10(30),tr,k,m,2,1,6,FAR(),probes=pr);b=S10.bmin10(S10._Owner10(30),tr,k,m,2,1,6,FAR())
            self.assertEqual(a,b)
            if best<=6:self.assertEqual(a,('ok',best));checked+=1;self.assertLessEqual(len(pr),1+3)
            else:self.assertEqual(a[0],'none');self.assertEqual(len(pr),1)
        self.assertGreater(checked,3)

    def test_clean_equals_A10(self):
        rng=random.Random(3602);k,m,s=2,4,2
        for _ in range(6):
            n=3;d=[[rng.randrange(n) for _ in range(k)] for _ in range(n)];e=[rng.randrange(m) for _ in range(n)]
            acts=[rng.randrange(k) for _ in range(10)];q=0;rd=[(e[0]>>1,e[0]&1)]
            for a in acts:q=d[q][a];rd.append((e[q]>>1,e[q]&1))
            def mk():
                st={'q':q}
                def ob(a):st['q']=d[st['q']][a];c=e[st['q']];return (c>>1,c&1)
                return ob,(lambda:(e[st['q']]>>1,e[st['q']]&1))
            ob,rr=mk();h=Hook();a10=S10.active10(rd,acts,k,s,n,ob,rr,FAR(),16,5,hook=h)
            for r in (3,5):
                for search in ('bisect','up'):
                    ob2,rr2=mk();a11=S.active11(rd,acts,k,s,n,ob2,rr2,FAR(),16,5,r,search,hook=Hook())
                    self.assertEqual(a11['stop'],a10['stop']);self.assertEqual(a11['used'],a10['used']);self.assertEqual(a11['B'],0)
                    self.assertEqual(a11['reads'],r*a11['used']);self.assertEqual(a11['trace'].readings,a10['trace'].readings)

    def test_noisy_loop_K_steps_and_searches_agree(self):
        rng=random.Random(3603);k,m,s=2,2,1;raised=0
        for _ in range(8):
            d=[[rng.randrange(3) for _ in range(k)] for _ in range(3)];e=[0,1,rng.randrange(2)]
            rd,acts=noisy_trace(rng,d,e,9,k,2);out={}
            for search in ('bisect','up'):
                st={'q':S10.final_state(d,acts)}
                def ob(a):st['q']=d[st['q']][a];return (e[st['q']],)
                rr=lambda:(e[st['q']],)
                x=S.active11(rd,acts,k,s,3,ob,rr,FAR(),12,4,3,search);out[search]=x
                self.assertLessEqual(x['used'],12);self.assertEqual(x['reads'],3*x['used'])
                self.assertEqual([b for _,b,_ in x['B_history']],sorted(b for _,b,_ in x['B_history']))
                for y in x['rounds']:
                    if 'obs' in y:self.assertEqual(y['reps'],3);self.assertTrue(all(len(z)==3 for z in y['raw']))
            self.assertEqual(out['bisect']['stop'],out['up']['stop']);self.assertEqual(out['bisect']['B'],out['up']['B'])
            raised+=out['bisect']['B']>0
        self.assertGreater(raised,0)

    def test_cap_returns_unknown(self):
        rng=random.Random(9);d=[[rng.randrange(8) for _ in range(3)] for _ in range(8)];e=[rng.randrange(4) for _ in range(8)]
        acts=[rng.randrange(3) for _ in range(150)];q=0;rd=[(e[0]>>1,e[0]&1)]
        for a in acts:q=d[q][a];rd.append((e[q]>>1,e[q]&1))
        for t in rng.sample(range(151),12):rd[t]=(1-rd[t][0],rd[t][1])
        tr=S10.Trace10(rd,acts,2);o=S10._Owner10(0.2);t0=perf_counter();st,B=S.bmin11(o,tr,3,4,8,1,27,FAR())
        self.assertLess(perf_counter()-t0,30);self.assertTrue(all(w<5 for w in o.query_walls))
        if st=='ok':self.assertLessEqual(B,27)

    def test_host_agnostic(self):
        src=pathlib.Path(S.__file__).read_text()
        for bad in ('import os','import threading','import subprocess','open(','socket','import time\n','print('):self.assertNotIn(bad,src)


if __name__=='__main__':unittest.main()
