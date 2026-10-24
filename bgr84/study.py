"""Deterministic no-reset benchmark. The teacher is evaluator-only.

Source worlds and goal sets are paired across exploration policies. The learner
sees its current fully observed typed state, legal actions and its own history.
The full reachable graph and shortest-path oracle are withheld from policies.
"""
from __future__ import annotations
from collections import Counter,deque
from random import Random
from time import perf_counter
from bgr60.generalist import GeneralLearner
from bgr60.worlds import factory
from bgr70.continuous import choose_online
from bgr83.frontier import choose_frontier
from .policy import BeliefExplorer

FAMILIES=('logic','switching','navigation','mixed','incompatible')
POLICIES=('epistemic','frontier','active','random')

def reachability(world,start):
    known={start};q=deque([start]);n=len(world.actions)
    while q:
        s=q.popleft()
        for a in range(n):
            t=world.transition(a,s)
            if t not in known:known.add(t);q.append(t)
    return frozenset(known)

def oracle_distances(world,start):
    q=deque([start]);distance={start:0}
    while q:
        s=q.popleft()
        for a in range(len(world.actions)):
            t=world.transition(a,s)
            if t not in distance:distance[t]=distance[s]+1;q.append(t)
    return distance

def evaluate(seed:int,family:str,policy:str,steps:int=120,checkpoints=(20,60,120)):
    world=factory(seed,family);schema,actions=world.public()
    learner=GeneralLearner(schema,actions)
    rng=Random(seed*931+73)
    state=tuple(rng.choice(dom) for dom in schema.domains)
    initial=state
    reachable=reachability(world,state) # PRIVILEGED EVALUATOR ONLY
    counts=Counter();trace=[];curve=[];first_complete=None
    explorer=BeliefExplorer() if policy=='epistemic' else None
    start_time=perf_counter()
    for t in range(steps):
        if policy=='epistemic':a=explorer.choose(learner,state,counts,t)
        elif policy=='frontier':a=choose_frontier(learner,state,counts)
        else:a=choose_online(learner,state,policy,rng,Counter({key[1]:cnt for key,cnt in counts.items() if key[0]==state}))
        if a is None:break
        before=state;state=world.transition(a,state)
        learner.observe(a,before,state)
        counts[(before,a)]+=1
        trace.append({'before':list(before),'action':a,'after':list(state)})
        if (t+1) in checkpoints or t+1==steps:
            total=len(reachable)*len(actions)
            cert=sum(learner.certified(ai,s)==world.transition(ai,s) for s in reachable for ai in range(len(actions)))
            wrong=sum(learner.certified(ai,s) not in (None,world.transition(ai,s)) for s in reachable for ai in range(len(actions)))
            if wrong:raise AssertionError('false certification')
            curve.append({'step':t+1,'certified_reachable':cert,'reachable_total':total})
            if cert==total and first_complete is None:first_complete=t+1
    time_used=perf_counter()-start_time
    total=len(reachable)*len(actions)
    cert=sum(learner.certified(ai,s)==world.transition(ai,s) for s in reachable for ai in range(len(actions)))
    wrong=sum(learner.certified(ai,s) not in (None,world.transition(ai,s)) for s in reachable for ai in range(len(actions)))
    # Fixed target goals depend on seed/initial only, not on policy-specific path.
    goals=sorted(x for x in reachable if x!=initial)
    picked=Random(seed*9901+77).sample(goals,k=min(4,len(goals)))
    planning=[]
    for goal in picked:
        plan=learner.plan(state,goal)
        actual=state
        if plan['actions'] is not None:
            for a in plan['actions']:actual=world.transition(a,actual)
        dist=oracle_distances(world,state).get(goal)
        planning.append({'goal':list(goal),'plan':plan['actions'],
                         'status':plan['status'], 'valid':plan['actions'] is not None and actual==goal,
                         'oracle_distance':dist,'optimal':plan['actions'] is not None and dist==len(plan['actions']),
                         'shortest_claim':bool(plan['shortest_claim'])})
    return {'seed':seed,'family':family,'policy':policy,'initial':list(initial),
            'steps':len(trace),'trace':trace,'reachable_states':len(reachable),
            'reachable_transitions':total,'certified':cert,'incorrect':wrong,
            'reachable_complete':cert==total,'first_complete_checkpoint':first_complete,
            'global_identified':learner.identified(),'candidate_checks':learner.candidate_checks,
            'model_action_counts':list(learner.remaining()),'curve':curve,'goals':planning,
            'policy_diagnostics':vars(explorer.stats) if explorer else None,
            'elapsed_seconds_informational':time_used}

def aggregate(cases):
    result={}
    for p in POLICIES:
        g=[c for c in cases if c['policy']==p]
        result[p]={
            'worlds':len(g),'reachable_complete':sum(c['reachable_complete'] for c in g),
            'certified':sum(c['certified'] for c in g),
            'total_reachable':sum(c['reachable_transitions'] for c in g),
            'incorrect':sum(c['incorrect'] for c in g),
            'goals':sum(len(c['goals']) for c in g),
            'valid_goals':sum(x['valid'] for c in g for x in c['goals']),
            'shortest_goals':sum(x['optimal'] for c in g for x in c['goals']),
            'total_candidate_checks':sum(c['candidate_checks'] for c in g),
            'elapsed_seconds_informational':round(sum(c['elapsed_seconds_informational'] for c in g),4),
        }
    return result
