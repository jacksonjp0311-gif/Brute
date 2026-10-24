"""Conditional world beliefs, exact-value oracle, symmetry/caching and safety."""
import unittest
from collections import Counter
from fractions import Fraction
from random import Random
from bgr87.finite_bayes import (STATES,MODEL_COUNT,RULE_COUNT,GAMMA,FiniteBelief,
     ModelViolation,ComputeBudgetExceeded,ExactPlanner,partition,true_transition,TRANSITIONS)
from experiments.independent_reference import (WORLDS,STATES as REF_STATES,
     rebuild_posterior,exhaustive_value,successors)
from bgr87.study import run_case,scenario

class ExactPlanningTests(unittest.TestCase):
    def test_catalogue_bijection_independent_code(self):
        self.assertEqual(STATES,REF_STATES)
        self.assertEqual(len(WORLDS),256)
        for m in range(MODEL_COUNT):
            for a in (0,1):
                for s in range(4):
                    self.assertEqual(true_transition(m,a,s),WORLDS[m][a][s])

    def test_posterior_filter_independent_reference(self):
        rng=Random(87)
        for _ in range(120):
            teacher=rng.randrange(MODEL_COUNT)
            p=FiniteBelief();s=rng.randrange(4);trace=[]
            for k in range(7):
                a=rng.randrange(2);n=true_transition(teacher,a,s)
                p.observe(s,a,n);trace.append((s,a,n));s=n
                self.assertEqual(p.ids,rebuild_posterior(trace))
                self.assertIn(teacher,p.ids)
                for action in (0,1):
                    self.assertEqual(set(p.possibilities(s,action)),set(successors(p.ids,s,action)))

    def test_bellman_value_against_separate_exact_oracle(self):
        prior=tuple(range(MODEL_COUNT))
        for s in range(4):
            for goal in range(4):
                if s==goal:continue
                for horizon in (1,2,3,4,5,6):
                    reference,q=exhaustive_value(s,goal,prior,horizon)
                    p=ExactPlanner(goal,expansion_budget=2000)
                    chosen,value=p.exact_action(s,prior,horizon)
                    self.assertEqual(value,reference)
                    self.assertEqual(value,q[chosen])
        # Posterior-conditional decisions, not just root priors.
        rng=Random(811)
        for _ in range(80):
            m=rng.randrange(MODEL_COUNT);p=FiniteBelief();s=rng.randrange(4)
            for k in range(rng.randrange(1,5)):
                a=rng.randrange(2);n=true_transition(m,a,s);p.observe(s,a,n);s=n
            goal=rng.choice([g for g in range(4) if g!=s])
            ref,q=exhaustive_value(s,goal,p.ids,4)
            policy=ExactPlanner(goal,expansion_budget=2000)
            a,val=policy.exact_action(s,p.ids,4)
            self.assertEqual(val,ref)
            self.assertEqual(val,q[a])

    def test_prior_action_exchangeability_proof(self):
        # For each paired action posterior with equal allowed rule sets, Q0=Q1.
        initial=FiniteBelief()
        for s in range(4):
            for goal in range(4):
                if s==goal:continue
                _,q=exhaustive_value(s,goal,initial.ids,5)
                self.assertEqual(q[0],q[1])
                adaptive=ExactPlanner(goal)
                a=adaptive.choose(s,initial,5,Counter(),mode='adaptive')
                self.assertEqual(a,0)
                self.assertEqual(adaptive.stats.proven_symmetry_decisions,1)
                self.assertEqual(adaptive.stats.nodes_expanded,0)

    def test_transposition_memo_preserves_actions_and_reduces_work(self):
        goal=3
        prior=FiniteBelief()
        policy=ExactPlanner(goal,expansion_budget=1000)
        s=0
        a,v=policy.exact_action(s,prior.ids,6)
        first=policy.stats.model_transition_checks
        b,w=policy.exact_action(s,prior.ids,6)
        self.assertEqual(a,b);self.assertEqual(v,w)
        # Root action bin checks remain, but cached future subtrees are reused.
        self.assertLess(policy.stats.model_transition_checks-first,first)
        self.assertGreater(policy.stats.cache_hits,0)

    def test_direct_goal_precedes_expensive_search(self):
        belief=FiniteBelief()
        # Find a class of observations that certifies a direct goal action.
        for m in range(MODEL_COUNT):
            trial=FiniteBelief();s=0;nextstate=true_transition(m,0,s)
            if nextstate==s:continue
            trial.observe(s,0,nextstate)
            if trial.certified(s,0)==nextstate:
                ctrl=ExactPlanner(nextstate)
                chosen=ctrl.choose(s,trial,6,mode='adaptive')
                self.assertEqual(chosen,0)
                self.assertEqual(ctrl.stats.proven_direct_goal_decisions,1)
                break
        else:self.fail('catalogue missing direct deterministic certifying case')

    def test_budget_fallback_and_exact_abstention(self):
        b=FiniteBelief()
        exact=ExactPlanner(3,expansion_budget=1)
        self.assertIsNone(exact.choose(0,b,6,mode='exact'))
        self.assertEqual(exact.stats.budget_exceeded,1)
        adap=ExactPlanner(3,expansion_budget=1)
        # Root symmetric, so optimization avoids budget use.
        self.assertEqual(adap.choose(0,b,6,mode='adaptive'),0)
        b.observe(0,0,true_transition(10,0,0))
        result=adap.choose(0,b,5,mode='adaptive')
        self.assertIn(result,(0,1))
        self.assertGreaterEqual(adap.stats.budget_exceeded,1)

    def test_external_scope_fail_closed(self):
        b=FiniteBelief();allow=lambda s:s in (0,1)
        ctrl=ExactPlanner(1,allowed=allow)
        decision=ctrl.choose(0,b,5,mode='adaptive')
        if decision is not None:
            self.assertTrue(all(allow(t) for t in partition(b.ids,0,decision)))
        # No permitted goal; refuse rather than self-authorize.
        ctrl2=ExactPlanner(3,allowed=lambda s:s!=3)
        self.assertIsNone(ctrl2.choose(0,b,4,mode='adaptive'))
        self.assertEqual(ctrl2.stats.last_decision,'scope_refusal')

    def test_out_of_family_effect_rejected_transactionally(self):
        b=FiniteBelief();old=b.ids
        with self.assertRaises(ModelViolation):b.observe(0,0,3) # changes both bits
        self.assertEqual(b.ids,old)
        self.assertEqual(b.observations,[])

    def test_no_reset_paired_trials_and_soundness(self):
        for seed in range(15000,15018):
            trials=[run_case(seed,p,horizon=5,expansion_budget=600) for p in ('adaptive','exact','adaptive_low','myopic','simple_goal','legacy_goal','random')]
            self.assertEqual(len({(x['initial'],x['goal'],x['teacher_id_evaluator_only']) for x in trials}),1)
            for case in trials:
                self.assertEqual(case['final']==case['goal'],case['success'])
                self.assertLessEqual(case['steps'],5)
                self.assertTrue(all(case['trace'][j]['after']==case['trace'][j+1]['before'] for j in range(len(case['trace'])-1)))
                self.assertEqual(case['trace'][0]['before'],case['initial']) if case['trace'] else None
                self.assertTrue(all(true_transition(case['teacher_id_evaluator_only'],a,s)==t for s,a,t in case['certified_transitions']))

if __name__=='__main__':unittest.main()
