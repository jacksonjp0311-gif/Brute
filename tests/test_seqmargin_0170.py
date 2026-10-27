"""brute.seqmargin / brute.region3 unit tests (plan 019 sequential_margin, alphabet3_block)."""
import unittest
from fractions import Fraction
from brute.seqmargin import boundary,crossing_bit,SeqMarginRegionSpace,seqmargin_supports
from brute.noisyregion import m_rule,noisy_supports
from brute.region3 import rg3_supports,rgn3_supports,rgnb3_supports


def changes(m):return [b for b in range(1,len(m)) if m[b]>m[b-1]]


class SeqMargin(unittest.TestCase):
    def test_plan_examples(self):
        self.assertEqual(changes(boundary(46)),[1,3,15,38]);self.assertEqual(changes(boundary(58)),[1,2,14,35])
        self.assertEqual(changes(boundary(68)),[1,2,13,33,57])

    def test_vs_fixed_m(self):
        for B in list(range(44,59))+list(range(66,71)):self.assertEqual(boundary(B)[-1],m_rule(B),B)
        for B in (40,41,42,60,61,62,63,64):self.assertEqual(boundary(B)[-1],m_rule(B)+1,B)

    def test_crossing_probability_within_delta(self):
        for B in (20,46,58):
            m=boundary(B);p=Fraction(1,50);dist={0:Fraction(1)};crossed=Fraction(0)
            for b in range(1,B+1):
                nd={}
                for s,x in dist.items():nd[s]=nd.get(s,0)+x*(1-p);nd[s+1]=nd.get(s+1,0)+x*p
                crossed+=sum(x for s,x in nd.items() if s>m[b]);dist={s:x for s,x in nd.items() if s<=m[b]}
                self.assertLessEqual(crossed,Fraction(1,100)*b/B)

    def test_bad_input(self):
        for args in ((-1,),(True,),(10,0.5),(10,0.02,0),(10,0.02,1),(10,'x')):
            with self.assertRaises(ValueError):boundary(*args)
        for bd in ([],[0,2,1],[0,-1],[0,True]):
            with self.assertRaises(ValueError):SeqMarginRegionSpace(4,bd)

    def test_crossing_bit(self):
        bd=[0,1,1,2];self.assertIsNone(crossing_bit([1,0,1],bd));self.assertEqual(crossing_bit([1,1,0],bd),2)

    def test_zero_boundary_equals_rgn0(self):
        init=(0,1);acts=[0,1,1,0,1,0];obs=[(1,None),(0,0),(None,1),(1,1),(0,None),(1,0)]
        a=seqmargin_supports(init,acts,obs,4,[0]*13);b=noisy_supports(init,acts,obs,4,0)
        self.assertEqual(a['support'],b['support']);self.assertEqual(a['m'],[0]*6)

    def test_three_actions_noise_free(self):
        # 2-state toggle on action 2, stay on 0 / 1; codes 0 and 3
        init=(0,0);acts=[2,2,0,1,2,2,0,2,1,2];q=0;obs=[]
        for a in acts:
            q=1-q if a==2 else q;obs.append((0,0) if q==0 else (1,1))
        r=rg3_supports(init,acts,obs)
        self.assertTrue(all(s is not None for row in r['support'] for s in row))
        n=rgn3_supports(init,acts,obs,1);g=rgnb3_supports(init,acts,obs,[0,1]+[1]*21)
        for x in (r,n,g):self.assertEqual(len(x['support']),len(acts))


if __name__=='__main__':unittest.main()
