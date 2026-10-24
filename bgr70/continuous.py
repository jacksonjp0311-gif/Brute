"""No-reset, one-state-at-a-time learning harness. Teacher is evaluator-only.

This does not supply privileged counterfactual states. It does supply a typed
state interface, fully observed current state, and known legal actions.
"""
from __future__ import annotations
from collections import Counter
from random import Random
from bgr60.generalist import GeneralLearner
from bgr60.worlds import factory


def choose_online(learner, state, policy, rng, counts):
    if policy=='random':return rng.randrange(len(learner.actions))
    if policy=='cyclic':return sum(counts.values())%len(learner.actions)
    if policy not in ('active','transfer'):raise ValueError('unknown policy')
    scored=[]
    for a,bank in enumerate(learner.banks):
        options=learner.possible_outcomes(a,state)
        uncertainty=len(options)-1
        novelty=1/(1+counts[a])
        hint=0
        if policy=='transfer' and learner.templates:
            hint=sum(learner._template_match(h) for h in bank)/max(1,len(bank))*.05
        scored.append((uncertainty+novelty*.1+hint,-counts[a],-a,a))
    return max(scored)[-1]


def run(seed,family,policy,steps=100,templates=()):
    w=factory(seed,family);schema,actions=w.public()
    learner=GeneralLearner(schema,actions,templates=templates)
    rng=Random(seed*931+73);state=tuple(rng.choice(d) for d in schema.domains)
    counts=Counter();trace=[];first=None
    for t in range(steps):
        a=choose_online(learner,state,policy,rng,counts)
        next_state=w.transition(a,state)
        learner.observe(a,state,next_state)
        trace.append({'t':t,'action':a,'before':list(state),'after':list(next_state),
                      'remaining':list(learner.remaining())})
        state=next_state;counts[a]+=1
        if first is None and learner.identified():first=t+1
    certified=wrong=0
    for a in range(len(actions)):
        for s in schema.all_states():
            pred=learner.certified(a,s)
            if pred is not None:
                certified+=1;wrong+=pred!=w.transition(a,s)
    return {'seed':seed,'family':family,'policy':policy,'steps':steps,
            'identified':learner.identified(),'first_identified':first,
            'certified':certified,'incorrect':wrong,'trace':trace,
            'candidate_checks':learner.candidate_checks,
            'templates_exported':[t.data() for t in learner.extracted_templates()] if learner.identified() else []}
