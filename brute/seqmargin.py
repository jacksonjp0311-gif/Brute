"""Brute v0.17.0 sequential-margin tolerant region RGNB_n (BRUTE_PLAN_019 sequential_margin; docs/research/
BRUTE_DEVIATIONS_019.md #101 items 1-4). New file; brute/noisyregion.py and brute/region.py are imported unchanged.

boundary(B, eps_bar, delta) -> [m(0), ..., m(B)]: m(0) = 0 and m(b) is the smallest integer >= m(b-1) such that, under iid
Bernoulli(eps_bar) flips, P(running flip count exceeded the boundary at some bit <= b) <= delta * b / B (linear alpha
spending), by an exact dynamic program over the running count (fractions.Fraction of the decimal strings).

SeqMarginRegionSpace(n, boundary, k) is brute.noisyregion.NoisyRegionSpace whose cardinality bound is set, before every
rebuild, to m(b_t) where b_t = observed bits in readings 0..t (#101 item 1: one constraint sum(flips) <= m(b_t) per build;
prefix constraints are not added, which can only make the region larger, so soundness is unchanged). Emptiness and
budget_exhausted stay sticky (#101 item 3).

Lemma (Exact, conditional): if the running flip count never exceeds m(b) and n* <= n, the true machine is in the region at
every step (its total flips over readings 0..t are <= m(b_t)), so every singleton support is the latent code.
"""
from __future__ import annotations
from fractions import Fraction
from brute.region import PRODUCTION_CONF_BUDGET
from brute.noisyregion import NoisyRegionSpace,observed_bits,rgn_decide

__all__=['boundary','crossing_bit','SeqMarginRegionSpace','supports_k','trajectory_supports','seqmargin_supports','rgnb_decide']
rgnb_decide=rgn_decide


def _frac(x,name):
    if isinstance(x,bool) or not isinstance(x,(int,float,Fraction)):raise ValueError(name+' must be a number')
    return Fraction(str(x)) if isinstance(x,float) else Fraction(x)


def boundary(B,eps_bar=0.02,delta=0.01):
    if isinstance(B,bool) or not isinstance(B,int) or B<0:raise ValueError('B must be a non-negative int')
    p=_frac(eps_bar,'eps_bar');d=_frac(delta,'delta')
    if not (0<=p<Fraction(1,2)):raise ValueError('eps_bar must be in [0, 0.5)')
    if not (0<d<1):raise ValueError('delta must be in (0, 1)')
    q=1-p;m=[0];dist=[Fraction(1)];crossed=Fraction(0)
    for b in range(1,B+1):
        nd=[Fraction(0)]*(len(dist)+1)
        for s,x in enumerate(dist):nd[s]+=x*q;nd[s+1]+=x*p
        mb=m[-1]
        while crossed+sum(nd[mb+1:])>d*b/B:mb+=1
        crossed+=sum(nd[mb+1:]);dist=nd[:mb+1];m.append(mb)
    return m


def crossing_bit(flip_sequence,bd):
    """First bit b (1-based, observed-bit order) whose running flip count exceeds bd[b]; None if never."""
    s=0
    for b,x in enumerate(flip_sequence,start=1):
        s+=int(bool(x))
        if s>bd[b]:return b
    return None


class SeqMarginRegionSpace(NoisyRegionSpace):
    def __init__(self,max_states,bd,k=2,s=2,conf_budget=PRODUCTION_CONF_BUDGET):
        if not isinstance(bd,(list,tuple)) or not bd or any(isinstance(x,bool) or not isinstance(x,int) or x<0 for x in bd):
            raise ValueError('boundary must be a non-empty list of non-negative ints')
        if any(bd[i+1]<bd[i] for i in range(len(bd)-1)):raise ValueError('boundary must be non-decreasing')
        super().__init__(max_states,bd[0],k,s,conf_budget);self.boundary=list(bd)

    def _build(self):
        b=observed_bits(self.readings)
        if b>=len(self.boundary):raise ValueError('more observed bits than the boundary covers')
        self.m_bound=self.boundary[b];super()._build()


def supports_k(R,k):
    """[(support_b, unknown_b) for b in 0..k-1] of a region space before the next action (as region_supports, k actions)."""
    out=[]
    for b in range(k):
        R.unk=0;s=R.predict_support(b);u=R.unk+int(R.status=='budget_exhausted')
        out.append((list(s) if s is not None else None,u))
    return out


def trajectory_supports(R,initial,actions,observations,k):
    """Supports at steps 1..T (step i+1 computed on readings 0..i), with the bound in force at each step."""
    R.initialize(tuple(initial));S=[];U=[];M=[];st=[]
    try:
        for a,o in zip(actions,observations):
            row=supports_k(R,k);S.append([x for x,_ in row]);U.append([u for _,u in row]);M.append(R.m_bound);st.append(R.status)
            R.observe(a,tuple(o))
    finally:R.close()
    return {'support':S,'unknown':U,'m':M,'status':st}


def seqmargin_supports(initial,actions,observations,n,bd,k=2,conf_budget=PRODUCTION_CONF_BUDGET):
    return trajectory_supports(SeqMarginRegionSpace(n,bd,k,conf_budget=conf_budget),initial,actions,observations,k)
