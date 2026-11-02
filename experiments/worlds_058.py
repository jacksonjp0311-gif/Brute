"""Worlds for study BRUTE-0550-READBITS-058 (experiments/BRUTE_PLAN_058.json design.worlds; new file).
For seed s the transitions, start and passive prefix are exactly worlds_050 scale20 for s (worlds_026 actions, eps 0).
Families: 'scale20' keeps the original 2-bit emissions; 'scale20r2' / 'scale20r3' / 'scale20r4' replace them with
[rng.randrange(2**B) for q in range(n)], rng = random.Random(s*11+580+B). Reading of code c with B bits: bit j = (c>>(B-1-j))&1."""
import random
from experiments import worlds_050 as W50
from experiments.worlds_026 import actions as _actions

BITS={'scale20':2,'scale20r2':2,'scale20r3':3,'scale20r4':4}
SIZES={f:20 for f in BITS}
EMISSION_RNG='random.Random(seed*11+580+B).randrange(2**B), one draw per state in index order'


class World58:
    def __init__(self,n,k,s,transitions,emissions,start,seed,family):
        self.n=n;self.k=k;self.s=s;self.transitions=transitions;self.emissions=emissions;self.start=start;self.seed=seed;self.family=family


def emissions(seed,B,n=20):
    r=random.Random(seed*11+580+B);return tuple(r.randrange(1<<B) for _ in range(n))


def world(seed,family):
    if family not in BITS:raise ValueError(family)
    w=W50.world(seed,'scale20');B=BITS[family]
    em=tuple(w.emissions) if family=='scale20' else emissions(seed,B,w.n)
    return World58(w.n,w.k,B,tuple(tuple(r) for r in w.transitions),em,w.start,seed,family)


def actions(seed,eps,k):return _actions(seed,eps,k)


def bits(code,B):return tuple((code>>(B-1-j))&1 for j in range(B))
