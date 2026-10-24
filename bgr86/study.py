"""Goal-conditioned no-reset research benchmark.

The hidden teacher appears exclusively in the evaluator. Policies see only the
public schema/actions, their actual observed state, a declared goal, and their
own learned hypotheses. Goal selection via reference BFS is evaluator-only and
identical for every policy of one world. No simulator reset occurs inside a run.
"""
from __future__ import annotations
from collections import Counter,deque
from random import Random
from time import perf_counter
from bgr60.generalist import GeneralLearner
from bgr60.worlds import factory
from bgr70.continuous import choose_online
from bgr83.frontier import choose_frontier
from bgr85.certification import certify_reachable,certified_goal_plan
from .controller import GoalValueExplorer,certified_routes

FAMILIES=('logic','switching','navigation','mixed','incompatible')
POLICIES=('goal_value','certified_goal','frontier','active','random')


def oracle_distances(world,initial):
    """Evaluator-only graph search; never passed to a policy."""
    distance={initial:0};q=deque([initial])
    while q:
        s=q.popleft()
        for a in range(len(world.actions)):
            t=world.transition(a,s)
            if t not in distance:distance[t]=distance[s]+1;q.append(t)
    return distance


def oracle_goal(seed,world,initial,min_distance=2):
    distances=oracle_distances(world,initial)
    eligible=[s for s,d in distances.items() if d>=min_distance]
    if not eligible:eligible=[s for s,d in distances.items() if d>=1]
    if not eligible:return None,None
    # Select from farthest states rather than biased fixed vertex labels.
    cutoff=max(distances[s] for s in eligible)
    hardest=[s for s in eligible if distances[s]==cutoff]
    goal=Random(seed*1009+711).choice(sorted(hardest))
    return goal,distances[goal]


def run_case(seed:int,family:str,policy:str,budget:int=45,checkpoints=(10,25,45),
             goal_min_distance=2):
    if policy not in POLICIES:raise ValueError('policy')
    world=factory(seed,family);schema,actions=world.public()
    rng=Random(seed*931+73)
    initial=tuple(rng.choice(dom) for dom in schema.domains)
    goal,oracle_cost=oracle_goal(seed,world,initial,goal_min_distance)
    if goal is None:
        return {'seed':seed,'family':family,'policy':policy,'eligible':False,'initial':list(initial),
                'goal':None,'oracle_initial_shortest':None,'steps':0,'reached':False,
                'trace':[],'reason':'no distinct reachable goal','registered_budget':budget,'elapsed_informational':0}
    learner=GeneralLearner(schema,actions)
    selector=GoalValueExplorer(goal) if policy=='goal_value' else None
    visits=Counter();trace=[];current=initial;first_reachable_proof=None
    start=perf_counter();first_success=None;curve=[]
    for t in range(budget):
        if current==goal:
            first_success=t;break
        if policy=='goal_value':a=selector.choose(learner,current,visits,t)
        elif policy=='certified_goal':
            routes=certified_routes(learner,current)
            a=routes[goal][0] if goal in routes and routes[goal] else choose_frontier(learner,current,visits)
        elif policy=='frontier':a=choose_frontier(learner,current,visits)
        else:
            action_visits=Counter({aa:visits[(current,aa)] for aa in range(len(actions))})
            a=choose_online(learner,current,policy,rng,action_visits)
        if a is None:break
        next_state=world.transition(a,current)
        learner.observe(a,current,next_state)
        visits[(current,a)]+=1
        trace.append({'before':list(current),'action':a,'after':list(next_state),
                      'candidates_after':len(learner.banks[a]),
                      'decision':selector.stats.last_decision if selector else policy})
        current=next_state
        if first_reachable_proof is None:
            proof=certify_reachable(learner,initial)
            if proof.complete:first_reachable_proof=t+1
        if t+1 in checkpoints:
            # Does not influence action selection, only checkpoint reporting.
            curve.append({'step':t+1,'candidate_checks':learner.candidate_checks,
                          'visited_states':len({s for (s,a) in visits}),
                          'initial_closed':certify_reachable(learner,initial).complete})
    if current==goal and first_success is None:first_success=len(trace)
    oracle_reach=oracle_distances(world,initial)
    reach_total=len(oracle_reach)*len(actions)
    certified=incorrect=0
    for s in oracle_reach:
        for a in range(len(actions)):
            pred=learner.certified(a,s)
            if pred is not None:
                certified+=1;incorrect+=int(pred!=world.transition(a,s))
    assert incorrect==0
    last_plan=certified_goal_plan(learner,current,goal)
    if last_plan['plan'] is not None:
        pos=current
        for a in last_plan['plan']:pos=world.transition(a,pos)
        assert pos==goal
        if last_plan.get('shortest_claim'):
            from bgr85.study import oracle_shortest
            assert len(last_plan['plan'])==oracle_shortest(world,current,goal)
    return {'seed':seed,'family':family,'policy':policy,'eligible':True,
            'initial':list(initial),'goal':list(goal),'oracle_initial_shortest':oracle_cost,
            'registered_budget':budget,'steps':len(trace),'reached':first_success is not None,
            'steps_to_goal':first_success,'final':list(current),
            'trace':trace,'knowledge_certified':certified,'knowledge_possible':reach_total,
            'knowledge_wrong':incorrect,'initial_proof_step':first_reachable_proof,
            'final_initial_reachable_complete':certify_reachable(learner,initial).complete,
            'final_goal_plan':last_plan,
            'candidate_checks':learner.candidate_checks,'goal_learner_diagnostics':selector.stats.data() if selector else None,
            'curve':curve,'elapsed_informational':perf_counter()-start}


def aggregate(cases):
    out={}
    for policy in POLICIES:
        cs=[c for c in cases if c['policy']==policy]
        eligible=[c for c in cs if c['eligible']]
        times=[c['steps_to_goal'] for c in eligible if c['reached']]
        penalty=[c['steps_to_goal'] if c['reached'] else c['registered_budget']+1 for c in eligible]
        out[policy]={'world_records':len(cs),'eligible_goals':len(eligible),'success':sum(c['reached'] for c in eligible),
                     'success_within_10':sum(c['reached'] and c['steps_to_goal']<=10 for c in eligible),
                     'success_within_25':sum(c['reached'] and c['steps_to_goal']<=25 for c in eligible),
                     'total_actions':sum(c['steps'] for c in eligible),
                     'mean_actions_success':round(sum(times)/len(times),3) if times else None,
                     'mean_penalized_goal_actions':round(sum(penalty)/len(penalty),3) if penalty else None,
                     'sum_penalized_goal_actions':sum(penalty),
                     'correct_certified':sum(c['knowledge_certified'] for c in eligible),
                     'wrong_certified':sum(c['knowledge_wrong'] for c in eligible),
                     'reachable_complete_at_stop':sum(c['final_initial_reachable_complete'] for c in eligible),
                     'candidate_checks':sum(c['candidate_checks'] for c in eligible),
                     'elapsed_informational':round(sum(c['elapsed_informational'] for c in eligible),4)}
    return out
