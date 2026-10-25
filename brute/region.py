"""Brute v0.5.0 backend: RegionK, the constraint region generalised to k actions and m = 2**s codes, tri-state.

Pre-registered in experiments/BRUTE_PLAN_007.json (backend). New file: brute/geometry.py (v0.4.0, 2 actions x 4 codes,
UNKNOWN folded into False) stays frozen. The encoding is the BRUTE_PLAN_006 representation with range(2) -> range(k)
and range(4) -> range(m): one-hot x[t][q], d[q][a][r], e[q][c]; canonical first-visit naming; derived A, V, Tr, nx, nc.

Tri-state: every solve returns True (SAT), False (UNSAT) or None (UNKNOWN: the conflict budget was hit). Every query
returns (answer, unknowns) where `unknowns` counts the UNKNOWN solves that the answer used. Conservative semantics:
  support / y1k code query UNKNOWN -> the code counts as possible
  saturated() UNKNOWN              -> saturated (blocks certification)
  feasibility UNKNOWN              -> RegionSpace status 'budget_exhausted' (sticky, as enumeration budget exhaustion)
RegionSpace is a SymbolicLearner-shaped adapter (status, evidence, predict_support, observe, max_states, count=None)
so the frozen v0.1.0-v0.4.0 learner code can run on the region; rows are never enumerated (count is None).
"""
from __future__ import annotations
from itertools import combinations
from pysat.solvers import Solver

SOLVER='g3'
PRODUCTION_CONF_BUDGET=100000
STRESS_CONF_BUDGET=20


def codes_mask(obs,s):
    """Bitmask over m=2**s codes compatible with obs (tuple of s bits or None; bit j of code c is (c>>(s-1-j))&1)."""
    if len(obs)!=s:raise ValueError(f'observation must have {s} entries')
    out=0
    for c in range(1<<s):
        if all(b is None or ((c>>(s-1-j))&1)==b for j,b in enumerate(obs)):out|=1<<c
    for b in obs:
        if b not in (None,0,1):raise ValueError('observation entries must be 0, 1 or None')
    return out


class RegionK:
    """CNF region of complete <=n Moore machines (k actions, m codes) consistent with masks[0..T] under actions."""
    def __init__(self,n,k,m,masks,actions,conf_budget=PRODUCTION_CONF_BUDGET,solver=SOLVER,symmetry=True):
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
        for t in range(1,T+1):
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
                xs=[self.x[t][q] for t in range(T) if actions[t]==a]
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

    # ---- plumbing ---------------------------------------------------------------------------------------------------
    def _v(self):
        self.nv+=1;return self.nv

    def _amo(self,lits):
        for a,b in combinations(lits,2):self.cl.append([-a,-b])

    def _one(self,lits):
        self.cl.append(list(lits));self._amo(lits)

    def _solve(self,assume):
        """True / False / None (UNKNOWN: conflict budget hit). conf_budget None = exact (no limit)."""
        self.calls+=1
        if self.conf_budget is None:return self.s.solve(assumptions=assume)
        self.s.conf_budget(self.conf_budget);r=self.s.solve_limited(assumptions=assume)
        if r is None:self.unknown+=1
        return r

    def _add(self,clauses):
        for c in clauses:self.s.add_clause(c)

    def close(self):
        if self.s is not None:self.s.delete();self.s=None

    def __enter__(self):return self

    def __exit__(self,*exc):self.close()

    def __del__(self):
        try:self.close()
        except Exception:pass

    @property
    def size(self):return {'variables':self.base_vars,'clauses':self.base_clauses}

    # ---- queries (answer, unknowns) ----------------------------------------------------------------------------------
    @property
    def feasible(self):
        """True / False / None (UNKNOWN)."""
        return self._sat

    def support(self,b):
        """Projection on the next code after action b: (sorted tuple, unknowns); UNKNOWN codes are included."""
        if self._sat is not True:return None,int(self._sat is None)
        out=[];u=0
        for c in range(self.m):
            r=self._solve([self.nc[b][c]])
            if r is None:u+=1
            if r is not False:out.append(c)
        return tuple(out),u

    def saturated(self):
        """(True iff every machine visits all n states, unknowns); UNKNOWN counts as saturated."""
        if self._sat is not True:return None,int(self._sat is None)
        g=self._v();self._add([[-g]+[-x for x in self.V]])
        r=self._solve([g]);self._add([[-g]])
        if r is None:return True,1
        return (not r),0

    def y1k(self,b,mask):
        """Y1k union (frozen geometry.fibre_support with one mask): successor codes for action b over every visited state
        compatible with `mask`; unknown edges open only at the current state. (sorted tuple, unknowns)."""
        if self._sat is not True:return None,int(self._sat is None)
        n=self.n;out=[];u=0;P=None
        for c in range(self.m):
            v=self._v;g=v();C=[]
            P=[v() for _ in range(n)]
            C.append([-g]+P)
            for a_,b_ in combinations(P,2):C.append([-g,-a_,-b_])
            for q in range(n):
                C.append([-P[q],self.V[q]])
                C.append([-P[q]]+[self.A[q][cc] for cc in range(self.m) if mask>>cc&1])
            K1=[v() for _ in range(n)];K2=[v() for _ in range(n)];W=[v() for _ in range(n)]
            for j in range(n):
                C.append([-P[j],K1[j],K2[j]])
                C.append([-K1[j],self.Tr[j][b]])
                for r in range(n):C.append([-K1[j],-self.d[j][b][r],self.A[r][c]])
                C.append([-K2[j],-self.Tr[j][b]]);C.append([-K2[j],self.x[self.T][j]])
                C.append([-K2[j]]+W+[-x for x in self.V])
                C.append([-W[j],self.V[j]]);C.append([-W[j],self.A[j][c]])
            self._add(C)
            r=self._solve([g])
            if r is None:u+=1
            if r is not False:out.append(c)
            self._add([[-g]])
        return tuple(out),u

    def extended(self,action,code):
        """The region after one more fully observed step (action, code): a lookahead copy (new solver)."""
        return RegionK(self.n,self.k,self.m,self.masks+[1<<code],self.actions+[action],self.conf_budget,self.solver,self.symmetry)


class RegionSpace:
    """SymbolicLearner-shaped version space on RegionK (no rows). One region per evidence prefix, rebuilt lazily after
    each observation; answers are memoised per step and each use adds its unknowns to `self.unk` (reset by callers)."""
    def __init__(self,max_states,max_prefixes=None,k=2,s=2,conf_budget=PRODUCTION_CONF_BUDGET):
        self.max_states=max_states;self.max_prefixes=max_prefixes;self.k=k;self.s=s;self.m=1<<s
        self.conf_budget=conf_budget
        self.evidence=[];self.status='uninitialized';self.masks=[];self.acts=[]
        self.region=None;self._memo={};self.unk=0;self.unknown_total=0
        self.max_rows_seen=0;self.last_failure=None;self.peak_clauses=0;self.peak_vars=0;self.regions_built=0

    count=None   # rows are not enumerated
    belief=property(lambda self:(_ for _ in ()).throw(AttributeError('RegionSpace enumerates no rows')))

    def _build(self):
        if self.region is not None:self.region.close()
        self.region=RegionK(self.max_states,self.k,self.m,self.masks,self.acts,self.conf_budget);self._memo={}
        self.regions_built+=1;self.peak_clauses=max(self.peak_clauses,self.region.base_clauses)
        self.peak_vars=max(self.peak_vars,self.region.base_vars)
        f=self.region.feasible
        if f is None:
            self.unknown_total+=1;self.status='budget_exhausted';self.last_failure='SAT conflict budget hit on feasibility'
            self.region.close();self.region=None
        elif f is False:
            self.status='grammar_contradicted';self.last_failure='region empty';self.region.close();self.region=None
        else:self.status='supported'

    def initialize(self,obs):
        if self.evidence:raise ValueError('already initialized')
        self.masks=[codes_mask(obs,self.s)];self.evidence.append((None,tuple(obs)));self._build()

    def observe(self,action,obs):
        if not self.evidence:raise ValueError('not initialized')
        if action not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        mask=codes_mask(obs,self.s);self.evidence.append((action,tuple(obs)))
        if self.status!='supported':return
        self.masks.append(mask);self.acts.append(action);self._build()

    def _q(self,key,fn):
        if key not in self._memo:
            res,u=fn();self._memo[key]=(res,u);self.unknown_total+=u
        res,u=self._memo[key];self.unk+=u;return res

    def predict_support(self,action):
        if action not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        if self.status!='supported':return None
        return self._q(('sup',action),lambda:self.region.support(action))

    def saturated(self):
        if self.status!='supported':return None
        return self._q(('sat',),self.region.saturated)

    def y1k(self,action,mask):
        if self.status!='supported':return None
        return self._q(('y1k',action,mask),lambda:self.region.y1k(action,mask))

    def extended(self,action,code):
        """RegionK copy after (action, full code); the caller closes it. None if not supported."""
        if self.status!='supported':return None
        return self.region.extended(action,code)

    def close(self):
        if self.region is not None:self.region.close();self.region=None
