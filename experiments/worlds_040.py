"""World generators for study BRUTE-0370-APART-CUBE-040 (experiments/BRUTE_PLAN_040.json worlds; deviation #152 fixes the
readings below). New file; experiments/worlds_026.py and worlds_039.py are frozen and imported only.

scale16 / scale14: the frozen experiments.worlds_026.scale_world(seed, n) (k = 3, 2 observation bits, m = 4 codes).
control_cycle3: as in worlds_026 (k = 2).
lowobs12 (new family): 12 states, k = 3, uniform random transitions, start uniform, emissions uniform over only the codes
{0, 1} (one bit of information per step; the reading space is still the 2-bit, 4-code space), drawn by rejection from
Random(seed*140040 + 40040 + n) (distinct from worlds_026's seed*130363 + 4026 + n and worlds_039's seed*170039 + 39039 + n);
accepted iff strongly connected and minimal_states == n. Passive action stream and readings: worlds_026.actions /
worlds_026.trajectory (eps 0). Hidden truth never reaches a learner."""
from __future__ import annotations
import random
from experiments.worlds_007 import HiddenWorldK,minimal_states
from experiments import worlds_026 as W26
from experiments.worlds_026 import _strong,actions,trajectory,bits,HORIZON,S_BITS

__all__=['SIZES','FAMILIES','lowobs_world','world','actions','trajectory','bits','HORIZON','S_BITS']
SIZES={'scale16':16,'scale14':14,'lowobs12':12,'control_cycle3':3}
FAMILIES=('scale16','scale14','lowobs12','control_cycle3')


def lowobs_world(seed,n=12,family='lowobs12'):
    rng=random.Random(seed*140040+40040+n);k=3
    for _ in range(100000):
        T=tuple(tuple(rng.randrange(n) for _ in range(k)) for _ in range(n));start=rng.randrange(n)
        em=tuple(rng.randrange(2) for _ in range(n))
        if not _strong(T,n):continue
        w=HiddenWorldK(n,k,S_BITS,T,em,start,seed,family)
        if minimal_states(w)==n:return w
    raise ValueError('no minimal strongly connected low-observation machine in 100000 draws')


def world(seed,family):
    if family in ('scale14','scale16'):return W26.scale_world(seed,SIZES[family],family)
    if family=='lowobs12':return lowobs_world(seed,12,family)
    if family=='control_cycle3':return W26.world(seed,family)
    raise ValueError(f'unknown family {family!r}')
