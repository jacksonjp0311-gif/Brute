"""Brute v0.12.0 bounded transfer (BRUTE_PLAN_014 transfer_definition). New file; every existing brute module untouched.

Bounded support (learner-visible): before acting, for action b, the projection of the next code over every complete
Moore machine with <= n states (start state 0) consistent with the evidence so far: brute.region.RegionSpace(n)
.predict_support(b) (UNKNOWN codes count as possible; status != 'supported' -> None). Its unknown count is the number
of UNKNOWN solves the answer used, plus 1 when the region status is 'budget_exhausted' (feasibility UNKNOWN), so a
recorded support with unknown == 0 is exact.

RG (library-free): the SP8 certificate if any; else after burn-in, with SP8 published support S not None, certify c if
the region at n states is {c} and c in S (rule 'rg').

DLF (the bounded transfer license, margin 1): the SP8 certificate if any ('sp8'); else after burn-in with S not None:
  (1) the region at FB = 4 states is {c}, c in S                                                   -> c ('rg')
  (2) the library is alive and unanimous on c, c in S, the region at min(n_L + margin, FB) is {c}   -> c ('license')
Exact: DLF certificates contain RG4 certificates, which contain SP8 certificates; RG4 is sound for every target with
<= 4 states; DLF is sound for every target with <= min(n_L + margin, 4) states.
"""
from __future__ import annotations
from brute.region import RegionSpace
from brute.transfer import TransferTracker

FB=4
MARGIN=1


def region_supports(R):
    """((support_0, unknown_0), (support_1, unknown_1)) of a RegionSpace before the next action."""
    out=[]
    for b in (0,1):
        R.unk=0;s=R.predict_support(b);u=R.unk+int(R.status=='budget_exhausted')
        out.append((list(s) if s is not None else None,u))
    return tuple(out)


def bounded_supports(initial,actions,observations,ns):
    """{str(n): {'support': [[s0, s1] per step], 'unknown': [[u0, u1] per step]}} along a recorded trajectory."""
    out={}
    for n in ns:
        R=RegionSpace(n);R.initialize(tuple(initial));S=[];U=[]
        try:
            for a,o in zip(actions,observations):
                (s0,u0),(s1,u1)=region_supports(R);S.append([s0,s1]);U.append([u0,u1]);R.observe(a,tuple(o))
        finally:R.close()
        out[str(n)]={'support':S,'unknown':U}
    return out


def _single(s):return s[0] if s is not None and len(s)==1 else None


def rg_decide(step,burn_in,sp8_certificate,sp8_support,region_support):
    """(certificate, rule) of RG at one (step, action)."""
    if sp8_certificate is not None:return sp8_certificate,'sp8'
    if step<=burn_in or sp8_support is None:return None,None
    c=_single(region_support)
    if c is not None and c in sp8_support:return c,'rg'
    return None,None


def dlf_decide(step,burn_in,sp8_certificate,sp8_support,region_fb,region_license,library_alive,library_prediction):
    """(certificate, rule, reason). reason is None when certified, else the failing condition (see brute.api.certify2)."""
    if sp8_certificate is not None:return sp8_certificate,'sp8',None
    if step<=burn_in:return None,None,'burn-in'
    if sp8_support is None:return None,None,'sp8-support-unavailable'
    g=_single(region_fb)
    if g is not None and g in sp8_support:return g,'rg',None
    if library_alive is None:return None,None,('outside-sp8-support' if g is not None else 'region-not-singleton')
    if not library_alive:return None,None,'library-refuted'
    p=library_prediction
    if p is None:return None,None,'library-split'
    if p not in sp8_support:return None,None,'outside-sp8-support'
    if _single(region_license)!=p:return None,None,'bounded-region-not-singleton'
    return p,'license',None


class BoundedTransfer:
    """DLF with one library along one trajectory: decide(step, b, ...) before acting, observe(step, a, obs) after."""
    def __init__(self,hypotheses,min_n,initial_obs,burn_in,margin=MARGIN):
        if margin not in (0,1) or isinstance(margin,bool):raise ValueError('margin must be 0 or 1')
        self.margin=margin;self.min_n=min_n;self.license_bound=min(min_n+margin,FB);self.burn_in=burn_in
        self.tracker=TransferTracker(hypotheses,tuple(initial_obs),burn_in)

    def decide(self,step,b,sp8_certificate,sp8_support,supports):
        """supports: {n: region support for action b}; needs FB and license_bound."""
        tr=self.tracker
        return dlf_decide(step,self.burn_in,sp8_certificate,sp8_support,supports[FB],supports[self.license_bound],
                          bool(tr.alive),tr.predict(b))

    def observe(self,step,action,obs):self.tracker.observe(step,action,tuple(obs))
