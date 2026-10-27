"""Brute v0.13.0 embeddable certify interface, version 3 (BRUTE_PLAN_015 api_definition). New file; brute/api/certify.py,
certify2.py and every other brute/api file untouched.

Certifier3 = brute.certify/2 (Certifier2: query / observe / close unchanged, certification RG4 or DLF margin 1) plus
suggest_action(default_action=0): the RSX action rule (brute.regionsplit.rsx_choose) on the RegionSpace(4) bounded
supports and the frozen SP8 LU-R experiment choice, where default_action is the host's passive action (SP8's tie-break).

    c = Certifier3(); c.initialize((0, 1)); c.suggest_action() -> {'api': 'brute.certify/3', 'action': 0 | 1,
        'rule': 'rsx' | 'sp8', 'bounded_sizes': [k_0, k_1], 'step': int}
    c.query(b) -> the brute.certify/2 dict with 'api': 'brute.certify/3'

The suggestion never changes what is certified; acting on it changes which evidence arrives. Host-agnostic: no I/O,
network, threads, subprocesses or global state. A certificate is a claim about the declared family (deterministic Moore,
<= 4 states, stationary, 2 actions, 2 bits) attested by the caller; outside it the answer means nothing.
"""
from __future__ import annotations
from brute.api.certify import _act
from brute.api.certify2 import Certifier2,BURN_IN,REASONS
from brute.boundedtransfer import FB,region_supports
from brute.regionsplit import bounded_sizes,rsx_choose

API='brute.certify/3'
__all__=['API','REASONS','Certifier3','certify3','suggest3']


class Certifier3(Certifier2):
    def query(self,action):
        q=super().query(action);q['api']=API;return q

    def suggest_action(self,default_action=0):
        if self.step is None:raise ValueError('initialize first')
        d=_act(default_action);sp=self._sp8._L.experiment(d)['action']
        sizes=bounded_sizes(region_supports(self._R[FB]));a,rule=rsx_choose(self.step+1,BURN_IN,sizes,sp)
        return {'api':API,'action':a,'rule':rule,'bounded_sizes':sizes,'step':self.step}


def _replay(observations,actions,library):
    observations=list(observations);actions=list(actions)
    if len(observations)!=len(actions)+1:raise ValueError('need len(observations) == len(actions) + 1')
    c=Certifier3(library=library).initialize(observations[0])
    try:
        for a,o in zip(actions,observations[1:]):c.observe(a,o)
    except Exception:
        c.close();raise
    return c


def certify3(observations,actions,query_action,library=None):
    """Stateless: observations[0] is the initial observation; len(observations) == len(actions) + 1."""
    c=_replay(observations,actions,library)
    try:return c.query(query_action)
    finally:c.close()


def suggest3(observations,actions,default_action=0):
    """Stateless RSX suggestion after the given history."""
    c=_replay(observations,actions,None)
    try:return c.suggest_action(default_action)
    finally:c.close()
