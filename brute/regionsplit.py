"""Brute v0.13.0 region-split action rule (RSX) and evidence-derived bound (EB) (BRUTE_PLAN_015 transfer_definition).
New file; every existing brute module untouched.

RSX (learner-visible action rule): at step t > burn_in act b = argmax |bounded_support[4][b]| (the RegionSpace(4)
projection of the next code, UNKNOWN codes counted as possible; a None support counts as size 0). Ties go to the SP8
LU-R choice (with two actions a tie between maximisers is k_0 == k_1); if max size <= 1 (every support a singleton or
unavailable) the SP8 LU-R choice. Steps <= burn_in use the SP8 choice. The rule is a policy, not a certifier: it changes
which evidence is gathered, never what is certified (certification stays RG4 / DLF, frozen in brute.boundedtransfer).

EB (evidence-derived bound): n_E = min{n in 1..4 : the RegionSpace(n) region is non-empty, i.e. its support for action 0
is not None}; bound = min(n_E + margin, 4). Decision at (t, b): the RG4 decision if it certifies; else after burn-in with
SP8 support S not None and bound not None, certify c if the region at `bound` states is {c} and c in S (rule 'eb').
Inferred (not Exact): EB is sound only for targets whose true state count is <= bound; n_E is a lower bound on the
state count, so EB can be unsound when the target needs more than n_E + margin states.
"""
from __future__ import annotations
from brute.boundedtransfer import FB,rg_decide,_single

RULES=('rsx','sp8')


def bounded_sizes(supports):
    """[k_0, k_1] from region_supports(...) output ((s_0, u_0), (s_1, u_1)); None -> 0."""
    return [len(s) if s is not None else 0 for s,_ in supports]


def rsx_choose(step,burn_in,sizes,sp8_action):
    """(action, rule) of RSX at one step."""
    if sp8_action not in (0,1):raise ValueError('sp8_action must be 0 or 1')
    if step<=burn_in:return sp8_action,'sp8'
    k0,k1=sizes
    if max(k0,k1)<=1 or k0==k1:return sp8_action,'sp8'
    return (0 if k0>k1 else 1),'rsx'


def evidence_bound(nonempty,margin):
    """(n_E, bound) from {n: bool} for n in 1..4."""
    if margin not in (1,2):raise ValueError('margin must be 1 or 2')
    nE=next((n for n in (1,2,3,4) if nonempty[n]),None)
    return nE,(min(nE+margin,FB) if nE is not None else None)


def eb_decide(step,burn_in,sp8_certificate,sp8_support,region_fb,region_bound,bound):
    """(certificate, rule) of EB at one (step, action); rule in 'sp8' | 'rg' | 'eb' | None."""
    c,r=rg_decide(step,burn_in,sp8_certificate,sp8_support,region_fb)
    if c is not None:return c,r
    if step<=burn_in or sp8_support is None or bound is None:return None,None
    e=_single(region_bound)
    if e is not None and e in sp8_support:return e,'eb'
    return None,None
