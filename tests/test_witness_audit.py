"""F4 (v0.1.1): learner_witness_audit finds no <=5-state witness against a certificate,
and finds a replay-verified one when the <=5 margin disagrees."""
import unittest
from bgr89.worlds import world as old_world,actions
from brute.core.learner import Status,Reason
from brute.fallback import FallbackBruteLearner
from scripts.witness_audit import learner_witness_audit,replay_machine

TAU=1.433141502274


class WitnessAudit(unittest.TestCase):
    def scan(self,seed,family,mask):
        truth=old_world(seed,family);h=truth.start
        L=FallbackBruteLearner(tau=TAU);L.initialize(truth.observed(h,mask,-1))
        out={'certified':[],'margin_disagrees':[]}
        for i,a in enumerate(actions(seed,44)):
            f=L.predict(a)
            if f.status==Status.CERTIFIED:out['certified'].append(learner_witness_audit(L,a,f.certificate))
            elif f.reason==Reason.MARGIN_DISAGREES:
                r=learner_witness_audit(L,a,f.support[0]);out['margin_disagrees'].append(r)
                if r['checked'] and r['witness']:
                    m=r['machine'];end=replay_machine(m,L.margin.evidence)
                    self.assertIsNotNone(end)
                    self.assertNotEqual(m['emissions'][m['transitions'][end*2+a]],f.support[0])
                    self.assertLessEqual(m['states'],5)
                    self.assertIn(r['code'],f.margin_support)
            h=truth.next(h,a);L.observe(a,truth.observed(h,mask,i))
        return out

    def test_certified_steps_have_no_witness_and_disagreements_do(self):
        cert=dis=0
        for seed,fam,mask in [(930001,'cycle3',.1),(940002,'switch3',.1),(960003,'unaliased2',.35)]:
            out=self.scan(seed,fam,mask)
            for r in out['certified']:
                self.assertTrue(r['checked']);self.assertFalse(r['witness']);cert+=1
            for r in out['margin_disagrees']:
                self.assertTrue(r['checked']);self.assertTrue(r['witness']);dis+=1
        self.assertGreater(cert,0);self.assertGreater(dis,0)

    def test_replay_rejects_incompatible_machine(self):
        m={'states':1,'transitions':[0,0],'emissions':[3],'start':0}
        self.assertEqual(replay_machine(m,[(None,(1,1)),(0,(1,None))]),0)
        self.assertIsNone(replay_machine(m,[(None,(1,1)),(0,(0,None))]))
        self.assertIsNone(replay_machine(m,[(None,(0,1))]))

    def test_unsupported_margin_is_not_checked(self):
        L=FallbackBruteLearner(1,2,tau=TAU);L.initialize((0,0))
        for obs in [(1,1),(0,1),(1,0),(0,0),(1,1)]:L.observe(0,obs)
        r=learner_witness_audit(L,0,0)
        if L.margin.status!='supported':self.assertFalse(r['checked'])
        else:self.assertTrue(r['checked'])


if __name__=='__main__':unittest.main()
