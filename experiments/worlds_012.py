"""World generators for study BRUTE-0100-SUPPORT-TRANSFER-012 (BRUTE_PLAN_012 world_generators).

2x2 and transfer: the frozen study-011 generators re-exported unchanged. big78: moore78(seed) (new)."""
import random
from experiments.worlds_011 import world,next_hidden,FAMILIES_2X2,HiddenWorldK,minimal_states
from experiments.worlds_007 import _reach

__all__=['world','next_hidden','FAMILIES_2X2','HiddenWorldK','minimal_states','moore78','source_codes']


def moore78(seed):
    """random.Random(seed*130363+331); n = 7 + seed % 2; _reach transitions/start; 4 distinct codes; pattern
    (0,0,1,1,2,2,3,3)[:n] shuffled; 2 actions, 2 bits."""
    rng=random.Random(seed*130363+331);n=7+seed%2
    T,start=_reach(rng,n,2);codes=rng.sample(range(4),4);em=[codes[j] for j in (0,0,1,1,2,2,3,3)[:n]];rng.shuffle(em)
    return HiddenWorldK(n,2,2,T,tuple(em),start,seed,'moore78')


def source_codes(seed,family,steps,actions):
    """Fully observed source (mask 0.0): the learner sees the observation bits; codes are read from the bits."""
    w=world(seed,family);h=w.start;obs=[w.observed(h,0.0,-1)]
    for i,a in enumerate(actions):h=w.next(h,a);obs.append(w.observed(h,0.0,i))
    return [o[0]*2+o[1] for o in obs]
