"""Brute v0.20.0 embeddable certify interface, version 9 (BRUTE_PLAN_023; additive: brute/api/certify.py ... certify8.py
untouched). Streaming likelihood-ratio anytime noise-tolerant certification RGL4 for 2 or 3 actions; no planned length.

    c = Certifier9(initial, num_actions=2, eps_bar=0.02, delta=0.01, family_bound=4, burn_in=8, method='lr')
    c.current()  -> {'step': t, 'observed_bits': b_t, 'm': T(b_t), 'supports': [...], 'unknown': [...],
                     'certificates': [...], 'status': ..., 'attain': n or None}
    c.observe(action, reading); c.close()  (also a context manager)

    certify9(initial, actions, observations, num_actions=2, eps_bar=0.02, delta=0.01, family_bound=4, burn_in=8,
             method='lr') -> {'api': 'brute.certify/9', 'method', 'num_actions', 'observed_bits', 'steps', 'm',
             'supports', 'unknown', 'certificates' (steps 1 .. T+1), 'status', 'soundness'}

method 'lr' (default): T(b) = min(m_a(b; eps_bar, delta/2), min over exhibited witnesses of f_g + D_n - 1) with
D_n from delta_L = delta/2 (docs/research/v0.20.0/LR_LEMMA_023.md). method 'anytime': exactly brute.certify/8 (RGNA4,
m_a at delta), with api 'brute.certify/9'. Under iid flips with eps <= eps_bar independent of actions and mask and a true
machine with <= family_bound states, a stream of ANY length has a false certificate with probability <= delta (anytime).
Outside the attestation the answer means nothing. family_bound: only 4. Host-agnostic: no I/O, network, threads, child
processes or global state.
"""
from __future__ import annotations
from fractions import Fraction
from brute.api.certify import _obs
from brute.api.certify8 import Certifier8,_num,_int
from brute.boundedtransfer import FB
from brute.lrregion import LRRegionSpace
from brute.seqmargin import supports_k,rgnb_decide

API='brute.certify/9'
METHODS=('lr','anytime')
CONDITIONAL_ON='iid flips with eps <= eps_bar independent of actions and mask, and n* <= family_bound'
__all__=['API','METHODS','CONDITIONAL_ON','Certifier9','certify9','soundness']


def soundness(delta,method='lr'):
    return {'kind':'probabilistic','delta':delta,'method':method,'conditional_on':CONDITIONAL_ON,'anytime':True}


def _half(d):return Fraction(str(d))/2 if isinstance(d,float) else Fraction(d)/2


class Certifier9:
    def __init__(self,initial,num_actions=2,eps_bar=0.02,delta=0.01,family_bound=4,burn_in=8,method='lr'):
        if not isinstance(method,str) or method not in METHODS:raise ValueError("method must be 'lr' or 'anytime'")
        self.method=method
        if method=='anytime':
            self._c8=Certifier8(initial,num_actions,eps_bar,delta,family_bound,burn_in);self.R=None;return
        self._c8=None
        if _int(num_actions,'num_actions') not in (2,3):raise ValueError('num_actions must be 2 or 3')
        if isinstance(family_bound,bool) or family_bound!=FB:raise ValueError('family_bound must be 4 in brute.certify/9')
        if _int(burn_in,'burn_in')<0:raise ValueError('burn_in must be a non-negative int')
        _num(eps_bar,'eps_bar');_num(delta,'delta')
        if not (0<=eps_bar<0.5):raise ValueError('eps_bar must be in [0, 0.5)')
        if not (0<delta<1):raise ValueError('delta must be in (0, 1)')
        self.k=num_actions;self.burn=burn_in;self.delta=delta;init=_obs(initial);h=_half(delta)
        self.R=LRRegionSpace(FB,self.k,eps_bar,h,h);self.t=1;self.bits=sum(b is not None for b in init);self.steps=0
        try:self.R.initialize(init)
        except BaseException:self.R.close();raise
        self._row=None

    def current(self):
        if self._c8 is not None:return self._c8.current()
        if self._row is None:
            row=supports_k(self.R,self.k)
            self._row={'step':self.t,'observed_bits':self.bits,'m':self.R.m_bound,
                       'supports':[s for s,_ in row],'unknown':[u for _,u in row],
                       'certificates':[rgnb_decide(self.t,self.burn,s) for s,_ in row],'status':self.R.status,
                       'attain':self.R.last['attain']}
        return self._row

    def observe(self,action,reading):
        if self._c8 is not None:return self._c8.observe(action,reading)
        if isinstance(action,bool) or not isinstance(action,int) or action not in range(self.k):
            raise ValueError(f'action must be an int in 0..{self.k-1}')
        o=_obs(reading);self.current();self.R.observe(action,o)
        self.bits+=sum(b is not None for b in o);self.t+=1;self.steps+=1;self._row=None

    @property
    def observed_bits(self):return self._c8.bits if self._c8 is not None else self.bits

    def close(self):
        if self._c8 is not None:self._c8.close()
        else:self.R.close()

    def __enter__(self):return self

    def __exit__(self,*a):self.close();return False


def certify9(initial,actions,observations,num_actions=2,eps_bar=0.02,delta=0.01,family_bound=4,burn_in=8,method='lr'):
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    S=[];U=[];C=[];M=[]
    with Certifier9(initial,num_actions,eps_bar,delta,family_bound,burn_in,method) as c:
        for a,o in zip(acts+[None],obs+[None]):
            r=c.current();S.append(r['supports']);U.append(r['unknown']);C.append(r['certificates']);M.append(r['m'])
            if a is not None:c.observe(a,o)
        status=c.current()['status'];bits=c.observed_bits
    return {'api':API,'method':method,'num_actions':num_actions,'observed_bits':bits,'steps':len(acts),'m':M,
            'supports':S,'unknown':U,'certificates':C,'status':status,'soundness':soundness(delta,method)}
