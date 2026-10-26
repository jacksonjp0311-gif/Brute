"""GTI runner (scripts/run_tests_070.py) verdict logic and frozen-file check."""
import unittest,json
from scripts import run_tests_070 as T


def mods(extra=None):
    m={'test_study_005.py':{'tests_run':6,'skipped':[],'results':{f'test_study_005.Study005.t{i}':['ok',None] for i in range(6)}}}
    for n in T.NEW_TESTS:m[n]={'tests_run':1,'skipped':[],'results':{n[:-3]+'.X.t':['ok',None]}}
    for k,v in (extra or {}).items():m.setdefault(k.split('.')[0]+'.py',{'tests_run':0,'skipped':[],'results':{}})['results'][k]=v;m[k.split('.')[0]+'.py']['tests_run']+=1
    return m


class RunTests070(unittest.TestCase):
    plan=json.loads(T.PLAN.read_text())
    def plain(self,m):return {'tests_run':sum(d['tests_run'] for d in m.values()),'skipped':[]}
    def test_pass_and_declared(self):
        m=mods({'test_brute_repro.BruteRepro.test_verify_fails_under_tampered_results':['error','x']})
        V=T.verdict(m,self.plain(m),{'changed':[]},self.plan);self.assertTrue(V['passed'],V['clauses'])

    def test_undeclared_fails(self):
        m=mods({'test_x.A.b':['fail','x']});V=T.verdict(m,self.plain(m),{'changed':[]},self.plan)
        self.assertFalse(V['clauses']['i_only_declared_failures'])

    def test_k060(self):
        t='test_release_060.Release060.test_fast_verify_passes';m=mods({t:['fail','x']})
        self.assertFalse(T.verdict(m,self.plain(m),{'changed':[]},self.plan)['passed'])
        self.assertTrue(T.verdict(m,self.plain(m),{'changed':[]},self.plan,{'results':{t:['ok',None]}})['passed'])
        self.assertFalse(T.verdict(m,self.plain(m),{'changed':[]},self.plan,{'results':{t:['fail',None]}})['passed'])
        m=mods({'test_release_060.GT1.test_frozen_050_defect_still_recorded':['fail','x']})
        self.assertFalse(T.verdict(m,self.plain(m),{'changed':[]},self.plan,{'results':{}})['passed'])

    def test_count_mismatch_and_frozen(self):
        m=mods();p=self.plain(m);p['tests_run']+=1
        self.assertFalse(T.verdict(m,p,{'changed':[]},self.plan)['clauses']['iii_counts_match_plain'])
        self.assertFalse(T.verdict(m,self.plain(m),{'changed':[{'file':'x'}]},self.plan)['passed'])
        m=mods({'test_study_005.Study005.t0':['error','order']})
        self.assertFalse(T.verdict(m,self.plain(m),{'changed':[]},self.plan)['clauses']['ii_test_study_005_six_pass'])

    def test_frozen_files_unchanged(self):
        f=T.frozen_check();self.assertEqual(f['changed'],[]);self.assertIn('BRUTE_RELEASE_FREEZE_060.json',f['superseded_freezes'])


if __name__=='__main__':unittest.main()
