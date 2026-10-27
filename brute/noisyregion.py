"""Brute v0.16.0 tolerant region RGN_n(m) (BRUTE_PLAN_018 tolerant_region; docs/research/BRUTE_DEVIATIONS_018.md #97).

New file; brute/region.py is imported unchanged. RGN_n(m) is the frozen RegionK(n) CNF built with every mask fully open
(no observation clause) plus one fresh flip variable f per OBSERVED bit, tied to the bit by XOR clauses
  x[t][q] and e[q][c]  ->  f == (bit_j(c) != observed bit)
(bit j of code c is (c >> (s-1-j)) & 1, as brute.region.codes_mask), and the cardinality constraint sum(f) <= m
(pysat CardEnc, sequential counter). m = 0 is the frozen hard-clause region (every f forced to 0).

m_rule(B, eps_bar, delta): smallest m with P(Bin(B, eps_bar) > m) <= delta, exact rationals (fractions.Fraction of the
decimal strings of eps_bar and delta).

Lemma (Exact, conditional): if the realized flips are <= m and the true machine has <= n states, the true machine with
its emissions is in RGN_n(m) at every step, so a singleton support equals the latent next code. Unconditionally, under
iid flips with eps <= eps_bar, P(any false certificate on a trajectory) <= P(flips > m) <= delta (probabilistic).

NoisyRegionSpace is RegionSpace-shaped (status, unk, initialize, observe, predict_support, close) so that
brute.boundedtransfer.region_supports works on it; the region is rebuilt after each observation; 'grammar_contradicted'
(more than m flips needed) and 'budget_exhausted' are sticky. UNKNOWN solves count a code as possible (conservative).
"""
from __future__ import annotations
from fractions import Fraction
from math import comb
from pysat.card import CardEnc,EncType
from brute.region import RegionK,PRODUCTION_CONF_BUDGET

__all__=['m_rule','tolerant_region','NoisyRegionSpace','noisy_supports','rgn_decide','observed_bits']


def m_rule(B,eps_bar=0.02,delta=0.01):
    if isinstance(B,bool) or not isinstance(B,int) or B<0:raise ValueError('B must be a non-negative int')
    for x in (eps_bar,delta):
        if isinstance(x,bool) or not isinstance(x,(int,float,Fraction)):raise ValueError('eps_bar / delta must be numbers')
    p=Fraction(str(eps_bar)) if isinstance(eps_bar,float) else Fraction(eps_bar)
    d=Fraction(str(delta)) if isinstance(delta,float) else Fraction(delta)
    if not (0<=p<Fraction(1,2)):raise ValueError('eps_bar must be in [0, 0.5)')
    if not (0<d<1):raise ValueError('delta must be in (0, 1)')
    q=1-p;cdf=Fraction(0)
    for m in range(B+1):
        cdf+=comb(B,m)*p**m*q**(B-m)
        if 1-cdf<=d:return m
    return B


def observed_bits(readings):return sum(b is not None for o in readings for b in o)


def tolerant_region(n,readings,actions,m,k=2,s=2,conf_budget=PRODUCTION_CONF_BUDGET):
    """RegionK(n) over readings[0..T] (tuples of s bits or None) with flip variables and sum(flips) <= m."""
    if len(readings)!=len(actions)+1:raise ValueError('need one more reading than actions')
    full=(1<<(1<<s))-1;R=RegionK(n,k,1<<s,[full]*len(readings),actions,conf_budget)
    fs=[];cl=[]
    for t,o in enumerate(readings):
        if len(o)!=s:raise ValueError(f'reading must have {s} entries')
        for j,b in enumerate(o):
            if b is None:continue
            if b not in (0,1):raise ValueError('reading entries must be 0, 1 or None')
            f=R._v();fs.append(f)
            for q in range(n):
                for c in range(1<<s):
                    same=((c>>(s-1-j))&1)==b
                    cl.append([-R.x[t][q],-R.e[q][c],-f] if same else [-R.x[t][q],-R.e[q][c],f])
    if fs and m<len(fs):
        card=CardEnc.atmost(lits=fs,bound=m,top_id=R.nv,encoding=EncType.seqcounter);R.nv=max(R.nv,card.nv);cl+=card.clauses
    R._add(cl);R.flip_vars=len(fs);R.m_bound=m;R._sat=R._solve([])
    return R


class NoisyRegionSpace:
    def __init__(self,max_states,m,k=2,s=2,conf_budget=PRODUCTION_CONF_BUDGET):
        if isinstance(m,bool) or not isinstance(m,int) or m<0:raise ValueError('m must be a non-negative int')
        self.max_states=max_states;self.m_bound=m;self.k=k;self.s=s;self.conf_budget=conf_budget
        self.readings=[];self.acts=[];self.status='uninitialized';self.region=None;self._memo={};self.unk=0;self.unknown_total=0
        self.regions_built=0;self.peak_clauses=0

    def _build(self):
        if self.region is not None:self.region.close()
        self.region=tolerant_region(self.max_states,self.readings,self.acts,self.m_bound,self.k,self.s,self.conf_budget)
        self._memo={};self.regions_built+=1;f=self.region.feasible
        if f is None:self.unknown_total+=1;self.status='budget_exhausted';self.region.close();self.region=None
        elif f is False:self.status='grammar_contradicted';self.region.close();self.region=None
        else:self.status='supported'

    def initialize(self,obs):
        if self.readings:raise ValueError('already initialized')
        self.readings.append(tuple(obs));self._build()

    def observe(self,action,obs):
        if not self.readings:raise ValueError('not initialized')
        if action not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        if self.status!='supported':return
        self.readings.append(tuple(obs));self.acts.append(action);self._build()

    def predict_support(self,action):
        if action not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        if self.status!='supported':return None
        key=('sup',action)
        if key not in self._memo:
            res,u=self.region.support(action);self._memo[key]=(res,u);self.unknown_total+=u
        res,u=self._memo[key];self.unk+=u;return res

    def close(self):
        if self.region is not None:self.region.close();self.region=None


def noisy_supports(initial,actions,observations,n,m,conf_budget=PRODUCTION_CONF_BUDGET):
    """{'m', 'support': [[s0, s1] per step], 'unknown': [[u0, u1]], 'status': [status before each step]} along a trajectory
    (the support at step i is computed before reading i+1, as brute.boundedtransfer.bounded_supports)."""
    from brute.boundedtransfer import region_supports
    R=NoisyRegionSpace(n,m,conf_budget=conf_budget);R.initialize(tuple(initial));S=[];U=[];st=[]
    try:
        for a,o in zip(actions,observations):
            (s0,u0),(s1,u1)=region_supports(R);S.append([s0,s1]);U.append([u0,u1]);st.append(R.status);R.observe(a,tuple(o))
    finally:R.close()
    return {'m':m,'support':S,'unknown':U,'status':st}


def rgn_decide(step,burn_in,support):
    """RGN certificate (#97 item 1): the singleton code iff step > burn_in; no SP8 passthrough or filter."""
    if step<=burn_in or support is None or len(support)!=1:return None
    return support[0]
