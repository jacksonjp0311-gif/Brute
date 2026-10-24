"""A distinct finite-model enumerator and exact Bellman reference.

This module intentionally does NOT import bgr87.finite_bayes or its
transition array, cache, posterior filters, or planner. The underlying 2-bit
logical grammar and declared 9/10 discount match the preregistered theory.
It can independently check both the agent's posterior and optimal values.
"""
from __future__ import annotations
from fractions import Fraction
from functools import lru_cache
from itertools import product

STATES=tuple(product((0,1),repeat=2))
RULES=[]
for tgt in range(2):
    for name in ('set0','set1','flip','copy','not_other','xor','and','or'):
        row=[]
        for physical in STATES:
            own=physical[tgt];other=physical[1-tgt]
            if name=='set0':value=0
            elif name=='set1':value=1
            elif name=='flip':value=int(not own)
            elif name=='copy':value=other
            elif name=='not_other':value=int(not other)
            elif name=='xor':value=(own+other)%2
            elif name=='and':value=min(own,other)
            elif name=='or':value=max(own,other)
            after=list(physical);after[tgt]=value
            row.append(STATES.index(tuple(after)))
        RULES.append(tuple(row))
assert len(set(RULES))==16
WORLDS=tuple((rule_a,rule_b) for rule_a in RULES for rule_b in RULES)
GAMMA=Fraction(9,10)


def successors(candidates,physical,action):
    groups={}
    for i in candidates:
        observed=WORLDS[i][action][physical]
        if observed not in groups:groups[observed]=[]
        groups[observed].append(i)
    return {k:tuple(v) for k,v in sorted(groups.items())}


def rebuild_posterior(trajectory):
    survivors=tuple(range(len(WORLDS)))
    for s,a,obs in trajectory:
        survivors=tuple(i for i in survivors if WORLDS[i][a][s]==obs)
        if not survivors:raise ValueError('unsupported transition')
    return survivors


def exhaustive_value(state,goal,belief,horizon):
    """Separate exact dynamic program using rational arithmetic.

    Scores discounted probability of goal-reaching, not undiscouted reachability.
    """
    @lru_cache(None)
    def v(s,subset,t):
        if s==goal:return Fraction(1)
        if t==0:return Fraction(0)
        result=Fraction(0)
        for a in (0,1):
            bins=successors(subset,s,a)
            estimate=sum((Fraction(len(child),len(subset))*v(dst,child,t-1)
                         for dst,child in bins.items()),Fraction(0))
            result=max(result,GAMMA*estimate)
        return result
    q={}
    if state==goal:return Fraction(1),{0:Fraction(1),1:Fraction(1)}
    for a in (0,1):
        bins=successors(belief,state,a)
        q[a]=GAMMA*sum((Fraction(len(child),len(belief))*v(dst,child,horizon-1)
                        for dst,child in bins.items()),Fraction(0))
    return max(q.values()),q
