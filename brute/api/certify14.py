"""Brute v0.26.0 embeddable certify interface, version 14 (BRUTE_PLAN_029 A1 GAPI14; additive: brute/api/certify.py ...
certify13.py untouched). Adds search='s4': the v0.26.0 S4 exact search (brute.scalesearch4.ScaleRegion4: the S1 encoding
with one lazy solver per step, witness reuse, batched queries and a hard per-query cap; family_bound up to 16), method
'exact' only. search='region', 's2' and 's3' are brute.certify/13 unchanged (reported with api 'brute.certify/14').
  method 'exact' (s4): every reported "impossible" code is an UNSAT proof over all <= family_bound machines; soundness exact
                       conditional on noise-free readings and n* <= family_bound; an out-of-time code is in 'unknown',
                       counted possible, and a support carrying an unknown code is never certified.
Host-agnostic: no I/O, network, threads, child processes or global state.

    c = Certifier14(initial, num_actions=3, family_bound=16, search='s4'); c.current(); c.observe(action, reading); c.close()
    certify14(initial, actions, observations, ..., search='s4') -> {'api': 'brute.certify/14', 'search': 's4', ...}
"""
from __future__ import annotations
from brute.api.certify import _obs
from brute.api.certify8 import _num,_int
from brute.api.certify13 import Certifier13,soundness as soundness13
from brute.noisyregion import rgn_decide
from brute.scalesearch4 import ScaleRegion4,QUERY_S

API='brute.certify/14'
SEARCHES=('region','s2','s3','s4')
S4_METHODS=('exact',)
S4_MAX_BOUND=16
__all__=['API','SEARCHES','S4_METHODS','Certifier14','certify14','soundness']


def soundness(delta,method='betting',search='region'):
    if search!='s4':return soundness13(delta,method,search)
    return {'kind':'exact','delta':0.0,'method':'exact','search':'s4','anytime':True,
            'conditional_on':'noise-free readings and n* <= family_bound'}


class Certifier14:
    def __init__(self,initial,num_actions=2,eps_bar=0.02,delta=0.01,family_bound=4,burn_in=8,method=None,search='region',query_s=QUERY_S):
        if not isinstance(search,str) or search not in SEARCHES:raise ValueError("search must be 'region', 's2', 's3' or 's4'")
        self.search=search;self._c12=None;self.R=None
        if search!='s4':
            self._c12=Certifier13(initial,num_actions,eps_bar,delta,family_bound,burn_in,method,search,query_s);self.method=self._c12.method;return
        method=method or 'exact'
        if not isinstance(method,str) or method not in S4_METHODS:raise ValueError("method must be 'exact' with search='s4'")
        if _int(num_actions,'num_actions') not in (2,3,4):raise ValueError('num_actions must be 2, 3 or 4')
        if _int(family_bound,'family_bound')<1 or family_bound>S4_MAX_BOUND:raise ValueError(f'family_bound must be in 1..{S4_MAX_BOUND}')
        if _int(burn_in,'burn_in')<0:raise ValueError('burn_in must be a non-negative int')
        _num(eps_bar,'eps_bar');_num(delta,'delta');_num(query_s,'query_s')
        if not (0<eps_bar<0.5):raise ValueError('eps_bar must be in (0, 0.5)')
        if not (0<delta<1):raise ValueError('delta must be in (0, 1)')
        if not query_s>0:raise ValueError('query_s must be positive')
        self.method=method;self.k=num_actions;self.burn=burn_in;self.delta=delta;init=_obs(initial)
        self.R=ScaleRegion4(family_bound,num_actions,2,query_s)
        self.t=1;self.bits=sum(b is not None for b in init);self.steps=0;self._row=None
        try:self.R.initialize(init)
        except BaseException:self.close();raise

    def current(self):
        if self._c12 is not None:return self._c12.current()
        if self._row is None:
            row=[self.R.support(b) for b in range(self.k)]
            self._row={'step':self.t,'observed_bits':self.bits,'search':'s4','m':0,'supports':[s for s,_ in row],'unknown':[u for _,u in row],
                       'certificates':[rgn_decide(self.t,self.burn,s) if u==0 else None for s,u in row],'status':self.R.status}
        return self._row

    def observe(self,action,reading):
        if self._c12 is not None:return self._c12.observe(action,reading)
        if isinstance(action,bool) or not isinstance(action,int) or action not in range(self.k):
            raise ValueError(f'action must be an int in 0..{self.k-1}')
        o=_obs(reading);self.current();self.R.observe(action,o)
        self.bits+=sum(b is not None for b in o);self.t+=1;self.steps+=1;self._row=None

    @property
    def observed_bits(self):return self._c12.observed_bits if self._c12 is not None else self.bits

    def close(self):
        if self._c12 is not None:return self._c12.close()
        if self.R is not None:self.R.close()

    def __enter__(self):return self

    def __exit__(self,*a):self.close();return False


def certify14(initial,actions,observations,num_actions=2,eps_bar=0.02,delta=0.01,family_bound=4,burn_in=8,method=None,search='region',query_s=QUERY_S):
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    S=[];U=[];C=[];M=[]
    with Certifier14(initial,num_actions,eps_bar,delta,family_bound,burn_in,method,search,query_s) as c:
        for a,o in zip(acts+[None],obs+[None]):
            r=c.current();S.append(r['supports']);U.append(r['unknown']);C.append(r['certificates']);M.append(r['m'])
            if a is not None:c.observe(a,o)
        status=c.current()['status'];bits=c.observed_bits;meth=c.method
    return {'api':API,'search':search,'method':meth,'num_actions':num_actions,'observed_bits':bits,'steps':len(acts),'m':M,
            'supports':S,'unknown':U,'certificates':C,'status':status,'soundness':soundness(delta,meth,search)}
