"""Brute v0.16.0 embeddable certify interface, version 6 (BRUTE_PLAN_018; additive: brute/api/certify.py ... certify5.py
untouched). Noise-tolerant certification RGN4 on readings whose observed bits may be flipped iid with eps <= eps_bar.

    certify6(initial, actions, observations, planned_observed_bits, eps_bar=0.02, delta=0.01, family_bound=4, burn_in=8)
      initial: (b0, b1) with entries 0 / 1 / None; actions: [0 | 1, ...]; observations: one reading after each action
      planned_observed_bits: B = observed bits in the WHOLE planned trajectory, fixed before the first action (the m rule
      is only valid if B does not depend on the readings).
    -> {'api': 'brute.certify/6', 'm', 'planned_observed_bits', 'observed_bits', 'steps',
        'supports': [[s0, s1] per step 1 .. T+1] (sorted codes, None when no member remains),
        'unknown': [[u0, u1] ...], 'certificates': [[c0, c1] ...] (step T+1 = the next reading),
        'status': 'supported' | 'grammar_contradicted' | 'budget_exhausted',
        'soundness': {'kind': 'probabilistic', 'delta': delta, 'conditional_on': 'flips <= m and n* <= family_bound'}}

m = brute.noisyregion.m_rule(B, eps_bar, delta). A certificate at step t > burn_in is the single code consistent with some
<= family_bound-state Moore machine after at most m flips (no SP8 passthrough). If the realized flips are <= m and the true
machine has <= family_bound states, every certificate equals the noise-free reading (Exact); under the iid model with
eps <= eps_bar a case has a false certificate with probability <= delta. Outside the attestation the answer means nothing.
family_bound: only 4 is supported. Host-agnostic: no I/O, network, threads, subprocesses or global state.
"""
from __future__ import annotations
from fractions import Fraction
from brute.api.certify import _act,_obs
from brute.boundedtransfer import FB,region_supports
from brute.noisyregion import m_rule,NoisyRegionSpace,rgn_decide

API='brute.certify/6'
CONDITIONAL_ON='flips <= m and n* <= family_bound'
__all__=['API','CONDITIONAL_ON','certify6','soundness']


def soundness(delta):return {'kind':'probabilistic','delta':delta,'conditional_on':CONDITIONAL_ON}


def _num(x,name):
    if isinstance(x,bool) or not isinstance(x,(int,float,Fraction)):raise ValueError(name+' must be a number')
    return x


def certify6(initial,actions,observations,planned_observed_bits,eps_bar=0.02,delta=0.01,family_bound=4,burn_in=8):
    if isinstance(family_bound,bool) or family_bound!=FB:raise ValueError('family_bound must be 4 in brute.certify/6')
    if isinstance(burn_in,bool) or not isinstance(burn_in,int) or burn_in<0:raise ValueError('burn_in must be a non-negative int')
    B=planned_observed_bits
    if isinstance(B,bool) or not isinstance(B,int) or B<0:raise ValueError('planned_observed_bits must be a non-negative int')
    _num(eps_bar,'eps_bar');_num(delta,'delta')
    if not (0<=eps_bar<0.5):raise ValueError('eps_bar must be in [0, 0.5)')
    if not (0<delta<1):raise ValueError('delta must be in (0, 1)')
    init=_obs(initial);acts=[_act(a) for a in actions];obs=[_obs(o) for o in observations]
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    seen=sum(b is not None for o in [init]+obs for b in o)
    if seen>B:raise ValueError('more observed bits than planned_observed_bits')
    m=m_rule(B,eps_bar,delta);R=NoisyRegionSpace(FB,m);S=[];U=[];C=[]
    try:
        R.initialize(init)
        for t in range(1,len(acts)+2):
            (s0,u0),(s1,u1)=region_supports(R);S.append([s0,s1]);U.append([u0,u1]);C.append([rgn_decide(t,burn_in,s) for s in (s0,s1)])
            if t<=len(acts):R.observe(acts[t-1],obs[t-1])
        status=R.status
    finally:R.close()
    return {'api':API,'m':m,'planned_observed_bits':B,'observed_bits':seen,'steps':len(acts),'supports':S,'unknown':U,
            'certificates':C,'status':status,'soundness':soundness(delta)}
