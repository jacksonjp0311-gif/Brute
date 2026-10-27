"""Brute v0.15.0 bounded one-step lookahead action rule (RGL / RGLX) and attested license bound
(BRUTE_PLAN_017 transfer_definition; module name and RGL reading: deviations #86 and #88,
docs/research/BRUTE_DEVIATIONS_017.md). New file; every existing brute module untouched.

RGL (learner-visible action rule): after burn-in, for each action a let O_a be the RegionSpace(4) support for a (the
codes the next reading could take). For each o in O_a, extend the region by the fully observed step (a, o) and ask
whether some next action b then has a single-code support with 0 UNKNOWN solves ("o would force a certificate-ready
reading"). score_a = num_a / den_a (0 when den_a = 0). Exact fraction comparison; ties (0 = 0 included) -> the frozen
SP8 LU-R choice ('sp8'); else argmax ('rgl'). UNKNOWN solves only count against num (conservative) and are reported.
RGLX: RGL while RG4 has not certified the taken action at an earlier step, then the frozen study-015 RSX choice
(brute.regionsplit.rsx_choose) - the RSXL structure with the SP8 deferral replaced by RGL.

The rule is a policy, never a certifier: certificates still come from the frozen RG4 (brute.boundedtransfer.rg_decide),
so soundness is unchanged (Exact for the declared family). The lookahead score is a heuristic for "which action is more
likely to make the next reading certifiable"; it is not a probability (no prior over machines).

attested_license_bound(min_n, margin, family_bound): the library license is used only when min_n + margin >= family
bound, i.e. when the license region IS the family region (H_att_exact). Then the license can never fire beyond RG
(Exact); otherwise the attested arm runs RG only.

Host-agnostic: no I/O, network, threads, subprocesses or global state.
"""
from __future__ import annotations
from fractions import Fraction
from brute.regionsplit import rsx_choose

RULES=('rgl','rsx','sp8')


def lookahead_score(region,action,support):
    """(num, den, unknown) for one action. region: a supported brute.region.RegionSpace; support: its predict_support
    for `action` (sorted codes or None)."""
    if action not in (0,1) or isinstance(action,bool):raise ValueError('action must be 0 or 1')
    if support is None:return 0,0,0
    num=0;unk=0
    for o in support:
        R=region.extended(action,o)
        if R is None:return 0,len(support),len(support)
        try:
            f=R.feasible
            if f is None:unk+=1;continue
            if f is False:continue
            hit=False
            for b in (0,1):
                s,u=R.support(b)
                if u:unk+=1;continue
                if s is not None and len(s)==1:hit=True;break
            num+=int(hit)
        finally:R.close()
    return num,len(support),unk


def lookahead(region,supports):
    """{'num', 'den', 'unknown'} for both actions; supports = brute.boundedtransfer.region_supports(region)."""
    out={'num':[0,0],'den':[0,0],'unknown':[0,0]}
    for a in (0,1):
        n,d,u=lookahead_score(region,a,supports[a][0]);out['num'][a]=n;out['den'][a]=d;out['unknown'][a]=u
    return out


def score(look,a):
    return Fraction(look['num'][a],look['den'][a]) if look['den'][a] else Fraction(0)


def rgl_choose(step,burn_in,look,sp8_action):
    """(action, rule) of RGL at one step; look = lookahead(...) or None at burn-in."""
    if sp8_action not in (0,1) or isinstance(sp8_action,bool):raise ValueError('sp8_action must be 0 or 1')
    if step<=burn_in:return sp8_action,'sp8'
    if look is None:raise ValueError('lookahead required after burn-in')
    s0,s1=score(look,0),score(look,1)
    if s0==s1:return sp8_action,'sp8'
    return (0 if s0>s1 else 1),'rgl'


def rglx_choose(step,burn_in,sizes,look,sp8_action,certified_before):
    """(action, rule) of RGLX: RGL until RG4 certified the taken action at an earlier step, then RSX on the sizes."""
    if not isinstance(certified_before,bool):raise ValueError('certified_before must be a bool')
    if certified_before:return rsx_choose(step,burn_in,sizes,sp8_action)
    return rgl_choose(step,burn_in,look,sp8_action)


def needs_lookahead(step,burn_in,certified_before,mode='rglx'):
    if mode not in ('rgl','rglx'):raise ValueError("mode must be 'rgl' or 'rglx'")
    return step>burn_in and (mode=='rgl' or not certified_before)


def attested_license_bound(min_n,margin,family_bound):
    """True iff the license region equals the family region (min_n + margin >= family_bound)."""
    for v,nm in ((min_n,'min_n'),(margin,'margin'),(family_bound,'family_bound')):
        if isinstance(v,bool) or not isinstance(v,int) or v<0:raise ValueError(f'{nm} must be a non-negative int')
    return min_n+margin>=family_bound
