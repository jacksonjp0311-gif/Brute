"""Brute v0.14.0 deferred region-split action rule (RSXL) and margin-2 library license (DLF2)
(BRUTE_PLAN_016 transfer_definition). New file; every existing brute module untouched.

RSXL (learner-visible action rule): act with the frozen SP8 LU-R choice while the gated certifier RG4 has issued no
certificate for the taken action at any earlier step on this trajectory (deferred = True); from the step after RG4's
first taken-action certificate on, act with the frozen study-015 RSX choice (brute.regionsplit.rsx_choose). Reading of
"no certificate" as "no certificate for the taken action" (RG4's first_cert_step): deviation #75,
docs/research/BRUTE_DEVIATIONS_016.md. Exact consequence: the RSXL trajectory equals the SP8 trajectory through RG4's
first certificate, so RG4 on RSXL certifies first at the same step as RG4 on SP8 (speedup unchanged); RSXL can only
change which evidence arrives afterwards. The rule is a policy, never a certifier.

DLF2 (reported only): brute.boundedtransfer.dlf_decide with the license region at min(n_L + margin, 4) for margin 1 or
2. Margin 1 equals the frozen BoundedTransfer; margin 2 is new here (the frozen class accepts 0 / 1 only). Soundness
of the license is Exact only when the target's true state count is <= the license bound (study-016 diagnostic,
docs/research/BRUTE_DIAG_LICENSE_016.md); with n_L >= 2 the margin-2 bound is 4 = FB, so DLF2 equals RG4 there (Exact).

Host-agnostic: no I/O, network, threads, subprocesses or global state.
"""
from __future__ import annotations
from brute.boundedtransfer import FB,dlf_decide
from brute.regionsplit import rsx_choose
from brute.transfer import TransferTracker

RULES=('rsx','sp8')
MARGINS=(1,2)


def rsxl_choose(step,burn_in,sizes,sp8_action,certified_before):
    """(action, rule) of RSXL at one step. certified_before: RG4 certified the taken action at some step < step."""
    if not isinstance(certified_before,bool):raise ValueError('certified_before must be a bool')
    if sp8_action not in (0,1) or isinstance(sp8_action,bool):raise ValueError('sp8_action must be 0 or 1')
    if not certified_before:return sp8_action,'sp8'
    return rsx_choose(step,burn_in,sizes,sp8_action)


class Deferral:
    """Tracks certified_before along one trajectory: call taken(certificate) once per step with RG4's certificate for the
    action actually taken (None if UNKNOWN), after choosing and before the next step."""
    def __init__(self):self.certified_before=False;self.first_cert_step=None;self.step=0

    def taken(self,certificate):
        self.step+=1
        if certificate is not None and not self.certified_before:self.certified_before=True;self.first_cert_step=self.step
        return self.certified_before


def license_bound(min_n,margin):
    if margin not in MARGINS or isinstance(margin,bool):raise ValueError('margin must be 1 or 2')
    if isinstance(min_n,bool) or not isinstance(min_n,int) or min_n<1:raise ValueError('min_n must be a positive int')
    return min(min_n+margin,FB)


class MarginTransfer:
    """DLF with one library along one trajectory at margin 1 or 2 (frozen dlf_decide; region at license_bound)."""
    def __init__(self,hypotheses,min_n,initial_obs,burn_in,margin=1):
        self.margin=margin;self.min_n=min_n;self.license_bound=license_bound(min_n,margin);self.burn_in=burn_in
        self.tracker=TransferTracker(hypotheses,tuple(initial_obs),burn_in)

    def decide(self,step,b,sp8_certificate,sp8_support,supports):
        """supports: {n: region support for action b}; needs FB and license_bound."""
        tr=self.tracker
        return dlf_decide(step,self.burn_in,sp8_certificate,sp8_support,supports[FB],supports[self.license_bound],
                          bool(tr.alive),tr.predict(b))

    def observe(self,step,action,obs):self.tracker.observe(step,action,tuple(obs))
