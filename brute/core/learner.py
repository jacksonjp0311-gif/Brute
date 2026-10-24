"""Brute v0.1.0 core: v0.90 symbolic support plus refusal gates (F1-F5, F7).

The learner sees only actions and masked sensor bits. It certifies the next
full code only when every gate agrees; otherwise it returns a typed refusal.

Gates, in order (BRUTE_v0.1.0_PLAN.md and experiments/BRUTE_PLAN_002.json):
  F1 family contradicted      -> OUT_OF_FAMILY / FAMILY_CONTRADICTED (+ retraction)
  F4 residual surprise alarm  -> OUT_OF_FAMILY / RESIDUAL_SURPRISE
     family budget exhausted  -> ABSTAIN / BUDGET_EXHAUSTED
     support has >1 code      -> POSSIBLE_SET
     margin budget exhausted  -> ABSTAIN / BUDGET_EXHAUSTED
  F2 margin (<= n+1) differs  -> ABSTAIN / MARGIN_DISAGREES
  F3 bound saturated          -> ABSTAIN / BOUND_SATURATED
  else CERTIFIED (conditional on DECLARED_FAMILY); public only with F5 attestation.
F7: published probabilities keep an open-world reserve epsilon/4 on every code.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from math import log
from typing import Optional
from bgr90.symbolic import SymbolicLearner,mask_for_observation
from bgr89.latent import LatentLearner,IncompatibleObservation

DECLARED_FAMILY='deterministic-moore<=4/stationary'
DEFAULT_MAX_PREFIXES=160000
DEFAULT_EPSILON=0.02
DEFAULT_WINDOW=8


class Status(str,Enum):
    CERTIFIED='CERTIFIED'
    POSSIBLE_SET='POSSIBLE_SET'
    ABSTAIN='ABSTAIN'
    OUT_OF_FAMILY='OUT_OF_FAMILY'
    ERROR='ERROR'


class Reason(str,Enum):
    MARGIN_DISAGREES='MARGIN_DISAGREES'
    BOUND_SATURATED='BOUND_SATURATED'
    RESIDUAL_SURPRISE='RESIDUAL_SURPRISE'
    BUDGET_EXHAUSTED='BUDGET_EXHAUSTED'
    UNATTESTED_SCOPE='UNATTESTED_SCOPE'
    FAMILY_CONTRADICTED='FAMILY_CONTRADICTED'
    NOT_INITIALIZED='NOT_INITIALIZED'
    INVALID_REQUEST='INVALID_REQUEST'
    INTERNAL='INTERNAL'


@dataclass(frozen=True)
class ScopeAttestation:
    """A laboratory statement that the world lies in `family`. Not a credential."""
    family:str
    issuer:str
    basis:str


@dataclass(frozen=True)
class BruteForecast:
    action:int
    status:Status
    reason:Optional[Reason]
    certificate:Optional[int]          # conditional on `family`; None unless CERTIFIED
    public_certificate:Optional[int]   # certificate + valid attestation + no alarm
    public_reason:Optional[Reason]     # why public_certificate is None when certified
    support:Optional[tuple[int,...]]   # exact <=family_states support, None if unavailable
    margin_support:Optional[tuple[int,...]]
    saturated:Optional[bool]
    probabilities:tuple[float,float,float,float]
    v090_probabilities:tuple[float,float,float,float]
    legacy_probabilities:Optional[tuple[float,float,float,float]]
    legacy_certificate:Optional[int]
    family:str
    residual:Optional[float]


def compatible_mass(probabilities,obs):
    mask=mask_for_observation(obs)
    return sum(p for c,p in enumerate(probabilities) if mask&(1<<c))


class BruteLearner:
    def __init__(self,family_states=4,margin_states=5,max_prefixes=DEFAULT_MAX_PREFIXES,
                 margin_max_prefixes=DEFAULT_MAX_PREFIXES,smoothing=.08,epsilon=DEFAULT_EPSILON,
                 window=DEFAULT_WINDOW,tau=None,attestation:ScopeAttestation|None=None):
        if margin_states<=family_states:raise ValueError('margin must exceed the family bound')
        if not 0<smoothing<=1:raise ValueError('smoothing must be in (0,1]')
        if not 0<epsilon<1:raise ValueError('epsilon must be in (0,1)')
        if window<1:raise ValueError('window must be positive')
        self.family_states=family_states;self.margin_states=margin_states
        self.family=f'deterministic-moore<={family_states}/stationary'
        self.smoothing=smoothing;self.epsilon=epsilon;self.window=window;self.tau=tau
        self.support=SymbolicLearner(family_states,max_prefixes)
        self.margin=SymbolicLearner(margin_states,margin_max_prefixes)
        self.legacy=LatentLearner((1,2,3));self.legacy_valid=True;self.legacy_contradiction_step=None
        self.attestation=None
        self.initialized=False
        self.surprises=[];self.residual=None
        self.alarm_step=None;self.contradiction_step=None
        self.issued=[];self.retracted=0
        if attestation is not None:self.attest(attestation)

    # -- scope ---------------------------------------------------------------
    def attest(self,attestation:ScopeAttestation):
        if not isinstance(attestation,ScopeAttestation):raise TypeError('ScopeAttestation required')
        self.attestation=attestation

    def revoke_attestation(self):self.attestation=None

    def attestation_valid(self):
        return (self.attestation is not None and self.attestation.family==self.family
                and self.alarm_step is None and self.support.status=='supported')

    # -- state ---------------------------------------------------------------
    def initialize(self,obs):
        if self.initialized:raise ValueError('already initialized')
        self.support.initialize(obs);self.margin.initialize(obs);self.legacy.initialize(obs)
        self.initialized=True

    @property
    def steps(self):return len(self.support.evidence)-1 if self.initialized else 0

    def saturated(self):
        if self.support.status!='supported':return None
        return all(p.used==self.family_states for p in self.support.belief)

    def _v090_probabilities(self,action,support):
        legacy_probs=None;legacy_cert=None
        if self.legacy_valid:
            legacy_probs,prior=self.legacy.predict(action)
            legacy_cert=prior[0] if len(prior)==1 else None
        if support is None:probs=(.25,)*4
        else:
            relaxed=[1/len(support) if i in support else 0. for i in range(4)]
            if legacy_probs is None:probs=tuple(relaxed)
            else:probs=tuple((1-self.smoothing)*legacy_probs[i]+self.smoothing*relaxed[i] for i in range(4))
        return tuple(probs),legacy_probs,legacy_cert

    def _decide(self,support,margin_support,saturated):
        fam=self.support.status
        if fam=='grammar_contradicted':return Status.OUT_OF_FAMILY,Reason.FAMILY_CONTRADICTED,None
        if self.alarm_step is not None:return Status.OUT_OF_FAMILY,Reason.RESIDUAL_SURPRISE,None
        if fam=='budget_exhausted':return Status.ABSTAIN,Reason.BUDGET_EXHAUSTED,None
        if fam!='supported':return Status.ERROR,Reason.INTERNAL,None
        if len(support)!=1:return Status.POSSIBLE_SET,None,None
        if self.margin.status=='budget_exhausted':return Status.ABSTAIN,Reason.BUDGET_EXHAUSTED,None
        if margin_support!=support:return Status.ABSTAIN,Reason.MARGIN_DISAGREES,None
        if saturated:return Status.ABSTAIN,Reason.BOUND_SATURATED,None
        return Status.CERTIFIED,None,support[0]

    def predict(self,action:int)->BruteForecast:
        if not self.initialized:raise ValueError('initialize first')
        if action not in (0,1):raise ValueError('action must be 0 or 1')
        support=self.support.predict_support(action)
        margin_support=self.margin.predict_support(action)
        saturated=self.saturated()
        p90,legacy_probs,legacy_cert=self._v090_probabilities(action,support)
        e=self.epsilon
        probs=tuple((1-e)*p+e/4 for p in p90)
        status,reason,cert=self._decide(support,margin_support,saturated)
        if cert is not None and cert not in support:  # F5 belief consistency, fail closed
            status,reason,cert=Status.ERROR,Reason.INTERNAL,None
        public=None;public_reason=None
        if cert is not None:
            if self.attestation_valid():public=cert
            else:public_reason=Reason.UNATTESTED_SCOPE
        return BruteForecast(action,status,reason,cert,public,public_reason,support,margin_support,
                             saturated,probs,p90,legacy_probs,legacy_cert,self.family,self.residual)

    def record_issued(self,forecast:BruteForecast):
        """Caller marks a forecast as acted on, so a later contradiction can retract it."""
        if forecast.certificate is not None:self.issued.append((self.steps+1,forecast.certificate))

    def observe(self,action:int,obs):
        if not self.initialized:raise ValueError('initialize first')
        mask_for_observation(obs)
        forecast=self.predict(action)
        s=-log(compatible_mass(forecast.probabilities,obs))
        self.surprises.append(s)
        self.support.observe(action,obs);self.margin.observe(action,obs)
        if self.legacy_valid:
            try:self.legacy.observe(action,obs)
            except IncompatibleObservation:
                self.legacy_valid=False;self.legacy_contradiction_step=self.steps
        if len(self.surprises)>=self.window:
            self.residual=round(sum(self.surprises[-self.window:])/self.window,12)  # 12 d.p. so audits compare the same number
            if self.tau is not None and self.alarm_step is None and self.residual>self.tau:
                self.alarm_step=self.steps
        if self.support.status=='grammar_contradicted' and self.contradiction_step is None:
            self.contradiction_step=self.steps
            self.retracted=len(self.issued)
        if self.support.status!='supported' or self.alarm_step is not None:
            self.attestation=None  # contradiction, budget loss or alarm revokes scope
        return s

    def retry(self,family_states=None,max_prefixes=None):
        """Replay all evidence under a new bound. Attestation never carries over."""
        new=BruteLearner(family_states or self.family_states,
                         max(self.margin_states,(family_states or self.family_states)+1),
                         max_prefixes or self.support.max_prefixes,self.margin.max_prefixes,
                         self.smoothing,self.epsilon,self.window,self.tau,None)
        ev=self.support.evidence
        new.initialize(ev[0][1])
        for a,obs in ev[1:]:new.observe(a,obs)
        return new

    def diagnostics(self):
        return {'family':self.family,'family_status':self.support.status,'margin_status':self.margin.status,
                'family_rows':self.support.count,'margin_rows':self.margin.count,
                'family_peak_rows':self.support.max_rows_seen,'margin_peak_rows':self.margin.max_rows_seen,
                'legacy_valid':self.legacy_valid,'legacy_contradiction_step':self.legacy_contradiction_step,
                'contradiction_step':self.contradiction_step,'alarm_step':self.alarm_step,
                'certificates_issued':len(self.issued),'certificates_retracted':self.retracted,
                'attested':self.attestation is not None}
