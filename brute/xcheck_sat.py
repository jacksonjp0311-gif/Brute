"""GX2' second encoding for the v0.6.0 breadth arms (BRUTE_PLAN_008).

Written by the same author as brute/region.py; it is a second implementation, not an independent one.
It deliberately does not import brute/region.py, brute/geometry.py or any enumeration code.

Encoding differences from brute/region.RegionK:
* the hidden path is S[t][q] (exactly-one, pairwise), the machine is T[q][a][r] (at-least-one plus a
  sequential-counter at-most-one) and E[q][c] (exactly-one, pairwise);
* no symmetry breaking: the start state is free (any label); `symmetry=True` adds first-visit naming,
  used only for model counting (GMC), never for the GX2' decisions;
* every query is a guarded clause set plus one assumption; the next-state code is forced through E
  directly (no next-code auxiliaries);
* solver: CaDiCaL 1.9.5 (pysat 'cadical195'), conflict budget 2,000,000 per query (plan GX2').

Every SAT answer is decoded into a concrete machine and start state and replayed in plain Python
(`replay`, `py_*`); a replay failure is counted as a witness failure. UNSAT answers are the proof
that a code is excluded. A query that hits the conflict budget returns None (UNKNOWN); callers must
treat the step as unchecked.
"""
from __future__ import annotations
from itertools import combinations
from pysat.solvers import Solver

SOLVER='cadical195'
CONF_BUDGET=2_000_000


class WitnessFailure(Exception):pass


def replay(machine,masks,actions):
    """Plain-Python replay of a decoded machine: returns the state path or raises WitnessFailure."""
    trans,emit,start=machine;q=start;path=[q]
    if not masks[0]>>emit[q]&1:raise WitnessFailure('emission of the start state outside mask 0')
    for t,a in enumerate(actions):
        q=trans[q][a];path.append(q)
        if not masks[t+1]>>emit[q]&1:raise WitnessFailure(f'emission outside mask {t+1}')
    return path


def py_compat(path,masks,m):
    """A[q] = codes compatible with every mask at a visit of q (only for visited q)."""
    A={}
    for t,q in enumerate(path):A[q]=A.get(q,(1<<m)-1)&masks[t]
    return A


def py_y1k_has(machine,path,masks,actions,n,m,b,mask,c,t0=None):
    trans,emit,start=machine;T=len(actions);A=py_compat(path,masks,m);V=set(path)
    for j in V:
        if not A[j]&mask:continue
        tr=any(path[t]==j and actions[t]==b for t in range(T))
        if tr and A[trans[j][b]]>>c&1:return True
        if not tr and path[T]==j and (any(A[w]>>c&1 for w in V) or len(V)<n):return True
        if t0 is not None and tr and not any(path[t]==j and actions[t]==b for t in range(t0,T)):return True
    return False


class XRegion:
    def __init__(self,n,k,m,masks,actions,conf_budget=CONF_BUDGET,symmetry=False):
        assert len(masks)==len(actions)+1
        self.n=n;self.k=k;self.m=m;self.masks=tuple(masks);self.actions=tuple(actions);self.T=len(actions)
        self.budget=conf_budget;self.top=0;self.unknown=0;self.witness_failures=0;self.queries=0
        C=self.clauses=[];v=self._v;T=self.T
        self.S=[[v() for _ in range(n)] for _ in range(T+1)]
        self.Tq=[[[v() for _ in range(n)] for _ in range(k)] for _ in range(n)]
        self.E=[[v() for _ in range(m)] for _ in range(n)]
        for row in self.S+[e for e in self.E]:
            C.append(list(row));C.extend([-a,-b] for a,b in combinations(row,2))
        for q in range(n):
            for a in range(k):
                row=self.Tq[q][a];C.append(list(row));self._seq_amo(row)
        for t in range(T+1):
            for q in range(n):
                C.append([-self.S[t][q]]+[self.E[q][c] for c in range(m) if self.masks[t]>>c&1])
                if t:
                    for p in range(n):C.append([-self.S[t-1][p],-self.Tq[p][self.actions[t-1]][q],self.S[t][q]])
        if symmetry:
            C.append([self.S[0][0]])
            for t in range(T+1):
                for q in range(1,n):C.append([-self.S[t][q]]+[self.S[u][q-1] for u in range(t)])
        # derived: Ac (mask compatibility), V (visited), Tr (traversed), NX (next state after b)
        self.Ac=[[v() for _ in range(m)] for _ in range(n)];self.V=[v() for _ in range(n)]
        self.Tr=[[v() for _ in range(k)] for _ in range(n)];self.NX=[[v() for _ in range(n)] for _ in range(k)]
        for q in range(n):
            for c in range(m):
                bad=[self.S[t][q] for t in range(T+1) if not self.masks[t]>>c&1]
                C.append([self.Ac[q][c]]+bad);C.extend([-self.Ac[q][c],-x] for x in bad)
            vis=[self.S[t][q] for t in range(T+1)]
            C.append([-self.V[q]]+vis);C.extend([self.V[q],-x] for x in vis)
            for a in range(k):
                xs=[self.S[t][q] for t in range(T) if self.actions[t]==a]
                C.append([-self.Tr[q][a]]+xs);C.extend([self.Tr[q][a],-x] for x in xs)
        for b in range(k):
            for q in range(n):
                for r in range(n):C.append([-self.S[T][q],-self.Tq[q][b][r],self.NX[b][r]])
            C.extend([-x,-y] for x,y in combinations(self.NX[b],2))
        self.s=Solver(name=SOLVER,bootstrap_with=C);self._sat=None

    def _v(self):
        self.top+=1;return self.top

    def _seq_amo(self,xs):
        """Sinz sequential-counter at-most-one."""
        if len(xs)<2:return
        s=[self._v() for _ in xs[:-1]];C=self.clauses
        C.append([-xs[0],s[0]])
        for i in range(1,len(xs)-1):
            C.append([-xs[i],s[i]]);C.append([-s[i-1],s[i]]);C.append([-xs[i],-s[i-1]])
        C.append([-xs[-1],-s[-1]])

    def close(self):
        self.s.delete()

    def _solve(self,assume):
        self.queries+=1;self.s.conf_budget(self.budget);r=self.s.solve_limited(assumptions=assume)
        if r is None:self.unknown+=1
        return r

    def _add(self,C):
        for c in C:self.s.add_clause(c)

    def decode(self,model):
        pos=set(x for x in model if x>0);n,k,m=self.n,self.k,self.m
        def one(row):
            hits=[i for i,x in enumerate(row) if x in pos]
            if len(hits)!=1:raise WitnessFailure('not one-hot')
            return hits[0]
        trans=[[one(self.Tq[q][a]) for a in range(k)] for q in range(n)]
        emit=[one(self.E[q]) for q in range(n)];start=one(self.S[0])
        return trans,emit,start

    def _witness(self,pred):
        """Decode the current model, replay it, and check the query-specific predicate in plain Python."""
        try:
            mach=self.decode(self.s.get_model());path=replay(mach,self.masks,self.actions)
            if not pred(mach,path):raise WitnessFailure('predicate')
        except WitnessFailure:
            self.witness_failures+=1

    # ---- queries ----
    def feasible(self):
        if self._sat is None:
            r=self._solve([])
            if r:self._witness(lambda mach,path:True)
            self._sat=r
        return self._sat

    def _guarded(self,C_fn,pred):
        g=self._v();C=C_fn(g);self._add(C);r=self._solve([g])
        if r:self._witness(pred)
        self._add([[-g]]);return r

    def support(self,b):
        """(codes possible after action b, unknowns); UNKNOWN counts as possible. None if infeasible."""
        f=self.feasible()
        if f is not True:return None,int(f is None)
        out=[];u=0;T=self.T
        for c in range(self.m):
            r=self._guarded(lambda g:[[-g,-self.NX[b][q],self.E[q][c]] for q in range(self.n)],
                            lambda mach,path,c=c:mach[1][mach[0][path[T]][b]]==c)
            if r is None:u+=1
            if r is not False:out.append(c)
        return tuple(out),u

    def saturated(self):
        """(saturated, unknowns): True iff no model leaves a state unvisited; UNKNOWN counts as saturated."""
        f=self.feasible()
        if f is not True:return True,int(f is None)
        r=self._guarded(lambda g:[[-g]+[-x for x in self.V]],lambda mach,path:len(set(path))<self.n)
        return (r is not True),int(r is None)

    def y1k(self,b,mask,t0=None):
        """(Y1k union over codes, unknowns); with t0, edges not traversed since t0 are opened (BR6)."""
        f=self.feasible()
        if f is not True:return None,int(f is None)
        n,m,T=self.n,self.m,self.T;out=[];u=0
        TrR=None
        if t0 is not None:
            TrR=[self._v() for _ in range(n)];C=[]
            for j in range(n):
                xs=[self.S[t][j] for t in range(t0,T) if self.actions[t]==b]
                C.append([-TrR[j]]+xs);C.extend([TrR[j],-x] for x in xs)
            self._add(C)
        for c in range(m):
            def cl(g,c=c):
                v=self._v;P=[v() for _ in range(n)];C=[[-g]+P]
                for j in range(n):
                    C.append([-P[j],self.V[j]])
                    C.append([-P[j]]+[self.Ac[j][cc] for cc in range(m) if mask>>cc&1])
                    k1,k2=v(),v();br=[k1,k2]
                    C.append([-k1,self.Tr[j][b]])
                    for r in range(n):C.append([-k1,-self.Tq[j][b][r],self.Ac[r][c]])
                    C.append([-k2,-self.Tr[j][b]]);C.append([-k2,self.S[T][j]])
                    C.append([-k2]+[-x for x in self.V]+[self._w(j2,c) for j2 in range(n)])
                    if TrR is not None:
                        k3=v();br.append(k3);C.append([-k3,self.Tr[j][b]]);C.append([-k3,-TrR[j]])
                    C.append([-P[j]]+br)
                return C
            r=self._guarded(cl,lambda mach,path,c=c:py_y1k_has(mach,path,self.masks,self.actions,n,m,b,mask,c,t0))
            if r is None:u+=1
            if r is not False:out.append(c)
        return tuple(out),u

    def _w(self,j,c):
        """aux var <-> V[j] and Ac[j][c] (one per (j,c), created lazily)."""
        if not hasattr(self,'_wm'):self._wm={}
        if (j,c) not in self._wm:
            w=self._v();self._wm[(j,c)]=w
            self._add([[-w,self.V[j]],[-w,self.Ac[j][c]],[w,-self.V[j],-self.Ac[j][c]]])
        return self._wm[(j,c)]

    def extended(self,action,code):
        return XRegion(self.n,self.k,self.m,self.masks+(1<<code,),self.actions+(action,),self.budget)


def mask_of(obs,s):
    """bitmask over codes c with every shown bit j equal to (c>>(s-1-j))&1."""
    out=0
    for c in range(2**s):
        if all(o is None or ((c>>(s-1-j))&1)==o for j,o in enumerate(obs)):out|=1<<c
    return out
