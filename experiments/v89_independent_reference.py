"""Separate scalar reference for the hidden Moore version-space calculations.

This module uses no NumPy and does not import bgr89.latent or its compiled
catalogue or update routines. It enumerates the bounded hypothesis grammar via
itertools, then filters hidden-state trajectories from public action/partial
observation records. Used to independently verify original case predictions.
"""
from __future__ import annotations
from collections import Counter
from itertools import product
from math import isclose


def visible_match(code,seen):
    bits=(code//2,code%2)
    return all(s is None or s==b for s,b in zip(seen,bits))


def enumerate_hypotheses(n):
    for transition in product(tuple(range(n)),repeat=2*n):
        for outputs in product((0,1,2,3),repeat=n):
            yield (transition,outputs,0)


class ScalarReference:
    def __init__(self,candidate_sizes=(1,2,3)):
        self.sizes=tuple(candidate_sizes)
        self.groups={n:[] for n in self.sizes}
        self.catalogue_size={n:(n**(n*2))*(4**n) for n in self.sizes}
        self.initialized=False
        self.observed=[]

    def initialize(self,initial):
        assert not self.initialized
        for n in self.sizes:
            self.groups[n]=[row for row in enumerate_hypotheses(n) if visible_match(row[1][0],initial)]
        assert any(self.groups.values())
        self.initialized=True
        self.observed.append((None,tuple(initial)))

    def predict(self,action):
        if not self.initialized:raise ValueError('init')
        prior_per_class=1./len(self.sizes)
        histogram=[0.]*4;models_total=0
        for n,group in self.groups.items():
            w=prior_per_class/self.catalogue_size[n]
            for transition,outputs,current in group:
                nxt=transition[2*current+action]
                histogram[outputs[nxt]]+=w
            models_total+=len(group)
        z=sum(histogram)
        assert z>0
        return tuple(x/z for x in histogram),tuple(k for k,x in enumerate(histogram) if x>0),models_total

    def observe(self,action,visible):
        provisional={}
        for n,group in self.groups.items():
            new=[]
            for transition,outputs,current in group:
                nxt=transition[2*current+action]
                if visible_match(outputs[nxt],visible):new.append((transition,outputs,nxt))
            provisional[n]=new
        if not any(provisional.values()):
            return False
        self.groups=provisional
        self.observed.append((action,tuple(visible)))
        return True

    def certify_class(self):
        supported=[n for n,group in self.groups.items() if group]
        return supported[0] if len(supported)==1 else None

    def certify_relation(self):
        eq=opp=True
        for group in self.groups.values():
            for _,outputs,_ in group:
                if any(o in (1,2) for o in outputs):eq=False
                if any(o in (0,3) for o in outputs):opp=False
                if not eq and not opp:return None
        return 'equal' if eq else 'opposite' if opp else None
