"""Brute v0.22.0 betting-test eps-adaptive likelihood-ratio region RGB6_n (BRUTE_PLAN_025 method, amendment A1;
docs/research/v0.22.0/BETTING_LEMMA_025.md, deviation #119). New file; brute/lrregion.py, brute/anytimemargin.py,
brute/noisyregion.py and brute/region.py are imported unchanged.

Level 0 (p_0 = eps_bar = 1/50): m_a0 = AnytimeBoundary(eps_bar, 1/400); offsets D0 = lr_offsets(.., 1/50, 1/400).
Adaptive levels j = 1, 2 (p_j = 1/100, 1/200): betting test of e >= p_j with the fixed mixture lambda_l = l/(4(1-p_j)),
l = 1..4, K_j(t, b) = mean_l (1 + lambda_l p_j)^(b-t) (1 - lambda_l (1-p_j))^t; level j becomes active (sticky) once
K_j(T0, b) >= 1/delta_cj = 800; active offsets Dj = lr_offsets(.., p_j, 1/800). Per step:
  T0 = min(m_a0(b), min over exhibited witnesses (w + D0_n - 1)),
  T6 = min(m_a0(b), min over exhibited witnesses (w + D_eff_n - 1)),  D_eff = elementwise min over level 0 and active levels,
with the RGL4 witness search (brute.lrregion rule, #108 cap) started from cap = m_a0(b) and loop m + D_eff_n - 1 < cap;
after an activation the search is continued under the new D_eff at the same step.

Soundness (Exact, conditional on the attested noise model; BETTING_LEMMA_025 §3): every singleton support after the burn-in
is the latent code except with probability <= 1/400 + 1/400 + 2(1/800 + 1/800) = 1/100. Horizon-free and prefix-stable.
Exact note (§4): with <= 178 observed bits no adaptive level can activate, so at horizon 88 RGB6 = T0.
"""
from __future__ import annotations
from fractions import Fraction
from brute.region import PRODUCTION_CONF_BUDGET
from brute.noisyregion import NoisyRegionSpace,tolerant_region,observed_bits
from brute.anytimemargin import AnytimeBoundary
from brute.seqmargin import supports_k
from brute.lrregion import lr_offsets,_decode,_frac

__all__=['DELTA','DELTA_A0','LEVELS','THRESHOLD','lambdas','wealth','levels','make_levels','BettingLRBound','BettingRegionSpace','betting_supports']
DELTA=Fraction(1,100);DELTA_A0=Fraction(1,400);THRESHOLD=800


def make_levels(eps_bar=0.02,delta=0.01):
    """((j, p_j, delta_Lj, delta_cj)) and delta_a0: p_j = eps_bar / 2^j (j = 0, 1, 2); delta_a0 = delta_L0 = delta/4,
    delta_cj = delta_Lj = delta/8 (j = 1, 2). Defaults give the study-025 values (BETTING_LEMMA_025 §2)."""
    p=_frac(eps_bar,'eps_bar');d=_frac(delta,'delta')
    if not (0<p<Fraction(1,2)):raise ValueError('eps_bar must be in (0, 0.5) for the betting method')
    if not (0<d<1):raise ValueError('delta must be in (0, 1)')
    return ((0,p,d/4,None),(1,p/2,d/8,d/8),(2,p/4,d/8,d/8)),d/4


LEVELS,_A0=make_levels();assert _A0==DELTA_A0


def lambdas(p):
    p=Fraction(p);return [Fraction(l,4)/(1-p) for l in (1,2,3,4)]


def wealth(p,t,b):
    """K(t, b) for H: e >= p (exact Fraction); t is capped at b (flips <= bits)."""
    if isinstance(t,bool) or not isinstance(t,int) or t<0 or not isinstance(b,int) or b<0:raise ValueError('t, b must be non-negative ints')
    p=Fraction(p);t=min(t,b);return sum((1+l*p)**(b-t)*(1-l*(1-p))**t for l in lambdas(p))/4


def levels(max_states=4,k=2,s=2,L=LEVELS):
    return [{'j':j,'p':str(p),'delta_L':str(dL),'delta_c':None if dc is None else str(dc),'D':lr_offsets(max_states,k,p,dL,s)}
            for j,p,dL,dc in L]


class BettingLRBound:
    """Per-step T0 / T6; start points s_n carried between calls (readings must only grow)."""
    def __init__(self,max_states=4,k=2,eps_bar=0.02,delta=0.01,s=2,conf_budget=PRODUCTION_CONF_BUDGET):
        self.N=max_states;self.k=k;self.s=s;self.conf_budget=conf_budget;self.L,self.delta_a0=make_levels(eps_bar,delta)
        self.levels=levels(max_states,k,s,self.L);self.D={l['j']:l['D'] for l in self.levels}
        self.anytime=AnytimeBoundary(self.L[0][1],self.delta_a0);self.start=[0]*max_states;self.active=set();self.sat_calls=0

    def _deff(self):
        lv=[0]+sorted(self.active);return [min(self.D[j][n] for j in lv) for n in range(self.N)]

    def bound(self,readings,actions):
        b=observed_bits(readings);ma=self.anytime.extend(b)[b];W=[];unk=0;calls=0
        while True:
            De=self._deff();cap=min([ma]+[w['w']+De[w['n']-1]-1 for w in W])
            for n in range(1,self.N+1):
                m=self.start[n-1];D=De[n-1]
                while m+D-1<cap:
                    R=tolerant_region(n,readings,actions,m,self.k,self.s,self.conf_budget);calls+=1
                    try:
                        f=R.feasible
                        if f is True:W.append(_decode(R,n,self.k,self.s,m));cap=m+D-1;break
                        if f is None:unk+=1
                    finally:R.close()
                    m+=1
                self.start[n-1]=m
            T0=min([ma]+[w['w']+self.D[0][w['n']-1]-1 for w in W])
            K={str(j):wealth(p,T0,b) for j,p,_,dc in self.L if dc is not None}
            new={j for j,p,_,dc in self.L if dc is not None and K[str(j)]>=1/dc}-self.active
            if not new:break
            self.active|=new
        self.sat_calls+=calls;De=self._deff();T=min([ma]+[w['w']+De[w['n']-1]-1 for w in W])
        eh=min(p for j,p,_,_ in self.L if j==0 or j in self.active)
        return {'T':T,'T0':T0,'M':ma,'active':sorted(self.active),'eps_hat_u':str(eh),'K':{j:round(float(v),6) for j,v in K.items()},
                'attain':W[-1]['n'] if W and T<ma else None,'witnesses':W,'witness_unknowns':unk,'witness_calls':calls}


class BettingRegionSpace(NoisyRegionSpace):
    """NoisyRegionSpace whose bound is T6; T6 is recomputed on every observation, also after a sticky status."""
    def __init__(self,max_states=4,k=2,eps_bar=0.02,delta=0.01,s=2,conf_budget=PRODUCTION_CONF_BUDGET):
        super().__init__(max_states,0,k,s,conf_budget)
        self.lr=BettingLRBound(max_states,k,eps_bar,delta,s,conf_budget);self.last=None

    def _bound(self):
        self.last=self.lr.bound(self.readings,self.acts);self.m_bound=self.last['T']

    def _build(self):
        self._bound();super()._build()

    def observe(self,action,obs):
        if not self.readings:raise ValueError('not initialized')
        if action not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        if self.status=='supported':return super().observe(action,obs)
        self.readings.append(tuple(obs));self.acts.append(action);self._bound()


def betting_supports(initial,actions,observations,max_states=4,k=2,eps_bar=0.02,delta=0.01,conf_budget=PRODUCTION_CONF_BUDGET):
    """Supports at steps 1..T (step i+1 on readings 0..i) plus the per-step b6 record."""
    R=BettingRegionSpace(max_states,k,eps_bar,delta,conf_budget=conf_budget);R.initialize(tuple(initial))
    S=[];U=[];Ms=[];st=[];keys=('T','T0','M','active','eps_hat_u','attain','witnesses','witness_unknowns','witness_calls')
    lr={k_:[] for k_ in keys};K={}
    try:
        for a,o in zip(actions,observations):
            row=supports_k(R,k);S.append([x for x,_ in row]);U.append([u for _,u in row]);Ms.append(R.m_bound);st.append(R.status)
            for key in keys:lr[key].append(R.last[key])
            for j,v in R.last['K'].items():K.setdefault(j,[]).append(v)
            R.observe(a,tuple(o))
    finally:R.close()
    lr['K']=K
    return {'support':S,'unknown':U,'m':Ms,'status':st,'lr':lr,'levels':R.lr.levels}
