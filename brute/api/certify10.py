"""Brute v0.21.0 embeddable certify interface, version 10 (BRUTE_PLAN_024; additive: brute/api/certify.py ... certify9.py
untouched). Adds method 'stitched' (RGL5, docs/research/v0.21.0/STITCHED_LEMMA_024.md); 'lr' = brute.certify/9 and
'anytime' = brute.certify/8, unchanged, reported with api 'brute.certify/10'.

    c = Certifier10(initial, num_actions=2, eps_bar=0.02, delta=0.01, family_bound=4, burn_in=8, method='stitched')
    c.current()  -> {'step', 'observed_bits', 'm', 'supports', 'unknown', 'certificates', 'status', 'attain'} (+ 'epoch'
                    for 'stitched')
    c.observe(action, reading); c.close()  (also a context manager)
    certify10(...) -> {'api': 'brute.certify/10', 'method', 'num_actions', 'observed_bits', 'steps', 'm', 'supports',
                       'unknown', 'certificates' (steps 1 .. T+1), 'status', 'soundness'}

method 'stitched' (default): T5(i) = min(M(i), min over exhibited witnesses of f_g + D_n - 1) where M is the running max
of the planned-count thresholds boundary(2*28*2^k, eps_bar, (delta/2)/((k+1)(k+2))) of epoch k(i) and D_n come from
delta_L = delta/2. Horizon-free; under iid flips with eps <= eps_bar independent of actions and mask and a true machine
with <= family_bound states, a stream of ANY length has a false certificate with probability <= delta. Outside the
attestation the answer means nothing. family_bound: only 4. Host-agnostic: no I/O, network, threads, child processes or
global state.
"""
from __future__ import annotations
from brute.api.certify import _obs
from brute.api.certify8 import _num,_int
from brute.api.certify9 import Certifier9,_half
from brute.boundedtransfer import FB
from brute.stitchedregion import StitchedRegionSpace
from brute.seqmargin import supports_k,rgnb_decide

API='brute.certify/10'
METHODS=('stitched','lr','anytime')
CONDITIONAL_ON='iid flips with eps <= eps_bar independent of actions and mask, and n* <= family_bound'
__all__=['API','METHODS','CONDITIONAL_ON','Certifier10','certify10','soundness']


def soundness(delta,method='stitched'):
    return {'kind':'probabilistic','delta':delta,'method':method,'conditional_on':CONDITIONAL_ON,'anytime':True}


class Certifier10:
    def __init__(self,initial,num_actions=2,eps_bar=0.02,delta=0.01,family_bound=4,burn_in=8,method='stitched'):
        if not isinstance(method,str) or method not in METHODS:raise ValueError("method must be 'stitched', 'lr' or 'anytime'")
        self.method=method
        if method!='stitched':
            self._c9=Certifier9(initial,num_actions,eps_bar,delta,family_bound,burn_in,method);self.R=None;return
        self._c9=None
        if _int(num_actions,'num_actions') not in (2,3):raise ValueError('num_actions must be 2 or 3')
        if isinstance(family_bound,bool) or family_bound!=FB:raise ValueError('family_bound must be 4 in brute.certify/10')
        if _int(burn_in,'burn_in')<0:raise ValueError('burn_in must be a non-negative int')
        _num(eps_bar,'eps_bar');_num(delta,'delta')
        if not (0<=eps_bar<0.5):raise ValueError('eps_bar must be in [0, 0.5)')
        if not (0<delta<1):raise ValueError('delta must be in (0, 1)')
        self.k=num_actions;self.burn=burn_in;self.delta=delta;init=_obs(initial);h=_half(delta)
        self.R=StitchedRegionSpace(FB,self.k,eps_bar,h,h);self.t=1;self.bits=sum(b is not None for b in init);self.steps=0
        try:self.R.initialize(init)
        except BaseException:self.R.close();raise
        self._row=None

    def current(self):
        if self._c9 is not None:return self._c9.current()
        if self._row is None:
            row=supports_k(self.R,self.k)
            self._row={'step':self.t,'observed_bits':self.bits,'m':self.R.m_bound,
                       'supports':[s for s,_ in row],'unknown':[u for _,u in row],
                       'certificates':[rgnb_decide(self.t,self.burn,s) for s,_ in row],'status':self.R.status,
                       'attain':self.R.last['attain'],'epoch':self.R.last['epoch']}
        return self._row

    def observe(self,action,reading):
        if self._c9 is not None:return self._c9.observe(action,reading)
        if isinstance(action,bool) or not isinstance(action,int) or action not in range(self.k):
            raise ValueError(f'action must be an int in 0..{self.k-1}')
        o=_obs(reading);self.current();self.R.observe(action,o)
        self.bits+=sum(b is not None for b in o);self.t+=1;self.steps+=1;self._row=None

    @property
    def observed_bits(self):return self._c9.observed_bits if self._c9 is not None else self.bits

    def close(self):
        if self._c9 is not None:self._c9.close()
        else:self.R.close()

    def __enter__(self):return self

    def __exit__(self,*a):self.close();return False


def certify10(initial,actions,observations,num_actions=2,eps_bar=0.02,delta=0.01,family_bound=4,burn_in=8,method='stitched'):
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    S=[];U=[];C=[];M=[]
    with Certifier10(initial,num_actions,eps_bar,delta,family_bound,burn_in,method) as c:
        for a,o in zip(acts+[None],obs+[None]):
            r=c.current();S.append(r['supports']);U.append(r['unknown']);C.append(r['certificates']);M.append(r['m'])
            if a is not None:c.observe(a,o)
        status=c.current()['status'];bits=c.observed_bits
    return {'api':API,'method':method,'num_actions':num_actions,'observed_bits':bits,'steps':len(acts),'m':M,
            'supports':S,'unknown':U,'certificates':C,'status':status,'soundness':soundness(delta,method)}
