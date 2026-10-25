"""Study-004 harness and its independent reference (plan G8a, G9, G11) on a few held-out cases."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from experiments.brute_common_004 import load,PLAN,VerificationError
from experiments.brute_study_004 import run_case_004,aggregate_004
from experiments.v020_independent_reference import audit_case

PLAN_=load(PLAN);TAU=PLAN_['residual_surprise']['tau']
CASES=[(1330002,'cycle3',.1),(1390002,'drift4',.1),(1380001,'ood5',.1)]
_cache={}


def case(seed,fam,m):
    if (seed,fam,m) not in _cache:_cache[(seed,fam,m)]=json.loads(json.dumps(run_case_004(seed,fam,m,PLAN_,TAU)))
    return copy.deepcopy(_cache[(seed,fam,m)])


class Study004(unittest.TestCase):
    def test_reference_agrees(self):
        for k in CASES:
            out=audit_case((case(*k),PLAN_,TAU))
            self.assertEqual(out['A']['steps'],44);self.assertEqual(out['P']['g8a_steps_checked'],44)
        self.assertGreater(audit_case((case(*CASES[1]),PLAN_,TAU))['P']['window_n4_steps'],0)

    def test_reference_detects_tampering(self):
        def t_score(c):c['arms']['A']['trace'][20]['experiment']['scores'][0]+=0.5
        def t_action(c):r=c['arms']['A']['trace'][15];r['action']=1-r['action']
        def t_cert(c):
            r=next(r for r in c['arms']['P']['trace'] if r['certificate'] is not None);r['certificate']=(r['certificate']+1)%4
        def t_cf(c):
            r=next(r for a in ('A','P') for r in c['arms'][a]['trace'] if r['counterfactual']['certificate'] is not None);r['counterfactual']['wrong']=True
        def t_issued(c):c['arms']['A']['issued'].append(c['arms']['A']['issued'][0])
        for fn in (t_score,t_action,t_cert,t_cf,t_issued):
            c=case(*CASES[0]);fn(c)
            with self.assertRaises(VerificationError,msg=fn.__name__):audit_case((c,PLAN_,TAU))
        c=case(*CASES[1]);r=next(r for r in c['arms']['P']['trace'] if r['forecast_source']=='window_n4');r['forecast_source']='suffix1'
        with self.assertRaises(VerificationError):audit_case((c,PLAN_,TAU))

    def test_reference_imports_no_brute(self):
        code='import sys;import experiments.v020_independent_reference;print([m for m in sys.modules if m=="brute" or m.startswith("brute.")])'
        out=subprocess.run([sys.executable,'-c',code],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
        self.assertEqual(out,'[]')

    def test_aggregate_and_dedup(self):
        cs=[case(*k) for k in CASES];s=aggregate_004(cs,PLAN_)
        for fam in ('cycle3','drift4','ood5'):
            for arm in ('A','P'):
                self.assertEqual(s[fam][arm]['duplicate_issued_pairs'],0);self.assertEqual(s[fam][arm]['duplicate_retraction_pairs'],0)
            self.assertEqual(s[fam]['G8a_passive_equivalence']['differing_steps'],0)
        self.assertGreater(s['cycle3']['A']['dual_coverage_post'],s['cycle3']['P']['dual_coverage_post'])


if __name__=='__main__':unittest.main()
