"""Brute v0.5.0 breadth learner (arms B5 / BM5 / BP5): k actions, s binary sensors (m = 2**s codes), RegionK backend.

Pre-registered in experiments/BRUTE_PLAN_007.json (breadth_learner, experiment_rules LU-R_k and M, backend). New file.
Gate order (as v0.1.0 + Y1k, generalised):
  family contradicted -> OUT_OF_FAMILY/FAMILY_CONTRADICTED; alarm on -> OUT_OF_FAMILY/RESIDUAL_SURPRISE;
  family budget_exhausted -> ABSTAIN/BUDGET_EXHAUSTED; |S_f(b)| != 1 -> POSSIBLE_SET;
  margin budget_exhausted -> ABSTAIN/BUDGET_EXHAUSTED; S_m(b) != S_f(b) -> ABSTAIN/MARGIN_DISAGREES;
  saturated -> ABSTAIN/BOUND_SATURATED; Y1k(b, latest mask) != S_f(b) -> ABSTAIN/RESYNC_AMBIGUOUS; else CERTIFIED;
  then the SOLVER_BUDGET overlay (any UNKNOWN used and not OUT_OF_FAMILY -> ABSTAIN/SOLVER_BUDGET).
Probabilities: (1-eps) uniform(S_f) + eps/m [family]; else (1-eps) uniform(S_m) + eps/m [margin]; else 1/m [uniform].
Alarm: residual (mean of the last W surprises, 12 d.p.) > tau; resume after W consecutive residuals <= tau with family and
margin supported. Public certificate iff certified, attested for the declared family and no alarm ever set.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import log,log2
from typing import Optional
from brute.core.learner import Status,Reason,ScopeAttestation
from brute.changepoint import Reason030
from brute.region import RegionSpace,codes_mask,PRODUCTION_CONF_BUDGET
from brute.region_learner import Reason050,BACKEND,POLICIES

DEFAULT_EPSILON=0.02
DEFAULT_WINDOW=8


def declared_family(n,k,s):return f'deterministic-moore<={n}/{k}-actions/{s}-sensors'


def retraction_reason_k(cert,observed,s):
    bits=[(cert>>(s-1-j))&1 for j in range(s)]
    if any(o is not None and o!=b for o,b in zip(observed,bits)):return 'falsified_by_observation'
    if all(o is not None for o in observed):return 'scope_withdrawn'
    return 'unverifiable_masked'


@dataclass(frozen=True)
class BreadthForecast:
    action:int
    status:Status
    reason:Optional[object]
    certificate:Optional[int]
    public_certificate:Optional[int]
    support:Optional[tuple]
    margin_support:Optional[tuple]
    saturated:Optional[bool]
    probabilities:tuple
    forecast_source:str
    solver_unknown:int
    family:str
    residual:Optional[float]


class BreadthBruteLearner:
    def __init__(self,family_states,margin_states,k,s,epsilon=DEFAULT_EPSILON,window=DEFAULT_WINDOW,tau=None,
                 attestation:ScopeAttestation|None=None,policy='LU-R',conf_budget=PRODUCTION_CONF_BUDGET,resume=True):
        if margin_states<=family_states:raise ValueError('margin must exceed the family bound')
        if k<2 or s<1:raise ValueError('need k>=2 actions and s>=1 sensors')
        if policy not in POLICIES:raise ValueError('policy must be LU-R or M')
        self.family_states=family_states;self.margin_states=margin_states;self.k=k;self.s=s;self.m=1<<s
        self.epsilon=epsilon;self.window=window;self.tau=tau;self.policy=policy;self.conf_budget=conf_budget;self.resume=resume
        self.family=declared_family(family_states,k,s)
        self.support=RegionSpace(family_states,None,k,s,conf_budget);self.margin=RegionSpace(margin_states,None,k,s,conf_budget)
        self.attestation=None;self.initialized=False
        self.surprises=[];self.residual=None;self.alarm_step=None;self.contradiction_step=None
        self.issued=[];self.retracted=0;self.issued_observations={}
        self._run=0;self.first_alarm_step=None;self.alarm_steps=[];self.resume_steps=[]
        self.lookahead_copies=0;self.lookahead_unknown_branches=0;self.volume_calls=0;self.forecasts_with_unknown=0
        if attestation is not None:self.attest(attestation)

    # ---- scope -------------------------------------------------------------------------------------------------------
    def attest(self,attestation):
        if not isinstance(attestation,ScopeAttestation):raise TypeError('ScopeAttestation required')
        self.attestation=attestation

    def attestation_valid(self):
        return (self.attestation is not None and self.attestation.family==self.family and self.alarm_step is None
                and self.support.status=='supported')

    # ---- state -------------------------------------------------------------------------------------------------------
    def initialize(self,obs):
        if self.initialized:raise ValueError('already initialized')
        self.support.initialize(obs);self.margin.initialize(obs);self.initialized=True

    @property
    def steps(self):return len(self.support.evidence)-1 if self.initialized else 0

    def _check_action(self,a):
        if a not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')

    def _decide(self,sup,msup,sat):
        fam=self.support.status
        if fam=='grammar_contradicted':return Status.OUT_OF_FAMILY,Reason.FAMILY_CONTRADICTED,None
        if self.alarm_step is not None:return Status.OUT_OF_FAMILY,Reason.RESIDUAL_SURPRISE,None
        if fam=='budget_exhausted':return Status.ABSTAIN,Reason.BUDGET_EXHAUSTED,None
        if fam!='supported':return Status.ERROR,Reason.INTERNAL,None
        if len(sup)!=1:return Status.POSSIBLE_SET,None,None
        if self.margin.status=='budget_exhausted':return Status.ABSTAIN,Reason.BUDGET_EXHAUSTED,None
        if msup!=sup:return Status.ABSTAIN,Reason.MARGIN_DISAGREES,None
        if sat:return Status.ABSTAIN,Reason.BOUND_SATURATED,None
        return Status.CERTIFIED,None,sup[0]

    def _probabilities(self,sup,msup):
        e=self.epsilon;m=self.m
        if self.support.status=='supported':S=sup;src='family'
        elif self.margin.status=='supported' and msup:S=msup;src='margin'
        else:return tuple([1/m]*m),'uniform'
        return tuple((1-e)*(1/len(S) if c in S else 0.)+e/m for c in range(m)),src

    def predict(self,action):
        if not self.initialized:raise ValueError('initialize first')
        self._check_action(action);self.support.unk=0;self.margin.unk=0
        sup=self.support.predict_support(action);msup=self.margin.predict_support(action);sat=self.support.saturated()
        status,reason,cert=self._decide(sup,msup,sat)
        if cert is not None and cert not in sup:status,reason,cert=Status.ERROR,Reason.INTERNAL,None
        if cert is not None and self.support.y1k(action,codes_mask(self.support.evidence[-1][1],self.s))!=(cert,):
            status,reason,cert=Status.ABSTAIN,Reason030.RESYNC_AMBIGUOUS,None
        unk=self.support.unk+self.margin.unk
        if unk and status!=Status.OUT_OF_FAMILY:status,reason,cert=Status.ABSTAIN,Reason050.SOLVER_BUDGET,None
        if unk:self.forecasts_with_unknown+=1
        probs,src=self._probabilities(sup,msup)
        public=cert if (cert is not None and self.attestation_valid()) else None
        return BreadthForecast(action,status,reason,cert,public,sup,msup,sat,probs,src,unk,self.family,self.residual)

    def record_issued(self,forecast):
        if forecast.certificate is None:return
        key=(self.steps+1,forecast.certificate)
        if key not in self.issued:self.issued.append(key)

    def observe(self,action,obs):
        if not self.initialized:raise ValueError('initialize first')
        self._check_action(action);mask=codes_mask(obs,self.s)
        f=self.predict(action)
        s=-log(sum(p for c,p in enumerate(f.probabilities) if mask>>c&1))
        self.surprises.append(s);was=self.alarm_step
        self.support.observe(action,obs);self.margin.observe(action,obs)
        if len(self.surprises)>=self.window:
            self.residual=round(sum(self.surprises[-self.window:])/self.window,12)
            if self.tau is not None and self.alarm_step is None and self.residual>self.tau:self.alarm_step=self.steps
        if self.support.status=='grammar_contradicted' and self.contradiction_step is None:
            self.contradiction_step=self.steps;self.retracted=len(self.issued)
        if self.support.status!='supported' or self.alarm_step is not None:self.attestation=None
        if self.issued and self.issued[-1][0]==self.steps:self.issued_observations[self.steps]=tuple(obs)
        if was is None and self.alarm_step is not None:
            self.alarm_steps.append(self.alarm_step);self._run=0
            if self.first_alarm_step is None:self.first_alarm_step=self.alarm_step
        elif self.resume and was is not None and self.alarm_step is not None:
            self._run=self._run+1 if (self.residual is not None and self.residual<=self.tau) else 0
            if self._run>=self.window and self.support.status=='supported' and self.margin.status=='supported':
                self.alarm_step=None;self._run=0;self.resume_steps.append(self.steps)
        return s

    # ---- experiment --------------------------------------------------------------------------------------------------
    def _live(self):
        return self.support.status=='supported' and self.margin.status=='supported' and self.alarm_step is None

    def _hit(self):self.lookahead_unknown_branches+=1

    def _certifiable_after(self,action,code):
        fam=self.support.extended(action,code);self.lookahead_copies+=1;mar=None
        try:
            if fam.feasible is None:self._hit();return 0
            if not fam.feasible:return 0
            sat,u=fam.saturated()
            if u:self._hit();return 0
            if sat:return 0
            singles={}
            for b in range(self.k):
                sb,u=fam.support(b)
                if u:self._hit();return 0
                if len(sb)!=1:continue
                y,u=fam.y1k(b,1<<code)
                if u:self._hit();return 0
                if y==sb:singles[b]=sb
            if not singles:return 0
            mar=self.margin.extended(action,code);self.lookahead_copies+=1
            if mar.feasible is None:self._hit();return 0
            if not mar.feasible:return 0
            tot=0
            for b,sb in singles.items():
                ms,u=mar.support(b)
                if u:self._hit();return 0
                tot+=ms==sb
            return tot
        finally:
            fam.close()
            if mar is not None:mar.close()

    def experiment_score(self,action):
        self._check_action(action)
        if not self._live():return 0.
        S=self.support.predict_support(action)
        return round(sum(self._certifiable_after(action,c) for c in S)/len(S),12)

    def volume(self,action):
        self.volume_calls+=1
        S=self.support.predict_support(action);tot=0.;full=self.k*log2(self.m)
        for c in S:
            f=self.support.extended(action,c)
            try:
                if f.feasible is not True:tot+=full;continue
                ys=[f.y1k(b,1<<c) for b in range(self.k)]
                if any(u for _,u in ys):tot+=full;continue
                tot+=sum(log2(len(y)) for y,_ in ys)
            finally:f.close()
        return round(tot/len(S),12)

    def proposal(self):
        if self.support.status!='supported' or self.margin.status!='supported':return 'NO_PROPOSAL','OUT_OF_SCOPE'
        if self.alarm_step is not None:return 'NO_PROPOSAL','RESIDUAL_ALARM'
        return 'PROPOSED',None

    def experiment(self,default_action):
        if not self.initialized:raise ValueError('initialize first')
        self._check_action(default_action)
        scores=[self.experiment_score(a) for a in range(self.k)]
        best=max(scores);tied=[b for b,x in enumerate(scores) if x==best];vol=None
        if self.policy=='M' and self._live() and len(tied)>1:
            vol=[self.volume(b) for b in range(self.k)];v=min(vol[b] for b in tied);cand=[b for b in tied if vol[b]==v]
        else:cand=tied
        a=default_action if default_action in cand else min(cand)
        p,why=self.proposal()
        return {'action':a,'score':scores[a],'scores':scores,'tied':len(tied)>1,'volumes':vol,'rule':self.policy,
                'proposal':p,'no_proposal_reason':why}

    # ---- bookkeeping -------------------------------------------------------------------------------------------------
    def retractions(self):
        out=[]
        for step,cert in self.issued[:self.retracted]:
            obs=self.issued_observations.get(step)
            out.append({'step':step,'certificate':cert,'observed':None if obs is None else list(obs),
                        'reason':'unverifiable_masked' if obs is None else retraction_reason_k(cert,obs,self.s)})
        return out

    def diagnostics(self):
        return {'backend':BACKEND,'family':self.family,'k':self.k,'s':self.s,'policy':self.policy,'conf_budget':self.conf_budget,
                'family_status':self.support.status,'margin_status':self.margin.status,
                'contradiction_step':self.contradiction_step,'alarm_step':self.alarm_step,'first_alarm_step':self.first_alarm_step,
                'alarm_steps':list(self.alarm_steps),'resume_steps':list(self.resume_steps),
                'certificates_issued':len(self.issued),'certificates_retracted':self.retracted,
                'attested':self.attestation is not None,
                'solver_unknown_total':self.support.unknown_total+self.margin.unknown_total,
                'forecasts_with_unknown':self.forecasts_with_unknown,'lookahead_copies':self.lookahead_copies,
                'lookahead_unknown_branches':self.lookahead_unknown_branches,'volume_calls':self.volume_calls,
                'family_peak_clauses':self.support.peak_clauses,'margin_peak_clauses':self.margin.peak_clauses,
                'family_peak_variables':self.support.peak_vars,'margin_peak_variables':self.margin.peak_vars}

    def close(self):
        self.support.close();self.margin.close()
