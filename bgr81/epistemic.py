"""Outcome-conditioned belief-space lookahead for no-reset finite learners.

Each hypothetical observation updates a copy of the version space. The score
is expected reduction in surviving structural candidates, NOT proven optimal
Bayesian information gain: unknown table values have an explicit uniform
predictive prior, and independent action banks are an approximation.
"""
from collections import Counter, defaultdict
from random import Random
from bgr60.generalist import GeneralLearner
from bgr60.worlds import factory
from bgr80.explore import choose as old_choose

def clone(learner):
    other=GeneralLearner(learner.schema,learner.actions,max_parents=learner.max_parents)
    other.banks=[[type(h)(h.target,h.parents,dict(h.table)) for h in bank] for bank in learner.banks]
    return other

def outcome_distribution(learner,action,state):
    weight=defaultdict(float)
    bank=learner.banks[action]
    for h in bank:
        opts=h.predict_values(state,learner.schema)
        for y in opts:
            after=list(state);after[h.target]=y
            weight[tuple(after)]+=1/(len(bank)*len(opts))
    return dict(weight)

def branch(learner,action,state):
    for outcome,weight in outcome_distribution(learner,action,state).items():
        future=clone(learner)
        future.observe(action,state,outcome)
        yield outcome,weight,future

def choose(learner,state,counts,depth=2,discount=.7):
    def value(model,s,horizon):
        if horizon==0:return 0.
        return max((action_value(model,s,a,horizon) for a in range(len(model.actions))),default=0.)
    def action_value(model,s,a,horizon):
        original=len(model.banks[a]);value=0.
        for outcome,p,updated in branch(model,a,s):
            shrink=(original-len(updated.banks[a]))/max(1,original)
            value+=p*(shrink+(discount*value_fn(updated,outcome,horizon-1) if horizon>1 else 0.))
        return value
    # Separate function avoids accidental name shadowing in recursion.
    def value_fn(model,s,horizon):return value(model,s,horizon)
    return max(range(len(learner.actions)),key=lambda a:(action_value(learner,state,a,depth)+.03/(1+counts[a]),-a))

def run(seed,family,policy,steps=120):
    world=factory(seed,family);schema,actions=world.public();learner=GeneralLearner(schema,actions)
    rng=Random(seed*931+73);state=tuple(rng.choice(d) for d in schema.domains)
    counts=Counter();trace=[];first=None
    for t in range(steps):
        if policy=='epistemic':a=choose(learner,state,counts)
        else:a=old_choose(learner,state,policy,rng,counts)
        nxt=world.transition(a,state);learner.observe(a,state,nxt)
        trace.append({'t':t,'action':a,'before':list(state),'after':list(nxt),'remaining':list(learner.remaining())})
        state=nxt;counts[a]+=1
        if first is None and learner.identified():first=t+1
    correct=wrong=0
    for a in range(len(actions)):
        for s in schema.all_states():
            pred=learner.certified(a,s)
            if pred is not None:correct+=1;wrong+=pred!=world.transition(a,s)
    return {'seed':seed,'family':family,'policy':policy,'steps':steps,'identified':learner.identified(),
            'first_identified':first,'certified':correct,'incorrect':wrong,'candidate_checks':learner.candidate_checks,'trace':trace}
