"""v0.2.0 learner (brute/active.py): X1 experiment, X2 window tier, X3 issuance de-duplication."""
import unittest
from bgr89.worlds import world as old_world,actions
from bgr90.worlds import world as new_world,step as new_step
from bgr90.symbolic import SymbolicLearner
from brute.core.learner import BruteLearner,Status
from brute.fallback import FallbackBruteLearner
from brute.active import ActiveBruteLearner,EXPERIMENT_RULE,FORECAST_SOURCES
from brute.release_version import RELEASE_VERSION

TAU=1.433141502274


def drive(seed,family,mask,policy=False,cls=ActiveBruteLearner):
    truth=(new_world if family in ('ood5','drift4') else old_world)(seed,family)
    h=truth.start;L=cls(4,5,160000,160000,.08,.02,8,TAU,None);L.initialize(truth.observed(h,mask,-1))
    out=[]
    for i,pa in enumerate(actions(seed,44)):
        a=L.experiment(pa)['action'] if policy else pa
        f=L.predict(a);L.record_issued(f)
        h=new_step(truth,h,a,i) if family=='drift4' else truth.next(h,a)
        L.observe(a,truth.observed(h,mask,i));out.append((a,f))
    return L,out


class Dedup(unittest.TestCase):
    def test_record_twice_once(self):
        """Bridge B1: predicting (and recording) twice at the same step records issuance once."""
        L=ActiveBruteLearner(4,5,tau=TAU);L.initialize((0,0))
        for _ in range(12):L.observe(0,(0,0))
        f=L.predict(0);self.assertEqual(f.status,Status.CERTIFIED)
        L.record_issued(f);L.record_issued(L.predict(0))
        self.assertEqual(L.issued,[(13,0)])
        C=FallbackBruteLearner(4,5,tau=TAU);C.initialize((0,0))
        for _ in range(12):C.observe(0,(0,0))
        g=C.predict(0);C.record_issued(g);C.record_issued(g)
        self.assertEqual(len(C.issued),2)   # frozen v0.1.1 behaviour, documented (API 1.1 keeps it)

    def test_retraction_listed_once(self):
        L=ActiveBruteLearner(4,5,tau=None);L.initialize((0,0))
        for _ in range(12):L.observe(0,(0,0))
        f=L.predict(0);L.record_issued(f);L.record_issued(f)
        L.observe(0,(1,1))
        for obs in ((1,0),(0,1),(1,1),(0,0)):
            if L.support.status=='grammar_contradicted':break
            L.observe(1,obs)
        self.assertEqual(L.support.status,'grammar_contradicted')
        if True:
            self.assertEqual(len(L.retractions()),1)
            self.assertEqual(L.retractions()[0]['reason'],'falsified_by_observation')


class PassiveEquivalence(unittest.TestCase):
    def test_same_as_v011_until_window(self):
        for seed,fam,mask in [(930002,'cycle3',.35),(990001,'drift4',.1),(980003,'ood5',.6)]:
            A,a=drive(seed,fam,mask);C,c=drive(seed,fam,mask,cls=FallbackBruteLearner)
            for (_,f),(_,g) in zip(a,c):
                for k in ('status','reason','certificate','public_certificate','support','margin_support','saturated'):
                    self.assertEqual(getattr(f,k),getattr(g,k),(seed,k))
                if f.forecast_source!='window_n4':
                    self.assertEqual(f.probabilities,g.probabilities);self.assertEqual(f.forecast_source,g.forecast_source)
                else:self.assertEqual(g.forecast_source,'suffix1')

    def test_window_tier_used_on_drift(self):
        L,out=drive(990002,'drift4',.1)
        srcs={f.forecast_source for _,f in out}
        self.assertIn('window_n4',srcs);self.assertTrue(srcs<=set(FORECAST_SOURCES))
        self.assertGreaterEqual(L.window_restarts,1)
        for _,f in out:
            self.assertGreaterEqual(min(f.probabilities),0.005-1e-15);self.assertAlmostEqual(sum(f.probabilities),1.0,places=9)
            if f.forecast_source=='window_n4':self.assertIsNone(f.certificate)


class Experiment(unittest.TestCase):
    def test_tie_goes_to_default_and_read_only(self):
        L=ActiveBruteLearner(4,5,tau=TAU);L.initialize((0,1))
        before=(L.support.belief,L.margin.belief,list(L.issued),L.steps)
        e0=L.experiment(0);e1=L.experiment(1)
        self.assertEqual(before,(L.support.belief,L.margin.belief,list(L.issued),L.steps))
        self.assertEqual(e0['rule'],EXPERIMENT_RULE)
        if e0['tied']:self.assertEqual((e0['action'],e1['action']),(0,1))

    def test_score_definition(self):
        """score(a) = mean over c in S4(a) of #b certifiable after a full observation c (recomputed here)."""
        L,_=drive(930002,'cycle3',.1)
        for a in (0,1):
            S=L.support.predict_support(a);tot=0
            for c in S:
                f=L.support.reconstruct();m=L.margin.reconstruct()
                f.observe(a,((c>>1)&1,c&1));m.observe(a,((c>>1)&1,c&1))
                if f.status!='supported' or m.status!='supported':continue
                if all(p.used==4 for p in f.belief):continue
                for b in (0,1):
                    s=f.predict_support(b)
                    tot+=len(s)==1 and m.predict_support(b)==s
            want=0. if L.alarm_step is not None else round(tot/len(S),12)
            self.assertEqual(L.experiment_score(a),want)

    def test_policy_never_changes_certification_rule(self):
        L,out=drive(930003,'cycle3',.1,policy=True)
        B=BruteLearner(4,5,160000,160000,.08,.02,8,TAU,None)
        ev=L.support.evidence;B.initialize(ev[0][1])
        for (a,f),(a2,obs) in zip(out,ev[1:]):
            g=B.predict(a)
            self.assertEqual((f.status,f.reason,f.certificate),(g.status,g.reason,g.certificate))
            B.observe(a2,obs)

    def test_counts(self):
        L,_=drive(930002,'cycle3',.35)
        e=L.experiment(0,counts=True)
        for c in e['per_action']:
            if c is None:continue
            self.assertEqual(len(c['family_code_rows']),4);self.assertLessEqual(max(c['family_code_rows']),c['family_rows'])

    def test_retry_keeps_class(self):
        L,_=drive(930002,'cycle3',.35);R=L.retry()
        self.assertIsInstance(R,ActiveBruteLearner);self.assertIsNone(R.attestation)


class Version(unittest.TestCase):
    def test_release_version(self):self.assertEqual(RELEASE_VERSION,'0.2.0')


if __name__=='__main__':unittest.main()
