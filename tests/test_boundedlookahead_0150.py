"""brute.boundedlookahead unit tests and the #89 equality: rsxl_n_trajectory(n = 4) == the frozen study-016 RSXL."""
import unittest
from brute.region import RegionSpace
from brute.boundedtransfer import region_supports
from brute.boundedlookahead import lookahead,rgl_choose,rglx_choose,attested_license_bound,needs_lookahead
from experiments.v0150_reference import ref_lookahead
import experiments.brute_study_016 as S16
import experiments.brute_study_017 as S17
from experiments.brute_common_009 import plan006_keys
from experiments.brute_common_013 import plan_view
from brute.core.learner import ScopeAttestation


class Lookahead(unittest.TestCase):
    def test_choose(self):
        L={'num':[1,1],'den':[2,3],'unknown':[0,0]}
        self.assertEqual(rgl_choose(9,8,L,1),(0,'rgl'));self.assertEqual(rgl_choose(8,8,None,1),(1,'sp8'))
        self.assertEqual(rglx_choose(9,8,[1,4],L,0,True),(1,'rsx'));self.assertEqual(rglx_choose(9,8,[1,4],L,1,False),(0,'rgl'))
        with self.assertRaises(ValueError):rgl_choose(9,8,None,0)
        with self.assertRaises(ValueError):rglx_choose(9,8,[1,1],L,0,1)
        self.assertTrue(needs_lookahead(9,8,False));self.assertFalse(needs_lookahead(9,8,True));self.assertTrue(needs_lookahead(9,8,True,'rgl'))

    def test_attested(self):
        self.assertTrue(attested_license_bound(3,1,4));self.assertFalse(attested_license_bound(2,1,4))
        with self.assertRaises(ValueError):attested_license_bound(True,1,4)

    def test_matches_exhaustive(self):
        acts=[0,1,1,0,1,0,0,1];obs=[(0,None),(None,1),(1,1),(None,None),(0,0),(1,None),(None,0),(1,0)];init=(0,1)
        ex=ref_lookahead(4,init,acts,obs);R=RegionSpace(4);R.initialize(init)
        try:
            for i,(a,o) in enumerate(zip(acts,obs)):
                L=lookahead(R,region_supports(R))
                for b in (0,1):
                    if L['unknown'][b]==0:self.assertEqual((L['num'][b],L['den'][b]),ex[i][b],(i,b))
                R.observe(a,o)
        finally:R.close()

    def test_rsxl_n4_equals_frozen(self):
        plan=S17.load(S17.PLAN);P13=S17.learner_plan(plan);tau6=plan['tau6']['value'];burn=plan['burn_in']
        p6=plan006_keys(plan_view(P13))
        for s in (8390001,8390005):
            fam=S17.smoke_family(s);attest=fam in P13['in_family_2x2']
            att=lambda:ScopeAttestation(p6['declared_family'],'evaluator','synthetic world built inside the family') if attest else None
            a=S16.rsxl_trajectory(s,fam,0.35,P13,tau6,att,burn);b=S17.rsxl_n_trajectory(s,fam,0.35,P13,tau6,att,burn,4)
            a.pop('wall_informational');b.pop('wall_informational');self.assertEqual(a,b,s)


if __name__=='__main__':unittest.main()
