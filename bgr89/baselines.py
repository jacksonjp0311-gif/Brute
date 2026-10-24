"""Transparent fixed-history empirical baselines on exactly the same masks.

A baseline observes no hidden states or full values of masked target bits.
It learns from complete emitted codes when available; missing codes remain
explicit tokens in each context. These simple baselines are NOT strong learned
hidden-state models and so cannot establish broad algorithmic superiority.
"""
from __future__ import annotations
from collections import defaultdict
from .latent import check_observation,code_to_bits

class SuffixFrequency:
    def __init__(self,context_steps=0,alpha=1.0):
        if context_steps not in (0,1,2,4):raise ValueError('bounded contexts 0/1/2/4')
        self.k=context_steps;self.alpha=float(alpha)
        self.actions=[];self.observations=[]
        self.counts=defaultdict(lambda:[0.]*4)
        self.history_length=0

    def initialize(self,observed):
        if self.observations:raise ValueError('initialized')
        self.observations.append(check_observation(observed))

    def key(self,action:int):
        recent=[]
        for j in range(max(0,len(self.actions)-self.k),len(self.actions)):
            recent.append((self.actions[j],self.observations[j+1]))
        return (tuple(recent),self.observations[-1] if self.k>=1 else (),action)

    def predict(self,action):
        k=self.key(action)
        tally=self.counts[k]
        total=sum(tally)+4*self.alpha
        return tuple((t+self.alpha)/total for t in tally)

    def observe(self,action,observed):
        observation=check_observation(observed)
        key=self.key(action)
        self.actions.append(action);self.observations.append(observation)
        if None not in observation:
            code=2*observation[0]+observation[1]
            self.counts[key][code]+=1
