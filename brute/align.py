"""Brute v0.8.0 aligned lookahead LU-C (arms SP8 on 2x2, BSP8 on breadth), pre-registered in
experiments/BRUTE_PLAN_010.json. New file: the frozen learners are subclassed, never edited or monkeypatched. Not a
default: the release default stays the v0.5.0 rule (Y1k, LU-R) whatever the outcome.

Implementation reading of the plan text (the second implementation experiments/v080_reference.py, committed
earlier, implements the same reading):

* Certification is the frozen SC7 / BSC7 code (SyncEventLearner / BreadthSyncEventLearner, rule 'CTR'), unchanged.
* LU-C N(a,c): as the frozen LU-R N(a,c) (extended family region feasible, not saturated; family support for b a
  single code s; margin support for b equal to s), except that the LU-R condition Y1k_ext(b, 1<<c) == {s} is
  skipped when step t+1 is calm: no recorded event u with (t+1) - u < W, and t+1 >= burn_in. Events the
  hypothetical observation itself could trigger are not anticipated. Non-calm branches use the LU-R Y1k test.
* Any solver budget hit in a branch -> 0 for that branch (frozen _hit accounting). Ties -> passive action (frozen).
* The frozen constructors require policy 'LU-R'; the learner object keeps policy 'LU-R' internally and the
  experiment output reports 'LU-C' (2x2 key 'policy', breadth key 'rule'); diagnostics()['lookahead'] = 'LU-C'.
"""
from __future__ import annotations
from brute.syncevent import SyncEventLearner,BreadthSyncEventLearner


class _AlignedLookahead:
    def _calm_next(self):
        t1=self.steps+1;ev=self.drift_events;ss=ev[-1] if ev else None
        return (ss is None or t1-ss>=self.recency_window) and t1>=self.burn_in

    def _certifiable_after(self,action,code):
        fam=self.support.extended(action,code);self.lookahead_copies+=1;mar=None
        try:
            if fam.feasible is None:self._hit();return 0
            if not fam.feasible:return 0
            sat,u=fam.saturated()
            if u:self._hit();return 0
            if sat:return 0
            calm=self._calm_next();singles={}
            for b in range(getattr(self,'k',2)):
                s,u=fam.support(b)
                if u:self._hit();return 0
                if len(s)!=1:continue
                if calm:singles[b]=s;continue
                y,u=fam.y1k(b,1<<code)
                if u:self._hit();return 0
                if y==s:singles[b]=s
            if not singles:return 0
            mar=self.margin.extended(action,code);self.lookahead_copies+=1
            if mar.feasible is None:self._hit();return 0
            if not mar.feasible:return 0
            tot=0
            for b,s in singles.items():
                ms,u=mar.support(b)
                if u:self._hit();return 0
                tot+=ms==s
            return tot
        finally:
            fam.close()
            if mar is not None:mar.close()

    def diagnostics(self):
        d=super().diagnostics();d['lookahead']='LU-C';return d


class AlignedSyncLearner(_AlignedLookahead,SyncEventLearner):
    """SP8: SC7 certification, LU-C action policy (2x2)."""
    def __init__(self,*args,**kwargs):
        if kwargs.get('rule','CTR')!='CTR':raise ValueError('SP8 uses rule CTR')
        kwargs['rule']='CTR';super().__init__(*args,**kwargs)

    def experiment(self,default_action,counts=False):
        out=super().experiment(default_action,counts);out['policy']='LU-C';return out


class AlignedBreadthSyncLearner(_AlignedLookahead,BreadthSyncEventLearner):
    """BSP8: BSC7 certification, LU-C action policy (breadth, k actions)."""
    def __init__(self,*args,**kwargs):
        if kwargs.get('rule','CTR')!='CTR':raise ValueError('BSP8 uses rule CTR')
        kwargs['rule']='CTR';super().__init__(*args,**kwargs)

    def experiment(self,default_action):
        out=super().experiment(default_action);out['rule']='LU-C';return out
