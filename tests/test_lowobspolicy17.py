"""v0.41.0: arm A16_xf (brute.lowobspolicy17). New file. xf_schedule is the length 1-3 lex words truncated at E (no random tail
for k = 3; a seeded tail for k <= 2); active17xf executes the schedule from the current state, then active16 with K - E
experiments; used = schedule + words; the deadline cuts the schedule; host-agnostic."""
import pathlib,random,unittest
from itertools import product
from time import perf_counter
from brute import lowobspolicy17 as X
from brute import scalesearch16 as S16
from brute.scalesearch import simulate


class TXF(unittest.TestCase):
    def test_schedule_k3_no_tail(self):
        s=X.xf_schedule(3,32,1);t=X.xf_schedule(3,32,999);self.assertEqual(s,t);self.assertEqual(len(s),32)
        self.assertEqual(s[:3],[0,1,2]);self.assertEqual(s[3:9],[0,0,0,1,0,2]);self.assertEqual(X.xf_schedule(3,102,0),X.xf_schedule(3,102,9))

    def test_schedule_k2_tail_seeded(self):
        a=X.xf_schedule(2,32,5);b=X.xf_schedule(2,32,5);c=X.xf_schedule(2,32,6)
        self.assertEqual(a,b);self.assertEqual(len(a),32);self.assertEqual(a[:2+8+24],[x for L in (1,2,3) for w in product(range(2),repeat=L) for x in w][:32])
        self.assertEqual(len(X.xf_schedule(2,40,5)),40);self.assertNotEqual(X.xf_schedule(2,60,5),X.xf_schedule(2,60,6))
        self.assertTrue(all(0<=x<2 for x in c))

    def _world(self,seed):
        rng=random.Random(seed);n,k,m=3,2,2
        T=[[rng.randrange(n) for _ in range(k)] for _ in range(n)];Em=[rng.randrange(m) for _ in range(n)];st=[0]
        def obs(a):st[0]=T[st[0]][a];return 1<<Em[st[0]]
        acts=[rng.randrange(k) for _ in range(6)];masks=[1<<Em[0]]
        for a in acts:st[0]=T[st[0]][a];masks.append(1<<Em[st[0]])
        return masks,acts,k,m,obs

    def test_active17xf_runs_schedule_then_active16(self):
        masks,acts,k,m,obs=self._world(7);seen=[]
        def o(a):seen.append(a);return obs(a)
        r=X.active17xf(masks,acts,k,m,4,o,perf_counter()+60,K=64,E=10,tail_seed=3)
        self.assertEqual(r['xf_used'],10);self.assertEqual(r['xf_actions'],X.xf_schedule(k,10,3));self.assertEqual(seen[:10],r['xf_actions'])
        self.assertEqual(r['used'],r['words_used']+10);self.assertEqual(len(seen),r['used']);self.assertEqual(r['K_total'],64)
        self.assertIn(r['stop'],('ID','IDF','AMB','K_spent','unknown'))

    def test_deadline_cuts_schedule(self):
        masks,acts,k,m,obs=self._world(8);t=[0.0]
        def clock():t[0]+=1.0;return t[0]
        r=X.active17xf(masks,acts,k,m,4,obs,3.5,K=64,E=10,clock=clock)
        self.assertLess(r['xf_used'],10);self.assertEqual(r['used'],r['words_used']+r['xf_used'])

    def test_host_agnostic(self):
        src=pathlib.Path(X.__file__).read_text()
        for bad in ('import os','subprocess','threading','open(','socket','multiprocessing'):self.assertNotIn(bad,src)


if __name__=='__main__':unittest.main()
