"""Brute v0.2.0 learner: active experimentation (X1), window rebuild (X2), issuance de-duplication (X3).

Pre-registered in experiments/BRUTE_PLAN_004.json (experiment_rule, window_tier, G9). New file; the frozen
v0.1.0 core (brute/core/learner.py) and v0.1.1 learner (brute/fallback.py) are subclassed, not edited.

Certification is unchanged: predict() is the v0.1.0 gate order with v0.1.1 fallback probabilities. The only
probability change is the window_n4 tier, which replaces suffix1 (and only suffix1) after a contradiction when a
fresh <=4 learner, restarted at each contradiction, is still supported: p=(1-eps)*suffix1|S renormalized+eps/4.

experiment(default_action) chooses the next action by a one-step certifiability lookahead (rule LU):
  score(a) = mean over c in S4(a) of N(a,c), N(a,c) = #{b : b would be CERTIFIED after observing c fully under a}
on copies of the family and margin beliefs. Ties go to default_action. Geometrically (Inferred): pick the cut most
likely to collapse the version space's projection on a queried coordinate to one point.
"""
from __future__ import annotations
from bgr90.symbolic import SymbolicLearner,BudgetExceeded,GrammarContradiction,ALL
from brute.fallback import FallbackBruteLearner,FallbackForecast

FORECAST_SOURCES=('v090','margin_n5','suffix1','window_n4','uniform')
EXPERIMENT_RULE='LU: one-step certifiability lookahead, uniform over the <=4 family support'
TIE_BREAK='default_action'
WINDOW_STATES=4
WINDOW_MAX_PREFIXES=160000


def _copy_update(learner,action,code):
    """Copy of `learner` after (action, full observation `code`); None if contradicted or over budget."""
    if learner.status!='supported':return None,0
    n=SymbolicLearner(learner.max_states,learner.max_prefixes);n.status='supported';n.belief=learner.belief;n.evidence=[None]
    try:n._update(action,1<<code)
    except (BudgetExceeded,GrammarContradiction) as exc:
        return None,(1 if isinstance(exc,BudgetExceeded) else 0)
    return n,0


def _row_codes(p,action,cap):
    d=p.trans[p.current*2+action]
    if d>=0:return p.masks[d],False
    u=0
    for j in range(p.used):u|=p.masks[j]
    if p.used<cap:u|=ALL
    return u,True


class ActiveBruteLearner(FallbackBruteLearner):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.window_learner=None;self.window_restarts=0;self.window_peak_rows=0
        self.lookahead_peak_rows=0;self.lookahead_budget_hits=0;self.lookahead_copies=0

    # -- X3 ------------------------------------------------------------------
    def record_issued(self,forecast):
        """Mark a certified forecast as acted on, at most once per (step, certificate)."""
        if forecast.certificate is None:return
        key=(self.steps+1,forecast.certificate)
        if key not in self.issued:self.issued.append(key)

    # -- X2 ------------------------------------------------------------------
    def _window_start(self,obs):
        self.window_learner=SymbolicLearner(WINDOW_STATES,WINDOW_MAX_PREFIXES)
        self.window_learner.initialize(obs);self.window_restarts+=1
        self.window_peak_rows=max(self.window_peak_rows,1)

    def _fallback(self,action,margin_support):
        probs,source,ablation=super()._fallback(action,margin_support)
        if source!='suffix1':return probs,source,ablation
        W=self.window_learner
        s=W.predict_support(action) if W is not None and W.status=='supported' else None
        if not s:return probs,source,ablation
        q=self.suffix.predict(action);z=sum(q[c] for c in s);e=self.epsilon
        p=tuple((1-e)*(q[c]/z if c in s else 0.)+e/4 for c in range(4))
        return p,'window_n4',ablation

    def observe(self,action,obs):
        was=self.support.status
        s=super().observe(action,obs)
        if self.support.status=='grammar_contradicted':
            if was=='supported':self._window_start(obs)
            elif self.window_learner is not None:
                self.window_learner.observe(action,obs)
                if self.window_learner.status!='supported':self._window_start(obs)
                else:self.window_peak_rows=max(self.window_peak_rows,self.window_learner.max_rows_seen)
        return s

    # -- X1 ------------------------------------------------------------------
    def _certifiable_after(self,action,code):
        fam,hit=_copy_update(self.support,action,code);self.lookahead_budget_hits+=hit;self.lookahead_copies+=1
        if fam is None:return 0
        self.lookahead_peak_rows=max(self.lookahead_peak_rows,fam.count)
        if all(p.used==fam.max_states for p in fam.belief):return 0
        singles={b:fam.predict_support(b) for b in (0,1)}
        singles={b:s for b,s in singles.items() if s and len(s)==1}
        if not singles:return 0
        mar,hit=_copy_update(self.margin,action,code);self.lookahead_budget_hits+=hit;self.lookahead_copies+=1
        if mar is None:return 0
        self.lookahead_peak_rows=max(self.lookahead_peak_rows,mar.count)
        return sum(mar.predict_support(b)==s for b,s in singles.items())

    def experiment_score(self,action):
        if action not in (0,1):raise ValueError('action must be 0 or 1')
        if self.support.status!='supported' or self.margin.status!='supported' or self.alarm_step is not None:return 0.
        S=self.support.predict_support(action)
        return round(sum(self._certifiable_after(action,c) for c in S)/len(S),12)

    def action_counts(self,action):
        """Per-action disagreement counts: how many <=4 rows admit each next code, and how many leave the edge open."""
        if self.support.status!='supported':return None
        rows=[0]*4;open_rows=0
        for p in self.support.belief:
            m,op=_row_codes(p,action,self.support.max_states);open_rows+=op
            for c in range(4):rows[c]+=m>>c&1
        return {'family_code_rows':rows,'family_open_rows':open_rows,'family_rows':self.support.count,
                'margin_rows':self.margin.count if self.margin.status=='supported' else None}

    def experiment(self,default_action,counts=False):
        if not self.initialized:raise ValueError('initialize first')
        if default_action not in (0,1):raise ValueError('action must be 0 or 1')
        scores=[self.experiment_score(a) for a in (0,1)]
        a=default_action if scores[0]==scores[1] else (0 if scores[0]>scores[1] else 1)
        out={'action':a,'score':scores[a],'scores':scores,'rule':EXPERIMENT_RULE,'tie_break':TIE_BREAK,
             'tied':scores[0]==scores[1]}
        if counts:out['per_action']=[self.action_counts(b) for b in (0,1)]
        return out

    def retry(self,family_states=None,max_prefixes=None):
        """Replay all evidence under a new bound with the v0.2.0 learner. Attestation never carries over."""
        new=ActiveBruteLearner(family_states or self.family_states,
                               max(self.margin_states,(family_states or self.family_states)+1),
                               max_prefixes or self.support.max_prefixes,self.margin.max_prefixes,
                               self.smoothing,self.epsilon,self.window,self.tau,None)
        ev=self.support.evidence
        new.initialize(ev[0][1])
        for a,obs in ev[1:]:new.observe(a,obs)
        return new

    def diagnostics(self):
        d=super().diagnostics()
        d.update({'window_restarts':self.window_restarts,'window_peak_rows':self.window_peak_rows,
                  'lookahead_peak_rows':self.lookahead_peak_rows,'lookahead_budget_hits':self.lookahead_budget_hits,
                  'lookahead_copies':self.lookahead_copies})
        return d
