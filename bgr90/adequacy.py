"""Provenance-aware forecast layer for known and unknown model grammar.

The exact four-state support engine can veto false unanimity by the restricted
three-state learner on in-grammar four-state worlds. It cannot prove that four
hidden states are sufficient from finite evidence. No public certificate is
created without an external, independently validated modelling assumption.

This software includes no external authorization system or actuator. The
`scope_verified` switch is a laboratory assumption, NOT a secure credential.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import log
from .symbolic import SymbolicLearner
from bgr89.latent import LatentLearner,IncompatibleObservation


@dataclass(frozen=True)
class Forecast:
    action:int
    probabilities:tuple[float,float,float,float]
    scoped_support:tuple[int,...]|None
    conditional_certificate:int|None
    public_certificate:int|None
    prior_three_state_certificate:int|None
    status:str
    scope_verified:bool
    warning:str


class AdequacyLearner:
    def __init__(self,max_states=4,max_prefixes=200000,smoothing=.08,scope_verified=False):
        if not 0<smoothing<=1:raise ValueError('smoothing must be between 0 and 1')
        self.max_states=max_states;self.smoothing=smoothing
        self.scope_verified=bool(scope_verified)
        self.support4=SymbolicLearner(max_states,max_prefixes)
        self.legacy=LatentLearner((1,2,3))
        self.legacy_valid=True
        self.legacy_contradiction_step=None
        self.status='uninitialized'
        self.predictions=0
        self.safe_refusals=0
        self.conditional_certs=0
        self.public_certs=0

    def initialize(self,obs):
        self.support4.initialize(obs);self.legacy.initialize(obs)
        self.status='supported'

    def predict(self,action):
        if self.status=='uninitialized':raise ValueError('initialize first')
        support=self.support4.predict_support(action)
        legacy_probs=None;prior_cert=None
        if self.legacy_valid:
            legacy_probs,prior_support=self.legacy.predict(action)
            prior_cert=prior_support[0] if len(prior_support)==1 else None
        # The symbolic support is exact as a set of possible next full sensor
        # values (conditional on the <=max_states deterministic grammar).
        # It supplies NO calibrated probability measure over completions.
        if support is None:
            probabilities=(.25,)*4
        else:
            relaxed=[1/len(support) if i in support else 0 for i in range(4)]
            if legacy_probs is None:probabilities=tuple(relaxed)
            else:
                # Assign conservative probability mass to the larger grammar
                # to avoid hard 0/1 extrapolation from a misspecified n<=3
                # Bayesian catalogue. No certification uses these weights.
                probabilities=tuple((1-self.smoothing)*legacy_probs[i]+self.smoothing*relaxed[i] for i in range(4))
        conditional=support[0] if support is not None and len(support)==1 else None
        public=conditional if self.scope_verified else None
        self.predictions+=1
        self.conditional_certs+=int(conditional is not None)
        self.public_certs+=int(public is not None)
        self.safe_refusals+=int(prior_cert is not None and public is None)
        return Forecast(action,tuple(probabilities),support,conditional,public,prior_cert,
                        self.support4.status,self.scope_verified,
                        'All certifications depend on an EXTERNALLY validated <=4-state deterministic grammar; finite evidence alone cannot certify this assumption.')

    def observe(self,action,obs):
        if self.status=='uninitialized':raise ValueError('initialize first')
        self.support4.observe(action,obs)
        if self.legacy_valid:
            try:self.legacy.observe(action,obs)
            except IncompatibleObservation:
                self.legacy_valid=False
                self.legacy_contradiction_step=len(self.support4.evidence)-1
        self.status=self.support4.status

    def retry(self,max_states=None,max_prefixes=None):
        self.support4=self.support4.reconstruct(max_states,max_prefixes)
        self.max_states=self.support4.max_states
        self.status=self.support4.status
        # Scope attestation cannot be inherited when the model family expands.
        self.scope_verified=False

    def diagnostics(self):
        return {'model_scope_max_states':self.max_states,'legacy_compatible':self.legacy_valid,
                'legacy_contradiction_step':self.legacy_contradiction_step,
                'symbolic':self.support4.snapshot(),'conditional_certifications':self.conditional_certs,
                'public_certifications':self.public_certs,'refusals':self.safe_refusals,
                'scope_verified_externally':self.scope_verified}
