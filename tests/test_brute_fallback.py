"""F0/F1 (v0.1.1): open-world fallback forecast; identical to v0.1.0 before contradiction."""
import unittest
from bgr89.worlds import world as old_world,actions
from bgr89.baselines import SuffixFrequency
from bgr90.worlds import world as new_world,step as new_step
from brute.core.learner import BruteLearner,Status,Reason,compatible_mass
from brute.fallback import FallbackBruteLearner,FallbackForecast,retraction_reason,FORECAST_SOURCES
from math import log

TAU=1.433141502274


def trace(seed,family,mask,n=44):
    truth=(new_world if family in ('ood5','drift4') else old_world)(seed,family)
    h=truth.start;init=truth.observed(h,mask,-1);out=[]
    for i,a in enumerate(actions(seed,n)):
        h=new_step(truth,h,a,i) if family=='drift4' else truth.next(h,a)
        out.append((a,truth.observed(h,mask,i),truth.emission(h)))
    return init,out


def run_pair(seed,family,mask):
    init,tr=trace(seed,family,mask)
    A=BruteLearner(tau=TAU);B=FallbackBruteLearner(tau=TAU);S=SuffixFrequency(1,0.7)
    for L in (A,B):L.initialize(init)
    S.initialize(init)
    rows=[]
    for a,obs,actual in tr:
        fa=A.predict(a);fb=B.predict(a);A.record_issued(fa);B.record_issued(fb)
        sp=S.predict(a)
        contradicted=B.support.status=='grammar_contradicted'
        sa=A.observe(a,obs);sb=B.observe(a,obs);S.observe(a,obs)
        rows.append((fa,fb,sa,sb,contradicted,sp,obs,actual))
    return A,B,rows


class Fallback(unittest.TestCase):
    CASES=[(1290999,'ood5',.1),(990001,'drift4',.1),(990003,'drift4',.35),(930001,'cycle3',.35),
           (970002,'ood4',.6),(980005,'ood5',.6)]

    def test_identical_to_v010_before_contradiction(self):
        for case in self.CASES:
            A,B,rows=run_pair(*case)
            for fa,fb,sa,sb,contra,_,_,_ in rows:
                self.assertIsInstance(fb,FallbackForecast)
                if contra:break
                for k in fa.__dataclass_fields__:self.assertEqual(getattr(fa,k),getattr(fb,k),(case,k))
                self.assertEqual(fb.forecast_source,'v090');self.assertEqual(sa,sb)

    def test_post_contradiction_rule(self):
        seen=set()
        for case in self.CASES:
            A,B,rows=run_pair(*case)
            for fa,fb,sa,sb,contra,sp,obs,actual in rows:
                self.assertAlmostEqual(sum(fb.probabilities),1.0,places=12)
                self.assertGreaterEqual(min(fb.probabilities),0.005-1e-15)
                self.assertIn(fb.forecast_source,FORECAST_SOURCES)
                if not contra:continue
                seen.add(fb.forecast_source)
                self.assertEqual((fb.status,fb.reason,fb.certificate,fb.public_certificate),
                                 (Status.OUT_OF_FAMILY,Reason.FAMILY_CONTRADICTED,None,None))
                if fb.forecast_source=='margin_n5':
                    m=fb.margin_support
                    want=tuple(.98*(1/len(m) if c in m else 0)+.005 for c in range(4))
                else:
                    self.assertEqual(fb.forecast_source,'suffix1')
                    want=tuple(.98*p+.005 for p in sp)
                for x,y in zip(fb.probabilities,want):self.assertAlmostEqual(x,y,places=15)
                self.assertAlmostEqual(sb,-log(compatible_mass(fb.probabilities,obs)),places=12)
        self.assertIn('margin_n5',seen)

    def test_never_certifies_after_contradiction_and_counts_match_v010(self):
        for case in self.CASES:
            A,B,rows=run_pair(*case)
            self.assertEqual(A.issued,B.issued);self.assertEqual(A.retracted,B.retracted)
            self.assertEqual(A.contradiction_step,B.contradiction_step)

    def test_retraction_reason(self):
        self.assertEqual(retraction_reason(2,(0,None)),'falsified_by_observation')
        self.assertEqual(retraction_reason(2,(None,1)),'falsified_by_observation')
        self.assertEqual(retraction_reason(2,(1,0)),'scope_withdrawn')
        self.assertEqual(retraction_reason(2,(1,None)),'unverifiable_masked')
        self.assertEqual(retraction_reason(2,(None,None)),'unverifiable_masked')
        with self.assertRaises(ValueError):retraction_reason(1,(2,0))

    def test_retractions_carry_reasons(self):
        found=0
        for seed in range(990001,990025):
            for mask in (.1,.35,.6):
                A,B,rows=run_pair(seed,'drift4',mask)
                rs=B.retractions()
                self.assertEqual(len(rs),B.retracted)
                for r in rs:
                    self.assertEqual(r['reason'],retraction_reason(r['certificate'],tuple(r['observed'])))
                    actual=[x[7] for x in rows][r['step']-1]
                    if r['reason']=='scope_withdrawn':self.assertEqual(actual,r['certificate'])
                    if r['reason']=='falsified_by_observation':self.assertNotEqual(actual,r['certificate'])
                found+=len(rs)
        self.assertGreater(found,0)

    def test_retry_keeps_v011_learner(self):
        init,tr=trace(930001,'cycle3',.1)
        L=FallbackBruteLearner(tau=TAU);L.initialize(init)
        for a,obs,_ in tr[:10]:L.observe(a,obs)
        R=L.retry(3)
        self.assertIsInstance(R,FallbackBruteLearner);self.assertEqual(R.steps,10);self.assertIsNone(R.attestation)
        self.assertEqual(R.suffix.observations,L.suffix.observations)

    def test_before_initialize_and_bad_action(self):
        L=FallbackBruteLearner()
        with self.assertRaises(ValueError):L.predict(0)
        L.initialize((0,0))
        with self.assertRaises(ValueError):L.predict(2)


if __name__=='__main__':unittest.main()
