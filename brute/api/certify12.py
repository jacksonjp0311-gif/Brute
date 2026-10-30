"""Brute v0.23.0 embeddable certify interface, version 12 (BRUTE_PLAN_026 GAPI12; additive: brute/api/certify.py ...
certify11.py untouched). Adds the keyword search: 'region' (default) is brute.certify/11 unchanged (reported with api
'brute.certify/12'); search='s2' answers on the v0.23.0 S2 exact search (brute.scalesearch) with family_bound up to 16:
  method 'exact'   : ScaleRegion(family_bound) on hard readings (None = unobserved bit); a deterministic answer: every
                     reported "impossible" code is an UNSAT proof over all <= family_bound machines; soundness exact
                     conditional on noise-free readings and n* <= family_bound;
  method 'betting' : RGB6_on_S2 (brute.scalebetting.ScaleBettingSpace): the frozen RGB6 flip bound T6 with the support
                     region on the S2 skeleton; probabilistic (delta), as brute.certify/11 'betting'.
Every query has a wall budget (query_s seconds); an out-of-time code is reported in 'unknown' and counted possible, and a
support carrying an unknown code is never certified. Certificates: the singleton code after burn_in (brute.noisyregion
rgn_decide). Host-agnostic: no I/O, network, threads, child processes or global state.

    c = Certifier12(initial, num_actions=3, family_bound=16, search='s2', method='exact')
    c.current(); c.observe(action, reading); c.close()
    certify12(initial, actions, observations, ..., search='s2') -> {'api': 'brute.certify/12', 'search', ...}
"""
from __future__ import annotations
from brute.api.certify import _obs
from brute.api.certify8 import _num,_int
from brute.api.certify11 import Certifier11,soundness as soundness11
from brute.noisyregion import rgn_decide
from brute.scalesearch import ScaleRegion,QUERY_S
from brute.scalebetting import ScaleBettingSpace

API='brute.certify/12'
SEARCHES=('region','s2')
S2_METHODS=('exact','betting')
S2_MAX_BOUND=16
__all__=['API','SEARCHES','S2_METHODS','Certifier12','certify12','soundness']


def soundness(delta,method='betting',search='region'):
    if search=='region':return soundness11(delta,method)
    if method=='exact':return {'kind':'exact','delta':0.0,'method':'exact','search':'s2','anytime':True,
                               'conditional_on':'noise-free readings and n* <= family_bound'}
    s=soundness11(delta,'betting');s['search']='s2';s['conditional_on']=s['conditional_on'].replace('family_bound','family_bound (S2)')
    return s


class Certifier12:
    def __init__(self,initial,num_actions=2,eps_bar=0.02,delta=0.01,family_bound=4,burn_in=8,method=None,search='region',query_s=QUERY_S):
        if not isinstance(search,str) or search not in SEARCHES:raise ValueError("search must be 'region' or 's2'")
        self.search=search
        if search=='region':
            self._c11=Certifier11(initial,num_actions,eps_bar,delta,family_bound,burn_in,method or 'betting');self.method=self._c11.method;return
        self._c11=None;method=method or 'exact'
        if not isinstance(method,str) or method not in S2_METHODS:raise ValueError("method must be 'exact' or 'betting' with search='s2'")
        if _int(num_actions,'num_actions') not in (2,3,4):raise ValueError('num_actions must be 2, 3 or 4')
        if _int(family_bound,'family_bound')<1 or family_bound>S2_MAX_BOUND:raise ValueError(f'family_bound must be in 1..{S2_MAX_BOUND}')
        if _int(burn_in,'burn_in')<0:raise ValueError('burn_in must be a non-negative int')
        _num(eps_bar,'eps_bar');_num(delta,'delta');_num(query_s,'query_s')
        if not (0<eps_bar<0.5):raise ValueError('eps_bar must be in (0, 0.5)')
        if not (0<delta<1):raise ValueError('delta must be in (0, 1)')
        if not query_s>0:raise ValueError('query_s must be positive')
        self.method=method;self.k=num_actions;self.burn=burn_in;self.delta=delta;init=_obs(initial)
        self.R=(ScaleRegion(family_bound,num_actions,2,query_s) if method=='exact'
                else ScaleBettingSpace(family_bound,num_actions,eps_bar,delta,2,query_s))
        self.t=1;self.bits=sum(b is not None for b in init);self.steps=0;self._row=None
        try:self.R.initialize(init)
        except BaseException:self.close();raise

    def _support(self,b):
        R=self.R
        if self.method=='exact':return R.support(b)
        if R.status=='budget_exhausted':return None,1
        u0=R.unknown_total;s=R.predict_support(b);return (None if s is None else tuple(s)),R.unknown_total-u0

    def current(self):
        if self._c11 is not None:r=dict(self._c11.current());r['search']='region';return r
        if self._row is None:
            row=[self._support(b) for b in range(self.k)]
            self._row={'step':self.t,'observed_bits':self.bits,'search':'s2',
                       'm':0 if self.method=='exact' else self.R.m_bound,'supports':[s for s,_ in row],'unknown':[u for _,u in row],
                       'certificates':[rgn_decide(self.t,self.burn,s) if u==0 else None for s,u in row],'status':self.R.status}
        return self._row

    def observe(self,action,reading):
        if self._c11 is not None:return self._c11.observe(action,reading)
        if isinstance(action,bool) or not isinstance(action,int) or action not in range(self.k):
            raise ValueError(f'action must be an int in 0..{self.k-1}')
        o=_obs(reading);self.current();self.R.observe(action,o)
        self.bits+=sum(b is not None for b in o);self.t+=1;self.steps+=1;self._row=None

    @property
    def observed_bits(self):return self._c11.observed_bits if self._c11 is not None else self.bits

    def close(self):
        if self._c11 is not None:return self._c11.close()
        R=getattr(self,'R',None)
        if R is None:return
        if self.method=='exact':R.close()
        elif R.region is not None:R.region.close();R.region=None

    def __enter__(self):return self

    def __exit__(self,*a):self.close();return False


def certify12(initial,actions,observations,num_actions=2,eps_bar=0.02,delta=0.01,family_bound=4,burn_in=8,method=None,search='region',query_s=QUERY_S):
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    S=[];U=[];C=[];M=[]
    with Certifier12(initial,num_actions,eps_bar,delta,family_bound,burn_in,method,search,query_s) as c:
        for a,o in zip(acts+[None],obs+[None]):
            r=c.current();S.append(r['supports']);U.append(r['unknown']);C.append(r['certificates']);M.append(r['m'])
            if a is not None:c.observe(a,o)
        status=c.current()['status'];bits=c.observed_bits;meth=c.method
    return {'api':API,'search':search,'method':meth,'num_actions':num_actions,'observed_bits':bits,'steps':len(acts),'m':M,
            'supports':S,'unknown':U,'certificates':C,'status':status,'soundness':soundness(delta,meth,search)}
