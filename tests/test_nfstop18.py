"""v0.42.0: arms A16_nf1 / A16_nf2 (brute.nfstop18). New file. active18 runs least14 up to CEIL18 = 16 and both rival searches
over n_min..n_min+delta; records carry delta, ceil and bound (= n_min + delta); a negative delta is refused; host-agnostic."""
import pathlib,random,unittest
from time import perf_counter
from brute import nfstop18 as N


class TNF(unittest.TestCase):
    def _world(self,seed):
        rng=random.Random(seed);n,k,m=3,2,2
        T=[[rng.randrange(n) for _ in range(k)] for _ in range(n)];Em=[rng.randrange(m) for _ in range(n)];st=[0]
        def obs(a):st[0]=T[st[0]][a];return 1<<Em[st[0]]
        acts=[rng.randrange(k) for _ in range(6)];masks=[1<<Em[0]]
        for a in acts:st[0]=T[st[0]][a];masks.append(1<<Em[st[0]])
        return masks,acts,k,m,obs

    def test_ceiling(self):self.assertEqual(N.CEIL18,16)

    def test_bound_and_keys(self):
        for d in (0,1,2):
            masks,acts,k,m,obs=self._world(5);seen=[]
            def o(a):seen.append(a);return obs(a)
            r=N.active18(masks,acts,k,m,d,o,perf_counter()+120,K=64)
            self.assertIn(r['stop'],('ID','IDF','AMB','K_spent','unknown'));self.assertEqual(r['delta'],d);self.assertEqual(r['ceil'],16)
            self.assertEqual(len(seen),r['used']);self.assertLessEqual(r['used'],64)
            if r['final']['n_min'] is not None:self.assertEqual(r['bound'],r['final']['n_min']+d)
            for rec in r['rounds']:
                if rec['n_min'] is not None:self.assertEqual(rec['bound'],rec['n_min']+d)

    def test_negative_delta(self):
        masks,acts,k,m,obs=self._world(6)
        with self.assertRaises(ValueError):N.active18(masks,acts,k,m,-1,obs,perf_counter()+10)

    def test_host_agnostic(self):
        src=pathlib.Path(N.__file__).read_text()
        for bad in ('import os','subprocess','threading','open(','socket','multiprocessing'):self.assertNotIn(bad,src)


if __name__=='__main__':unittest.main()
