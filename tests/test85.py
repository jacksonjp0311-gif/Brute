"""No-reset topological explorer, auditable reachable-completeness proof and safety."""
import unittest
from collections import Counter,deque
from random import Random
from bgr60.generalist import StateSchema,GeneralLearner
from bgr60.worlds import factory
from bgr85.topology import TopologyExplorer,certified_graph
from bgr85.certification import certify_reachable,verify_certificate,certified_goal_plan
from bgr85.study import run_case,reachable

class V85Tests(unittest.TestCase):
    def test_unknown_action_prevents_certificate(self):
        lr=GeneralLearner(StateSchema(('bit',),((0,1),)),('flip',))
        c=certify_reachable(lr,(0,))
        self.assertFalse(c.complete)
        self.assertEqual(c.states,((0,),))
        self.assertEqual(c.open_frontier,(((0,),0),))
        self.assertTrue(verify_certificate(lr,c))
    def test_certificate_matches_reachable_teacher(self):
        for fam in ('logic','switching','navigation','mixed','incompatible'):
            w=factory(91121,fam);schema,actions=w.public()
            lr=GeneralLearner(schema,actions)
            s=next(iter(schema.all_states()))
            for u in schema.all_states():
                for a in range(len(actions)):
                    lr.observe(a,u,w.transition(a,u))
            cert=certify_reachable(lr,s)
            self.assertTrue(cert.complete)
            self.assertTrue(verify_certificate(lr,cert))
            self.assertEqual(set(cert.states),set(reachable(w,s)))
            self.assertTrue(all(w.transition(a,u)==v for u,a,v in cert.edges))
    def test_unknown_edges_do_not_become_shortest(self):
        lr=GeneralLearner(StateSchema(('bit',),((0,1),)),('flip',))
        self.assertEqual(certified_goal_plan(lr,(0,),(1,))['status'],'abstain_unknown_reachability')
        lr.observe(0,(0,),(1,));lr.observe(0,(1,),(0,))
        c=certify_reachable(lr,(0,))
        self.assertTrue(c.complete)
        self.assertEqual(certified_goal_plan(lr,(0,),(1,))['plan'],[0])
        self.assertTrue(certified_goal_plan(lr,(0,),(1,))['shortest_claim'])
    def test_reachable_complete_without_global_identification(self):
        lr=GeneralLearner(StateSchema(('loc',),((0,1),)),('stay_here',))
        lr.observe(0,(0,),(0,))
        self.assertFalse(lr.identified())
        proof=certify_reachable(lr,(0,))
        self.assertTrue(proof.complete)
        self.assertEqual(proof.states,((0,),))
        self.assertEqual(certified_goal_plan(lr,(0,),(1,))['status'],'provably_unreachable_in_model_family')

    def test_provably_unreachable_from_closed_region(self):
        lr=GeneralLearner(StateSchema(('loc',),((0,1,2),)),('stay',))
        for s in lr.schema.all_states():lr.observe(0,s,s)
        c=certify_reachable(lr,(0,))
        self.assertTrue(c.complete)
        self.assertEqual(c.states,((0,),))
        self.assertEqual(certified_goal_plan(lr,(0,),(2,))['status'],'provably_unreachable_in_model_family')
    def test_separate_safety_scope_is_not_escalated(self):
        lr=GeneralLearner(StateSchema(('loc',),((0,1,2),)),('unknown','stay'))
        for s in lr.schema.all_states():lr.observe(1,s,s)
        topo=TopologyExplorer(allowed_state=lambda s:s!=(2,))
        a=topo.choose(lr,(0,),Counter())
        self.assertEqual(a,1)
        self.assertGreater(topo.stats.refused_safety,0)
    def test_certified_routes_no_teacher(self):
        lr=GeneralLearner(StateSchema(('loc',),((0,1,2),)),('advance',))
        lr.observe(0,(0,),(1,));lr.observe(0,(1,),(2,))
        routes,edges=certified_graph(lr,(0,))
        for s,route in routes.items():
            x=(0,)
            for a in route:
                x=lr.certified(a,x)
                self.assertIsNotNone(x)
            self.assertEqual(x,s)
    def test_no_reset_all_families(self):
        for fam in ('logic','switching','navigation','mixed','incompatible'):
            r=run_case(91122,fam,'topology',steps=60)
            self.assertEqual(r['incorrect'],0)
            self.assertEqual(len(r['trace']),60)
            self.assertTrue(all(not x['shortest_claim'] or x['optimal'] for x in r['goals']))
    def test_goal_is_hint_not_teacher_leak(self):
        lr=GeneralLearner(StateSchema(('a','b'),((0,1),(0,1))),('x','y'))
        explorer=TopologyExplorer(goal=(1,1))
        selected=explorer.choose(lr,(0,0),Counter())
        self.assertIn(selected,(0,1))
    def test_false_certification_if_teacher_outside_family_not_claimed(self):
        # This theorem assumes the true teacher is inside learner's hypothesis family.
        # It must never claim correctness for a contradictory observation.
        from bgr60.generalist import Contradiction
        lr=GeneralLearner(StateSchema(('a','b'),((0,1),(0,1))),('multi',))
        with self.assertRaises(Contradiction):lr.observe(0,(0,0),(1,1))
        self.assertFalse(certify_reachable(lr,(0,0)).complete)

if __name__=='__main__':unittest.main()
