"""run_tests_080 verdict: K_060 / K_070 clean-tag rules, clause (v) new-test rule, counts consistency."""
import json,unittest
from scripts import run_tests_080 as R
PLAN=json.loads(R.PLAN.read_text())


def mods(extra=None):
    m={'test_study_005.py':{'results':{f'test_study_005.T.t{i}':['ok'] for i in range(6)},'tests_run':6,'skipped':[]},
       'test_align.py':{'results':{'test_align.A.t':['ok']},'tests_run':1,'skipped':[]}}
    for k,v in (extra or {}).items():m[k]=v
    return m
PLAIN=lambda m:{'tests_run':sum(d['tests_run'] for d in m.values()),'skipped':[]}
OK={'changed':[]}


class RunTests080(unittest.TestCase):
    def test_clean_pass(self):
        m=mods();self.assertTrue(R.verdict(m,PLAIN(m),OK,PLAN,new_tests=('test_align.py',))['passed'])

    def test_k070_needs_clean_tag_pass(self):
        t='test_release_070.Release070.test_version_consistent'
        m=mods({'test_release_070.py':{'results':{t:['fail']},'tests_run':1,'skipped':[]}})
        self.assertFalse(R.verdict(m,PLAIN(m),OK,PLAN,new_tests=())['passed'])
        V=R.verdict(m,PLAIN(m),OK,PLAN,clean={'070':{'results':{t:['ok']}}},new_tests=())
        self.assertTrue(V['passed']);self.assertTrue(V['k_rules']['070']['applied'])
        V=R.verdict(m,PLAIN(m),OK,PLAN,clean={'070':{'results':{t:['fail']}}},new_tests=())
        self.assertFalse(V['passed'])

    def test_k070_other_test_not_covered(self):
        t='test_release_070.Release070.test_storage_round_trip'
        m=mods({'test_release_070.py':{'results':{t:['fail']},'tests_run':1,'skipped':[]}})
        self.assertFalse(R.verdict(m,PLAIN(m),OK,PLAN,clean={'070':{'results':{t:['ok']}}},new_tests=())['passed'])

    def test_new_test_failure_and_missing(self):
        m=mods();m['test_align.py']['results']['test_align.A.t']=['fail']
        V=R.verdict(m,PLAIN(m),OK,PLAN,new_tests=('test_align.py',));self.assertFalse(V['clauses']['v_new_tests_pass'])
        V=R.verdict(mods(),PLAIN(mods()),OK,PLAN,new_tests=('test_nope.py',));self.assertFalse(V['clauses']['v_new_tests_pass'])

    def test_counts_and_frozen(self):
        m=mods();self.assertFalse(R.verdict(m,{'tests_run':1,'skipped':[]},OK,PLAN,new_tests=())['clauses']['iii_counts_match_plain'])
        self.assertFalse(R.verdict(m,PLAIN(m),{'changed':[{'file':'x'}]},PLAN,new_tests=())['passed'])

    def test_new_tests_are_absent_from_v070(self):
        self.assertIn('test_jumphull.py',R.NEW_TESTS);self.assertNotIn('test_study_005.py',R.NEW_TESTS)


if __name__=='__main__':unittest.main()
