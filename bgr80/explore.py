"""No-reset, bounded-depth epistemic exploration over certified possible outcomes.

Planning is explicitly approximate: predicted state branching is generated from
surviving hypotheses, and does not model belief updates across future steps.
No teacher model is consulted by this selector.
"""
from collections import Counter
from random import Random
from bgr60.generalist import GeneralLearner
from bgr60.worlds import factory

def score_action(learner,state,a):
    options=learner.possible_outcomes(a,state)
    return (len(options)-1) / max(1,len(options))

def choose(learner,state,policy,rng,counts,depth=2,discount=.75):
    if policy=='random':return rng.randrange(len(learner.actions))
    if policy=='cyclic':return sum(counts.values())%len(learner.actions)
    if policy=='active':
        return max(range(len(learner.actions)),key=lambda a:(score_action(learner,state,a)+.06/(1+counts[a]),-a))
    if policy!='lookahead':raise ValueError('unsupported exploration policy')
    def future(s,remaining):
        if remaining==0:return 0.
        return max(score_action(learner,s,a)+discount*sum(future(t,remaining-1) for t in learner.possible_outcomes(a,s))/len(learner.possible_outcomes(a,s)) for a in range(len(learner.actions)))
    return max(range(len(learner.actions)),key=lambda a:(score_action(learner,state,a)+discount*sum(future(t,depth-1) for t in learner.possible_outcomes(a,state))/len(learner.possible_outcomes(a,state))+.06/(1+counts[a]),-a))

def run(seed,family,policy,steps=120,depth=2):
    world=factory(seed,family);schema,actions=world.public();learner=GeneralLearner(schema,actions)
    rng=Random(seed*931+73);state=tuple(rng.choice(d) for d in schema.domains)
    counts=Counter();trace=[];first=None
    for t in range(steps):
        a=choose(learner,state,policy,rng,counts,depth)
        nxt=world.transition(a,state);learner.observe(a,state,nxt)
        trace.append({'t':t,'action':a,'before':list(state),'after':list(nxt),'remaining':list(learner.remaining())})
        state=nxt;counts[a]+=1
        if first is None and learner.identified():first=t+1
    correct=incorrect=0
    for a in range(len(actions)):
        for s in schema.all_states():
            pred=learner.certified(a,s)
            if pred is not None:
                correct+=1;incorrect+=pred!=world.transition(a,s)
    return {'seed':seed,'family':family,'policy':policy,'steps':steps,'identified':learner.identified(),
            'first_identified':first,'certified':correct,'incorrect':incorrect,'candidate_checks':learner.candidate_checks,'trace':trace}
