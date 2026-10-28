"""Brute v0.19.0 embeddable certify interface, version 8 (BRUTE_PLAN_021; additive: brute/api/certify.py ... certify7.py
untouched). Streaming anytime-margin noise-tolerant certification RGNA4 for 2 or 3 actions; no planned length.

    c = Certifier8(initial, num_actions=2, eps_bar=0.02, delta=0.01, family_bound=4, burn_in=8)
    c.current()  -> {'step': t, 'observed_bits': b_t, 'm': m_a(b_t), 'supports': [...], 'unknown': [...],
                     'certificates': [...], 'status': ...}   (the next reading, after readings 0..t-1)
    c.observe(action, reading)   one action and the reading it produced; then c.current() is step t+1
    c.close()                    (also a context manager)

    certify8(initial, actions, observations, num_actions=2, eps_bar=0.02, delta=0.01, family_bound=4, burn_in=8)
    -> {'api': 'brute.certify/8', 'num_actions', 'observed_bits', 'steps', 'boundary': [m_a(0) .. m_a(b)],
        'm', 'supports', 'unknown', 'certificates' (steps 1 .. T+1), 'status', 'soundness'}  (= the streamed rows)

A certificate at step t > burn_in is the single code consistent with some <= family_bound-state Moore machine after at most
m_a(b_t) flips in readings 0..t-1. If the running flips never exceed m_a and the true machine has <= family_bound states,
every certificate equals the noise-free reading (Exact); under iid flips with eps <= eps_bar a stream of ANY length has a
false certificate with probability < delta (anytime). Outside the attestation the answer means nothing.
family_bound: only 4. Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from fractions import Fraction
from brute.api.certify import _obs
from brute.boundedtransfer import FB
from brute.anytimemargin import AnytimeRegionSpace
from brute.seqmargin import supports_k,rgnb_decide

API='brute.certify/8'
CONDITIONAL_ON='running flips <= m_a(b) and n* <= family_bound'
__all__=['API','CONDITIONAL_ON','Certifier8','certify8','soundness']


def soundness(delta):return {'kind':'probabilistic','delta':delta,'conditional_on':CONDITIONAL_ON,'anytime':True}


def _num(x,name):
    if isinstance(x,bool) or not isinstance(x,(int,float,Fraction)):raise ValueError(name+' must be a number')
    return x


def _int(x,name):
    if isinstance(x,bool) or not isinstance(x,int):raise ValueError(name+' must be an int')
    return x


class Certifier8:
    def __init__(self,initial,num_actions=2,eps_bar=0.02,delta=0.01,family_bound=4,burn_in=8):
        if _int(num_actions,'num_actions') not in (2,3):raise ValueError('num_actions must be 2 or 3')
        if isinstance(family_bound,bool) or family_bound!=FB:raise ValueError('family_bound must be 4 in brute.certify/8')
        if _int(burn_in,'burn_in')<0:raise ValueError('burn_in must be a non-negative int')
        _num(eps_bar,'eps_bar');_num(delta,'delta')
        if not (0<=eps_bar<0.5):raise ValueError('eps_bar must be in [0, 0.5)')
        if not (0<delta<1):raise ValueError('delta must be in (0, 1)')
        self.k=num_actions;self.burn=burn_in;self.delta=delta;init=_obs(initial)
        self.R=AnytimeRegionSpace(FB,self.k,eps_bar,delta);self.t=1;self.bits=sum(b is not None for b in init);self.steps=0
        try:self.R.initialize(init)
        except BaseException:self.R.close();raise
        self._row=None

    def current(self):
        if self._row is None:
            row=supports_k(self.R,self.k)
            self._row={'step':self.t,'observed_bits':self.bits,'m':self.R.anytime.extend(self.bits)[self.bits],
                       'supports':[s for s,_ in row],'unknown':[u for _,u in row],
                       'certificates':[rgnb_decide(self.t,self.burn,s) for s,_ in row],'status':self.R.status}
        return self._row

    def observe(self,action,reading):
        if isinstance(action,bool) or not isinstance(action,int) or action not in range(self.k):
            raise ValueError(f'action must be an int in 0..{self.k-1}')
        o=_obs(reading);self.current();self.R.observe(action,o)
        self.bits+=sum(b is not None for b in o);self.t+=1;self.steps+=1;self._row=None

    def boundary(self):return self.R.anytime.extend(self.bits)

    def close(self):self.R.close()

    def __enter__(self):return self

    def __exit__(self,*a):self.close();return False


def certify8(initial,actions,observations,num_actions=2,eps_bar=0.02,delta=0.01,family_bound=4,burn_in=8):
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    S=[];U=[];C=[];M=[]
    with Certifier8(initial,num_actions,eps_bar,delta,family_bound,burn_in) as c:
        for a,o in zip(acts+[None],obs+[None]):
            r=c.current();S.append(r['supports']);U.append(r['unknown']);C.append(r['certificates']);M.append(r['m'])
            if a is not None:c.observe(a,o)
        status=c.current()['status'];bd=c.boundary();bits=c.bits
    return {'api':API,'num_actions':num_actions,'observed_bits':bits,'steps':len(acts),'boundary':bd,'m':M,
            'supports':S,'unknown':U,'certificates':C,'status':status,'soundness':soundness(delta)}
