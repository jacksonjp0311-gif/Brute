"""Brute v0.15.0 embeddable certify interface, version 5 (BRUTE_PLAN_017 api_definition). New file; brute/api/certify.py
... certify4.py and every other brute/api file untouched.

Certifier5 = brute.certify/4 (Certifier4: query / observe / close unchanged, certification RG4 or DLF margin 1) plus a
lookahead suggestion: suggest_action(rule='rglx') returns the RGLX action (brute.boundedlookahead.rglx_choose): the RGL
one-step lookahead choice on the RegionSpace(4) region while RG4 has not certified the action actually taken at an
earlier step, the RSX region-split choice afterwards. rule='rgl' uses RGL throughout; rule='rsxl' / 'rsx' return the
brute.certify/4 deferred / plain suggestions re-labelled brute.certify/5.

    c = Certifier5(); c.initialize((0, 1)); c.suggest_action() -> {'api': 'brute.certify/5', 'action': 0 | 1,
        'rule': 'rgl' | 'rsx' | 'sp8', 'lookahead_score': float | None, 'lookahead': None | {'num', 'den', 'unknown'},
        'certified_before': bool, 'bounded_sizes': [k_0, k_1], 'step': int}
    lookahead_score is the chosen action's num / den when the lookahead was computed this step, else None.
    c.query(b) -> the brute.certify/4 dict with 'api': 'brute.certify/5'

family_bound: only 4 is supported in v0.15.0 (the declared family); any other value raises ValueError. The suggestion
never changes what is certified; acting on it changes which evidence arrives. The lookahead score is a heuristic, not a
probability. Host-agnostic: no I/O, network, threads, subprocesses or global state. A certificate is a claim about the
declared family (deterministic Moore, <= 4 states, stationary, 2 actions, 2 bits) attested by the caller; outside it the
answer means nothing.
"""
from __future__ import annotations
from brute.api.certify import _act,_obs
from brute.api.certify2 import BURN_IN,REASONS
from brute.api.certify4 import Certifier4
from brute.boundedtransfer import FB,region_supports
from brute.regionsplit import bounded_sizes
from brute.boundedlookahead import lookahead,rgl_choose,rglx_choose,needs_lookahead,score

API='brute.certify/5'
SUGGEST_RULES=('rglx','rgl','rsxl','rsx')
__all__=['API','REASONS','SUGGEST_RULES','Certifier5','certify5','suggest5']


class Certifier5(Certifier4):
    def __init__(self,library=None,margin=1,family_bound=4):
        if isinstance(family_bound,bool) or family_bound!=FB:raise ValueError('family_bound must be 4 in brute.certify/5')
        super().__init__(library=library,margin=margin);self.family_bound=family_bound

    def query(self,action):
        q=super().query(action);q['api']=API;return q

    def suggest_action(self,default_action=0,rule='rglx'):
        if self.step is None:raise ValueError('initialize first')
        if rule not in SUGGEST_RULES:raise ValueError(f'rule must be one of {SUGGEST_RULES}')
        if rule in ('rsxl','rsx'):
            s=Certifier4.suggest_action(self,default_action,rule=='rsxl');s['api']=API;s['lookahead_score']=None;s['lookahead']=None
            return s
        d=_act(default_action);sp=self._sp8._L.experiment(d)['action'];R=self._R[FB];rs=region_supports(R);sizes=bounded_sizes(rs)
        t=self.step+1;look=lookahead(R,rs) if needs_lookahead(t,BURN_IN,self.certified_before,rule) else None
        if rule=='rgl':a,r=rgl_choose(t,BURN_IN,look,sp)
        else:a,r=rglx_choose(t,BURN_IN,sizes,look,sp,self.certified_before)
        return {'api':API,'action':a,'rule':r,'lookahead_score':float(score(look,a)) if look is not None else None,'lookahead':look,
                'certified_before':self.certified_before,'bounded_sizes':sizes,'step':self.step}


def _replay(observations,actions,library):
    observations=list(observations);actions=list(actions)
    if len(observations)!=len(actions)+1:raise ValueError('need len(observations) == len(actions) + 1')
    c=Certifier5(library=library).initialize(observations[0])
    try:
        for a,o in zip(actions,observations[1:]):c.observe(a,o)
    except Exception:
        c.close();raise
    return c


def certify5(observations,actions,query_action,library=None):
    """Stateless: observations[0] is the initial observation; len(observations) == len(actions) + 1."""
    c=_replay(observations,actions,library)
    try:return c.query(query_action)
    finally:c.close()


def suggest5(observations,actions,rule='rglx',certified_before=None,default_action=0):
    """Stateless suggestion after the given history. certified_before=None derives it from the history (RG4 on the taken
    actions); a bool overrides it."""
    if certified_before is not None and not isinstance(certified_before,bool):raise ValueError('certified_before must be None or a bool')
    c=_replay(observations,actions,None)
    try:
        if certified_before is not None:c.certified_before=certified_before
        return c.suggest_action(default_action,rule)
    finally:c.close()
