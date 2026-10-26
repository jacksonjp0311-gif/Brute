"""Brute v0.11.0 SOUND TRANSFER (BRUTE_PLAN_013 transfer_definition). New file; brute/transfer.py is imported unchanged.

GatedTransfer (one target trajectory, learner-visible data only), modes:
  TR  (M = 0)  the frozen v0.10.0 rule: SP8 certificate, else after burn-in a unanimous surviving library prediction
               inside the SP8 published support.
  AT  (M = 6) / AT4 (M = 4)  applicability test: as TR, but the library may license a certificate only after M
               confirmed informative predictions (library unanimous on the TAKEN action's next code, SP8 support for it
               has >= 2 codes, the observation is fully unmasked and equals the prediction), counted on earlier steps.
  DR           dual region: keep an SP8 certificate c only if the library is refuted or forces c as well; never adds a
               certificate (Exact: DR certificates are a subset of SP8 certificates).
lx_choose: library experiment selection (LX). The library picks the action; certification stays SP8's own.
Not a default: the release default stays the v0.5.0 rule (Y1k, LU-R).
"""
from __future__ import annotations
from brute.transfer import TransferTracker

MODES={'TR':0,'AT':6,'AT4':4,'DR':None}
CENSOR=45


def _code(obs):return obs[0]*2+obs[1]


class GatedTransfer:
    def __init__(self,hypotheses,initial_obs,burn_in,mode):
        if mode not in MODES:raise ValueError(mode)
        self.mode=mode;self.M=MODES[mode];self.tracker=TransferTracker(hypotheses,initial_obs,burn_in);self.confirmations=0

    def decide(self,step,b,sp8_certificate,sp8_support):
        """(certificate, rule) for action b at this step (before observing it)."""
        tr=self.tracker;p=tr.predict(b)
        if self.mode=='DR':
            if sp8_certificate is None:return None,None
            if not tr.alive:return sp8_certificate,'dr-refuted'
            if p==sp8_certificate:return sp8_certificate,'dr-both'
            return None,'dr-disagree'
        c,rule=tr.decide(step,b,sp8_certificate,sp8_support)
        if rule=='transfer' and self.confirmations<self.M:return None,'at-blocked'
        return c,rule

    def observe(self,step,action,obs,sp8_support_taken):
        p=self.tracker.predict(action)
        if p is not None and sp8_support_taken is not None and len(sp8_support_taken)>=2 and None not in obs and _code(obs)==p:
            self.confirmations+=1
        self.tracker.observe(step,action,obs)


def code_groups(tracker,b):
    out={}
    for T,E,s in tracker.alive:c=E[T[s][b]];out[c]=out.get(c,0)+1
    return out


def lx_choose(tracker,sp8_action,lookahead):
    """(action, rule, v, largest_group[2], prediction[2]). lookahead(b, code) -> SP8 LU-C branch value."""
    n=len(tracker.alive);big=[max(g.values()) if g else 0 for g in (code_groups(tracker,0),code_groups(tracker,1))]
    pred=[tracker.predict(0),tracker.predict(1)]
    if n>=2 and min(big)<n:
        mins=[b for b in (0,1) if big[b]==min(big)];return (sp8_action if sp8_action in mins else mins[0]),'lx-split',None,big,pred
    if n>=1:
        v=[lookahead(b,pred[b]) for b in (0,1)]
        if v[0]!=v[1]:return (0 if v[0]>v[1] else 1),'lx-plan',v,big,pred
        return sp8_action,'sp8',v,big,pred
    return sp8_action,'sp8',None,big,pred
