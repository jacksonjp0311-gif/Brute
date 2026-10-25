"""Brute v0.6.0 drift-sound certification candidates (arms R6 / C6 on 2x2, BR6 / BC6 on breadth).

Pre-registered in experiments/BRUTE_PLAN_008.json (arms R6, C6, BR6, BC6; rule_constants_frozen). New file: the frozen
v0.5.0 learners (brute/region_learner.py, brute/breadth.py, brute/region.py) are subclassed, never edited. Not a
default: the release default stays the v0.5.0 rule (Y1k, LU-R) whatever the outcome (default_policy_rule).

Implementation reading of the plan text, fixed here before any v0.6.0 run (the second implementation
experiments/v060_reference.py, committed earlier, implements the same reading):

* EVENT STEPS. Step u (= number of observations after observing u) is an event if, after that observation, the residual
  (mean of the last W surprises, rounded to 12 d.p., as in the frozen learners) is > tau * surprise_fraction
  (tau6/2 on 2x2, tau7/2 on breadth), or a window-tier event happened at u (2x2: _window_start, i.e. the family
  contradiction or a window restart; breadth has no window tier, so its family contradiction is used; no certificate
  can follow a contradiction, so that choice cannot change a decision). s* = the last event step.
* R6 / BR6 (rule 'RO', recency-opened edges). At a prediction made after t observations the rule is ACTIVE iff s*
  exists and t - s* < W (= recency_window 8). Active: the Y1k union is computed with every transition edge (q, b) whose
  traversals all end at observations < s* (RegionK transition index < s*-1; transition i goes from observation i to i+1)
  treated as unknown and OPEN TO EVERY CODE AT EVERY FIBRE STATE; edges traversed at least once at index >= s*-1 keep
  the successor-code rule; never-traversed edges keep the Y1k convention (open only at the current state). Certified iff
  that union is exactly {c}; otherwise ABSTAIN / RESYNC_AMBIGUOUS. Not active: identical to A5.
* C6 / BC6 (rule 'CT', coverage-tracked). If the A5 Y1k union is {c}: certified as A5. Otherwise the pre-Y1k
  certificate c (FallbackBruteLearner gates on the full-history region = the tracked-state projection with the v0.1.0
  gates, the v0.2.0/A2 rule) is KEPT iff no event has happened in the session so far (no residual > tau/2, no window
  event, no contradiction) and t >= burn_in (8); otherwise ABSTAIN / RESYNC_AMBIGUOUS.
* Then the SOLVER_BUDGET overlay exactly as A5/B5. LU-R experiments, alarm, resume and probabilities are unchanged, so
  for the same evidence R6, C6 and A5 choose the same actions.
Each forecast carries cert_rule: None (no pre-Y1k certificate), 'Y1k', 'Y1k-recent', 'tracked-calm' or 'downgraded'.
"""
from __future__ import annotations
from dataclasses import dataclass,replace
from itertools import combinations
from typing import Optional
from bgr90.symbolic import mask_for_observation
from brute.core.learner import Status,Reason
from brute.fallback import FallbackBruteLearner
from brute.changepoint import Reason030
from brute.region import codes_mask
from brute.region_learner import RegionBruteLearner,RegionForecast,Reason050
from brute.breadth import BreadthBruteLearner,BreadthForecast

RULES=('RO','CT')
SURPRISE_FRACTION=0.5
RECENCY_WINDOW=8
BURN_IN=8


def y1k_recent(region,b,mask,t0):
    """RegionK Y1k union with aged edges opened: (sorted tuple, unknowns). t0 = first transition index that is recent."""
    if region._sat is not True:return None,int(region._sat is None)
    n=region.n;v=region._v;out=[];u=0;C=[]
    TrR=[v() for _ in range(n)]
    for j in range(n):
        xs=[region.x[t][j] for t in range(t0,region.T) if region.actions[t]==b]
        for x in xs:C.append([-x,TrR[j]])
        C.append([-TrR[j]]+xs)
    region._add(C)
    for c in range(region.m):
        g=v();C=[];P=[v() for _ in range(n)]
        C.append([-g]+P)
        for a_,b_ in combinations(P,2):C.append([-g,-a_,-b_])
        for q in range(n):
            C.append([-P[q],region.V[q]])
            C.append([-P[q]]+[region.A[q][cc] for cc in range(region.m) if mask>>cc&1])
        K1=[v() for _ in range(n)];K2=[v() for _ in range(n)];K3=[v() for _ in range(n)];W=[v() for _ in range(n)]
        for j in range(n):
            C.append([-P[j],K1[j],K2[j],K3[j]])
            C.append([-K1[j],region.Tr[j][b]])
            for r in range(n):C.append([-K1[j],-region.d[j][b][r],region.A[r][c]])
            C.append([-K2[j],-region.Tr[j][b]]);C.append([-K2[j],region.x[region.T][j]])
            C.append([-K2[j]]+W+[-x for x in region.V])
            C.append([-W[j],region.V[j]]);C.append([-W[j],region.A[j][c]])
            C.append([-K3[j],region.Tr[j][b]]);C.append([-K3[j],-TrR[j]])   # aged edge: open to every code
        region._add(C)
        r=region._solve([g])
        if r is None:u+=1
        if r is not False:out.append(c)
        region._add([[-g]])
    return tuple(out),u


class _DriftRule:
    """Mixin: event bookkeeping and the RO / CT decision. Needs self.support (RegionSpace), self.steps, self.tau."""
    def _init_rule(self,rule,surprise_fraction,recency_window,burn_in):
        if rule not in RULES:raise ValueError('rule must be RO or CT')
        self.rule=rule;self.surprise_fraction=surprise_fraction;self.recency_window=recency_window;self.burn_in=burn_in
        self.drift_events=[]

    def _event_threshold(self):return None if self.tau is None else self.tau*self.surprise_fraction

    def _note_event(self,window_event):
        th=self._event_threshold()
        if window_event or (th is not None and self.residual is not None and self.residual>th):self.drift_events.append(self.steps)

    def _recent_y1k(self,action,mask,t0):
        sp=self.support
        if sp.status!='supported':return None
        return sp._q(('y1kR',action,mask,t0),lambda:y1k_recent(sp.region,action,mask,t0))

    def _rule_decide(self,action,mask,cert):
        """(keep certificate?, cert_rule)."""
        t=self.steps;ev=self.drift_events
        if self.rule=='RO':
            ss=ev[-1] if ev else None
            if ss is not None and t-ss<self.recency_window:y=self._recent_y1k(action,mask,max(0,ss-1));path='Y1k-recent'
            else:y=self.support.y1k(action,mask);path='Y1k'
            return (True,path) if y==(cert,) else (False,'downgraded')
        if self.support.y1k(action,mask)==(cert,):return True,'Y1k'
        if not ev and t>=self.burn_in:return True,'tracked-calm'
        return False,'downgraded'

    def _rule_diag(self):
        return {'rule':self.rule,'surprise_fraction':self.surprise_fraction,'recency_window':self.recency_window,
                'burn_in':self.burn_in,'drift_events':list(self.drift_events)}


@dataclass(frozen=True)
class DriftForecast(RegionForecast):
    cert_rule:Optional[str]=None


class DriftSoundLearner(_DriftRule,RegionBruteLearner):
    """R6 (rule='RO') / C6 (rule='CT') on 2x2 worlds. RegionBruteLearner constructor plus rule constants."""
    def __init__(self,*args,rule='RO',surprise_fraction=SURPRISE_FRACTION,recency_window=RECENCY_WINDOW,burn_in=BURN_IN,**kwargs):
        super().__init__(*args,**kwargs)
        if self.policy!='LU-R':raise ValueError('R6/C6 use LU-R')
        self._init_rule(rule,surprise_fraction,recency_window,burn_in)

    def observe(self,action,obs):
        r0=self.window_restarts
        s=super().observe(action,obs)
        self._note_event(self.window_restarts>r0)
        return s

    def predict(self,action):
        for x in self._spaces():x.unk=0
        f=FallbackBruteLearner.predict(self,action);path=None
        if f.certificate is not None:
            keep,path=self._rule_decide(action,mask_for_observation(self.support.evidence[-1][1]),f.certificate)
            if not keep:f=replace(f,status=Status.ABSTAIN,reason=Reason030.RESYNC_AMBIGUOUS,certificate=None,public_certificate=None,public_reason=None)
        unk=sum(x.unk for x in self._spaces())
        if unk and f.status!=Status.OUT_OF_FAMILY:
            f=replace(f,status=Status.ABSTAIN,reason=Reason050.SOLVER_BUDGET,certificate=None,public_certificate=None,public_reason=None)
        if unk:self.forecasts_with_unknown+=1
        return DriftForecast(**{k:getattr(f,k) for k in f.__dataclass_fields__ if k!='solver_unknown'},solver_unknown=unk,cert_rule=path)

    def retry(self,family_states=None,max_prefixes=None):
        fs=family_states or self.family_states
        new=type(self)(fs,max(self.margin_states,fs+1),max_prefixes or self.support.max_prefixes,self.margin.max_prefixes,
                       self.smoothing,self.epsilon,self.window,self.tau,None,resume=self.resume,conf_budget=self.conf_budget,
                       policy=self.policy,rule=self.rule,surprise_fraction=self.surprise_fraction,
                       recency_window=self.recency_window,burn_in=self.burn_in)
        ev=self.support.evidence;new.initialize(ev[0][1])
        for a,obs in ev[1:]:new.observe(a,obs)
        return new

    def diagnostics(self):
        d=super().diagnostics();d.update(self._rule_diag());return d


@dataclass(frozen=True)
class BreadthDriftForecast(BreadthForecast):
    cert_rule:Optional[str]=None


class BreadthDriftLearner(_DriftRule,BreadthBruteLearner):
    """BR6 (rule='RO') / BC6 (rule='CT') on breadth worlds (tau = tau7)."""
    def __init__(self,*args,rule='RO',surprise_fraction=SURPRISE_FRACTION,recency_window=RECENCY_WINDOW,burn_in=BURN_IN,**kwargs):
        super().__init__(*args,**kwargs)
        if self.policy!='LU-R':raise ValueError('BR6/BC6 use LU-R')
        self._init_rule(rule,surprise_fraction,recency_window,burn_in)

    def observe(self,action,obs):
        c0=self.contradiction_step
        s=super().observe(action,obs)
        self._note_event(c0 is None and self.contradiction_step is not None)
        return s

    def predict(self,action):
        if not self.initialized:raise ValueError('initialize first')
        self._check_action(action);self.support.unk=0;self.margin.unk=0
        sup=self.support.predict_support(action);msup=self.margin.predict_support(action);sat=self.support.saturated()
        status,reason,cert=self._decide(sup,msup,sat)
        if cert is not None and cert not in sup:status,reason,cert=Status.ERROR,Reason.INTERNAL,None
        path=None
        if cert is not None:
            keep,path=self._rule_decide(action,codes_mask(self.support.evidence[-1][1],self.s),cert)
            if not keep:status,reason,cert=Status.ABSTAIN,Reason030.RESYNC_AMBIGUOUS,None
        unk=self.support.unk+self.margin.unk
        if unk and status!=Status.OUT_OF_FAMILY:status,reason,cert=Status.ABSTAIN,Reason050.SOLVER_BUDGET,None
        if unk:self.forecasts_with_unknown+=1
        probs,src=self._probabilities(sup,msup)
        public=cert if (cert is not None and self.attestation_valid()) else None
        return BreadthDriftForecast(action,status,reason,cert,public,sup,msup,sat,probs,src,unk,self.family,self.residual,cert_rule=path)

    def diagnostics(self):
        d=super().diagnostics();d.update(self._rule_diag());return d
