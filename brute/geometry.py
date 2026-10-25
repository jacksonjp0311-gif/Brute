"""Brute v0.4.0 geometry: the version space as a constraint region (an H-representation) instead of a list of rows.

Pre-registered in experiments/BRUTE_PLAN_006.json (representation). The enumeration learners store the version space
of <=n deterministic Moore machines consistent with the evidence as its points (rows; a V-representation). A
ConstraintRegion stores the constraints that cut it out (CNF over complete machines; an H-representation): one-hot
state-at-time x[t][q], transition d[q][a][r] and emission e[q][c]. Canonical first-visit naming (state q >= 1 is used
only after q-1 was visited) picks one representative per relabelling orbit, so the region lives on the quotient by
S_n -- the same naming the enumeration uses. Every learner query is a geometric operation on the region:

  feasible        non-emptiness (status supported vs contradicted)
  support(b)      projection on the next-code coordinate after action b
  saturated()     emptiness of the sub-region with an unvisited state
  fibre_support   Y1k / F2 certificate: projection over the fibre of the latest observation(s)
  observation     a cut (new clauses); `extended(...)` builds the region after one more hypothetical observation

Region size is O(n^2 T) clauses, independent of how many machines survive. Exactness against the enumeration is a
gated, measured claim (GR1/GR1b), not an assumption; the enumeration remains the production backend in v0.4.0.
This is a step toward the project's long-term geometric-reasoning goal; it is not evidence of general intelligence.
"""
from __future__ import annotations
from itertools import combinations
from pysat.solvers import Solver
from bgr90.symbolic import mask_for_observation

ALL=0b1111
SOLVER='g3'   # Glucose 3 (python-sat)


def full_mask(code):return 1<<code


class ConstraintRegion:
    """CNF region of complete <=n Moore machines consistent with masks[0..T] under actions[0..T-1].

    Derived variables (both directions): A[q][c] (code c compatible with every visit of q), V[q] (q visited),
    Tr[q][a] (edge (q,a) traversed), nx[b]/nc[b] (next state / next code after action b from the current state)."""
    def __init__(self,n,masks,actions,solver=SOLVER,symmetry=True,conf_budget=None):
        if len(masks)!=len(actions)+1:raise ValueError('need one more mask than actions')
        self.n=n;self.masks=list(masks);self.actions=list(actions);self.T=T=len(actions)
        self.nv=0;self.cl=[];v=self._v
        self.x=[[v() for _ in range(n)] for _ in range(T+1)]
        self.d=[[[v() for _ in range(n)] for _ in range(2)] for _ in range(n)]
        self.e=[[v() for _ in range(4)] for _ in range(n)]
        for row in self.x:self._one(row)
        for q in range(n):
            for a in range(2):self._one(self.d[q][a])
            self._one(self.e[q])
        self.cl.append([self.x[0][0]])
        if symmetry:
            for t in range(T+1):
                for q in range(1,n):self.cl.append([-self.x[t][q]]+[self.x[u][q-1] for u in range(t)])
        for t in range(1,T+1):
            a=actions[t-1]
            for q in range(n):
                for r in range(n):self.cl.append([-self.x[t-1][q],-self.d[q][a][r],self.x[t][r]])
        for t,m in enumerate(masks):
            for q in range(n):self.cl.append([-self.x[t][q]]+[self.e[q][c] for c in range(4) if m>>c&1])
        self.A=[[v() for _ in range(4)] for _ in range(n)]
        for q in range(n):
            for c in range(4):
                bad=[self.x[t][q] for t,m in enumerate(masks) if not m>>c&1]
                for b in bad:self.cl.append([-self.A[q][c],-b])
                self.cl.append([self.A[q][c]]+bad)
        self.V=[v() for _ in range(n)]
        for q in range(n):
            xs=[self.x[t][q] for t in range(T+1)]
            for b in xs:self.cl.append([-b,self.V[q]])
            self.cl.append([-self.V[q]]+xs)
        self.Tr=[[v() for _ in range(2)] for _ in range(n)]
        for q in range(n):
            for a in range(2):
                xs=[self.x[t][q] for t in range(T) if actions[t]==a]
                for b in xs:self.cl.append([-b,self.Tr[q][a]])
                self.cl.append([-self.Tr[q][a]]+xs)
        self.nx=[[v() for _ in range(n)] for _ in range(2)];self.nc=[[v() for _ in range(4)] for _ in range(2)]
        for b in range(2):
            for q in range(n):
                for r in range(n):self.cl.append([-self.x[T][q],-self.d[q][b][r],self.nx[b][r]])
            self._amo(self.nx[b])
            for r in range(n):
                for c in range(4):self.cl.append([-self.nx[b][r],-self.e[r][c],self.nc[b][c]])
            self._amo(self.nc[b])
        self.base_vars=self.nv;self.base_clauses=len(self.cl)
        self.s=Solver(name=solver,bootstrap_with=self.cl);self.calls=0;self.solver=solver
        self.conf_budget=conf_budget;self.unknown=0
        self._sat=self._solve([])

    @classmethod
    def from_observations(cls,n,initial,evidence,**kw):
        """initial observation and [(action, observation), ...] as recorded in traces."""
        return cls(n,[mask_for_observation(initial)]+[mask_for_observation(o) for _,o in evidence],[a for a,_ in evidence],**kw)

    def extended(self,action,code):
        """The region after one more fully observed step (action, code) -- a lookahead copy."""
        return ConstraintRegion(self.n,self.masks+[full_mask(code)],self.actions+[action],self.solver,conf_budget=self.conf_budget)

    def _v(self):
        self.nv+=1;return self.nv

    def _amo(self,lits):
        for a,b in combinations(lits,2):self.cl.append([-a,-b])

    def _one(self,lits):
        self.cl.append(list(lits));self._amo(lits)

    def _solve(self,assume):
        """Exact by default. With conf_budget (GR2 scaling runs only) a query that exceeds the conflict budget is
        counted in self.unknown and treated as unsatisfiable; callers must report or exclude such steps."""
        self.calls+=1
        if self.conf_budget is None:return self.s.solve(assumptions=assume)
        self.s.conf_budget(self.conf_budget);r=self.s.solve_limited(assumptions=assume)
        if r is None:self.unknown+=1;return False
        return r

    def _add(self,clauses):
        for c in clauses:self.s.add_clause(c)

    def close(self):
        self.s.delete()

    def __enter__(self):return self

    def __exit__(self,*exc):self.close()

    @property
    def feasible(self):return self._sat

    @property
    def size(self):return {'variables':self.base_vars,'clauses':self.base_clauses}

    def support(self,b):
        """Projection on the next code after action b (sorted tuple) or None if the region is empty."""
        if not self._sat:return None
        return tuple(c for c in range(4) if self._solve([self.nc[b][c]]))

    def saturated(self):
        """True iff every machine in the region visits all n states (no room left for an unseen state)."""
        if not self._sat:return None
        g=self._v();self._add([[-g]+[-x for x in self.V]])
        r=not self._solve([g]);self._add([[-g]]);return r

    def fibre_support(self,b,mask_hist,act_hist=()):
        """Union of successor codes for action b over the fibre: visited states reachable from a state compatible with
        mask_hist[0] through act_hist with each target compatible with the next mask (known edges only). Unknown edges
        are open (any visited state's codes, plus ALL if a state is unvisited) only at the current state (Y1k)."""
        if not self._sat:return None
        n=self.n;w=len(act_hist)
        if len(mask_hist)!=w+1:raise ValueError('mask_hist must be one longer than act_hist')
        out=[]
        for c in range(4):
            v=self._v;g=v();C=[]
            P=[[v() for _ in range(n)] for _ in range(w+1)]
            for i in range(w+1):
                C.append([-g]+P[i])
                for a_,b_ in combinations(P[i],2):C.append([-g,-a_,-b_])
                for q in range(n):
                    C.append([-P[i][q],self.V[q]])
                    C.append([-P[i][q]]+[self.A[q][cc] for cc in range(4) if mask_hist[i]>>cc&1])
            for i in range(1,w+1):
                a=act_hist[i-1]
                for q in range(n):
                    for r in range(n):
                        C.append([-P[i-1][q],-P[i][r],self.Tr[q][a]]);C.append([-P[i-1][q],-P[i][r],self.d[q][a][r]])
            K1=[v() for _ in range(n)];K2=[v() for _ in range(n)];W=[v() for _ in range(n)]
            for j in range(n):
                C.append([-P[w][j],K1[j],K2[j]])
                C.append([-K1[j],self.Tr[j][b]])
                for r in range(n):C.append([-K1[j],-self.d[j][b][r],self.A[r][c]])
                C.append([-K2[j],-self.Tr[j][b]]);C.append([-K2[j],self.x[self.T][j]])
                C.append([-K2[j]]+W+[-x for x in self.V])
                C.append([-W[j],self.V[j]]);C.append([-W[j],self.A[j][c]])
            self._add(C)
            if self._solve([g]):out.append(c)
            self._add([[-g]])
        return tuple(out)


def _count(fam,mar,b_codes_hist,resync):
    """LU / LU-R count on lookahead regions fam (<=4) and mar (<=5)."""
    if not fam.feasible or fam.saturated():return 0
    tot=0;hist=b_codes_hist
    for b in (0,1):
        s=fam.support(b)
        if len(s)!=1:continue
        if resync and fam.fibre_support(b,*hist)!=s:continue
        if not mar.feasible:return 0
        tot+=mar.support(b)==s
    return tot


def lookahead_score(r4,r5,action,resync=True,fibre_w=0,depth=1):
    """LU (resync False) / LU-R / LU2-R / F2-scored lookahead from regions r4 (<=4) and r5 (<=5), both feasible and
    with no alarm (the caller applies those gates). Mirrors the enumeration rule; lookahead copies are `extended`."""
    S=r4.support(action);tot=0.
    for c in S:
        f=r4.extended(action,c);m=r5.extended(action,c)
        h=_hist(f,fibre_w)
        n1=_count(f,m,h,resync) if f.feasible else 0;v=n1
        if depth==2 and f.feasible and not f.saturated() and m.feasible:
            best=0.
            for a2 in (0,1):
                S2=f.support(a2);t=0.
                for c2 in S2:
                    f2=f.extended(a2,c2);m2=m.extended(a2,c2)
                    t+=_count(f2,m2,_hist(f2,fibre_w),resync) if f2.feasible else 0
                    f2.close();m2.close()
                if S2:best=max(best,t/len(S2))
            v+=best
        tot+=v;f.close();m.close()
    return round(tot/len(S),12) if S else 0.


def _hist(region,w):
    masks=region.masks[-(w+1):];acts=region.actions[len(region.actions)-(len(masks)-1):] if len(masks)>1 else []
    return masks,acts
