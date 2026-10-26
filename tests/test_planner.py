"""v0.7.0 P7 (brute.planner): objective, counting sources agree, certification isolation (GP1 iv) on a smoke seed."""
import unittest,copy,time
from fractions import Fraction
from experiments.brute_common import load
from experiments.brute_study_009 import run_job,PLAN
from experiments import v070_reference as R
from brute.planner import e1,choose,enumerate_pairs,ganak_fibres,count_decision,CountPlanLearner
from scripts.check_planning_009 import replay,recount_all


class Planner009(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=load(PLAN);cls.c=run_job(('smoke-planning','cycle3',2190025,0.35),cls.plan)[1]

    def test_objective(self):
        self.assertEqual(e1([2,2]),Fraction(2));self.assertIsNone(e1([0,0]))
        a,E1,E2=choose([[3,1],[2,2]],None,0);self.assertEqual(a,1);self.assertEqual(E1,[Fraction(10,4),Fraction(2)])
        self.assertEqual(choose([[2,2],[2,2]],None,1)[0],1)              # tie -> a_L
        self.assertEqual(choose([[1,0],[0,0]],None,0)[0],None)           # N_a = 0 -> fallback

    def test_planned_trace_and_reference(self):
        tr=self.c['arms']['P7']['trace'];pl=[r['planner'] for r in tr if r['planner']]
        self.assertEqual(len(pl),36);self.assertTrue(all(p['planned'] and p['source']=='enumeration' for p in pl))
        self.assertTrue(all(r['planner'] is None for r in tr[:8]))
        v=R.plan_view(self.plan);ok,msg,t=R.audit_trace(self.c,'P7',v,self.plan['tau6']['value'],self.plan['tau7']['value'])
        self.assertTrue(ok,msg);self.assertEqual(t['planned'],36)

    def test_enumeration_equals_ganak(self):
        rs=[r['planner']['region'] for r in self.c['arms']['P7']['trace'] if r['planner']][:3]
        for g in rs:
            c,_,_=enumerate_pairs(g['n'],g['masks'],g['actions'])
            out=count_decision(g['n'],g['masks'],g['actions'],30.)        # forked child, enumeration source
            self.assertEqual(out['counts'],c)
        items=[{'source':'enumeration','region':g} for g in rs]
        for it,(src,c2,why,_) in zip(items,recount_all(items,2)):
            self.assertEqual(src,'ganak');self.assertIsNone(why)
            self.assertEqual(c2,enumerate_pairs(it['region']['n'],it['region']['masks'],it['region']['actions'])[0])

    def test_certification_isolation_replay(self):
        self.assertEqual(replay(self.c,self.plan),[])
        c=copy.deepcopy(self.c);r=c['arms']['P7']['trace'][20];r['probabilities']=[round(x+1e-9,12) for x in r['probabilities']]
        self.assertTrue(replay(c,self.plan))

    def test_policy_guard(self):
        with self.assertRaises(ValueError):CountPlanLearner(6,6,1000,1000,0.1,0.01,8,1.0,None,policy='M')


if __name__=='__main__':unittest.main()
