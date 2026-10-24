"""Unbiased finite-prior goal study with no resets inside an episode.

World model, start and goal sampled BEFORE policy runs, independently. Goals
are NOT preselected as teacher-reachable. All policies share identical prior,
actual observations and budgets. Reference model ID is never passed to policy.
"""
from __future__ import annotations
from collections import Counter
from random import Random
from time import perf_counter
from .finite_bayes import (STATES,MODEL_COUNT,ACTIONS,FiniteBelief,ExactPlanner,
                          true_transition, ModelViolation)
from bgr60.generalist import GeneralLearner,StateSchema
from bgr86.controller import allowed_outcomes,certified_routes,GoalValueExplorer

POLICIES=('adaptive','exact','adaptive_low','myopic','simple_goal','legacy_goal','random')


def scenario(seed:int,cohort:str="uniform"):
    rng=Random(seed*4093+11031)
    model_id=rng.randrange(MODEL_COUNT)
    initial=rng.randrange(4)
    options=[i for i in range(4) if i!=initial]
    if cohort=='uniform':goal=rng.choice(options)
    elif cohort=='distant':goal=3-initial  # flip both observable bits
    else:raise ValueError('unregistered cohort')
    return model_id,initial,goal


def simple_goal(learner,state,goal,visits):
    """Faithful v0.86 posthoc strong simple-goal control on two bits."""
    s=STATES[state];g=STATES[goal]
    routes=certified_routes(learner,s)
    if g in routes and routes[g]:return routes[g][0]
    choices=[]
    for target,route in routes.items():
        for a in range(len(learner.actions)):
            outcomes=allowed_outcomes(learner,target,a)
            if outcomes is None or len(outcomes)==1:continue
            chance=sum(o==g for o in outcomes)/len(outcomes)
            closeness=sum(1/(1+sum(x!=y for x,y in zip(o,g))) for o in outcomes)/len(outcomes)
            score=5*chance+closeness-.15*len(route)-.08*visits[(STATES.index(target),a)]
            choices.append((score,-len(route),-a,route,a))
    if choices:
        *_,route,a=max(choices)
        return route[0] if route else a
    return min(range(len(learner.actions)),key=lambda a:(visits[(s,a)],a))


def run_case(seed:int,policy:str,horizon:int=6,expansion_budget:int=800,cohort:str="uniform"):
    if policy not in POLICIES:raise ValueError('policy')
    if horizon<1:raise ValueError('horizon')
    hidden_model,state,goal=scenario(seed,cohort)
    initial=state
    belief=FiniteBelief()
    trusted=GeneralLearner(StateSchema(('x','y'),((0,1),(0,1))),ACTIONS)
    planner=ExactPlanner(goal,expansion_budget=60 if policy=='adaptive_low' else expansion_budget)
    legacy=GoalValueExplorer(STATES[goal]) if policy=='legacy_goal' else None
    visited=Counter();trace=[]
    rng=Random(seed*98711+11)
    t0=perf_counter()
    for step in range(horizon):
        if state==goal:break
        if policy in ('adaptive','exact','adaptive_low','myopic'):
            action=planner.choose(state,belief,horizon-step,visited,mode='adaptive' if policy=='adaptive_low' else policy)
        elif policy=='simple_goal':action=simple_goal(trusted,state,goal,visited)
        elif policy=='legacy_goal':
            tuple_visits=Counter({(STATES[s],a):v for (s,a),v in visited.items()})
            action=legacy.choose(trusted,STATES[state],tuple_visits,step)
        else:action=rng.randrange(len(ACTIONS))
        if action is None:break
        after=true_transition(hidden_model,action,state) # evaluator only
        prior=len(belief.ids)
        belief.observe(state,action,after)
        trusted.observe(action,STATES[state],STATES[after])
        assert hidden_model in belief.ids
        visited[(state,action)]+=1
        trace.append({'before':state,'action':action,'after':after,
                      'survivors_before':prior,'survivors_after':len(belief.ids),
                      'controller_decision':planner.stats.last_decision if policy in ('adaptive','exact','adaptive_low','myopic') else policy})
        state=after
    certs=[]
    for s in range(4):
        for a in range(2):
            prediction=belief.certified(s,a)
            if prediction is not None:
                assert prediction==true_transition(hidden_model,a,s)
                certs.append((s,a,prediction))
    return {'seed':seed,'cohort':cohort,'policy':policy,'initial':initial,'goal':goal,
            # hidden teacher identifier intentionally withheld from policy;
            # reported only for independent evaluator audit.
            'teacher_id_evaluator_only':hidden_model,
            'horizon':horizon,'steps':len(trace),'success':state==goal,
            'final':state,'trace':trace,'surviving_models':len(belief.ids),
            'certified_transitions':certs,'certified_count':len(certs),
            'compute':vars(planner.stats),'legacy_compute':legacy.stats.data() if legacy is not None else None,'elapsed_seconds_informational':perf_counter()-t0}


def summarize(cases):
    by={}
    for p in POLICIES:
        subset=[x for x in cases if x['policy']==p]
        times=[x['steps'] if x['success'] else x['horizon']+1 for x in subset]
        by[p]={'episodes':len(subset),'success':sum(x['success'] for x in subset),
               'success_within_3':sum(x['success'] and x['steps']<=3 for x in subset),
               'total_actions':sum(x['steps'] for x in subset),
               'sum_penalized_actions':sum(times),
               'certified_predictions':sum(x['certified_count'] for x in subset),
               'model_transition_checks':sum(x['compute']['model_transition_checks'] for x in subset),
               'nodes_expanded':sum(x['compute']['nodes_expanded'] for x in subset),
               'budget_fallback_calls':sum(x['compute']['budget_exceeded'] for x in subset),
               'elapsed_seconds_informational':round(sum(x['elapsed_seconds_informational'] for x in subset),5)}
    return by
