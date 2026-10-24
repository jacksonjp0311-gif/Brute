"""Reference-only reachable-state identifiability bound, not learner input."""
from collections import deque
from random import Random
from bgr60.worlds import factory
from bgr60.generalist import GeneralLearner

def analyze(seed,family):
    w=factory(seed,family);schema,actions=w.public();rng=Random(seed*931+73)
    initial=tuple(rng.choice(d) for d in schema.domains)
    q=deque([initial]);visited={initial}
    while q:
        s=q.popleft()
        for a in range(len(actions)):
            nxt=w.transition(a,s)
            if nxt not in visited:visited.add(nxt);q.append(nxt)
    # Stronger-than-agent counterfactual: oracle supplies every transition from
    # every state reachable from the fixed start. Still may not identify rules.
    learner=GeneralLearner(schema,actions)
    for s in sorted(visited):
        for a in range(len(actions)):learner.observe(a,s,w.transition(a,s))
    return {'seed':seed,'family':family,'reachable_states':len(visited),
            'total_states':len(schema.all_states()),'reachable_oracle_identified':learner.identified(),
            'remaining':list(learner.remaining())}
