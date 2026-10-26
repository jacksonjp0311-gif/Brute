"""Brute v0.8.0 jump-hull certification (arm J8 on 2x2), pre-registered in experiments/BRUTE_PLAN_010.json.

New file: the frozen learners (brute/syncevent.py, brute/driftsound.py and below) are subclassed, never edited or
monkeypatched. Not a default: the release default stays the v0.5.0 rule (Y1k, LU-R) whatever the outcome.

Implementation reading of the plan text, fixed here (the second implementation experiments/v080_reference.py,
committed earlier, implements the same reading):

* JumpRegionK = RegionK (same variables, symmetry clause and bound) with the transition constraint into the LAST
  observation removed (transitions for t = 1..T-1 only) and that transition not counted as a traversal (Tr over
  t < T-1). The hidden state at T may be any state whose output fits mask T. At T = 0 there is no transition and
  JumpRegionK is identical to RegionK (no special case).
* Y1kJ(b, mask) = RegionK.y1k evaluated on JumpRegionK; it contains Y1k(b, mask) (fewer constraints).
* J8 = frozen SyncEventLearner(rule='RO') (S7); a certificate c that S7 keeps is kept only if Y1kJ(action, mask of
  the last observation) == {c} (cert_rule path + '+hull'), else ABSTAIN / RESYNC_AMBIGUOUS ('hull-downgraded').
  Hull queries go through RegionSpace._q, so their solver unknowns count toward the SOLVER_BUDGET overlay.
* hull_record(): {'0': sorted Y1kJ(0, mask), '1': sorted Y1kJ(1, mask)} and the unknowns of those two queries while
  the family is supported, else (None, 0). Recorded by the study harness after the step's predicts (memo reuse).
"""
from __future__ import annotations
from bgr90.symbolic import mask_for_observation
from brute.region import RegionK
from brute.syncevent import SyncEventLearner
from pysat.solvers import Solver


class JumpRegionK(RegionK):
    """RegionK with the last transition (observation T-1 -> T) removed and not counted as a traversal."""
    def __init__(self,n,k,m,masks,actions,conf_budget,solver='g3',symmetry=True):
        if len(masks)!=len(actions)+1:raise ValueError('need one more mask than actions')
        self.n=n;self.k=k;self.m=m;self.masks=list(masks);self.actions=list(actions);self.T=T=len(actions)
        self.solver=solver;self.symmetry=symmetry;self.conf_budget=conf_budget
        self.nv=0;self.cl=[];v=self._v;K=range(k);M=range(m)
        self.x=[[v() for _ in range(n)] for _ in range(T+1)]
        self.d=[[[v() for _ in range(n)] for _ in K] for _ in range(n)]
        self.e=[[v() for _ in M] for _ in range(n)]
        for row in self.x:self._one(row)
        for q in range(n):
            for a in K:self._one(self.d[q][a])
            self._one(self.e[q])
        self.cl.append([self.x[0][0]])
        if symmetry:
            for t in range(T+1):
                for q in range(1,n):self.cl.append([-self.x[t][q]]+[self.x[u][q-1] for u in range(t)])
        for t in range(1,T):                       # the transition into T is omitted (jump)
            a=actions[t-1]
            for q in range(n):
                for r in range(n):self.cl.append([-self.x[t-1][q],-self.d[q][a][r],self.x[t][r]])
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
        self.Tr=[[v() for _ in K] for _ in range(n)]
        for q in range(n):
            for a in K:
                xs=[self.x[t][q] for t in range(T-1) if actions[t]==a]   # the jump is not a traversal
                for b in xs:self.cl.append([-b,self.Tr[q][a]])
                self.cl.append([-self.Tr[q][a]]+xs)
        self.nx=[[v() for _ in range(n)] for _ in K];self.nc=[[v() for _ in M] for _ in K]
        for b in K:
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


class JumpSyncLearner(SyncEventLearner):
    """J8: S7 (rule 'RO') with the jump-hull condition on every kept certificate."""
    def __init__(self,*args,**kwargs):
        if kwargs.get('rule','RO')!='RO':raise ValueError('J8 uses rule RO')
        super().__init__(*args,**kwargs);self._jr=None;self._jr_built=None
        self.hull_downgrades=0;self.hull_queries=0

    def _jump_region(self):
        sp=self.support
        if self._jr_built!=sp.regions_built:
            if self._jr is not None:self._jr.close()
            self._jr=JumpRegionK(sp.max_states,sp.k,sp.m,sp.masks,sp.acts,sp.conf_budget,sp.region.solver,sp.region.symmetry)
            self._jr_built=sp.regions_built
        return self._jr

    def _hull(self,action,mask):
        """Y1kJ(action, mask) via the support space memo (unknowns added to support.unk); None if unsupported."""
        sp=self.support
        if sp.status!='supported':return None
        def fn():
            self.hull_queries+=1;r,u=self._jump_region().y1k(action,mask)
            return (tuple(range(sp.m)) if r is None else r),u      # UNKNOWN feasibility: every code (never certifies)
        return sp._q(('y1kJ',action,mask),fn)

    def _rule_decide(self,action,mask,cert):
        keep,path=super()._rule_decide(action,mask,cert)
        if not keep:return keep,path
        if self._hull(action,mask)!=(cert,):
            self.hull_downgrades+=1;return False,'hull-downgraded'
        return True,path+'+hull'

    def hull_record(self):
        """({'0': [...], '1': [...]}, unknowns) while the family is supported, else (None, 0)."""
        sp=self.support
        if sp.status!='supported':return None,0
        mask=mask_for_observation(sp.evidence[-1][1]);u0=sp.unk
        out={str(b):sorted(self._hull(b,mask)) for b in (0,1)}
        sp.unk=u0                                               # recording never changes a published forecast
        return out,sum(sp._memo[('y1kJ',b,mask)][1] for b in (0,1))

    def diagnostics(self):
        d=super().diagnostics();d.update({'certification':'J8 jump-hull','hull_downgrades':self.hull_downgrades,
                                          'hull_queries':self.hull_queries});return d

    def close(self):
        if self._jr is not None:self._jr.close();self._jr=None
        return super().close()
