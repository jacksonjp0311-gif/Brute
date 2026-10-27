"""Cross-checks of experiments/v0170_reference.py (same author; #101 item 7)."""
import unittest
import numpy as np
from experiments.v0170_reference import (costs_tables,costs_partial,ref_boundary,ref_world3,ref_trajectory3,_minimal,_sc,
                                         supports_for,first_crossing)


def traj2(seed):
    rng=np.random.default_rng([seed,19,99]);d=rng.integers(0,4,(4,2));e=rng.integers(0,4,4);q=0;acts=[];obs=[]
    def o(c):return tuple(None if rng.random()<0.35 else (((c>>(1-j))&1)^int(rng.random()<0.05)) for j in (0,1))
    init=o(int(e[0]))
    for _ in range(44):
        a=int(rng.integers(0,2));q=int(d[q,a]);acts.append(a);obs.append(o(int(e[q])))
    return init,acts,obs


class Reference0170(unittest.TestCase):
    def test_boundary_plan_examples(self):
        for B,ch in ((46,[1,3,15,38]),(58,[1,2,14,35]),(68,[1,2,13,33,57])):
            m=ref_boundary(B);self.assertEqual([b for b in range(1,B+1) if m[b]>m[b-1]],ch)

    def test_two_methods_agree_on_two_actions(self):
        for seed in range(8590001,8590007):
            init,acts,obs=traj2(seed);full=costs_tables(init,acts,obs)
            for mmax in (0,1,3):
                part,_=costs_partial(2,init,acts,obs,mmax);cap=mmax+1
                self.assertEqual([([[min(x,cap) for x in r] for r in row],min(lo,cap)) for row,lo in full],part)
                for ms in ([mmax]*44,):
                    self.assertEqual(supports_for(full,ms,2),supports_for(part,ms,2))

    def test_world3_minimal_connected(self):
        for seed in range(8590016,8590020):
            D,E=ref_world3(seed);self.assertTrue(_sc(D) and _minimal(D,E))
            *_,rd,truth=ref_trajectory3(seed,0.0);self.assertEqual(len(rd),45);self.assertEqual(len(truth),44)

    def test_noise_free_truth_in_support(self):
        D,E,acts,states,lat,rd,truth=ref_trajectory3(8590016,0.0)
        c,_=costs_partial(3,tuple(rd[0]),acts,[tuple(o) for o in rd[1:]],0);S=supports_for(c,[0]*44,3)
        for i in range(44):
            for b in range(3):self.assertIn(truth[i][b],S[i][b])

    def test_crossing(self):
        self.assertIsNone(first_crossing([0]*10,[0]*11));self.assertEqual(first_crossing([0,1],[0,0,0]),2)


if __name__=='__main__':unittest.main()
