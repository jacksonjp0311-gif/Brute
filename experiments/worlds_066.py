"""Worlds and noise for study BRUTE-0630-SEQNOISE24-066 (experiments/BRUTE_PLAN_066.json design.worlds; new file).
  world(seed, family): exactly worlds_064.world(seed, family) for family 'scale20' (20 states) or 'scale24' (24 states), 2-bit,
  noise-free emissions;
  actions(seed, eps, k): worlds_026.actions (passive prefix; called with eps 0);
  Noise(seed, eps): exactly worlds_065.Noise (random.Random(seed*13+650+int(round(1000*eps))), order (t, read, bit), one random()
  per bit, flip iff draw < eps). Re-reads do not move the hidden state."""
from experiments import worlds_064 as W64
from experiments import worlds_065 as W65
from experiments.worlds_058 import bits

FAMILIES=('scale20','scale24');SIZES={'scale20':20,'scale24':24};BITS=2
Noise=W65.Noise;noise_seed=W65.noise_seed


def world(seed,family):
    if family not in FAMILIES:raise ValueError(family)
    return W64.world(seed,family)


def actions(seed,eps,k):return W64.actions(seed,eps,k)


def clean(w,q):return bits(w.emissions[q],BITS)
