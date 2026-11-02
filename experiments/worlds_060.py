"""Worlds for study BRUTE-0570-SCALE24W-060 (experiments/BRUTE_PLAN_060.json design.worlds; new file).
For seed s and family 'scale24r4' (n 24) or 'scale32r4' (n 32): transitions and start exactly worlds_026.scale_world(s, n)
(3 actions, minimal and strongly connected under its own 2-bit draw); emissions replaced by worlds_058.emissions(s, 4, n), i.e.
[random.Random(s*11+580+4).randrange(16) for q in range(n)]; passive prefix worlds_026.actions(s, 0, 3) (176 steps). Noise-free.
These are exactly the worlds of scripts/probe_060.py. Reading of code c with 4 bits: bit j = (c>>(3-j))&1.
true_size(w) (reported, Moore partition refinement) is the minimal size under the 4-bit emissions; labels are behaviour-based."""
from experiments import worlds_026 as W26
from experiments import worlds_058 as W58

BITS=4;SIZES={'scale24r4':24,'scale32r4':32}


class World60:
    def __init__(self,n,k,s,transitions,emissions,start,seed,family):
        self.n=n;self.k=k;self.s=s;self.transitions=transitions;self.emissions=emissions;self.start=start;self.seed=seed;self.family=family


def world(seed,family):
    if family not in SIZES:raise ValueError(family)
    n=SIZES[family];b=W26.scale_world(seed,n)
    return World60(n,b.k,BITS,tuple(tuple(r) for r in b.transitions),W58.emissions(seed,BITS,n),b.start,seed,family)


def actions(seed,eps,k):return W26.actions(seed,eps,k)


def bits(code,B=BITS):return W58.bits(code,B)


def true_size(w):
    """Number of behaviour classes of the reachable machine (Moore refinement)."""
    reach={w.start};st=[w.start]
    while st:
        q=st.pop()
        for a in range(w.k):
            x=w.transitions[q][a]
            if x not in reach:reach.add(x);st.append(x)
    cls={q:w.emissions[q] for q in reach}
    while True:
        sig={q:(cls[q],)+tuple(cls[w.transitions[q][a]] for a in range(w.k)) for q in reach}
        ids={};new={q:ids.setdefault(sig[q],len(ids)) for q in sorted(reach)}
        if len(set(new.values()))==len(set(cls.values())):return len(ids)
        cls=new
