"""Brute v0.9.0 jump-WINDOW certification (arm J9 on 2x2), pre-registered in experiments/BRUTE_PLAN_011.json
(jump_window_definition). New file: frozen learners (brute/align.py, brute/syncevent.py, brute/region.py and below)
are subclassed, never edited or monkeypatched. Not a default: the release default stays the v0.5.0 rule.

Implementation reading of the plan text, fixed here (the second implementation experiments/v090_reference.py,
committed earlier, implements the same reading by row enumeration):

* JumpWindowRegionK(K) = RegionK (same variables, symmetry clause, state bound, x0 = 0) plus one selector j_t for
  each t in J(T) = {max(1, T-K+1), ..., T-1} with at most one selector true. The transition clause into observation
  t becomes [-x[t-1][q], -d[q][a][r], x[t][r], j_t]: with j_t true the state at t is free (still bound by the mask,
  the symmetry clause and every later transition). The transition into the LAST observation T is always kept.
* A jump transition is not a traversal: for t + 1 in J(T), Tr[q][a] counts x[t][q] only through an auxiliary
  y <-> x[t][q] AND NOT j_{t+1}. With J(T) empty the region is RegionK exactly (no selector, same clauses).
* Y1kW(b, mask) = RegionK.y1k evaluated on JumpWindowRegionK; it contains Y1k(b, mask) (every RegionK machine is a
  window machine with all selectors false).
* J9 = brute.align.AlignedSyncLearner (SP8: rule CTR, LU-C) unchanged, plus: a certificate c that SP8 keeps is kept
  only if Y1kW(action, mask of the last observation) == {c} (cert_rule path + '+whull'), else ABSTAIN /
  RESYNC_AMBIGUOUS ('whull-downgraded'). Hull queries go through RegionSpace._q (memo key ('y1kW', action, mask)),
  so their solver unknowns count toward SOLVER_BUDGET. UNKNOWN feasibility: every code (never certifies).
  The LU-C lookahead is unchanged (it does not anticipate the hull; disclosed in the plan).
* hull_record(): ({'0': sorted Y1kW(0, mask), '1': sorted Y1kW(1, mask)}, unknowns of those two queries) while the
  family is supported, else (None, 0); recorded by the study harness after the step's predicts (memo reuse).
"""
from __future__ import annotations
from bgr90.symbolic import mask_for_observation
from brute.region import RegionK
from brute.align import AlignedSyncLearner
from pysat.solvers import Solver

WINDOW_K=4


def window_positions(T,K):
    """J(T) = {max(1, T-K+1), ..., T-1}."""
    return list(range(max(1,T-K+1),T))


class JumpWindowRegionK(RegionK):
    """RegionK with at most one free (jump) transition into an observation of J(T); the last transition is kept."""
    def __init__(self,n,k,m,masks,actions,conf_budget,solver='g3',symmetry=True,K=WINDOW_K):
        if len(masks)!=len(actions)+1:raise ValueError('need one more mask than actions')
        self.n=n;self.k=k;self.m=m;self.masks=list(masks);self.actions=list(actions);self.T=T=len(actions)
        self.solver=solver;self.symmetry=symmetry;self.conf_budget=conf_budget;self.window_K=K
        self.nv=0;self.cl=[];v=self._v;KA=range(k);M=range(m)
        self.x=[[v() for _ in range(n)] for _ in range(T+1)]
        self.d=[[[v() for _ in range(n)] for _ in KA] for _ in range(n)]
        self.e=[[v() for _ in M] for _ in range(n)]
        for row in self.x:self._one(row)
        for q in range(n):
            for a in KA:self._one(self.d[q][a])
            self._one(self.e[q])
        self.cl.append([self.x[0][0]])
        if symmetry:
            for t in range(T+1):
                for q in range(1,n):self.cl.append([-self.x[t][q]]+[self.x[u][q-1] for u in range(t)])
        self.window=window_positions(T,K);self.j={t:v() for t in self.window}
        self._amo(list(self.j.values()))
        for t in range(1,T+1):
            a=actions[t-1];sel=[self.j[t]] if t in self.j else []
            for q in range(n):
                for r in range(n):self.cl.append([-self.x[t-1][q],-self.d[q][a][r],self.x[t][r]]+sel)
        for t,mk in enumerate(masks):
            for q in range(n):self.cl.append([-self.x[t][q]]+[self.e[q][c] for c in M if mk>>c&1])
        self.A=[[v() for _ in M] for _ in range(n)]
        for q in range(n):
            for c in M:
                bad=[self.x[t][q] for t,mk in enumerate(masks) if not mk>>c&1]
                for b in bad:self.cl.append([-self.A[q][c],-b])
                self.cl.append([self.A[q][c]]+bad)
        self.V=[v() for _ in range(n)]
        for q in range(n):
            xs=[self.x[t][q] for t in range(T+1)]
            for b in xs:self.cl.append([-b,self.V[q]])
            self.cl.append([-self.V[q]]+xs)
        self.Tr=[[v() for _ in KA] for _ in range(n)]
        for q in range(n):
            for a in KA:
                xs=[]
                for t in range(T):
                    if actions[t]!=a:continue
                    if t+1 in self.j:                      # traversal only if the transition t -> t+1 is not the jump
                        y=v();jj=self.j[t+1];xq=self.x[t][q]
                        self.cl+= [[-y,xq],[-y,-jj],[y,-xq,jj]];xs.append(y)
                    else:xs.append(self.x[t][q])
                for b in xs:self.cl.append([-b,self.Tr[q][a]])
                self.cl.append([-self.Tr[q][a]]+xs)
        self.nx=[[v() for _ in range(n)] for _ in KA];self.nc=[[v() for _ in M] for _ in KA]
        for b in KA:
            for q in range(n):
                for r in range(n):self.cl.append([-self.x[T][q],-self.d[q][b][r],self.nx[b][r]])
            self._amo(self.nx[b])
            for r in range(n):
                for c in M:self.cl.append([-self.nx[b][r],-self.e[r][c],self.nc[b][c]])
            self._amo(self.nc[b])
        self.base_vars=self.nv;self.base_clauses=len(self.cl)
        self.s=Solver(name=solver,bootstrap_with=self.cl);self.cl=None
        self.calls=0;self.unknown=0
        self._sat=self._solve([])


class WindowSyncLearner(AlignedSyncLearner):
    """J9: SP8 (rule CTR, LU-C) with the jump-window hull condition on every kept certificate."""
    def __init__(self,*args,window_K=WINDOW_K,**kwargs):
        super().__init__(*args,**kwargs);self.window_K=window_K;self._jr=None;self._jr_built=None
        self.hull_downgrades=0;self.hull_queries=0

    def _window_region(self):
        sp=self.support
        if self._jr_built!=sp.regions_built:
            if self._jr is not None:self._jr.close()
            self._jr=JumpWindowRegionK(sp.max_states,sp.k,sp.m,sp.masks,sp.acts,sp.conf_budget,sp.region.solver,
                                       sp.region.symmetry,K=self.window_K)
            self._jr_built=sp.regions_built
        return self._jr

    def _hull(self,action,mask):
        """Y1kW(action, mask) via the support space memo (unknowns added to support.unk); None if unsupported."""
        sp=self.support
        if sp.status!='supported':return None
        def fn():
            self.hull_queries+=1;r,u=self._window_region().y1k(action,mask)
            return (tuple(range(sp.m)) if r is None else r),u      # UNKNOWN feasibility: every code (never certifies)
        return sp._q(('y1kW',action,mask),fn)

    def _rule_decide(self,action,mask,cert):
        keep,path=super()._rule_decide(action,mask,cert)
        if not keep:return keep,path
        if self._hull(action,mask)!=(cert,):
            self.hull_downgrades+=1;return False,'whull-downgraded'
        return True,path+'+whull'

    def hull_record(self):
        """({'0': [...], '1': [...]}, unknowns) while the family is supported, else (None, 0)."""
        sp=self.support
        if sp.status!='supported':return None,0
        mask=mask_for_observation(sp.evidence[-1][1]);u0=sp.unk
        out={str(b):sorted(self._hull(b,mask)) for b in (0,1)}
        sp.unk=u0                                               # recording never changes a published forecast
        return out,sum(sp._memo[('y1kW',b,mask)][1] for b in (0,1))

    def diagnostics(self):
        d=super().diagnostics();d.update({'certification':'J9 jump-window hull','window_K':self.window_K,
                                          'hull_downgrades':self.hull_downgrades,'hull_queries':self.hull_queries});return d

    def close(self):
        if self._jr is not None:self._jr.close();self._jr=None
        return super().close()
