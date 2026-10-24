"""Certified-route frontier explorer; no oracle, reset, or privileged transitions.

The route to a frontier is formed only from unanimously certified edges.
At a frontier, perform an uncertain action. Never assume uncertified paths.
"""
from collections import deque,Counter
from random import Random
from bgr60.generalist import GeneralLearner
from bgr60.worlds import factory
from bgr70.continuous import choose_online

def choose_frontier(learner,state,counts):
    paths={state:()};q=deque([state]);best=None
    while q:
        s=q.popleft();route=paths[s]
        for a in range(len(learner.actions)):
            outcomes=learner.possible_outcomes(a,s)
            if len(outcomes)>1:
                # Prefer short safe routes and experiments not yet attempted.
                candidate=(len(route),counts[(s,a)],-len(outcomes),a,s,route)
                if best is None or candidate<best:best=candidate
            elif len(outcomes)==1:
                t=next(iter(outcomes))
                if t not in paths:
                    paths[t]=route+(a,);q.append(t)
    if best is not None:
        return best[5][0] if best[5] else best[3]
    return min(range(len(learner.actions)),key=lambda a:(counts[(state,a)],a))

def run(seed,family,policy,steps=120):
    world=factory(seed,family);schema,actions=world.public();learner=GeneralLearner(schema,actions)
    rng=Random(seed*931+73);state=tuple(rng.choice(d) for d in schema.domains)
    counts=Counter();trace=[];first=None
    for t in range(steps):
        if policy=='frontier':a=choose_frontier(learner,state,counts)
        else:a=choose_online(learner,state,policy,rng,Counter({k[1]:v for k,v in counts.items() if k[0]==state}))
        nxt=world.transition(a,state);learner.observe(a,state,nxt)
        trace.append({'before':list(state),'action':a,'after':list(nxt)})
        counts[(state,a)]+=1;state=nxt
        if first is None and learner.identified():first=t+1
    # Evaluation-only oracle reachability, not exposed to the learner.
    seen={tuple(trace[0]['before'])};q=deque(seen)
    while q:
        s=q.popleft()
        for a in range(len(actions)):
            nxt=world.transition(a,s)
            if nxt not in seen:seen.add(nxt);q.append(nxt)
    correct=wrong=0
    for s in seen:
        for a in range(len(actions)):
            pred=learner.certified(a,s)
            if pred is not None:
                correct+=1;wrong+=int(pred!=world.transition(a,s))
    return {'seed':seed,'family':family,'policy':policy,'steps':steps,'reachable_total':len(seen)*len(actions),'certified':correct,'incorrect':wrong,'reachable_complete':correct==len(seen)*len(actions),'global_identified':learner.identified(),'first_identified':first,'trace':trace,'candidate_checks':learner.candidate_checks}
