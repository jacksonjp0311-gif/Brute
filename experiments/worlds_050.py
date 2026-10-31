"""World dispatch for study BRUTE-0470-SCALE20-REPLICATION-NOISE12-050 (experiments/BRUTE_PLAN_050.json). New file.
scale20 and the frozen 047 families come from experiments/worlds_047 unchanged; scale12 (control and noise12 hidden machines) is
the frozen worlds_026.world(seed, 'scale12') generator. None of those files is edited.
NoisyStepWorld answers the plan's re-read question (design.reread_assumption, deviation #173 item 3): the frozen generators do
NOT offer a re-read (worlds_026.flips fixes ONE flip pattern per reading index t of a precomputed trajectory, and
brute_study_033.StepWorld has only reset() / step(), noise-free), so this module adds the declared interface: reset() and
step(action) move the hidden state and return nothing; read() returns the current emission with each of its S_BITS bits flipped
independently with probability eps, and never changes the hidden state. Flips come from random.Random seeded per (seed, eps) with
tag 50 and never read the hidden truth. Hidden truth never reaches a learner."""
from __future__ import annotations
import random
from experiments import worlds_026 as W26
from experiments import worlds_047 as W47
from experiments.worlds_026 import actions,bits,HORIZON,S_BITS

__all__=['SIZES','world','actions','bits','HORIZON','S_BITS','NoisyStepWorld']
SIZES={**W47.SIZES,'scale12':12}


def world(seed,family):
    if family=='scale12':return W26.world(seed,'scale12')
    return W47.world(seed,family)


class NoisyStepWorld:
    """reset() / step(a) move the hidden state (no reading); read() is a noisy reading of the current state (state unchanged)."""
    def __init__(self,w,seed,eps):
        self._w=w;self._h=None;self.k=w.k;self.steps=0;self.reads=0;self.flipped=0;self.eps=eps
        self._rng=random.Random((seed*1000003+int(round(eps*1000))*7919+50)%(2**64))

    def reset(self):self._h=self._w.start;self.steps=0

    def step(self,a):
        if a not in range(self.k):raise ValueError('bad action')
        self._h=self._w.transitions[self._h][a];self.steps+=1

    def read(self):
        b=list(W26.bits(self._w.emissions[self._h]));self.reads+=1
        for j in range(S_BITS):
            if self.eps>0 and self._rng.random()<self.eps:b[j]^=1;self.flipped+=1
        return tuple(b)
