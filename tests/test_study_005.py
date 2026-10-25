"""Study-005 harness and its independent reference (plan G8a, G9, G11, G14 metrics) on a few held-out cases."""
import copy,json,subprocess,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
from experiments.brute_common_005 import load,PLAN,VerificationError,is_stale
from experiments.brute_study_005 import run_case_005,aggregate_005,MAIN_ARMS,EXT_ARMS,jobs_for
from experiments.v030_independent_reference import audit_case
from brute.evaluation import no_time

PLAN_=load(PLAN);TAU=PLAN_['residual_surprise']['tau']
CASES=[(1430002,'cycle3',.1),(1490001,'drift4',.1),(1480001,'ood5',.1)]
_cache={}


def case(seed,fam,m,arms=MAIN_ARMS):
    k=(seed,fam,m,arms)
    if k not in _cache:_cache[k]=json.loads(json.dumps(run_case_005(seed,fam,m,PLAN_,TAU,arms)))
    return copy.deepcopy(_cache[k])


class Study005(unittest.TestCase):
    def test_jobs_match_plan(self):
        main,ext=jobs_for(PLAN_,TAU);self.assertEqual(len(main),7*24*3);self.assertEqual(len(ext),72*3)
        self.assertEqual(tuple(PLAN_['extended_drift4_block']['arms']),EXT_ARMS)
        self.assertEqual([s for s in range(1,45) if is_stale(s)][:3],[13,14,15]);self.assertFalse(is_stale(23))

    def test_reference_agrees(self):
        for k in CASES:
            out=audit_case((case(*k),PLAN_,TAU))
            self.assertEqual(sorted(out),sorted(MAIN_ARMS))
            for t in out.values():self.assertEqual(t['steps'],44)
            self.assertEqual(out['P3']['g8a_steps_checked'],44)
        out=audit_case((case(1491001,'drift4',.1,EXT_ARMS),PLAN_,TAU));self.assertEqual(sorted(out),sorted(EXT_ARMS))

    def test_reference_detects_tampering(self):
        def t_score(c):c['arms']['A3']['trace'][20]['experiment']['scores'][0]+=0.5
        def t_action(c):r=c['arms']['E2']['trace'][15];r['action']=1-r['action']
        def t_check(c):r=c['arms']['E2']['trace'][30];r['experiment']['check']=not r['experiment']['check']
        def t_resync(c):
            r=next(r for r in c['arms']['P3']['trace'] if r['reason']=='RESYNC_AMBIGUOUS');r.update(status='CERTIFIED',reason=None)
        def t_cert(c):
            r=next(r for r in c['arms']['A2']['trace'] if r['certificate'] is not None);r['certificate']=(r['certificate']+1)%4
        def t_issued(c):c['arms']['A3']['issued'].append(c['arms']['A3']['issued'][0])
        for fn in (t_score,t_action,t_check,t_resync,t_cert,t_issued):
            c=case(*CASES[0]);fn(c)
            with self.assertRaises(VerificationError,msg=fn.__name__):audit_case((c,PLAN_,TAU))

    def test_reference_imports_no_brute(self):
        code='import sys;import experiments.v030_independent_reference;print([m for m in sys.modules if m=="brute" or m.startswith("brute.")])'
        out=subprocess.run([sys.executable,'-c',code],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
        self.assertEqual(out,'[]')

    def test_aggregate(self):
        cs=[case(*k) for k in CASES];s=aggregate_005(cs,PLAN_)
        for fam in ('cycle3','drift4','ood5'):
            for arm in MAIN_ARMS:
                self.assertEqual(s[fam][arm]['duplicate_issued_pairs'],0);self.assertEqual(s[fam][arm]['resync_issued'],0)
            g=s[fam]['G8a_passive_equivalence']
            self.assertEqual((g['probability_or_source_differences'],g['certificate_differences'],g['non_resync_differences']),(0,0,0))
        self.assertEqual(s['cycle3']['A3']['check_steps_post'],0)

    def test_deterministic(self):
        a=run_case_005(*CASES[1],PLAN_,TAU);b=run_case_005(*CASES[1],PLAN_,TAU)
        self.assertEqual(json.dumps(no_time(a),sort_keys=True),json.dumps(no_time(b),sort_keys=True))


if __name__=='__main__':unittest.main()
