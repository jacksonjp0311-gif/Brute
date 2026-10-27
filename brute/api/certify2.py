"""Brute v0.12.0 embeddable certify interface, version 2 (BRUTE_PLAN_014 api_definition). New file; brute/api/certify.py
and every other brute/api file untouched.

Observations in; a certified next code or UNKNOWN (with a reason) out. Host-agnostic: no I/O, network, threads,
subprocesses or global state. Inside: the frozen SP8 learner (as brute.certify/1), the bounded regions
brute.region.RegionSpace(4) and RegionSpace(min(n_L + 1, 4)), and with a library the frozen TransferTracker; the
decision is brute.boundedtransfer.dlf_decide (margin 1).

    c = Certifier2(); c.initialize((0, 1)); c.observe(1, (1, None)); c.query(0)
    -> {'api': 'brute.certify/2', 'status': 'CERTIFIED' | 'UNKNOWN', 'answer': int | None, 'support': list | None,
        'bounded_support': list | None, 'rule': 'sp8' | 'rg' | 'license' | None, 'reason': None | str, 'step': int}

library: None or {'hypotheses': brute.transfer.expand(...)[0], 'min_n': n_L}. Without a library brute.certify/2
certifies exactly where RG4 does (a superset of brute.certify/1). reason (UNKNOWN only), in DLF order: 'burn-in',
'sp8-support-unavailable', then without a library the failing region condition ('region-not-singleton' or
'outside-sp8-support'), with a library the failing license condition ('library-refuted', 'library-split',
'outside-sp8-support', 'bounded-region-not-singleton'). 'no-library' is reserved and not emitted (deviation #60,
docs/research/BRUTE_DEVIATIONS_014.md). A certificate is a claim about the declared family (deterministic Moore,
<= 4 states, stationary, 2 actions, 2 bits) attested by the caller; outside it the answer means nothing.
"""
from __future__ import annotations
from brute.api.certify import Certifier,_obs,_act
from brute.region import RegionSpace
from brute.transfer import TransferTracker
from brute.boundedtransfer import FB,dlf_decide,region_supports

API='brute.certify/2'
REASONS=('burn-in','sp8-support-unavailable','region-not-singleton','outside-sp8-support','library-refuted',
         'library-split','bounded-region-not-singleton','no-library')
BURN_IN=8


class Certifier2:
    def __init__(self,library=None,margin=1):
        if margin!=1 or isinstance(margin,bool):raise ValueError('brute.certify/2 requires margin=1 (margin 0 is unsound under aliasing stress)')
        if library is not None:
            if not isinstance(library,dict) or set(library)<{'hypotheses','min_n'}:raise ValueError("library must be {'hypotheses': H, 'min_n': n_L}")
            n=library['min_n']
            if isinstance(n,bool) or not isinstance(n,int) or n<1:raise ValueError('library min_n must be a positive int')
        self._lib=library;self._sp8=Certifier();self._tr=None
        self._nb=min(library['min_n']+margin,FB) if library is not None else None
        self._R={};self.step=None

    def initialize(self,observation):
        if self.step is not None:raise ValueError('already initialized')
        o=_obs(observation);self._sp8.initialize(o)
        for n in {FB,self._nb}-{None}:
            self._R[n]=RegionSpace(n);self._R[n].initialize(o)
        if self._lib is not None:self._tr=TransferTracker(self._lib['hypotheses'],o,BURN_IN)
        self.step=0;return self

    def _regions(self):return {n:region_supports(R) for n,R in self._R.items()}

    def query(self,action):
        if self.step is None:raise ValueError('initialize first')
        b=_act(action);q=self._sp8.query(b);sup=q['support'];reg=self._regions()
        fb=reg[FB][b][0];lic=reg[self._nb][b][0] if self._nb is not None else None
        tr=self._tr;alive=None if tr is None else bool(tr.alive);pred=None if tr is None else tr.predict(b)
        c,rule,reason=dlf_decide(self.step+1,BURN_IN,q['answer'],sup,fb,lic,alive,pred)
        return {'api':API,'status':'CERTIFIED' if c is not None else 'UNKNOWN','answer':c,'support':sup,
                'bounded_support':fb,'rule':rule,'reason':reason,'step':self.step}

    def observe(self,action,observation):
        if self.step is None:raise ValueError('initialize first')
        a=_act(action);o=_obs(observation);self._sp8.observe(a,o)
        for R in self._R.values():R.observe(a,o)
        self.step+=1
        if self._tr is not None:self._tr.observe(self.step,a,o)
        return self

    def close(self):
        self._sp8.close()
        for R in self._R.values():R.close()


def certify2(observations,actions,query_action,library=None):
    """Stateless: observations[0] is the initial observation; len(observations) == len(actions) + 1."""
    observations=list(observations);actions=list(actions)
    if len(observations)!=len(actions)+1:raise ValueError('need len(observations) == len(actions) + 1')
    c=Certifier2(library=library).initialize(observations[0])
    try:
        for a,o in zip(actions,observations[1:]):c.observe(a,o)
        return c.query(query_action)
    finally:c.close()
