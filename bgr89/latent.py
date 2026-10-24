"""Exact version-space filtering for unknown, hidden finite predictive states.

The observation is a pair of anonymous binary channels, either of which may
be missing. No hidden state index, emission map, transition rule, hidden-state
count (within publicly declared 1..max_states), or true state is supplied.

One fully specified hypothesis is a deterministic Moore transducer with n
latent states (n<=3), two named but uninterpreted actions, two-bit emissions,
and initial hidden state 0 (other labels are a gauge). Surviving worlds are
updated by observed actions and partial successor observations.

Unanimous certificates use ALL surviving hypotheses regardless of their prior
weight. Probabilistic predictions additionally assign equal total prior mass
to each candidate cardinality, rather than overweighting large model classes.
This remains a *supplied finite automaton meta-grammar*, NOT unconstrained
latent causal representation discovery.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
from collections import defaultdict
import hashlib
import numpy as np


class IncompatibleObservation(RuntimeError):
    """A new observation contradicts every surviving hidden-state machine."""


def code_to_bits(value:int):
    return ((value>>1)&1,value&1)


def matches_observation(codes:np.ndarray,observation):
    """Whether underlying two-channel emissions agree with visible bits."""
    b0,b1=observation
    keep=np.ones(codes.shape,dtype=np.bool_)
    if b0 is not None:keep &= ((codes>>1)&1)==b0
    if b1 is not None:keep &= (codes&1)==b1
    return keep


def check_observation(observation):
    if len(observation)!=2 or any(x not in (0,1,None) for x in observation):
        raise ValueError('Expected two independent nullable binary channels')
    return tuple(observation)


@lru_cache(maxsize=4)
def machine_catalogue(n:int):
    """A constant, immutable catalogue. First latent coordinate is gauge-fixed to 0."""
    if n not in (1,2,3):raise ValueError('supported latent width 1..3')
    trans_ids=np.arange(n**(2*n),dtype=np.int32)
    trans_digits=np.stack([(trans_ids//(n**j))%n for j in range(2*n)],axis=1).astype(np.uint8)
    trans_digits=trans_digits.reshape(-1,n,2)
    emit_ids=np.arange(4**n,dtype=np.int32)
    emissions=np.stack([(emit_ids//(4**j))%4 for j in range(n)],axis=1).astype(np.uint8)
    ts=np.repeat(trans_digits,4**n,axis=0)
    es=np.tile(emissions,(len(trans_ids),1))
    ts.setflags(write=False);es.setflags(write=False)
    return ts,es


@dataclass
class LatentBank:
    n:int
    active:np.ndarray
    current:np.ndarray
    @classmethod
    def make(cls,n):
        trans,emissions=machine_catalogue(n)
        return cls(n,np.ones(len(trans),dtype=np.bool_),np.zeros(len(trans),dtype=np.uint8))
    @property
    def count(self):return int(np.count_nonzero(self.active))


class LatentLearner:
    """Exact finite-world support and an explicit categorical predictive mixture.

    A transactional update prevents a contradiction from partially mutating
    any bank. A prediction certificate requires unanimity over every surviving
    machine, including those with negligibly small (but nonzero) mass.
    """
    def __init__(self,candidate_sizes=(1,2,3),class_prior=None):
        self.sizes=tuple(sorted(set(candidate_sizes)))
        if not self.sizes or any(n not in (1,2,3) for n in self.sizes):
            raise ValueError('finite candidate state counts must be subset of 1,2,3')
        self.banks={n:LatentBank.make(n) for n in self.sizes}
        weights=class_prior if class_prior is not None else {n:1. for n in self.sizes}
        if any(float(weights.get(n,0))<=0 for n in self.sizes):
            raise ValueError('Every supported class needs a positive weight')
        total=sum(float(weights[n]) for n in self.sizes)
        self.prior={n:float(weights[n])/total for n in self.sizes}
        self.initialized=False
        self.history=[]
        self.model_evaluations=0

    def _normalization(self):
        weights={}
        for n,b in self.banks.items():
            weights[n]=self.prior[n]*b.count/len(b.active)
        denom=sum(weights.values())
        if denom<=0:raise IncompatibleObservation('no supported latent model remains')
        return {n:val/denom for n,val in weights.items()}

    def initialize(self,observation):
        if self.initialized:raise ValueError('already initialized')
        observation=check_observation(observation)
        proposals={}
        for n,b in self.banks.items():
            _,em=machine_catalogue(n)
            proposals[n]=b.active & matches_observation(em[:,0],observation)
        if not any(np.any(a) for a in proposals.values()):
            raise IncompatibleObservation('initial observation unsupported')
        for n,a in proposals.items():self.banks[n].active=a
        self.initialized=True
        self.history.append({'action':None,'observation':observation})

    def predict(self,action:int):
        if not self.initialized:raise ValueError('initialize with current observation')
        if action not in (0,1):raise ValueError('action must be 0 or 1')
        votes=np.zeros(4,dtype=np.float64)
        posterior=self._normalization()
        all_possible=set()
        for n,bank in self.banks.items():
            if bank.count==0:continue
            trans,em=machine_catalogue(n)
            ids=np.flatnonzero(bank.active)
            successors=trans[ids,bank.current[ids],action]
            outputs=em[ids,successors]
            histogram=np.bincount(outputs.astype(np.intp),minlength=4)
            votes+=posterior[n]*histogram/len(ids)
            all_possible.update(np.flatnonzero(histogram).tolist())
            self.model_evaluations+=len(ids)
        if not all_possible:raise AssertionError('empty version space')
        votes/=votes.sum()
        return tuple(float(p) for p in votes),tuple(sorted(all_possible))

    def certify(self,action:int):
        _,support=self.predict(action)
        return support[0] if len(support)==1 else None

    def observe(self,action:int, observation):
        if not self.initialized:raise ValueError('must initialize')
        if action not in (0,1):raise ValueError('action must be 0 or 1')
        observation=check_observation(observation)
        updates={}
        for n,b in self.banks.items():
            trans,em=machine_catalogue(n)
            new_current=trans[np.arange(len(b.current)),b.current,action]
            possible=em[np.arange(len(b.current)),new_current]
            new_active=b.active & matches_observation(possible,observation)
            updates[n]=(new_current,new_active)
            self.model_evaluations+=b.count
        if not any(np.any(m) for _,m in updates.values()):
            raise IncompatibleObservation('all candidate hidden causal systems contradicted; state unchanged')
        for n,(new_current,new_active) in updates.items():
            b=self.banks[n];b.current=new_current;b.active=new_active
        self.history.append({'action':action,'observation':observation})

    def class_mass(self):
        return self._normalization()

    def certify_state_count(self):
        candidates=[n for n,b in self.banks.items() if b.count>0]
        # Only representation-size identifiability in the supplied grammar;
        # isomorphic/split states can make this intrinsically ambiguous.
        return candidates[0] if len(candidates)==1 else None

    def certify_sensor_relation(self):
        """Prove a two-channel relation over every *future-reachable* hidden state.

        Returns 'equal', 'opposite', or None. Never infer a universal relation
        from the few emissions already observed or from posterior likelihood.
        """
        can_equal=can_opposite=True
        for n,b in self.banks.items():
            if not b.count:continue
            trans,em=machine_catalogue(n)
            ids=np.flatnonzero(b.active)
            currents=b.current[ids]
            # Conservative overapproximation: check *all* states in every
            # surviving machine. This can abstain even when current-state
            # future reachability is narrower; it cannot falsely certify.
            emits=em[ids]
            if np.any((emits[:, :] == 1)|(emits[:, :] == 2)):
                can_equal=False
            if np.any((emits[:, :] == 0)|(emits[:, :] == 3)):
                can_opposite=False
            if not can_equal and not can_opposite:return None
        return 'equal' if can_equal else 'opposite' if can_opposite else None

    def snapshot(self):
        return {'supported_models':sum(b.count for b in self.banks.values()),
                'class_models':{str(n):b.count for n,b in self.banks.items()},
                'class_mass':{str(n):round(p,12) for n,p in self.class_mass().items()},
                'state_count_certified':self.certify_state_count(),
                'sensor_relation_certified':self.certify_sensor_relation(),
                'visible_observations':len(self.history),'model_evaluations':self.model_evaluations}
