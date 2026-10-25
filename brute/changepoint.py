"""Brute v0.3.0 learner: resynchronization-robust certification (Y1k) and the LU-R lookahead.

Pre-registered in experiments/BRUTE_PLAN_005.json (certification_rule, experiment_rule). New file; brute/core/*,
brute/fallback.py and brute/active.py (v0.2.0) are subclassed, not edited.

Y1k (certification). The v0.1.0 gate order is kept and one test is added after it. A CERTIFIED forecast with code x
for action b stays certified only if, for every surviving <=4 row p and every visited state j of p whose emission set
meets the latest observation mask m, the successor emission of (j, b) is x. A known edge contributes its target's
emission set; an unknown edge counts as open (every visited emission, plus all codes if the row can still grow) only
at the row's current state and is skipped elsewhere. Otherwise: ABSTAIN / RESYNC_AMBIGUOUS. Geometrically (Inferred):
the certificate must be constant on the fibre of the version space over the latest observation, so an unseen jump at
the latest step cannot leave a stale certificate. Probabilities are unchanged, so surprise, alarms and tau are too.

LU-R (policy). The v0.2.0 LU lookahead with the Y1k test applied to the copied family (m = the full observation c).
Optional CHECK_RUN k (0 for v0.3.0; 3 for the study-005 mechanism arm E2): when the family and margin are supported
with no alarm and the choice equals each of the last k taken actions, the other action is taken (check=True).
"""
from __future__ import annotations
from dataclasses import replace
from enum import Enum
from bgr90.symbolic import ALL,mask_for_observation
from brute.core.learner import Status
from brute.active import ActiveBruteLearner,_copy_update

RESYNC_RULE='Y1k: certificate constant over every visited state consistent with the latest observation in every <=4 row (known edges; open edge only at the current state)'
EXPERIMENT_RULE_030='LU-R: one-step certifiability lookahead scored with the Y1k test'
CHECK_RULE='untaken-branch check after CHECK_RUN equal taken actions'


class Reason030(str,Enum):
    RESYNC_AMBIGUOUS='RESYNC_AMBIGUOUS'


def resync_support(learner,action,mask):
    """Y1k union of successor codes for `action` over the fibre of `learner` (a SymbolicLearner) over `mask`.

    Returns a sorted tuple of codes, or None if the learner is not supported."""
    if learner.status!='supported':return None
    union=0
    for p in learner.belief:
        for j in range(p.used):
            if not p.masks[j]&mask:continue
            d=p.trans[j*2+action]
            if d>=0:union|=p.masks[d]
            elif j==p.current:
                for k in range(p.used):union|=p.masks[k]
                if p.used<learner.max_states:union|=ALL
            if union==ALL:return (0,1,2,3)
    return tuple(c for c in range(4) if union>>c&1)


class ChangePointBruteLearner(ActiveBruteLearner):
    """v0.3.0: Y1k certification + LU-R. `resync=False` gives v0.2.0 certification (used by the E2 arm)."""
    resync=True
    check_run=0

    def __init__(self,*args,resync=None,check_run=None,**kwargs):
        super().__init__(*args,**kwargs)
        if resync is not None:self.resync=bool(resync)
        if check_run is not None:self.check_run=int(check_run)

    def _last_mask(self):return mask_for_observation(self.support.evidence[-1][1])

    def predict(self,action):
        f=super().predict(action)
        if self.resync and f.certificate is not None and resync_support(self.support,action,self._last_mask())!=(f.certificate,):
            return replace(f,status=Status.ABSTAIN,reason=Reason030.RESYNC_AMBIGUOUS,certificate=None,
                           public_certificate=None,public_reason=None)
        return f

    def _certifiable_after(self,action,code):
        if not self.resync:return super()._certifiable_after(action,code)
        fam,hit=_copy_update(self.support,action,code);self.lookahead_budget_hits+=hit;self.lookahead_copies+=1
        if fam is None:return 0
        self.lookahead_peak_rows=max(self.lookahead_peak_rows,fam.count)
        if all(p.used==fam.max_states for p in fam.belief):return 0
        singles={b:fam.predict_support(b) for b in (0,1)}
        singles={b:s for b,s in singles.items() if s and len(s)==1 and resync_support(fam,b,1<<code)==s}
        if not singles:return 0
        mar,hit=_copy_update(self.margin,action,code);self.lookahead_budget_hits+=hit;self.lookahead_copies+=1
        if mar is None:return 0
        self.lookahead_peak_rows=max(self.lookahead_peak_rows,mar.count)
        return sum(mar.predict_support(b)==s for b,s in singles.items())

    def proposal(self):
        """('PROPOSED', None) or ('NO_PROPOSAL', 'OUT_OF_SCOPE' | 'RESIDUAL_ALARM') (brute.api/1.3)."""
        if self.support.status!='supported' or self.margin.status!='supported':return 'NO_PROPOSAL','OUT_OF_SCOPE'
        if self.alarm_step is not None:return 'NO_PROPOSAL','RESIDUAL_ALARM'
        return 'PROPOSED',None

    def experiment(self,default_action,counts=False):
        """Read-only: the chosen action and scores; check=True when the untaken-branch check overrode the choice."""
        out=super().experiment(default_action,counts)
        if self.resync:out['rule']=EXPERIMENT_RULE_030
        out['check']=False
        k=self.check_run
        if k and self.support.status=='supported' and self.margin.status=='supported' and self.alarm_step is None:
            past=[a for a,_ in self.support.evidence[1:]][-k:]
            if len(past)==k and all(a==out['action'] for a in past):
                b=1-out['action'];out.update(action=b,score=out['scores'][b],check=True)
        out['proposal'],out['no_proposal_reason']=self.proposal()
        return out

    def retry(self,family_states=None,max_prefixes=None):
        """Replay all evidence under a new bound with the same learner class and settings. Attestation never carries over."""
        new=type(self)(family_states or self.family_states,max(self.margin_states,(family_states or self.family_states)+1),
                       max_prefixes or self.support.max_prefixes,self.margin.max_prefixes,
                       self.smoothing,self.epsilon,self.window,self.tau,None,resync=self.resync,check_run=self.check_run)
        ev=self.support.evidence;new.initialize(ev[0][1])
        for a,obs in ev[1:]:new.observe(a,obs)
        return new

    def diagnostics(self):
        d=super().diagnostics();d.update({'resync':self.resync,'check_run':self.check_run});return d
