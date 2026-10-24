"""Brute v0.1.0 soundness gates (F1-F5). Uses study-001 seeds only, never study-002 seeds."""
import json,unittest
from pathlib import Path
from brute.core.learner import BruteLearner,ScopeAttestation,Status,Reason
from brute.evaluation import run_case
ROOT=Path(__file__).resolve().parents[1]
PLAN=json.loads((ROOT/'experiments/BRUTE_PLAN_002.json').read_text())
ATT=ScopeAttestation('deterministic-moore<=2/stationary','test','constructed')


def constant_learner(steps=6,**kw):
    L=BruteLearner(2,3,**kw);L.initialize((0,0));out=[]
    for _ in range(steps):
        f=L.predict(0);L.record_issued(f);out.append(f);L.observe(0,(0,0))
    return L,out


class BruteAbstention(unittest.TestCase):
    def test_contradiction_yields_out_of_family_and_retraction(self):
        L,out=constant_learner()
        issued=sum(f.certificate is not None for f in out);self.assertGreater(issued,0)
        L.observe(0,(1,1))
        f=L.predict(0)
        self.assertEqual((f.status,f.reason),(Status.OUT_OF_FAMILY,Reason.FAMILY_CONTRADICTED))
        self.assertIsNone(f.certificate);self.assertEqual(f.probabilities,(.25,)*4)
        self.assertEqual(L.diagnostics()['certificates_retracted'],issued)

    def test_margin_gate_blocks_ood5_false_certificates(self):
        # study-001 seeds where v0.90 issued wrong certificates on ood5
        control=brute=0
        for seed,rate in ((980001,.1),(980001,.35),(980002,.6)):
            c=run_case(seed,'ood5',rate,PLAN,None)
            control+=sum(r['v090_wrong'] for r in c['trace']);brute+=sum(r['brute_wrong'] for r in c['trace'])
        self.assertGreater(control,0);self.assertEqual(brute,0)

    def test_margin_gate_preserves_in_family_soundness(self):
        for fam,seed in (('cycle3',930002),('switch3',940003),('unstructured3',950004),('unaliased2',960005),('ood4',970006)):
            for rate in PLAN['mask_rates']:
                c=run_case(seed,fam,rate,PLAN,None)
                self.assertFalse(any(r['brute_wrong'] or r['public_wrong'] for r in c['trace']))

    def test_saturated_bound_abstains(self):
        L=BruteLearner(2,3);L.initialize((0,0));seen=[]
        for i in range(8):
            f=L.predict(0);seen.append((f.status,f.reason,f.saturated));L.observe(0,(1,1) if i%2==0 else (0,0))
        self.assertIn((Status.ABSTAIN,Reason.BOUND_SATURATED,True),seen)
        self.assertFalse(any(s==Status.CERTIFIED for s,_,_ in seen))

    def test_residual_surprise_flags_drift4(self):
        quiet=run_case(990002,'drift4',.1,PLAN,None)
        self.assertFalse(any(r['alarm_after'] for r in quiet['trace']))
        R=[r['residual_after'] for r in quiet['trace'] if r['residual_after'] is not None]
        tau=sorted(R)[len(R)//2]
        loud=run_case(990002,'drift4',.1,PLAN,tau)
        k=next(i for i,r in enumerate(loud['trace']) if r['alarm_after'])
        self.assertGreater(loud['trace'][k]['residual_after'],tau)
        after=loud['trace'][k+1:]
        self.assertTrue(after and all(r['status']=='OUT_OF_FAMILY' and r['certificate'] is None for r in after))
        self.assertTrue(all(r['alarm_after'] for r in after))  # sticky

    def test_every_certificate_names_its_family_and_is_belief_consistent(self):
        L,out=constant_learner()
        for f in out:
            self.assertEqual(f.family,'deterministic-moore<=2/stationary')
            if f.certificate is not None:
                self.assertEqual(f.status,Status.CERTIFIED)
                self.assertEqual(f.support,(f.certificate,));self.assertEqual(f.margin_support,(f.certificate,))
            else:self.assertNotEqual(f.status,Status.CERTIFIED)

    def test_public_cert_requires_attestation_margin_and_no_alarm(self):
        _,out=constant_learner()
        self.assertTrue(all(f.public_certificate is None for f in out))
        self.assertTrue(any(f.public_reason==Reason.UNATTESTED_SCOPE for f in out))
        L,out=constant_learner(attestation=ATT)
        self.assertTrue(all(f.public_certificate==f.certificate for f in out))
        self.assertTrue(any(f.status==Status.ABSTAIN and f.public_certificate is None for f in out))  # margin first
        wrong=BruteLearner(2,3,attestation=ScopeAttestation('other-family','test','x'));wrong.initialize((0,0))
        for _ in range(5):wrong.observe(0,(0,0))
        self.assertIsNone(wrong.predict(0).public_certificate)
        L,_=constant_learner(9,attestation=ATT,tau=-1.0)  # any residual alarms
        f=L.predict(0);self.assertEqual(f.reason,Reason.RESIDUAL_SURPRISE);self.assertIsNone(f.public_certificate)
        self.assertIsNone(L.attestation)

    def test_retry_revokes_attestation(self):
        L,_=constant_learner(attestation=ATT)
        self.assertIsNotNone(L.predict(0).public_certificate)
        R=L.retry(3)
        self.assertIsNone(R.attestation);self.assertEqual(R.family,'deterministic-moore<=3/stationary')
        self.assertEqual(len(R.support.evidence),len(L.support.evidence))
        self.assertIsNone(R.predict(0).public_certificate)


if __name__=='__main__':unittest.main()
