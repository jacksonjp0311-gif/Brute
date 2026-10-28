"""Brute v0.20.0 likelihood-ratio anytime region RGL_n (BRUTE_PLAN_023 method; docs/research/v0.20.0/LR_LEMMA_023.md).
New file; brute/noisyregion.py, brute/seqmargin.py, brute/anytimemargin.py and brute/region.py are imported unchanged.

Hypothesis class H = union over n = 1..N of H_n (RegionK representations: start state, transition table [n]x[k]->[n],
emission [n]->{0..2^s-1}), |H_n| = n * n^(k n) * (2^s)^n, prior pi(g) = 1/(N |H_n|). With r = eps_bar/(1-eps_bar),
D_n = least D with (1/r)^D >= N |H_n| / delta_L (exact Fractions). At each step the bound is
  T(b) = min(m_a(b; eps_bar, delta_a), min over exhibited witnesses g_n in H_n of (f_{g_n} + D_n) - 1)
with m_a the frozen v0.19.0 AnytimeBoundary. Witnesses are found by the frozen tolerant_region feasibility check, searched
upward from the previous step's start point and only while they could lower T (deviation #108). Only exhibited (SAT)
witnesses lower T; UNSAT / UNKNOWN answers never do.

Soundness (Exact, conditional on the attested noise model): if the noise is iid Bernoulli(e), e <= eps_bar, independent
of the actions and the mask, and the true machine has <= N states, P(the true machine ever has more than T(b) flips)
<= delta_L + delta_a, so every singleton support after the burn-in is the latent code except with that probability.
"""
from __future__ import annotations
from fractions import Fraction
from brute.region import PRODUCTION_CONF_BUDGET
from brute.noisyregion import NoisyRegionSpace,tolerant_region,observed_bits
from brute.anytimemargin import AnytimeBoundary
from brute.seqmargin import supports_k

__all__=['class_size','lr_offsets','LRBound','LRRegionSpace','lr_supports']


def _frac(x,name):
    if isinstance(x,bool) or not isinstance(x,(int,float,Fraction)):raise ValueError(name+' must be a number')
    return Fraction(str(x)) if isinstance(x,float) else Fraction(x)


def class_size(n,k=2,s=2):
    """|H_n| = n * n^(k n) * (2^s)^n."""
    return n*n**(k*n)*(1<<s)**n


def lr_offsets(max_states=4,k=2,eps_bar=0.02,delta_L=0.005,s=2):
    """[D_1 .. D_N]; None when eps_bar == 0 (no LR part: the bound is m_a, which is 0)."""
    p=_frac(eps_bar,'eps_bar');d=_frac(delta_L,'delta_L')
    if not (0<=p<Fraction(1,2)):raise ValueError('eps_bar must be in [0, 0.5)')
    if not (0<d<1):raise ValueError('delta_L must be in (0, 1)')
    if p==0:return None
    inv=(1-p)/p;out=[]
    for n in range(1,max_states+1):
        need=max_states*class_size(n,k,s)/d;D=0;x=Fraction(1)
        while x<need:x*=inv;D+=1
        out.append(D)
    return out


def _decode(R,n,k,s,w):
    pos={l for l in R.s.get_model() if l>0}
    d=[[next(r for r in range(n) if R.d[q][a][r] in pos) for a in range(k)] for q in range(n)]
    e=[next(c for c in range(1<<s) if R.e[q][c] in pos) for q in range(n)]
    return {'n':n,'w':w,'d':d,'e':e}


class LRBound:
    """Per-step T(b); start points s_n carried between calls (readings must only grow)."""
    def __init__(self,max_states=4,k=2,eps_bar=0.02,delta_L=0.005,delta_a=0.005,s=2,conf_budget=PRODUCTION_CONF_BUDGET):
        self.N=max_states;self.k=k;self.s=s;self.conf_budget=conf_budget
        self.anytime=AnytimeBoundary(eps_bar,delta_a);self.D=lr_offsets(max_states,k,eps_bar,delta_L,s)
        self.start=[0]*max_states;self.sat_calls=0

    def bound(self,readings,actions):
        b=observed_bits(readings);ma=self.anytime.extend(b)[b];cap=ma;W=[];unk=0;calls=0
        if self.D is not None:
            for n in range(1,self.N+1):
                m=self.start[n-1];D=self.D[n-1]
                while m+D-1<cap:
                    R=tolerant_region(n,readings,actions,m,self.k,self.s,self.conf_budget);calls+=1
                    try:
                        f=R.feasible
                        if f is True:W.append(_decode(R,n,self.k,self.s,m));cap=m+D-1;break
                        if f is None:unk+=1
                    finally:R.close()
                    m+=1
                self.start[n-1]=m
        self.sat_calls+=calls
        return {'T':cap,'m_a':ma,'attain':W[-1]['n'] if W else None,'witnesses':W,'witness_unknowns':unk,'witness_calls':calls}


class LRRegionSpace(NoisyRegionSpace):
    """NoisyRegionSpace whose bound is T(b); T is recomputed on every observation, also after a sticky status."""
    def __init__(self,max_states=4,k=2,eps_bar=0.02,delta_L=0.005,delta_a=0.005,s=2,conf_budget=PRODUCTION_CONF_BUDGET):
        super().__init__(max_states,0,k,s,conf_budget)
        self.lr=LRBound(max_states,k,eps_bar,delta_L,delta_a,s,conf_budget);self.last=None

    def _bound(self):
        self.last=self.lr.bound(self.readings,self.acts);self.m_bound=self.last['T']

    def _build(self):
        self._bound();super()._build()

    def observe(self,action,obs):
        if not self.readings:raise ValueError('not initialized')
        if action not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        if self.status=='supported':return super().observe(action,obs)
        self.readings.append(tuple(obs));self.acts.append(action);self._bound()


def lr_supports(initial,actions,observations,max_states=4,k=2,eps_bar=0.02,delta_L=0.005,delta_a=0.005,
                conf_budget=PRODUCTION_CONF_BUDGET):
    """Supports at steps 1..T (step i+1 on readings 0..i) plus the per-step LR record."""
    R=LRRegionSpace(max_states,k,eps_bar,delta_L,delta_a,conf_budget=conf_budget);R.initialize(tuple(initial))
    S=[];U=[];M=[];st=[];lr={'T':[],'attain':[],'witnesses':[],'witness_unknowns':[],'witness_calls':[]}
    try:
        for a,o in zip(actions,observations):
            row=supports_k(R,k);S.append([x for x,_ in row]);U.append([u for _,u in row]);M.append(R.m_bound);st.append(R.status)
            for key in lr:lr[key].append(R.last[key])
            R.observe(a,tuple(o))
    finally:R.close()
    return {'support':S,'unknown':U,'m':M,'status':st,'lr':lr,'D':R.lr.D}
