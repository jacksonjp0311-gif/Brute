"""World generators for study BRUTE-040-GEOMETRY-006: the new perm4 family (BRUTE_PLAN_006 new_family_perm4) plus a
dispatcher to the frozen bgr89 (5 original families) and bgr90 (ood5, drift4) generators."""
import random
from bgr89.worlds import world as old_world,HiddenWorld
from bgr90.worlds import world as new_world,step as new_step

FAMILIES_006=('cycle3','switch3','unstructured3','unaliased2','ood4','ood5','drift4','perm4')


def perm4(seed):
    rng=random.Random(seed*104729+211)
    p0=list(range(4));rng.shuffle(p0)
    p1=list(range(4));rng.shuffle(p1)
    transitions=tuple((p0[s],p1[s]) for s in range(4))
    codes=rng.sample(range(4),3)
    emissions=[codes[0],codes[0],codes[1],codes[2]];rng.shuffle(emissions)
    start=rng.randrange(4)
    return HiddenWorld(4,transitions,tuple(emissions),start,seed,'perm4')


def world(seed,family):
    if family=='perm4':return perm4(seed)
    if family in ('ood5','drift4'):return new_world(seed,family)
    return old_world(seed,family)


def next_hidden(truth,hidden,action,i):
    return new_step(truth,hidden,action,i) if truth.family=='drift4' else truth.next(hidden,action)
