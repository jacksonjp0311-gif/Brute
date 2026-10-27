"""Brute v0.14.0 embeddable certify interface, version 4 (BRUTE_PLAN_016 api_definition). New file; brute/api/certify.py,
certify2.py, certify3.py and every other brute/api file untouched.

Certifier4 = brute.certify/3 (Certifier3: query / observe / close unchanged, certification RG4 or DLF margin 1) plus a
deferred suggestion: suggest_action(default_action=0, deferred=True) returns the RSXL action
(brute.deferredsplit.rsxl_choose): the frozen SP8 LU-R choice until RG4 has certified the action actually taken at some
earlier step, the RSX region-split choice afterwards. deferred=False gives the plain brute.certify/3 RSX suggestion.
certified_before is tracked by observe(): before each step is applied, RG4's certificate for the observed action is
computed (frozen brute.boundedtransfer.rg_decide on the SP8 certificate / support and the RegionSpace(4) support).

    c = Certifier4(); c.initialize((0, 1)); c.suggest_action() -> {'api': 'brute.certify/4', 'action': 0 | 1,
        'rule': 'sp8' | 'rsx', 'deferred': bool, 'certified_before': bool, 'bounded_sizes': [k_0, k_1], 'step': int}
    'deferred' is True when the deferral is in force at this step (deferred=True and not certified_before).
    c.query(b) -> the brute.certify/3 dict with 'api': 'brute.certify/4'

The suggestion never changes what is certified; acting on it changes which evidence arrives. Host-agnostic: no I/O,
network, threads, subprocesses or global state. A certificate is a claim about the declared family (deterministic Moore,
<= 4 states, stationary, 2 actions, 2 bits) attested by the caller; outside it the answer means nothing.
"""
from __future__ import annotations
from brute.api.certify import _act,_obs
from brute.api.certify2 import BURN_IN,REASONS
from brute.api.certify3 import Certifier3
from brute.boundedtransfer import FB,region_supports,rg_decide
from brute.regionsplit import bounded_sizes
from brute.deferredsplit import rsxl_choose

API='brute.certify/4'
__all__=['API','REASONS','Certifier4','certify4','suggest4']


class Certifier4(Certifier3):
    def __init__(self,library=None,margin=1):
        super().__init__(library=library,margin=margin);self.certified_before=False

    def query(self,action):
        q=super().query(action);q['api']=API;return q

    def _rg4(self,b):
        q=self._sp8.query(b);fb=region_supports(self._R[FB])[b][0]
        return rg_decide(self.step+1,BURN_IN,q['answer'],q['support'],fb)[0]

    def suggest_action(self,default_action=0,deferred=True):
        if self.step is None:raise ValueError('initialize first')
        if not isinstance(deferred,bool):raise ValueError('deferred must be a bool')
        d=_act(default_action);sp=self._sp8._L.experiment(d)['action'];sizes=bounded_sizes(region_supports(self._R[FB]))
        cb=self.certified_before if deferred else True
        a,rule=rsxl_choose(self.step+1,BURN_IN,sizes,sp,cb)
        return {'api':API,'action':a,'rule':rule,'deferred':not cb,'certified_before':self.certified_before,
                'bounded_sizes':sizes,'step':self.step}

    def observe(self,action,observation):
        if self.step is None:raise ValueError('initialize first')
        a=_act(action);_obs(observation)
        if not self.certified_before and self._rg4(a) is not None:self.certified_before=True
        return super().observe(a,observation)


def _replay(observations,actions,library):
    observations=list(observations);actions=list(actions)
    if len(observations)!=len(actions)+1:raise ValueError('need len(observations) == len(actions) + 1')
    c=Certifier4(library=library).initialize(observations[0])
    try:
        for a,o in zip(actions,observations[1:]):c.observe(a,o)
    except Exception:
        c.close();raise
    return c


def certify4(observations,actions,query_action,library=None):
    """Stateless: observations[0] is the initial observation; len(observations) == len(actions) + 1."""
    c=_replay(observations,actions,library)
    try:return c.query(query_action)
    finally:c.close()


def suggest4(observations,actions,certified_before=None,default_action=0):
    """Stateless RSXL suggestion after the given history. certified_before=None derives it from the history (RG4 on the
    taken actions); a bool overrides it (a host that tracks its own certificates)."""
    if certified_before is not None and not isinstance(certified_before,bool):raise ValueError('certified_before must be None or a bool')
    c=_replay(observations,actions,None)
    try:
        if certified_before is not None:c.certified_before=certified_before
        return c.suggest_action(default_action,True)
    finally:c.close()
