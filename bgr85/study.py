"""Registered no-reset benchmark, matched source worlds across policies.

The learner/policy receives no oracle full-model, hidden transition table, or
counterfactual state resets. Oracle reachable states and shortest goals are
only consulted by the separate evaluator after learning.
"""
from __future__ import annotations
from collections import Counter,deque
from random import Random
from time import perf_counter
from bgr60.generalist import GeneralLearner
from bgr60.worlds import factory
from bgr70.continuous import choose_online
from bgr83.frontier import choose_frontier
from bgr84.policy import BeliefExplorer
from .topology import TopologyExplorer
from .certification import certify_reachable

FAMILIES=('logic','switching','navigation','mixed','incompatible')
POLICIES=('topology','frontier','active','random','epistemic')


def reachable(world,start):
    seen={start};q=deque([start]);actions=len(world.actions)
    while q:
        s=q.popleft()
        for a in range(actions):
            t=world.transition(a,s)
            if t not in seen:seen.add(t);q.append(t)
    return frozenset(seen)


def oracle_shortest(world,start,goal):
    if start==goal:return 0
    q=deque([(start,0)]);seen={start}
    while q:
        s,d=q.popleft()
        for a in range(len(world.actions)):
            t=world.transition(a,s)
            if t==goal:return d+1
            if t not in seen:seen.add(t);q.append((t,d+1))
    return None


def run_case(seed:int,family:str,policy:str,steps:int=120,checkpoints=(20,60,120)):
    world=factory(seed,family);schema,actions=world.public()
    learner=GeneralLearner(schema,actions)
    rng=Random(seed*931+73)
    initial=tuple(rng.choice(dom) for dom in schema.domains)
    state=initial;counts=Counter();history=[];curve=[]
    start=perf_counter()
    first_proof=None;proof_trace=[]
    explorer=TopologyExplorer() if policy=='topology' else BeliefExplorer() if policy=='epistemic' else None
    for t in range(steps):
        if policy=='topology':a=explorer.choose(learner,state,counts,t)
        elif policy=='epistemic':a=explorer.choose(learner,state,counts,t)
        elif policy=='frontier':a=choose_frontier(learner,state,counts)
        else:
            action_counts=Counter({k[1]:v for k,v in counts.items() if k[0]==state})
            a=choose_online(learner,state,policy,rng,action_counts)
        if a is None:break
        before=state;after=world.transition(a,state)
        learner.observe(a,before,after)
        counts[(before,a)]+=1;state=after
        history.append({'before':list(before),'action':a,'after':list(after),'candidates_after':len(learner.banks[a])})
        if first_proof is None:
            current_proof=certify_reachable(learner,initial)
            if current_proof.complete:first_proof=t+1
        if t+1 in checkpoints:
            proof=certify_reachable(learner,initial)
            proof_trace.append({'step':t+1,'complete':proof.complete,'closed_states':len(proof.states),
                                'unknown_boundary':len(proof.open_frontier),'sha256':proof.sha256})

            curve.append({'step':t+1,'candidate_checks':learner.candidate_checks,'visited':len({k[0] for k in counts})})
    elapsed=perf_counter()-start
    final_proof=certify_reachable(learner,initial)
    # Oracle reachable graph is evaluation-only, not exposed to policy.
    reach=reachable(world,initial)
    true_total=len(reach)*len(actions)
    cert=wrong=0
    for s in reach:
        for a in range(len(actions)):
            pred=learner.certified(a,s)
            truth=world.transition(a,s)
            if pred is not None:cert+=1;wrong+=pred!=truth
    if wrong:raise AssertionError('unsafe false certification')
    options=[s for s in sorted(reach) if s!=initial]
    goals=Random(seed*9901+77).sample(options,k=min(4,len(options)))
    plans=[]
    for goal in goals:
        prediction=learner.plan(state,goal)
        terminal=state
        if prediction['actions'] is not None:
            for a in prediction['actions']:terminal=world.transition(a,terminal)
        shortest=oracle_shortest(world,state,goal)
        plans.append({'goal':list(goal),'actions':prediction['actions'],'status':prediction['status'],
          'valid':terminal==goal if prediction['actions'] is not None else False,
          'oracle_shortest':shortest,'shortest_claim':prediction['shortest_claim'],
          'optimal':prediction['actions'] is not None and shortest==len(prediction['actions'])})
    return {'seed':seed,'family':family,'policy':policy,'initial':list(initial),'final':list(state),
      'trace':history,'steps':len(history),'reachable_states':len(reach),
      'reachable_total':true_total,'certified':cert,'incorrect':wrong,
      'reachable_complete':cert==true_total,'global_identified':learner.identified(),
      'proof_reachable_complete':final_proof.complete,'proof_first_complete':first_proof,
      'proof_states':len(final_proof.states),'proof_frontier':len(final_proof.open_frontier),
      'proof_sha256':final_proof.sha256,'proof_checkpoints':proof_trace,
      'candidate_checks':learner.candidate_checks,'model_bank_counts':list(learner.remaining()),
      'goals':plans,'curve':curve,'policy_diagnostics':vars(explorer.stats) if explorer else None,
      'elapsed_informational':elapsed}


def aggregate(cases):
    out={}
    for policy in POLICIES:
        items=[x for x in cases if x['policy']==policy]
        out[policy]={'worlds':len(items),'reachable_complete':sum(x['reachable_complete'] for x in items),
          'certified':sum(x['certified'] for x in items),'possible_reachable':sum(x['reachable_total'] for x in items),
          'incorrect':sum(x['incorrect'] for x in items),
          'proven_complete':sum(x['proof_reachable_complete'] for x in items),
          'steps_savable':sum(max(0,x['steps']-x['proof_first_complete']) for x in items if x['proof_first_complete'] is not None),
          'plans':sum(len(x['goals']) for x in items),
          'plans_valid':sum(p['valid'] for x in items for p in x['goals']),
          'plans_optimal':sum(p['optimal'] for x in items for p in x['goals']),
          'candidate_checks':sum(x['candidate_checks'] for x in items),
          'elapsed_informational':round(sum(x['elapsed_informational'] for x in items),4)}
    return out
