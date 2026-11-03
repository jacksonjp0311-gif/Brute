"""Worlds and noise for study BRUTE-0620-SEQNOISE2B20-065 (experiments/BRUTE_PLAN_065.json design.worlds; new file).
  world(seed): exactly worlds_064.world(seed, 'scale20') (2-bit, noise-free emissions, the 063/064 family);
  actions(seed, eps, k): worlds_026.actions (passive prefix; called with eps 0);
  Noise(seed, eps): every bit of every reading is flipped independently with probability eps, drawn from
  random.Random(seed*13+650+int(round(1000*eps))) in the fixed order (t, read, bit), one random() per bit, flip iff draw < eps.
  Readings are drawn one at a time (read()) until certify/20s.more() is False; re-reads do not move the hidden state."""
import random
from experiments import worlds_064 as W64
from experiments.worlds_058 import bits

FAMILY='scale20';SIZE=20;BITS=2


def world(seed,family=FAMILY):
    if family!=FAMILY:raise ValueError(family)
    return W64.world(seed,FAMILY)


def actions(seed,eps,k):return W64.actions(seed,eps,k)


def clean(w,q):return bits(w.emissions[q],BITS)


def noise_seed(seed,eps):return seed*13+650+int(round(1000*eps))


class Noise:
    def __init__(self,seed,eps):
        self.eps=eps;self.rng=random.Random(noise_seed(seed,eps)) if eps>0 else None;self.draws=0

    def read(self,clean_bits):
        """One noisy reading of the clean bit tuple (one random() per bit, in bit order)."""
        if self.rng is None:return tuple(clean_bits)
        out=[]
        for b in clean_bits:self.draws+=1;out.append(b^1 if self.rng.random()<self.eps else b)
        return tuple(out)
