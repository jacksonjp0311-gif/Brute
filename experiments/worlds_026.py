"""World generators for study BRUTE-0230-SCALE-026 (experiments/BRUTE_PLAN_026.json worlds; deviation #123 item 2).

scale8 / scale12 / scale16: random strongly connected deterministic Moore machines with n = 8 / 12 / 16 states, k = 3
actions, s = 2 observation bits (m = 4 codes), minimal (pairwise distinguishable). Drawn by rejection from
Random(seed*130363 + 4026 + n): transitions uniform, start uniform, emissions uniform over the 4 codes; accept iff strongly
connected and minimal_states == n. control_cycle3: the frozen experiments.worlds_013 cycle3 family (k = 2).
The noise and action streams are seeded per (seed, eps) and never read the hidden truth. Hidden truth never reaches a learner."""
from __future__ import annotations
import random
from experiments.worlds_007 import HiddenWorldK,minimal_states
from experiments.worlds_013 import world as world_013

SCALE={'scale8':8,'scale12':12,'scale16':16}
FAMILIES=('scale8','scale12','scale16','control_cycle3')
HORIZON=176;S_BITS=2


def _strong(T,n):
    for rev in (False,True):
        adj={q:set() for q in range(n)}
        for q in range(n):
            for r in T[q]:
                (adj[r] if rev else adj[q]).add(q if rev else r)
        seen={0};st=[0]
        while st:
            q=st.pop()
            for r in adj[q]:
                if r not in seen:seen.add(r);st.append(r)
        if len(seen)!=n:return False
    return True


def scale_world(seed,n,family=None):
    rng=random.Random(seed*130363+4026+n);k=3
    for _ in range(100000):
        T=tuple(tuple(rng.randrange(n) for _ in range(k)) for _ in range(n));start=rng.randrange(n)
        em=tuple(rng.randrange(1<<S_BITS) for _ in range(n))
        if not _strong(T,n):continue
        w=HiddenWorldK(n,k,S_BITS,T,em,start,seed,family or f'scale{n}')
        if minimal_states(w)==n:return w
    raise ValueError('no minimal strongly connected machine in 100000 draws')


def world(seed,family):
    if family in SCALE:return scale_world(seed,SCALE[family],family)
    if family=='control_cycle3':
        w=world_013(seed,'cycle3')
        return HiddenWorldK(w.n,2,S_BITS,tuple(tuple(r) for r in w.transitions),tuple(w.emissions),w.start,seed,family)
    raise ValueError(f'unknown family {family!r}')


def actions(seed,eps,k,steps=HORIZON):
    """Declared uniform random action policy (deviation #123 item 4: replaces SP8, which is 2-action only)."""
    rng=random.Random(seed*72031+26+int(round(eps*1000))*7);return tuple(rng.randrange(k) for _ in range(steps))


def flips(seed,eps,steps=HORIZON):
    """Bit flips for readings 0..steps (tag 26): flips[t][j] is True iff bit j of reading t is flipped."""
    if eps==0:return tuple((False,)*S_BITS for _ in range(steps+1))
    rng=random.Random((seed*1000003+int(round(eps*1000))*7919+26)%(2**64))
    return tuple(tuple(rng.random()<eps for _ in range(S_BITS)) for _ in range(steps+1))


def bits(code):return tuple((code>>(S_BITS-1-j))&1 for j in range(S_BITS))


def trajectory(w,seed,eps,steps=HORIZON):
    """{'actions', 'readings' (noisy, fully observed), 'latent' codes 0..steps, 'states'}; latent is evaluator only."""
    acts=actions(seed,eps,w.k,steps);fl=flips(seed,eps,steps);h=w.start;st=[h];lat=[w.emissions[h]]
    for a in acts:h=w.transitions[h][a];st.append(h);lat.append(w.emissions[h])
    rd=[tuple(b^int(f) for b,f in zip(bits(c),fr)) for c,fr in zip(lat,fl)]
    return {'actions':acts,'readings':rd,'latent':lat,'states':st}
