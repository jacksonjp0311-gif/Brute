"""Brute v0.11.0 embeddable certify interface (BRUTE_PLAN_013 api_definition). New file; brute/api/* untouched.

Observations in; a certified next code or UNKNOWN out. Host-agnostic: no I/O, network, threads, subprocesses or global
state; the frozen SP8 learner (brute.align.AlignedSyncLearner, CTR certification) with the study-013 constants.

    c = Certifier(); c.initialize((0, 1)); c.observe(1, (1, None)); c.query(0)
    -> {'api': 'brute.certify/1', 'status': 'CERTIFIED' | 'UNKNOWN', 'answer': int | None, 'support': list | None, 'step': int}

An observation is a pair of bits, each 0, 1 or None (masked); a code is bit0 * 2 + bit1. With library_hypotheses (the
brute.transfer.expand output) the dual-region rule applies: certify only if SP8 certifies and the library is refuted
or forces the same code. A certificate is a claim about the declared family (deterministic Moore, <= 4 states,
stationary, 2 actions, 2 bits); outside it the answer means nothing.
"""
from __future__ import annotations
from brute.core.learner import ScopeAttestation
from brute.align import AlignedSyncLearner
from brute.transfer import TransferTracker

API='brute.certify/1'
FAMILY='deterministic-moore<=4/stationary'
# BRUTE_PLAN_013 via plan_view / plan006_keys (tests/test_api_certify_0110 checks these against the plan)
BASE=(4,5,160000,160000,0.08,0.02,8);TAU6=1.645215321642
KW={'surprise_fraction':0.5,'recency_window':8,'burn_in':8}


def _obs(o):
    if not isinstance(o,(tuple,list)) or len(o)!=2 or any(x not in (0,1,None) or isinstance(x,bool) for x in o):
        raise ValueError('observation must be a pair of bits 0 / 1 / None')
    return tuple(o)


def _act(a):
    if a not in (0,1) or isinstance(a,bool):raise ValueError('action must be 0 or 1')
    return a


class Certifier:
    def __init__(self,family_states=4,mask_bits=2,actions=2,library_hypotheses=None,attested=True):
        if (family_states,mask_bits,actions)!=(4,2,2) or any(isinstance(x,bool) for x in (family_states,mask_bits,actions)):
            raise ValueError('brute.certify/1 supports family_states=4, mask_bits=2, actions=2 only')
        att=ScopeAttestation(FAMILY,'host','caller attests the world lies in the family') if attested else None
        self._L=AlignedSyncLearner(*BASE,TAU6,att,policy='LU-R',rule='CTR',**KW)
        self._H=library_hypotheses;self._tr=None;self.step=None

    def initialize(self,observation):
        if self.step is not None:raise ValueError('already initialized')
        o=_obs(observation);self._L.initialize(o);self.step=0
        if self._H is not None:self._tr=TransferTracker(self._H,o,KW['burn_in'])
        return self

    def query(self,action):
        if self.step is None:raise ValueError('initialize first')
        f=self._L.predict(_act(action));c=f.certificate;sup=list(f.support) if f.support is not None else None;rule='sp8' if c is not None else None
        if c is not None and self._tr is not None and self._tr.alive and self._tr.predict(action)!=c:c,rule=None,'dr-disagree'
        return {'api':API,'status':'CERTIFIED' if c is not None else 'UNKNOWN','answer':c,'support':sup,'step':self.step,'rule':rule}

    def observe(self,action,observation):
        if self.step is None:raise ValueError('initialize first')
        a=_act(action);o=_obs(observation);fs=(self._L.predict(0),self._L.predict(1))
        self._L.record_issued(fs[a]);self._L.observe(a,o);self.step+=1
        if self._tr is not None:self._tr.observe(self.step,a,o)
        return self

    def close(self):self._L.close()


def certify(observations,actions,query_action,library_hypotheses=None):
    """Stateless: observations[0] is the initial observation; len(observations) == len(actions) + 1."""
    observations=list(observations);actions=list(actions)
    if len(observations)!=len(actions)+1:raise ValueError('need len(observations) == len(actions) + 1')
    c=Certifier(library_hypotheses=library_hypotheses).initialize(observations[0])
    try:
        for a,o in zip(actions,observations[1:]):c.observe(a,o)
        return c.query(query_action)
    finally:c.close()
