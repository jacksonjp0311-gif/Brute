"""Brute v0.5.0 learner (arms A5 / M5): the v0.4.0 rules with every version-space query on the SAT region.

Pre-registered in experiments/BRUTE_PLAN_007.json (arms A5, M5; backend; experiment_rules). New file: the frozen
v0.1.0-v0.4.0 learners (brute/core/*, fallback.py, active.py, changepoint.py, resume.py) are subclassed, never edited.

RegionBruteLearner = ResumeBruteLearner (Y1k + LU-R + tau6 + resume, v0.1.1 probabilities, v0.2.0 window tier) with the
family (<=4), margin (<=5) and window (<=4) version spaces replaced by brute.region.RegionSpace, the lookahead copies
built with RegionK.extended, and the SOLVER_BUDGET overlay: a forecast that used >=1 UNKNOWN solver answer and is not
OUT_OF_FAMILY becomes ABSTAIN / SOLVER_BUDGET with no certificate. policy='M' adds the projection-volume tie-break.
"""
from __future__ import annotations
from dataclasses import dataclass,replace
from enum import Enum
from math import log2
from bgr90.symbolic import mask_for_observation
from brute.core.learner import Status
from brute.fallback import FallbackBruteLearner,FallbackForecast
from brute.active import WINDOW_STATES,WINDOW_MAX_PREFIXES
from brute.changepoint import Reason030
from brute.resume import ResumeBruteLearner
from brute.region import RegionSpace,PRODUCTION_CONF_BUDGET

BACKEND='sat-region'
POLICIES=('LU-R','M')


class Reason050(str,Enum):
    SOLVER_BUDGET='SOLVER_BUDGET'


@dataclass(frozen=True)
class RegionForecast(FallbackForecast):
    solver_unknown:int=0


class RegionBruteLearner(ResumeBruteLearner):
    """A5 (policy 'LU-R') / M5 (policy 'M'). Same constructor as ResumeBruteLearner plus conf_budget and policy."""
    def __init__(self,*args,conf_budget=PRODUCTION_CONF_BUDGET,policy='LU-R',**kwargs):
        kwargs.setdefault('resync',True);kwargs.setdefault('check_run',0)
        super().__init__(*args,**kwargs)
        if policy not in POLICIES:raise ValueError('policy must be LU-R or M')
        if self.depth!=1 or self.fibre_w!=0 or not self.resync or self.check_run:
            raise ValueError('the region learner implements depth 1, fibre_w 0, Y1k, no check run only')
        self.conf_budget=conf_budget;self.policy=policy
        self.support=RegionSpace(self.family_states,self.support.max_prefixes,conf_budget=conf_budget)
        self.margin=RegionSpace(self.margin_states,self.margin.max_prefixes,conf_budget=conf_budget)
        self.lookahead_unknown_branches=0;self.volume_calls=0;self.forecasts_with_unknown=0

    # ---- version spaces ----------------------------------------------------------------------------------------------
    def _window_start(self,obs):
        if self.window_learner is not None:self.window_learner.close()
        self.window_learner=RegionSpace(WINDOW_STATES,WINDOW_MAX_PREFIXES,conf_budget=self.conf_budget)
        self.window_learner.initialize(obs);self.window_restarts+=1

    def _spaces(self):
        return [x for x in (self.support,self.margin,self.window_learner) if x is not None]

    def saturated(self):
        return self.support.saturated()

    # ---- forecast ----------------------------------------------------------------------------------------------------
    def predict(self,action):
        for x in self._spaces():x.unk=0
        f=FallbackBruteLearner.predict(self,action)   # v0.1.0 gates + v0.1.1/v0.2.0 probabilities on the region
        if f.certificate is not None and self.support.y1k(action,mask_for_observation(self.support.evidence[-1][1]))!=(f.certificate,):
            f=replace(f,status=Status.ABSTAIN,reason=Reason030.RESYNC_AMBIGUOUS,certificate=None,public_certificate=None,public_reason=None)
        unk=sum(x.unk for x in self._spaces())
        if unk and f.status!=Status.OUT_OF_FAMILY:
            f=replace(f,status=Status.ABSTAIN,reason=Reason050.SOLVER_BUDGET,certificate=None,public_certificate=None,public_reason=None)
        if unk:self.forecasts_with_unknown+=1
        return RegionForecast(**{k:getattr(f,k) for k in f.__dataclass_fields__},solver_unknown=unk)

    # ---- lookahead ---------------------------------------------------------------------------------------------------
    def _certifiable_after(self,action,code):
        """LU-R N(a,c) on RegionK copies; any UNKNOWN in the branch makes it 0 (lookahead_budget_hits)."""
        fam=self.support.extended(action,code);self.lookahead_copies+=1;mar=None
        try:
            if fam.feasible is None:self._hit();return 0
            if not fam.feasible:return 0
            sat,u=fam.saturated()
            if u:self._hit();return 0
            if sat:return 0
            singles={}
            for b in (0,1):
                s,u=fam.support(b)
                if u:self._hit();return 0
                if len(s)!=1:continue
                y,u=fam.y1k(b,1<<code)
                if u:self._hit();return 0
                if y==s:singles[b]=s
            if not singles:return 0
            mar=self.margin.extended(action,code);self.lookahead_copies+=1
            if mar.feasible is None:self._hit();return 0
            if not mar.feasible:return 0
            tot=0
            for b,s in singles.items():
                ms,u=mar.support(b)
                if u:self._hit();return 0
                tot+=ms==s
            return tot
        finally:
            fam.close()
            if mar is not None:mar.close()

    def _hit(self):
        self.lookahead_budget_hits+=1;self.lookahead_unknown_branches+=1

    def volume(self,action):
        """M tie-break V(a) = round(mean over c in S_f(a) of sum_b log2 |Y1k_f'(b,{c})|, 12); an infeasible or UNKNOWN
        branch contributes k*log2(m) = 4."""
        self.volume_calls+=1;self.support.unk=0
        S=self.support.predict_support(action);tot=0.
        for c in S:
            f=self.support.extended(action,c)
            try:
                if f.feasible is not True:tot+=2*log2(4);continue
                ys=[f.y1k(b,1<<c) for b in (0,1)]
                if any(u for _,u in ys):tot+=2*log2(4);continue
                tot+=sum(log2(len(y)) for y,_ in ys)
            finally:f.close()
        return round(tot/len(S),12)

    def action_counts(self,action):
        """Row counts do not exist on the region backend (rows are not enumerated)."""
        return None

    def experiment(self,default_action,counts=False):
        out=super().experiment(default_action,counts)
        live=self.support.status=='supported' and self.margin.status=='supported' and self.alarm_step is None
        out['policy']=self.policy;out['volumes']=None
        if self.policy=='M' and live and out['tied']:
            vol=[self.volume(b) for b in (0,1)];out['volumes']=vol
            if vol[0]!=vol[1]:
                a=0 if vol[0]<vol[1] else 1;out.update(action=a,score=out['scores'][a])
        return out

    # ---- bookkeeping -------------------------------------------------------------------------------------------------
    def retry(self,family_states=None,max_prefixes=None):
        """Replay all evidence under a new bound with the same class and settings. Attestation never carries over."""
        fs=family_states or self.family_states
        new=type(self)(fs,max(self.margin_states,fs+1),max_prefixes or self.support.max_prefixes,self.margin.max_prefixes,
                       self.smoothing,self.epsilon,self.window,self.tau,None,resume=self.resume,
                       conf_budget=self.conf_budget,policy=self.policy)
        ev=self.support.evidence;new.initialize(ev[0][1])
        for a,obs in ev[1:]:new.observe(a,obs)
        return new

    def diagnostics(self):
        d=super().diagnostics()
        d.update({'backend':BACKEND,'policy':self.policy,'conf_budget':self.conf_budget,
                  'solver_unknown_total':sum(x.unknown_total for x in (self.support,self.margin))+(self.window_learner.unknown_total if self.window_learner else 0),
                  'forecasts_with_unknown':self.forecasts_with_unknown,'lookahead_unknown_branches':self.lookahead_unknown_branches,
                  'volume_calls':self.volume_calls,'family_peak_clauses':self.support.peak_clauses,
                  'margin_peak_clauses':self.margin.peak_clauses,'family_peak_variables':self.support.peak_vars,
                  'margin_peak_variables':self.margin.peak_vars})
        return d

    def close(self):
        for x in self._spaces():x.close()
