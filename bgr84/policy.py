"""Bounded belief-branch exploration for a shared finite causal learner.

No reference-model access or oracle resets. Future branches update candidate
operator rules using imaginary observations. The Gini-style outcome weights are
heuristic, not calibrated probabilities. Safety rules must be separately
provided by an authority; a learner cannot authorize unsafe actions.
"""
from __future__ import annotations
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from math import log2
from typing import Callable
from bgr60.generalist import GeneralLearner, Hypothesis

State = tuple[int, ...]


def outcome_weights(learner: GeneralLearner, action: int, state: State, bank=None):
    """Predictive mixture over syntactic candidates, uniform missing table entries.

    Unknown table entries are not treated as known predictions. All outcome
    alternatives remain possible even when their heuristic weight is low.
    """
    learner.schema.validate(state)
    bank = learner.banks[action] if bank is None else bank
    weights=defaultdict(float)
    if not bank: return {}
    for h in bank:
        candidates=h.predict_values(state,learner.schema)
        for value in candidates:
            new=list(state); new[h.target]=value
            weights[tuple(new)] += 1.0/(len(bank)*len(candidates))
    return dict(weights)


def posterior_bank(learner:GeneralLearner, action:int, before:State, after:State, bank=None):
    """Conditional posterior for ONE hypothetical action outcome, no mutation."""
    bank = learner.banks[action] if bank is None else bank
    survivors=[]
    for h in bank:
        if any(before[j]!=after[j] for j in range(len(before)) if j!=h.target):continue
        key=h.key(before)
        if key in h.table and h.table[key]!=after[h.target]:continue
        h2=Hypothesis(h.target,h.parents,dict(h.table))
        h2.table[key]=after[h.target]
        survivors.append(h2)
    return survivors


def entropy(weights):
    return -sum(p*log2(p) for p in weights.values() if p>0)


def safe_outcomes(outcomes, allow_state:Callable[[State],bool]|None):
    return allow_state is None or all(allow_state(s) for s in outcomes)


def forward_certified_routes(learner:GeneralLearner,start:State,maximum=24,allow_state=None):
    """Only certified edges can be used as routes to a frontier."""
    routes={start:()};q=deque([start])
    while q and len(routes)<maximum:
        s=q.popleft()
        for a in range(len(learner.actions)):
            nxt=learner.certified(a,s)
            if nxt is None or not safe_outcomes((nxt,),allow_state) or nxt in routes:continue
            routes[nxt]=routes[s]+(a,)
            q.append(nxt)
    return routes


@dataclass
class PolicyDiagnostics:
    modeled_outcomes:int=0
    hypothetical_posterior_filters:int=0
    frontier_vertices:int=0
    truncated_branches:int=0
    fallback_decisions:int=0
    unsafe_refusals:int=0


class BeliefExplorer:
    """Score reachable epistemic experiments including conditional future observations.

    There is no privileged reset, future target truth, or teacher state lookup.
    Candidates are routed via certified transitions, plus direct uncertified
    actions with budgeted hypothetical outcome branches. Each branch updates
    the relevant operator's posterior before evaluating its next experiment.

    `allowed_state` is an external sandbox safety policy, never inferred or
    updated by the learner. If an action has ANY disallowed possible outcome,
    it cannot be selected. All alternatives remain in the belief model.
    """
    def __init__(self,horizon=2,frontier_limit=24,branch_budget=10,
                 novelty_weight=0.07,travel_penalty=0.05,
                 allowed_state=None):
        if horizon!=2:raise ValueError('only two-stage lookahead audited')
        self.horizon=horizon;self.frontier_limit=frontier_limit
        self.branch_budget=branch_budget
        self.novelty_weight=novelty_weight
        self.travel_penalty=travel_penalty
        self.allowed_state=allowed_state
        self.stats=PolicyDiagnostics()

    def choose(self, learner:GeneralLearner, state:State,counts:Counter,
               step:int, return_diagnostics=False):
        n=len(learner.actions)
        routes=forward_certified_routes(learner,state,self.frontier_limit,self.allowed_state)
        self.stats.frontier_vertices+=len(routes)
        best=None
        for s,route in routes.items():
            for a in range(n):
                w=outcome_weights(learner,a,s)
                self.stats.modeled_outcomes+=len(w)
                if not w:continue
                if not safe_outcomes(w,self.allowed_state):
                    self.stats.unsafe_refusals+=1
                    continue
                # Unknown outcomes have explicit branches. No certification
                # from posterior weights; confidence is not authority.
                ig=entropy(w)
                immediate=ig + self.novelty_weight/(1+counts[(s,a)])
                if len(w)>self.branch_budget:
                    self.stats.truncated_branches+=1
                    # Missing branches cause abstention from deep scoring,
                    # not a fabricated expected utility.
                    next_value=0.0
                else:
                    next_value=0.0
                    for after,prob in w.items():
                        posterior=posterior_bank(learner,a,s,after)
                        self.stats.hypothetical_posterior_filters+=1
                        if not posterior:raise AssertionError('impossible forecast branch')
                        future=0.0
                        for b in range(n):
                            nxt=outcome_weights(learner,b,after,posterior if b==a else None)
                            self.stats.modeled_outcomes+=len(nxt)
                            if not safe_outcomes(nxt,self.allowed_state):continue
                            future=max(future,entropy(nxt)+self.novelty_weight/(1+counts[(after,b)]))
                        next_value+=prob*future
                score=immediate+0.6*next_value-self.travel_penalty*len(route)
                # Penalize repeatedly testing precisely the same input.
                score-=0.10*counts[(s,a)]
                candidate=(score,-len(route),-counts[(s,a)],-a,s,route,a)
                if best is None or candidate>best:best=candidate
        if best is not None:
            route=best[-2]
            result=route[0] if route else best[-1]
            # Route actions have been certified but still separately checked
            # against the external safety scope.
            if self.allowed_state is not None:
                options=learner.possible_outcomes(result,state)
                if not safe_outcomes(options,self.allowed_state):raise AssertionError('unsafe route')
            return (result,best[0]) if return_diagnostics else result
        self.stats.fallback_decisions+=1
        safe=[a for a in range(n) if safe_outcomes(learner.possible_outcomes(a,state),self.allowed_state)]
        if not safe:return (None,None) if return_diagnostics else None
        choice=min(safe,key=lambda a:(counts[(state,a)],a))
        return (choice,0.0) if return_diagnostics else choice
