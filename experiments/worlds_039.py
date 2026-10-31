"""World generators for study BRUTE-0360-CLEAN-SCALE-039 (experiments/BRUTE_PLAN_039.json worlds; deviation #150 fixes the
readings below). New file; experiments/worlds_026.py is frozen and imported only.

scale12 / scale14 / scale16: the frozen experiments.worlds_026.scale_world(seed, n) (random strongly connected minimal Moore
machines, k = 3 actions, 2 observation bits, m = 4 codes). control_cycle3: as in worlds_026 (k = 2).
perm12 (new family): k = 3 actions, each a permutation of the 12 states (reversible group automaton), drawn by
rejection from Random(seed*170039 + 39039 + n) (a stream distinct from worlds_026's seed*130363 + 4026 + n): per action a
random.shuffle of 0..n-1, start uniform, emissions uniform over the 4 codes; accepted iff strongly connected and
minimal_states == n. The passive action stream and the readings are worlds_026.actions / worlds_026.trajectory (eps 0).
Hidden truth never reaches a learner."""
from __future__ import annotations
import random
from experiments.worlds_007 import HiddenWorldK,minimal_states
from experiments import worlds_026 as W26
from experiments.worlds_026 import _strong,actions,trajectory,bits,HORIZON,S_BITS

__all__=['SIZES','FAMILIES','perm_world','world','actions','trajectory','bits','HORIZON','S_BITS']
SIZES={'scale12':12,'scale14':14,'scale16':16,'perm12':12,'control_cycle3':3}
FAMILIES=('scale16','scale14','scale12','perm12','control_cycle3')


def perm_world(seed,n=12,family='perm12'):
    rng=random.Random(seed*170039+39039+n);k=3
    for _ in range(100000):
        cols=[]
        for _ in range(k):p=list(range(n));rng.shuffle(p);cols.append(p)
        T=tuple(tuple(cols[a][q] for a in range(k)) for q in range(n));start=rng.randrange(n)
        em=tuple(rng.randrange(1<<S_BITS) for _ in range(n))
        if not _strong(T,n):continue
        w=HiddenWorldK(n,k,S_BITS,T,em,start,seed,family)
        if minimal_states(w)==n:return w
    raise ValueError('no minimal strongly connected permutation machine in 100000 draws')


def world(seed,family):
    if family in ('scale12','scale14','scale16'):return W26.scale_world(seed,SIZES[family],family)
    if family=='perm12':return perm_world(seed,12,family)
    if family=='control_cycle3':return W26.world(seed,family)
    raise ValueError(f'unknown family {family!r}')
