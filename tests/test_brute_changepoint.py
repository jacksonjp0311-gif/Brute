"""v0.3.0 learner (brute/changepoint.py): Y1k resync certification, LU-R experiments, check option, proposal."""
import unittest
from brute.core.learner import Status
from brute.active import ActiveBruteLearner,EXPERIMENT_RULE
from brute.changepoint import ChangePointBruteLearner,Reason030,resync_support,EXPERIMENT_RULE_030
from brute.release_version_030 import RELEASE_VERSION
from tests.test_brute_active import drive,TAU

CASES=[(1390001,'drift4',.1),(1330002,'cycle3',.1),(1340002,'switch3',.35),(1350001,'unstructured3',.1),(1380001,'ood5',.1)]


class ChangePoint(unittest.TestCase):
    def test_version(self):self.assertEqual(RELEASE_VERSION,'0.3.0')

    def test_resync_off_is_v020(self):
        """resync=False, check_run=0 reproduces the frozen v0.2.0 learner exactly (passive and active)."""
        class Off(ChangePointBruteLearner):resync=False
        for k in CASES:
            for pol in (False,True):
                _,a=drive(*k,policy=pol);_,b=drive(*k,policy=pol,cls=Off)
                self.assertEqual([(x,f) for x,f in a],[(x,f) for x,f in b],k)

    def test_passive_only_downgrades(self):
        """Passive: probabilities identical to v0.2.0; certificates a subset; every difference is RESYNC_AMBIGUOUS."""
        down=0
        for k in CASES:
            _,a=drive(*k);_,b=drive(*k,cls=ChangePointBruteLearner)
            for (x,f),(y,g) in zip(a,b):
                self.assertEqual(f.probabilities,g.probabilities);self.assertEqual(f.forecast_source,g.forecast_source)
                if g.status!=f.status:
                    down+=1;self.assertEqual((f.status,g.status,g.reason),(Status.CERTIFIED,Status.ABSTAIN,Reason030.RESYNC_AMBIGUOUS))
                    self.assertIsNone(g.certificate);self.assertIsNone(g.public_certificate)
                else:self.assertEqual(f.certificate,g.certificate)
        self.assertGreater(down,0)

    def test_union_contains_certificate(self):
        """A constant world: the Y1k union is exactly the certificate."""
        L=ActiveBruteLearner(4,5,tau=TAU);L.initialize((0,0))
        for _ in range(12):L.observe(0,(0,0))
        f=L.predict(0);self.assertEqual(f.status,Status.CERTIFIED)
        self.assertEqual(resync_support(L.support,0,1),(0,))

    def test_experiment_fields_and_rule(self):
        L=ChangePointBruteLearner(4,5,tau=TAU);L.initialize((0,0))
        for _ in range(5):L.observe(0,(0,0))
        e=L.experiment(1)
        self.assertEqual(e['rule'],EXPERIMENT_RULE_030);self.assertFalse(e['check'])
        self.assertEqual((e['proposal'],e['no_proposal_reason']),('PROPOSED',None))
        self.assertFalse(ChangePointBruteLearner(4,5,tau=TAU,resync=False).resync)

    def test_check_run_forces_other_branch(self):
        L=ChangePointBruteLearner(4,5,tau=TAU,resync=False,check_run=3);L.initialize((0,0))
        for _ in range(3):L.observe(0,(0,0))
        e=L.experiment(0);self.assertEqual(e['rule'],EXPERIMENT_RULE)
        base=ActiveBruteLearner(4,5,tau=TAU);base.initialize((0,0))
        for _ in range(3):base.observe(0,(0,0))
        b=base.experiment(0)
        if b['action']==0:self.assertTrue(e['check']);self.assertEqual(e['action'],1);self.assertEqual(e['score'],e['scores'][1])
        else:self.assertFalse(e['check'])

    def test_no_proposal_after_contradiction(self):
        L=ChangePointBruteLearner(4,5,tau=None);L.initialize((0,0))
        for _ in range(12):L.observe(0,(0,0))
        L.observe(0,(1,1))
        for obs in ((1,0),(0,1),(1,1),(0,0)):
            L.observe(1,obs)
            if L.support.status=='grammar_contradicted':break
        self.assertEqual(L.support.status,'grammar_contradicted')
        e=L.experiment(0);self.assertEqual((e['proposal'],e['no_proposal_reason']),('NO_PROPOSAL','OUT_OF_SCOPE'))
        self.assertEqual(e['scores'],[0.,0.])

    def test_retry_keeps_class_and_settings(self):
        L=ChangePointBruteLearner(4,5,tau=TAU,resync=False,check_run=3);L.initialize((0,0))
        for _ in range(4):L.observe(1,(0,1))
        R=L.retry(3)
        self.assertIs(type(R),ChangePointBruteLearner);self.assertEqual((R.resync,R.check_run),(False,3))
        self.assertEqual(R.diagnostics()['check_run'],3);self.assertEqual(R.support.evidence,L.support.evidence)


if __name__=='__main__':unittest.main()
