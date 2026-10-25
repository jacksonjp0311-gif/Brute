"""v0.5.0 implementation tests (smoke seeds 901-903 only; no held-out seed is touched)."""
import random,unittest
from brute.region import RegionK,RegionSpace,codes_mask,STRESS_CONF_BUDGET
from brute.region_learner import RegionBruteLearner,Reason050
from brute.breadth import BreadthBruteLearner,declared_family
from brute.core.learner import Status
from bgr90.symbolic import mask_for_observation
from experiments import v050_reference as R
from experiments.worlds_007 import breadth_world,passive_actions,FAMILIES_BREADTH,minimal_states


def _hist(w,seed,steps,rate):
    acts=passive_actions(seed,steps,w.k);h=w.start;obs=[w.observed(h,rate,-1)]
    for i,a in enumerate(acts):h=w.next(h,a);obs.append(w.observed(h,rate,i))
    return acts,obs


class Region(unittest.TestCase):
    def test_codes_mask_equals_frozen_mask_for_s2(self):
        for o in [(a,b) for a in (0,1,None) for b in (0,1,None)]:self.assertEqual(codes_mask(o,2),mask_for_observation(o))

    def test_worlds_equal_second_implementation(self):
        for fam in FAMILIES_BREADTH:
            for seed in (901,902,903):
                a=breadth_world(seed,fam);b=R.breadth_world(seed,fam)
                self.assertEqual((a.transitions,a.emissions,a.start),(tuple(map(tuple,b.transitions)),tuple(b.emissions),b.start))
                self.assertEqual(passive_actions(seed,20,a.k),tuple(R.passive_actions(seed,20,a.k)))
                for st in range(-1,6):self.assertEqual(a.observed(a.start,0.35,st),b.observed(b.start,0.35,st))
                self.assertLessEqual(minimal_states(a),a.n)

    def test_region_equals_enumeration_k3_s3(self):
        """support / saturated / Y1k of RegionK equal the second implementation's row enumeration (n<=4)."""
        checked=0
        for fam in ('act3','sens3'):
            w=breadth_world(901,fam);acts,obs=_hist(w,901,14,0.35)
            for n in (3,4):
                rows=R.k_initial(R.codes_of(obs[0],w.s),w.k)
                for t in range(len(acts)+1):
                    if t:
                        rows,st=R.k_observe(rows,acts[t-1],R.codes_of(obs[t],w.s),n,w.k,10**6)
                        if st!='supported':break
                    g=RegionK(n,w.k,w.m,[codes_mask(o,w.s) for o in obs[:t+1]],list(acts[:t]),conf_budget=None)
                    self.assertTrue(g.feasible)
                    for b in range(w.k):
                        self.assertEqual(tuple(g.support(b)[0]),tuple(R.k_support(rows,b,n,w.k,w.m)))
                        self.assertEqual(tuple(g.y1k(b,codes_mask(obs[t],w.s))[0]),tuple(sorted(R.k_y1k(rows,b,R.codes_of(obs[t],w.s),n,w.k,w.m))))
                    self.assertEqual(g.saturated()[0],R.k_saturated(rows,n));g.close();checked+=1
        self.assertGreater(checked,20)


class ForcedUnknown(unittest.TestCase):
    def test_tiny_budget_abstains_with_reason(self):
        """conf_budget tiny: every forecast that used an UNKNOWN answer is ABSTAIN/SOLVER_BUDGET or OUT_OF_FAMILY, never certified."""
        w=breadth_world(901,'big6');acts,obs=_hist(w,901,30,0.35)
        L=BreadthBruteLearner(6,7,2,2,conf_budget=1);L.initialize(obs[0]);seen=0
        for a,o in zip(acts,obs[1:]):
            for b in range(2):
                f=L.predict(b)
                if f.solver_unknown:
                    seen+=1;self.assertIsNone(f.certificate)
                    self.assertTrue(f.reason==Reason050.SOLVER_BUDGET or f.status in (Status.OUT_OF_FAMILY,Status.ABSTAIN))
            L.observe(a,o)
        L.close();self.assertGreater(seen,0)

    def test_feasibility_unknown_is_budget_exhausted(self):
        S=RegionSpace(6,k=2,s=2,conf_budget=0)
        w=breadth_world(902,'big6');acts,obs=_hist(w,902,30,0.6);S.initialize(obs[0])
        for a,o in zip(acts,obs[1:]):
            S.observe(a,o)
            if S.status!='supported':break
        self.assertIn(S.status,('budget_exhausted','supported'))
        S.close()


class A5EqualsA4(unittest.TestCase):
    def test_smoke_seed_trace_equal(self):
        from experiments.brute_common_007 import load,PLAN
        from experiments.brute_study_007 import run_case_2x2
        plan=load(PLAN);F=('status','reason','certificate','public_certificate','support','margin_support','saturated','probabilities','forecast_source')
        for fam in ('cycle3','drift4'):
            c=run_case_2x2(901,fam,0.35,plan,plan['tau6']['value'],('A5','A4'))
            for r,q in zip(c['arms']['A5']['trace'],c['arms']['A4']['trace']):
                self.assertEqual(r['action'],q['action'])
                for x in F:self.assertEqual(r[x],q[x],(fam,r['step'],x))
            self.assertEqual(c['arms']['A5']['issued'],c['arms']['A4']['issued'])


class Breadth(unittest.TestCase):
    def test_declared_family_string(self):
        self.assertEqual(declared_family(6,2,2),'deterministic-moore<=6/2-actions/2-sensors')


class Service15(unittest.TestCase):
    def test_roundtrip(self):
        from brute.api.service_v050 import BruteServiceV050,API_VERSION
        s=BruteServiceV050(tau=1.0)
        from brute.api.alphabet import DEFAULT_ALPHABET as A
        o={c.name:v for c,v in zip(A.channels,(1,0))}
        r=s.handle({'api_version':'brute.api/1.5','session_id':'x','op':'initialize','observation':o})
        self.assertEqual(r['status'],'ACKNOWLEDGED');self.assertEqual(r['api_version'],API_VERSION)
        self.assertIsNone(r['evidence']['surviving_rows']);self.assertEqual(r['evidence']['backend'],'sat-region')
        act=A.actions[0]
        for _ in range(6):s.handle({'api_version':'brute.api/1.5','session_id':'x','op':'observe','action':act,'observation':o})
        p=s.handle({'api_version':'brute.api/1.5','session_id':'x','op':'predict','action':act})
        self.assertIn(p['status'],('CERTIFIED','POSSIBLE_SET','ABSTAIN'));self.assertIsInstance(p['evidence']['solver_unknown'],int)
        e=s.handle({'api_version':'brute.api/1.5','session_id':'x','op':'experiment'})
        self.assertEqual(e['experiment']['policy'],'LU-R')


if __name__=='__main__':unittest.main()
