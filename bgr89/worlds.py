"""Reference-only hidden deterministic transducers; never imported by learner.

Each world exposes two anonymous observed channels and two unnamed actions.
Two different hidden states often share an observable code. A random sensor
mask hides one or both bits; the learner is not told the true latent state,
world type, state count, transition law or emission map.
"""
from __future__ import annotations
from dataclasses import dataclass
from random import Random
from .latent import code_to_bits

FAMILIES=('cycle3','switch3','unstructured3','unaliased2','ood4')

@dataclass(frozen=True)
class HiddenWorld:
    n:int
    transitions:tuple[tuple[int,int],...]
    emissions:tuple[int,...]
    start:int
    seed:int
    family:str
    def emission(self,hidden:int):return self.emissions[hidden]
    def next(self,hidden:int,action:int):
        if not 0<=hidden<self.n or action not in (0,1):raise ValueError('invalid hidden state/action')
        return self.transitions[hidden][action]
    def observed(self,hidden:int,rate:float,step:int):
        bits=code_to_bits(self.emission(hidden))
        rng=Random((self.seed*1299709+step*23011+701)% (2**64))
        return tuple(bit if rng.random()>=rate else None for bit in bits)


def world(seed:int,family:str):
    if family not in FAMILIES:raise ValueError(family)
    rng=Random(seed*118763+101)
    n=4 if family=='ood4' else 2 if family=='unaliased2' else 3
    indices=list(range(n));rng.shuffle(indices)
    # Hidden-state permutation must not be supplied to the learner.
    inverse={old:new for new,old in enumerate(indices)}
    if family in ('cycle3','ood4'):
        canonical=[((s+1)%n,(s-1)%n) for s in range(n)]
    elif family=='switch3':
        canonical=[((s+1)%n,(s if s==2 else 1-s)) for s in range(n)]
    elif family=='unstructured3':
        canonical=[(rng.randrange(n),rng.randrange(n)) for s in range(n)]
    else:
        canonical=[(1-s,s) for s in range(n)]
    permute_actions=rng.randrange(2)
    transitions=[]
    for old in indices:
        a,b=canonical[old]
        successors=(b,a) if permute_actions else (a,b)
        transitions.append(tuple(inverse[x] for x in successors))
    choices=rng.sample(range(4),2)
    if family=='unaliased2':emit=[choices[0],choices[1]]
    elif family=='ood4':emit=[choices[0],choices[0],choices[0],choices[1]]
    else:emit=[choices[0],choices[0],choices[1]]
    raw=tuple(emit[i] for i in indices)
    start=inverse[rng.randrange(n)]
    return HiddenWorld(n,tuple(transitions),raw,start,seed,family)


def actions(seed:int,steps:int):
    rng=Random(seed*72031+37)
    return tuple(rng.randrange(2) for _ in range(steps))
