"""Evaluator-only extra out-of-grammar stress worlds (n=5 and stochastic).

Not imported by bgr90 learner. Included to falsify unsupported universal
certainty claims and assess how assumption gates behave on novelty.
"""
from dataclasses import dataclass
from random import Random
from bgr89.worlds import HiddenWorld

FAMILIES=('ood5','drift4')


def world(seed:int,family:str):
    if family not in FAMILIES:raise ValueError(family)
    if family=='ood5':
        rng=Random(seed*883103+103)
        n=5
        # A cycle with an observable marker and two aliased orbits.
        canonical=[((i+1)%n,(i+2)%n) for i in range(n)]
        perm=list(range(n));rng.shuffle(perm);lookup={old:new for new,old in enumerate(perm)}
        swap=rng.randrange(2)
        trans=tuple(tuple(lookup[x] for x in ((canonical[old][1],canonical[old][0]) if swap else canonical[old])) for old in perm)
        signatures=[0,0,1,1,2]; rng.shuffle(signatures)
        # Hidden labels and emission identities shuffled separately.
        emission_codes=list(range(4));rng.shuffle(emission_codes)
        emissions=tuple(emission_codes[signatures[old]] for old in perm)
        initial=lookup[rng.randrange(n)]
        return HiddenWorld(n,trans,emissions,initial,seed,family)
    rng=Random(seed*521237+97)
    n=4
    transition=tuple((rng.randrange(n),rng.randrange(n)) for _ in range(n))
    emissions=tuple(rng.randrange(4) for _ in range(n))
    start=rng.randrange(n)
    return HiddenWorld(n,transition,emissions,start,seed,family)


def step(world,hidden,action,t):
    if world.family=='drift4' and t>0 and t%11==0:
        # This is a deliberate, environment-level nonstationary deviation.
        # A deterministic Moore-machine model need not fit the full history.
        return (world.next(hidden,action)+1)%world.n
    return world.next(hidden,action)
