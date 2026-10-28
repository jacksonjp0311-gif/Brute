"""Brute v0.19.0 anytime (horizon-free) sequential-margin region RGNA_n (BRUTE_PLAN_021 anytime_margin;
docs/research/v0.19.0/ANYTIME_LEMMA_021.md). New file; brute/seqmargin.py and brute/noisyregion.py are imported unchanged.

AnytimeBoundary(eps_bar, delta) grows m_a(0), m_a(1), ... on demand: m_a(0) = 0 and m_a(b) is the smallest integer
>= m_a(b-1) such that, under iid Bernoulli(eps_bar) flips, P(running flip count exceeded the boundary at some bit <= b)
<= A(b) = delta * (6 / pi_u^2) * sum_{j<=b} 1/j^2 with pi_u = 355/113 > pi, so A(b) < delta for every b (Exact). Exact
fractions.Fraction dynamic program over the running count. No planned horizon: the boundary is prefix-stable (Exact).

AnytimeRegionSpace(n, k) is brute.seqmargin.SeqMarginRegionSpace whose boundary is extended before every rebuild, so it
can be fed one reading at a time with no planned length. anytime_supports() is the batch form (trajectory_supports).
Soundness (Exact, conditional): as brute.seqmargin; if the running flips never exceed m_a(b) and n* <= n, every singleton
support is the latent code; under iid flips with eps <= eps_bar that condition fails with probability < delta.
"""
from __future__ import annotations
from fractions import Fraction
from brute.region import PRODUCTION_CONF_BUDGET
from brute.noisyregion import observed_bits
from brute.seqmargin import SeqMarginRegionSpace,trajectory_supports,crossing_bit

__all__=['PI_U','allowance','AnytimeBoundary','anytime_boundary','crossing_bit','AnytimeRegionSpace','anytime_supports']
PI_U=Fraction(355,113)


def _frac(x,name):
    if isinstance(x,bool) or not isinstance(x,(int,float,Fraction)):raise ValueError(name+' must be a number')
    return Fraction(str(x)) if isinstance(x,float) else Fraction(x)


def _check(p,d):
    if not (0<=p<Fraction(1,2)):raise ValueError('eps_bar must be in [0, 0.5)')
    if not (0<d<1):raise ValueError('delta must be in (0, 1)')


def allowance(b,delta=0.01):
    """A(b) (exact Fraction)."""
    if isinstance(b,bool) or not isinstance(b,int) or b<0:raise ValueError('b must be a non-negative int')
    d=_frac(delta,'delta');return d*6/(PI_U*PI_U)*sum((Fraction(1,j*j) for j in range(1,b+1)),Fraction(0))


class AnytimeBoundary:
    """Incremental m_a(0..L); extend(L) returns a copy of m_a(0..L)."""
    def __init__(self,eps_bar=0.02,delta=0.01):
        self.p=_frac(eps_bar,'eps_bar');self.d=_frac(delta,'delta');_check(self.p,self.d)
        self.scale=self.d*6/(PI_U*PI_U);self.h=Fraction(0);self.m=[0];self.dist=[Fraction(1)];self.crossed=Fraction(0)

    def extend(self,L):
        if isinstance(L,bool) or not isinstance(L,int) or L<0:raise ValueError('length must be a non-negative int')
        q=1-self.p
        while len(self.m)<=L:
            b=len(self.m);self.h+=Fraction(1,b*b);A=self.scale*self.h
            nd=[Fraction(0)]*(len(self.dist)+1)
            for s,x in enumerate(self.dist):nd[s]+=x*q;nd[s+1]+=x*self.p
            mb=self.m[-1]
            while self.crossed+sum(nd[mb+1:])>A:mb+=1
            self.crossed+=sum(nd[mb+1:]);self.dist=nd[:mb+1];self.m.append(mb)
        return self.m[:L+1]


def anytime_boundary(L,eps_bar=0.02,delta=0.01):
    """[m_a(0), ..., m_a(L)]."""
    return AnytimeBoundary(eps_bar,delta).extend(L)


class AnytimeRegionSpace(SeqMarginRegionSpace):
    def __init__(self,max_states,k=2,eps_bar=0.02,delta=0.01,s=2,conf_budget=PRODUCTION_CONF_BUDGET):
        self.anytime=AnytimeBoundary(eps_bar,delta)
        super().__init__(max_states,self.anytime.extend(0),k,s,conf_budget)

    def _build(self):
        self.boundary=self.anytime.extend(observed_bits(self.readings));super()._build()


def anytime_supports(initial,actions,observations,n,k=2,eps_bar=0.02,delta=0.01,conf_budget=PRODUCTION_CONF_BUDGET):
    return trajectory_supports(AnytimeRegionSpace(n,k,eps_bar,delta,conf_budget=conf_budget),initial,actions,observations,k)
