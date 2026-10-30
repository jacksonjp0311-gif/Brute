"""RGB6_on_S2 (BRUTE_PLAN_026 arm; deviation #123 item 5): the frozen v0.22.0 RGB6 flip bound (brute.bettingregion
BettingLRBound, unchanged: T6 from the betting e-process over the anytime boundary) with the support region built on the
S2 skeleton (brute.scalesearch.ScaleTolerant: BFS-canonical <= n machines, flips, sum(flips) <= T6), rebuilt per step.
The certificate is the frozen RGN rule (brute.noisyregion.rgn_decide). Host-agnostic: no I/O, threads or processes."""
from __future__ import annotations
from brute.bettingregion import BettingRegionSpace
from brute.scalesearch import ScaleTolerant,QUERY_S

__all__=['ScaleBettingSpace']


class ScaleBettingSpace(BettingRegionSpace):
    def __init__(self,max_states=16,k=3,eps_bar=0.02,delta=0.01,s=2,query_s=QUERY_S):
        super().__init__(max_states,k,eps_bar,delta,s);self.query_s=query_s

    def _build(self):
        self._bound()
        if self.region is not None:self.region.close()
        self.region=ScaleTolerant(self.max_states,self.readings,self.acts,self.m_bound,self.k,self.s,self.query_s)
        self._memo={};self.regions_built+=1;f=self.region.feasible
        if f is None:self.unknown_total+=1;self.status='budget_exhausted';self.region.close();self.region=None
        elif f is False:self.status='grammar_contradicted';self.region.close();self.region=None
        else:self.status='supported'
