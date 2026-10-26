"""Brute v0.10.0 support-window certification (arm J10), pre-registered in experiments/BRUTE_PLAN_012.json
(J10_definition). New file: brute/jumpwindow.py (J9) and every frozen learner are subclassed, never edited.

* supW(b) = RegionK.support(b) evaluated on JumpWindowRegionK(K=4): the exact projection of the next code after b over
  every (machine, at most one window jump) consistent with the evidence (frozen tri-state: UNKNOWN codes are included;
  UNKNOWN feasibility -> every code, never certifies).
* J10 = J9 with ONE change: a certificate c that SP8 keeps survives iff supW(action) == (c,) (cert_rule path + '+wsupp'),
  else ABSTAIN / RESYNC_AMBIGUOUS ('wsupp-downgraded'). Memo key ('supW', action) through RegionSpace._q.
* hull_record(): ({'0': sorted supW(0), '1': sorted supW(1)}, unknowns) while the family is supported, else (None, 0).
"""
from __future__ import annotations
from brute.align import AlignedSyncLearner
from brute.jumpwindow import WindowSyncLearner


class SupportWindowLearner(WindowSyncLearner):
    """J10: SP8 (rule CTR, LU-C) with the exact jump-window SUPPORT condition on every kept certificate."""

    def _supw(self,action):
        sp=self.support
        if sp.status!='supported':return None
        def fn():
            self.hull_queries+=1;r,u=self._window_region().support(action)
            return (tuple(range(sp.m)) if r is None else r),u
        return sp._q(('supW',action),fn)

    def _rule_decide(self,action,mask,cert):
        keep,path=AlignedSyncLearner._rule_decide(self,action,mask,cert)
        if not keep:return keep,path
        if self._supw(action)!=(cert,):
            self.hull_downgrades+=1;return False,'wsupp-downgraded'
        return True,path+'+wsupp'

    def hull_record(self):
        sp=self.support
        if sp.status!='supported':return None,0
        u0=sp.unk;out={str(b):sorted(self._supw(b)) for b in (0,1)};sp.unk=u0
        return out,sum(sp._memo[('supW',b)][1] for b in (0,1))

    def diagnostics(self):
        d=super().diagnostics();d['certification']='J10 jump-window support';return d
