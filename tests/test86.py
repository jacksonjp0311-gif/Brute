"""Tests for goal-directed information value, invariants and no-reset safety."""
import unittest
from collections import Counter
from random import Random
from bgr60.generalist import StateSchema,GeneralLearner
from bgr60.worlds import factory
from bgr86.controller import (allowed_outcomes,robust_goal_depth,optimistic_distances,
    certified_routes,GoalValueExplorer)
from bgr86.study import run_case,oracle_distances,oracle_goal


class GoalLearningTests(unittest.TestCase):
    def test_unknown_outcomes_never_masquerade_as_certified(self):
        lr=GeneralLearner(StateSchema(('bit',),((0,1),)),('x',))
        self.assertIsNone(lr.certified(0,(0,)))
        d=optimistic_distances(lr,(1,))
        self.assertEqual(d[(0,)],1)
        self.assertIsNone(lr.certified(0,(0,)))
        self.assertEqual(lr.history,[])

    def test_goal_certified_route_precedes_exploration(self):
        lr=GeneralLearner(StateSchema(('x',),((0,1,2),)),('next','unknown'))
        lr.observe(0,(0,),(1,));lr.observe(0,(1,),(2,))
        # Another operation has not been observed, but the shortest known
        # route toward goal is unambiguous and uses action 0.
        p=GoalValueExplorer((2,))
        self.assertEqual(p.choose(lr,(0,),Counter()),0)
        self.assertEqual(p.stats.last_decision,'certified_goal_route')
        self.assertEqual(lr.history[-1]['before'],[1])

    def test_robust_all_outcomes_and_no_fabricated_certification(self):
        lr=GeneralLearner(StateSchema(('x',),((0,1),)),('unknown','stay'))
        lr.observe(1,(0,),(0,));lr.observe(1,(1,),(1,))
        depth=robust_goal_depth(lr,(1,))
        self.assertEqual(depth[(1,)],0)
        self.assertNotIn((0,),depth)
        self.assertIsNone(lr.certified(0,(0,)))

    def test_belief_actions_obey_external_safety_scope(self):
        lr=GeneralLearner(StateSchema(('x',),((0,1,2),)),('unknown','stay'))
        for s in lr.schema.all_states():lr.observe(1,s,s)
        p=GoalValueExplorer((1,),allowed_state=lambda s:s!=(2,))
        a=p.choose(lr,(0,),Counter())
        self.assertEqual(a,1)
        self.assertGreater(p.stats.rejected_unsafe_actions,0)
        self.assertIsNone(allowed_outcomes(lr,(0,),0,lambda s:s!=(2,)))

    def test_if_all_paths_unsafe_abstain(self):
        lr=GeneralLearner(StateSchema(('x',),((0,1,2),)),('unknown',))
        p=GoalValueExplorer((1,),allowed_state=lambda s:s!=(2,))
        self.assertIsNone(p.choose(lr,(0,),Counter()))
        self.assertEqual(p.stats.last_decision,'abstain_no_safe_action')

    def test_goal_takes_priority_over_unrelated_unknown_action(self):
        lr=GeneralLearner(StateSchema(('x','y'),((0,1),(0,1))),('advance','mystery'))
        # Sufficient evidence for a deterministic x action at state (0,0)
        # and from (1,0) to (1,0); mystery remains unresolved.
        lr.observe(0,(0,0),(1,0))
        lr.observe(0,(1,0),(1,0))
        p=GoalValueExplorer((1,0))
        self.assertEqual(p.choose(lr,(0,0),Counter()),0)
        self.assertEqual(p.stats.last_decision,'certified_goal_route')

    def test_paired_goals_independent_of_exploration_policy(self):
        cases=[run_case(74131,'switching',p,budget=12) for p in
               ('goal_value','certified_goal','frontier','active','random')]
        self.assertEqual(len({tuple(c['initial']) for c in cases}),1)
        self.assertEqual(len({tuple(c['goal'] or ()) for c in cases}),1)
        self.assertTrue(all(c.get('knowledge_wrong',0)==0 for c in cases))
        self.assertTrue(all(c['steps']<=12 for c in cases))
        for c in cases:
            if c['eligible']:
                self.assertEqual(c['reached'],c['final']==c['goal'])
                self.assertEqual(c['steps_to_goal'],c['steps'] if c['reached'] else None)

    def test_real_world_progress_and_no_reset(self):
        for fam in ('logic','switching','navigation','mixed','incompatible'):
            for pol in ('goal_value','frontier','random'):
                case=run_case(74131,fam,pol,budget=18)
                self.assertTrue(all(c['before']==case['initial'] for c in case['trace'][:1]))
                self.assertTrue(all(case['trace'][i]['after']==case['trace'][i+1]['before']
                                    for i in range(len(case['trace'])-1)))
                self.assertEqual(case.get('knowledge_wrong',0),0)
                if case['eligible'] and case['reached']:
                    self.assertNotEqual(case['initial'],case['goal'])
                    self.assertGreaterEqual(case['steps_to_goal'],case['oracle_initial_shortest'])

    def test_independent_reference_reconstructs_hidden_rule_posterior(self):
        from experiments.v86_independent_audit import audit_case
        for fam in ('logic','navigation','mixed'):
            case=run_case(74220,fam,'goal_value',budget=16)
            out=audit_case(case,16)
            self.assertEqual(out['false_certifications'],0)
            self.assertEqual(out['goal_succeeded'],case['reached'])

    def test_robust_successor_paths_are_all_certified_or_safe(self):
        # A robust depth rule cannot rely on an outcome known to be unsafe.
        lr=GeneralLearner(StateSchema(('s',),((0,1,2),)),('act',))
        lr.observe(0,(0,),(1,))
        safe=lambda s:s!=(2,)
        d=robust_goal_depth(lr,(1,),safe)
        if (0,) in d:
            self.assertTrue(all(x in d for x in allowed_outcomes(lr,(0,),0,safe)))
        self.assertIsNone(allowed_outcomes(lr,(2,),0,safe) if (2,) in lr.schema.all_states() else None)

    def test_external_oracle_is_not_imported_by_controller(self):
        import inspect,bgr86.controller as module
        src=inspect.getsource(module)
        self.assertNotIn('from bgr60.worlds',src)
        self.assertNotIn('world.transition',src)
        self.assertNotIn('oracle_goal',src)

    def test_optimistic_routes_are_not_safety_or_certainty(self):
        lr=GeneralLearner(StateSchema(('loc',),((0,1,2),)),('move',))
        self.assertIn((0,),optimistic_distances(lr,(2,)))
        self.assertIsNone(lr.certified(0,(0,)))
        self.assertEqual(certified_routes(lr,(0,)),{(0,):()})
        self.assertEqual(len(lr.history),0)

if __name__=='__main__': unittest.main()
