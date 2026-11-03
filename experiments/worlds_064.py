"""Worlds for study BRUTE-0610-SCALE2B24-064 (experiments/BRUTE_PLAN_064.json design.worlds; new file).
Original 2-bit emissions, noise-free, passive prefix worlds_026.actions(seed, 0, k) in every family.
  'scale20': exactly worlds_058.world(seed, 'scale20') (the study-063 family).
  'scale24': exactly worlds_026.scale_world(seed, 24) (minimal and strongly connected as drawn; the capability probe 064 world)."""
from experiments import worlds_058 as W58
from experiments import worlds_026 as W26

BITS={'scale20':2,'scale24':2}
SIZES={'scale20':20,'scale24':24}


class World64:
    def __init__(self,n,k,s,transitions,emissions,start,seed,family):
        self.n=n;self.k=k;self.s=s;self.transitions=transitions;self.emissions=emissions;self.start=start;self.seed=seed;self.family=family


def world(seed,family):
    if family=='scale20':w=W58.world(seed,'scale20')
    elif family=='scale24':w=W26.scale_world(seed,24)
    else:raise ValueError(family)
    if w.n!=SIZES[family] or w.s!=2:raise ValueError('world size or bits differ')
    return World64(w.n,w.k,w.s,tuple(tuple(r) for r in w.transitions),tuple(w.emissions),w.start,seed,family)


def actions(seed,eps,k):return W26.actions(seed,eps,k)
