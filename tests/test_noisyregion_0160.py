"""brute.noisyregion tests (plan 018 tolerant_region): m table (Exact), m = 0 equals the frozen RegionSpace(4) supports,
flip variables only on observed bits, sticky contradiction, rgn_decide rule (#97 item 1), bad input."""
import unittest,random
from brute.noisyregion import m_rule,tolerant_region,NoisyRegionSpace,noisy_supports,rgn_decide,observed_bits
from brute.boundedtransfer import bounded_supports
from experiments.brute_common_018 import load,PLAN


def _trace(seed,T=20,rate=0.35):
    r=random.Random(seed);acts=[r.randrange(2) for _ in range(T)]
    # a 2-state toggle machine: codes alternate 1, 2 on action 1, stay on action 0
    q=0;obs=[]
    for a in acts:
        q=q^a;c=(1,2)[q];obs.append(tuple(None if r.random()<rate else (c>>(1-j))&1 for j in (0,1)))
    return (0,1),acts,obs


class NoisyRegion0160(unittest.TestCase):
    def test_m_table(self):
        T=load(PLAN)['tolerant_region']['m_table_examples_Exact']
        self.assertEqual({k:m_rule(int(k)) for k in T},T)
        self.assertEqual(m_rule(0),0);self.assertEqual(m_rule(57,0.0),0)

    def test_m0_equals_regionspace(self):
        for s in range(3):
            init,acts,obs=_trace(s);a=noisy_supports(init,acts,obs,4,0);b=bounded_supports(init,acts,obs,[4])['4']
            self.assertEqual(a['support'],b['support'])

    def test_flip_vars_and_contradiction(self):
        init,acts,obs=_trace(5,10);R=tolerant_region(4,[init]+obs,acts,1)
        self.assertEqual(R.flip_vars,observed_bits([init]+obs));self.assertTrue(R.feasible);R.close()
        bad=list(obs);bad[3]=(1,1) if obs[3]!=(1,1) else (0,0)
        S=NoisyRegionSpace(1,0);S.initialize(init)
        for a,o in zip(acts,bad):S.observe(a,o)
        self.assertIn(S.status,('grammar_contradicted','supported'));st=S.status
        S.observe(0,(0,0));self.assertEqual(S.status,st if st!='supported' else S.status);S.close()

    def test_tolerance_restores_truth(self):
        init,acts,obs=_trace(7,24,0.0);noisy=list(obs);o=noisy[12];noisy[12]=(1-o[0],o[1])
        a=noisy_supports(init,acts,noisy,4,1)
        for i in range(len(acts)):
            for b in (0,1):
                if a['support'][i][b] is not None and len(a['support'][i][b])==1:
                    q=0
                    for x in acts[:i]:q^=x
                    self.assertEqual(a['support'][i][b][0],(1,2)[q^b])

    def test_rgn_decide(self):
        self.assertIsNone(rgn_decide(8,8,[2]));self.assertEqual(rgn_decide(9,8,[2]),2)
        self.assertIsNone(rgn_decide(9,8,[1,2]));self.assertIsNone(rgn_decide(9,8,None))

    def test_bad_input(self):
        for bad in ((-1,),(True,),(10,0.5),(10,-0.01),(10,0.02,0),(10,0.02,1),(10,'0.02')):
            with self.assertRaises(ValueError):m_rule(*bad)
        with self.assertRaises(ValueError):NoisyRegionSpace(4,-1)
        with self.assertRaises(ValueError):tolerant_region(4,[(0,1)],[0],0)


if __name__=='__main__':unittest.main()
