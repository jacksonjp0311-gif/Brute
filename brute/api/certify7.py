"""Brute v0.17.0 embeddable certify interface, version 7 (BRUTE_PLAN_019; additive: brute/api/certify.py ... certify6.py
untouched). Sequential-margin noise-tolerant certification RGNB4, for 2 or 3 actions.

    certify7(initial, actions, observations, planned_observed_bits, num_actions=2, eps_bar=0.02, delta=0.01,
             family_bound=4, burn_in=8)
      initial: (b0, b1) with entries 0 / 1 / None; actions: [0 .. num_actions-1, ...]; observations: one reading per action
      planned_observed_bits: B = observed bits in the WHOLE planned trajectory, fixed before the first action.
    -> {'api': 'brute.certify/7', 'num_actions', 'planned_observed_bits', 'observed_bits', 'steps',
        'boundary': [m(0) .. m(B)] (brute.seqmargin.boundary), 'm': [bound in force at steps 1 .. T+1],
        'supports': [[s_0 .. s_{k-1}] per step 1 .. T+1] (sorted codes, None when no member remains),
        'unknown': [[u_0 ..] ...], 'certificates': [[c_0 ..] ...] (step T+1 = the next reading),
        'status': 'supported' | 'grammar_contradicted' | 'budget_exhausted',
        'soundness': {'kind': 'probabilistic', 'delta': delta, 'conditional_on': 'running flips <= m(b) and n* <= family_bound'}}

A certificate at step t > burn_in is the single code consistent with some <= family_bound-state Moore machine after at most
m(b_t) flips in readings 0..t (b_t observed bits so far). If the running flip count never exceeds the boundary and the
true machine has <= family_bound states, every certificate equals the noise-free reading (Exact); under iid flips with
eps <= eps_bar a case has a false certificate with probability <= delta. Outside the attestation the answer means nothing.
family_bound: only 4. Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from fractions import Fraction
from brute.api.certify import _obs
from brute.boundedtransfer import FB
from brute.seqmargin import boundary,SeqMarginRegionSpace,supports_k,rgnb_decide

API='brute.certify/7'
CONDITIONAL_ON='running flips <= m(b) and n* <= family_bound'
__all__=['API','CONDITIONAL_ON','certify7','soundness']


def soundness(delta):return {'kind':'probabilistic','delta':delta,'conditional_on':CONDITIONAL_ON}


def _num(x,name):
    if isinstance(x,bool) or not isinstance(x,(int,float,Fraction)):raise ValueError(name+' must be a number')
    return x


def _int(x,name):
    if isinstance(x,bool) or not isinstance(x,int):raise ValueError(name+' must be an int')
    return x


def certify7(initial,actions,observations,planned_observed_bits,num_actions=2,eps_bar=0.02,delta=0.01,family_bound=4,burn_in=8):
    if _int(num_actions,'num_actions') not in (2,3):raise ValueError('num_actions must be 2 or 3')
    if isinstance(family_bound,bool) or family_bound!=FB:raise ValueError('family_bound must be 4 in brute.certify/7')
    if _int(burn_in,'burn_in')<0:raise ValueError('burn_in must be a non-negative int')
    B=_int(planned_observed_bits,'planned_observed_bits')
    if B<0:raise ValueError('planned_observed_bits must be a non-negative int')
    _num(eps_bar,'eps_bar');_num(delta,'delta')
    if not (0<=eps_bar<0.5):raise ValueError('eps_bar must be in [0, 0.5)')
    if not (0<delta<1):raise ValueError('delta must be in (0, 1)')
    k=num_actions;init=_obs(initial);acts=list(actions);obs=[_obs(o) for o in observations]
    for a in acts:
        if isinstance(a,bool) or not isinstance(a,int) or a not in range(k):raise ValueError(f'action must be an int in 0..{k-1}')
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    seen=sum(b is not None for o in [init]+obs for b in o)
    if seen>B:raise ValueError('more observed bits than planned_observed_bits')
    bd=boundary(B,eps_bar,delta);R=SeqMarginRegionSpace(FB,bd,k);S=[];U=[];C=[];M=[]
    try:
        R.initialize(init);rd=[init]+obs
        for t in range(1,len(acts)+2):
            # the bound in force after readings 0..t-1 (a contradicted space stops rebuilding, so R.m_bound can be stale)
            row=supports_k(R,k);S.append([s for s,_ in row]);U.append([u for _,u in row]);M.append(bd[sum(b is not None for o in rd[:t] for b in o)])
            C.append([rgnb_decide(t,burn_in,s) for s,_ in row])
            if t<=len(acts):R.observe(acts[t-1],obs[t-1])
        status=R.status
    finally:R.close()
    return {'api':API,'num_actions':k,'planned_observed_bits':B,'observed_bits':seen,'steps':len(acts),'boundary':bd,'m':M,
            'supports':S,'unknown':U,'certificates':C,'status':status,'soundness':soundness(delta)}
