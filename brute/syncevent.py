"""Brute v0.7.0 synchronous-event certification candidates (arms S7 / SC7 on 2x2, BS7 / BSC7 on breadth).

Pre-registered in experiments/BRUTE_PLAN_009.json (arms, event_triggers, rule_constants_frozen). New file: the frozen
v0.6.0 learners (brute/driftsound.py) and everything below them are subclassed, never edited or monkeypatched. Not a
default: the release default stays the v0.5.0 rule (Y1k, LU-R) whatever the outcome.

Implementation reading of the plan text, fixed here before any v0.7.0 run (the second implementation
experiments/v070_reference.py, committed earlier, implements the same reading):

* EVENTS. Step u is an event iff, after observing u, any of
  E1  the frozen v0.6.0 event (_DriftRule._note_event: residual > tau/2, or the window-tier / contradiction event);
  E2  the published forecast for the taken action at u (the forecast the frozen observe() computes first, captured
      here, not recomputed) carried a certificate c and bit c is not in the observation mask;
  E3  the surprise s_u returned by the frozen observe() is > tau (tau6 on 2x2, tau7 on breadth).
  Event steps go to drift_events (as v0.6.0, so the frozen recency machinery reads them unchanged); the triggers that
  fired are recorded in diagnostics()['event_triggers'] as [step, ['E1'|'E2'|'E3', ...]].
* rule 'RO' (S7 / BS7): the frozen R6 decision with the extended event set.
* rule 'CTR' (SC7 / BSC7): built on the frozen rule='CT' learner; the decision is: if the latest event s* has
  t - s* < W: Y1k-recent with t0 = max(0, s*-1) ('Y1k-recent'); else Y1k union {c} ('Y1k'); else the pre-Y1k
  certificate is kept iff t >= burn_in ('tracked-calm'); else ABSTAIN / RESYNC_AMBIGUOUS ('downgraded').
* alarms, resume, probabilities, LU-R and the SOLVER_BUDGET overlay are the frozen code paths.
"""
from __future__ import annotations
from bgr90.symbolic import mask_for_observation
from brute.region import codes_mask
from brute.driftsound import DriftSoundLearner,BreadthDriftLearner,SURPRISE_FRACTION,RECENCY_WINDOW,BURN_IN

RULES_009=('RO','CTR')


class _SyncEvents:
    """Mixin over a frozen _DriftRule learner: forecast capture, E2/E3 events, the CTR decision."""
    def _init_sync(self,rule):
        if rule not in RULES_009:raise ValueError('rule must be RO or CTR')
        self.rule=rule;self.event_triggers=[];self._capture=False;self._captured=None

    def predict(self,action):
        f=super().predict(action)
        if self._capture and self._captured is None:self._captured=f
        return f

    def _sync_observe(self,action,obs,mask):
        n0=len(self.drift_events);self._capture=True;self._captured=None
        try:s=super().observe(action,obs)
        finally:self._capture=False
        f=self._captured;self._captured=None;fired=[]
        if len(self.drift_events)>n0:fired.append('E1')
        if f is not None and f.certificate is not None and not (mask>>f.certificate&1):fired.append('E2')
        if self.tau is not None and s>self.tau:fired.append('E3')
        if fired:
            if 'E1' not in fired:self.drift_events.append(self.steps)
            self.event_triggers.append([self.steps,fired])
        return s

    def _rule_decide(self,action,mask,cert):
        if self.rule!='CTR':return super()._rule_decide(action,mask,cert)
        t=self.steps;ev=self.drift_events;ss=ev[-1] if ev else None
        if ss is not None and t-ss<self.recency_window:
            return (True,'Y1k-recent') if self._recent_y1k(action,mask,max(0,ss-1))==(cert,) else (False,'downgraded')
        if self.support.y1k(action,mask)==(cert,):return True,'Y1k'
        if t>=self.burn_in:return True,'tracked-calm'
        return False,'downgraded'

    def diagnostics(self):
        d=super().diagnostics();d['event_triggers']=[list(x) for x in self.event_triggers];return d


class SyncEventLearner(_SyncEvents,DriftSoundLearner):
    """S7 (rule='RO') / SC7 (rule='CTR') on 2x2 worlds."""
    def __init__(self,*args,rule='RO',surprise_fraction=SURPRISE_FRACTION,recency_window=RECENCY_WINDOW,burn_in=BURN_IN,**kwargs):
        if rule not in RULES_009:raise ValueError('rule must be RO or CTR')
        super().__init__(*args,rule='RO' if rule=='RO' else 'CT',surprise_fraction=surprise_fraction,
                         recency_window=recency_window,burn_in=burn_in,**kwargs)
        self._init_sync(rule)

    def observe(self,action,obs):
        return self._sync_observe(action,obs,mask_for_observation(obs))


class BreadthSyncEventLearner(_SyncEvents,BreadthDriftLearner):
    """BS7 (rule='RO') / BSC7 (rule='CTR') on breadth worlds (tau = tau7)."""
    def __init__(self,*args,rule='RO',surprise_fraction=SURPRISE_FRACTION,recency_window=RECENCY_WINDOW,burn_in=BURN_IN,**kwargs):
        if rule not in RULES_009:raise ValueError('rule must be RO or CTR')
        super().__init__(*args,rule='RO' if rule=='RO' else 'CT',surprise_fraction=surprise_fraction,
                         recency_window=recency_window,burn_in=burn_in,**kwargs)
        self._init_sync(rule)

    def observe(self,action,obs):
        return self._sync_observe(action,obs,codes_mask(obs,self.s))
