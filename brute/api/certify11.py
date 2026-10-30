"""Brute v0.22.0 embeddable certify interface, version 11 (BRUTE_PLAN_025 + A1; additive: brute/api/certify.py ...
certify10.py untouched). Adds method 'betting' (RGB6, docs/research/v0.22.0/BETTING_LEMMA_025.md); 'stitched' =
brute.certify/10, 'lr' = brute.certify/9 and 'anytime' = brute.certify/8, unchanged, reported with api 'brute.certify/11'.

    c = Certifier11(initial, num_actions=2, eps_bar=0.02, delta=0.01, family_bound=4, burn_in=8, method='betting')
    c.current()  -> {'step', 'observed_bits', 'm', 'supports', 'unknown', 'certificates', 'status', 'attain'} (+ 'active',
                    'eps_hat_u' for 'betting')
    c.observe(action, reading); c.close()  (also a context manager)
    certify11(...) -> {'api': 'brute.certify/11', 'method', 'num_actions', 'observed_bits', 'steps', 'm', 'supports',
                       'unknown', 'certificates' (steps 1 .. T+1), 'status', 'soundness'}

method 'betting' (default): T6(i) = min(M(i), min over exhibited witnesses of w + D_eff,n - 1), M = the anytime boundary at
eps_bar, delta/4; D_eff = elementwise min of the level-0 offsets (eps_bar, delta/4) and those of every ACTIVE level j = 1, 2
(p_j = eps_bar/2^j, delta/8); level j activates (sticky) once the mixture-betting wealth on the level-0 witness bound
reaches 8/delta. Total delta = delta/4 + delta/4 + 2(delta/8 + delta/8). Horizon-free; under iid flips with eps <= eps_bar
independent of actions and mask and a true machine with <= family_bound states, a stream of ANY length has a false
certificate with probability <= delta. A level that never activates costs nothing and gains nothing: then T6 equals the
level-0 rule (Exact, lemma §4). Outside the attestation the answer means nothing. family_bound: only 4. Host-agnostic:
no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from brute.api.certify import _obs
from brute.api.certify8 import _num,_int
from brute.api.certify10 import Certifier10
from brute.boundedtransfer import FB
from brute.bettingregion import BettingRegionSpace
from brute.seqmargin import supports_k,rgnb_decide

API='brute.certify/11'
METHODS=('betting','stitched','lr','anytime')
CONDITIONAL_ON='iid flips with eps <= eps_bar independent of actions and mask, and n* <= family_bound'
__all__=['API','METHODS','CONDITIONAL_ON','Certifier11','certify11','soundness']


def soundness(delta,method='betting'):
    return {'kind':'probabilistic','delta':delta,'method':method,'conditional_on':CONDITIONAL_ON,'anytime':True}


class Certifier11:
    def __init__(self,initial,num_actions=2,eps_bar=0.02,delta=0.01,family_bound=4,burn_in=8,method='betting'):
        if not isinstance(method,str) or method not in METHODS:raise ValueError("method must be 'betting', 'stitched', 'lr' or 'anytime'")
        self.method=method
        if method!='betting':
            self._c10=Certifier10(initial,num_actions,eps_bar,delta,family_bound,burn_in,method);self.R=None;return
        self._c10=None
        if _int(num_actions,'num_actions') not in (2,3):raise ValueError('num_actions must be 2 or 3')
        if isinstance(family_bound,bool) or family_bound!=FB:raise ValueError('family_bound must be 4 in brute.certify/11')
        if _int(burn_in,'burn_in')<0:raise ValueError('burn_in must be a non-negative int')
        _num(eps_bar,'eps_bar');_num(delta,'delta')
        if not (0<eps_bar<0.5):raise ValueError("eps_bar must be in (0, 0.5) for method 'betting'")
        if not (0<delta<1):raise ValueError('delta must be in (0, 1)')
        self.k=num_actions;self.burn=burn_in;self.delta=delta;init=_obs(initial)
        self.R=BettingRegionSpace(FB,self.k,eps_bar,delta);self.t=1;self.bits=sum(b is not None for b in init);self.steps=0
        try:self.R.initialize(init)
        except BaseException:self.R.close();raise
        self._row=None

    def current(self):
        if self._c10 is not None:return self._c10.current()
        if self._row is None:
            row=supports_k(self.R,self.k);L=self.R.last
            self._row={'step':self.t,'observed_bits':self.bits,'m':self.R.m_bound,
                       'supports':[s for s,_ in row],'unknown':[u for _,u in row],
                       'certificates':[rgnb_decide(self.t,self.burn,s) for s,_ in row],'status':self.R.status,
                       'attain':L['attain'],'active':L['active'],'eps_hat_u':L['eps_hat_u']}
        return self._row

    def observe(self,action,reading):
        if self._c10 is not None:return self._c10.observe(action,reading)
        if isinstance(action,bool) or not isinstance(action,int) or action not in range(self.k):
            raise ValueError(f'action must be an int in 0..{self.k-1}')
        o=_obs(reading);self.current();self.R.observe(action,o)
        self.bits+=sum(b is not None for b in o);self.t+=1;self.steps+=1;self._row=None

    @property
    def observed_bits(self):return self._c10.observed_bits if self._c10 is not None else self.bits

    def close(self):
        if self._c10 is not None:self._c10.close()
        else:self.R.close()

    def __enter__(self):return self

    def __exit__(self,*a):self.close();return False


def certify11(initial,actions,observations,num_actions=2,eps_bar=0.02,delta=0.01,family_bound=4,burn_in=8,method='betting'):
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    S=[];U=[];C=[];M=[]
    with Certifier11(initial,num_actions,eps_bar,delta,family_bound,burn_in,method) as c:
        for a,o in zip(acts+[None],obs+[None]):
            r=c.current();S.append(r['supports']);U.append(r['unknown']);C.append(r['certificates']);M.append(r['m'])
            if a is not None:c.observe(a,o)
        status=c.current()['status'];bits=c.observed_bits
    return {'api':API,'method':method,'num_actions':num_actions,'observed_bits':bits,'steps':len(acts),'m':M,
            'supports':S,'unknown':U,'certificates':C,'status':status,'soundness':soundness(delta,method)}
