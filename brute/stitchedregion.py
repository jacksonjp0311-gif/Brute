"""Brute v0.21.0 stitched likelihood-ratio region RGL5_n (BRUTE_PLAN_024 method; docs/research/v0.21.0/STITCHED_LEMMA_024.md).
New file; brute/lrregion.py, brute/seqmargin.py, brute/noisyregion.py and brute/region.py are imported unchanged.

Epochs: step i (support computed on readings 0..i-1) is in epoch k(i) = 0 for i <= 28, else the least k with i <= 28*2^k;
H_k = 28*2^k, B_k = 2*H_k, delta_k = delta_a / ((k+1)(k+2)) (exact). bd_k = frozen brute.seqmargin.boundary(B_k, eps_bar,
delta_k). Stitched margin M(i) = max(M(i-1), bd_k(i)[b_i]). The bound is
  T5(i) = min(M(i), min over exhibited witnesses g_n of (w_n + D_n) - 1)
with the RGL4 witness search (brute.lrregion rule, deviation #108 cap) started from cap = M(i).

Soundness (Exact, conditional on the attested noise model): P(the running flips ever exceed M) < sum_k delta_k <= delta_a,
P(the true machine is ever removed by the LR part) <= delta_L, so every singleton support after the burn-in is the latent
code except with probability < delta_L + delta_a. Horizon-free and prefix-stable (no planned length is read).
"""
from __future__ import annotations
from fractions import Fraction
from brute.region import PRODUCTION_CONF_BUDGET
from brute.noisyregion import NoisyRegionSpace,tolerant_region,observed_bits
from brute.seqmargin import boundary,supports_k
from brute.lrregion import lr_offsets,_decode,_frac

__all__=['H0','epoch_of','epoch_delta','epochs','StitchedMargin','StitchedLRBound','StitchedRegionSpace','stitched_supports']
H0=28


def epoch_of(i):
    if isinstance(i,bool) or not isinstance(i,int) or i<1:raise ValueError('step must be a positive int')
    k=0
    while i>H0*2**k:k+=1
    return k


def epoch_delta(k,delta_a=0.005):
    return _frac(delta_a,'delta_a')/((k+1)*(k+2))


def epochs(T,delta_a=0.005):
    return [{'k':k,'H':H0*2**k,'B':2*H0*2**k,'delta':str(epoch_delta(k,delta_a))} for k in range(epoch_of(T)+1)]


class StitchedMargin:
    """M(i) for i = 1, 2, ...; call at(i, b) with non-decreasing i."""
    def __init__(self,eps_bar=0.02,delta_a=0.005):
        self.p=_frac(eps_bar,'eps_bar');self.da=_frac(delta_a,'delta_a');self.bd={};self.M=0
        if not (0<self.da<1):raise ValueError('delta_a must be in (0, 1)')

    def table(self,k):
        if k not in self.bd:self.bd[k]=boundary(2*H0*2**k,self.p,epoch_delta(k,self.da))
        return self.bd[k]

    def at(self,i,b):
        k=epoch_of(i);bd=self.table(k)
        if b>=len(bd):raise ValueError('more observed bits than epoch B_k covers')
        self.M=max(self.M,bd[b]);return k,self.M


class StitchedLRBound:
    """Per-step T5; start points s_n carried between calls (readings must only grow)."""
    def __init__(self,max_states=4,k=2,eps_bar=0.02,delta_L=0.005,delta_a=0.005,s=2,conf_budget=PRODUCTION_CONF_BUDGET):
        self.N=max_states;self.k=k;self.s=s;self.conf_budget=conf_budget
        self.margin=StitchedMargin(eps_bar,delta_a);self.D=lr_offsets(max_states,k,eps_bar,delta_L,s)
        self.start=[0]*max_states;self.sat_calls=0

    def bound(self,readings,actions):
        i=len(readings);b=observed_bits(readings);ep,M=self.margin.at(i,b);cap=M;W=[];unk=0;calls=0
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
        return {'T':cap,'M':M,'epoch':ep,'attain':W[-1]['n'] if W else None,'witnesses':W,'witness_unknowns':unk,'witness_calls':calls}


class StitchedRegionSpace(NoisyRegionSpace):
    """NoisyRegionSpace whose bound is T5; T5 is recomputed on every observation, also after a sticky status."""
    def __init__(self,max_states=4,k=2,eps_bar=0.02,delta_L=0.005,delta_a=0.005,s=2,conf_budget=PRODUCTION_CONF_BUDGET):
        super().__init__(max_states,0,k,s,conf_budget)
        self.lr=StitchedLRBound(max_states,k,eps_bar,delta_L,delta_a,s,conf_budget);self.last=None

    def _bound(self):
        self.last=self.lr.bound(self.readings,self.acts);self.m_bound=self.last['T']

    def _build(self):
        self._bound();super()._build()

    def observe(self,action,obs):
        if not self.readings:raise ValueError('not initialized')
        if action not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        if self.status=='supported':return super().observe(action,obs)
        self.readings.append(tuple(obs));self.acts.append(action);self._bound()


def stitched_supports(initial,actions,observations,max_states=4,k=2,eps_bar=0.02,delta_L=0.005,delta_a=0.005,
                      conf_budget=PRODUCTION_CONF_BUDGET):
    """Supports at steps 1..T (step i+1 on readings 0..i) plus the per-step lr5 record."""
    R=StitchedRegionSpace(max_states,k,eps_bar,delta_L,delta_a,conf_budget=conf_budget);R.initialize(tuple(initial))
    S=[];U=[];Ms=[];st=[];lr={'T':[],'M':[],'epoch':[],'attain':[],'witnesses':[],'witness_unknowns':[],'witness_calls':[]}
    try:
        for a,o in zip(actions,observations):
            row=supports_k(R,k);S.append([x for x,_ in row]);U.append([u for _,u in row]);Ms.append(R.m_bound);st.append(R.status)
            for key in lr:lr[key].append(R.last[key])
            R.observe(a,tuple(o))
    finally:R.close()
    return {'support':S,'unknown':U,'m':Ms,'status':st,'lr':lr,'D':R.lr.D}
