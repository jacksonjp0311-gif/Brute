"""Worlds and reading noise for study BRUTE-0560-NOISYWIDE-059 (experiments/BRUTE_PLAN_059.json design.worlds; new file).
World: for seed s exactly worlds_058 'scale20r4' for s (worlds_050 scale20 transitions, start and passive prefix; random 4-bit
emissions from random.Random(s*11+580+4)). Noise: each observation t (t = 1 is the initial reading) is read k_t times; every bit of
every read is flipped independently with probability eps, drawn from rng = random.Random(s*13+590+int(round(1000*eps))) in the fixed
order (t, read, bit): one rng.random() per bit, flip iff the draw < eps. eps 0 draws nothing. Re-reads do not move the hidden state."""
import random
from experiments import worlds_058 as W58

FAMILY='scale20r4';BITS=4;SIZE=20
NOISE_RNG='random.Random(seed*13+590+int(round(1000*eps))); one random() per bit in order (t, read, bit); flip iff draw < eps'


def world(seed):return W58.world(seed,FAMILY)


def actions(seed,eps,k):return W58.actions(seed,eps,k)


def bits(code,B=BITS):return W58.bits(code,B)


class Noise:
    def __init__(self,seed,eps):
        self.eps=eps;self.rng=random.Random(seed*13+590+int(round(1000*eps))) if eps>0 else None

    def reads(self,clean,k):
        """k noisy copies of the clean bit tuple."""
        if self.rng is None:return [tuple(clean) for _ in range(k)]
        out=[]
        for _ in range(k):out.append(tuple(b^1 if self.rng.random()<self.eps else b for b in clean))
        return out
