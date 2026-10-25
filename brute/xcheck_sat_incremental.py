"""Incremental GX2' second encoding (post-release verification of v0.6.0; NOT part of the frozen v0.6.0 sources).

Same encoding and same queries as brute/xcheck_sat.XRegion (frozen), but one CaDiCaL 1.9.5 instance per (case, bound N)
is kept alive and the evidence is added layer by layer instead of re-encoding the whole problem for every evidence
prefix. Differences from XRegion are purely structural:

* machine variables Tq[q][a][r] and E[q][c] are created once per solver (same constraints as XRegion);
* each evidence position t is a *layer* with its own path row S[t][q] (exactly-one), its mask clause, its transition
  clauses from layer t-1, and the derived variables Ac/V/Tr defined by a chain over the previous layer
  (Ac_t[q][c] <-> Ac_{t-1}[q][c] and (c in mask_t or not S_t[q]); V_t[q] <-> V_{t-1}[q] or S_t[q];
  Tr_t[q][a] <-> Tr_{t-1}[q][a] or (a_{t-1}=a and S_{t-1}[q])). These are logically equivalent to XRegion's flat
  definitions over the whole prefix;
* every layer's clauses are guarded by an activation literal g_L. Committed (main-trajectory) layers get the unit [g_L];
  a one-step hypothetical extension (used by the LU-R score and the status update) is queried under the assumption g_L,
  and disabled with [-g_L] when a sibling is committed;
* per-step queries (support, saturation, Y1k, Y1k-recent) are the same guarded clause sets as XRegion, solved under
  assumptions [g_L, g_query] and retired with the unit [-g_query];
* optional (`symmetry=True`, OFF unless requested): first-visit state naming S_0[0] and S_t[q] -> V_{t-1}[q-1]. This is
  NOT in XRegion's GX2' decision encoding; it preserves satisfiability of every query because every query (support,
  saturation, Y1k, Y1k-recent) is invariant under renaming the hidden states, so SAT/UNSAT answers are unchanged;
* the conflict budget is the same 2,000,000 per solve call; every SAT answer is decoded and replayed in plain Python
  (reusing xcheck_sat.replay / py_y1k_has), exactly as XRegion does.

SAT/UNSAT answers are therefore semantically identical to XRegion's. Which queries hit the conflict budget (UNKNOWN) can
differ, because learnt clauses are kept between queries; that only moves steps between checked and unchecked.
"""
from __future__ import annotations
from itertools import combinations
from pysat.solvers import Solver
from brute.xcheck_sat import SOLVER,CONF_BUDGET,WitnessFailure,replay,py_y1k_has


class _Layer:
    __slots__=('g','T','masks','actions','rows','Ac','V','Tr','NX','TrR','W','sat','committed','dead')


class IncSolver:
    """One live CaDiCaL instance for one bound N with a main (committed) trajectory plus one-step extensions."""
    def __init__(self,n,k,m,conf_budget=CONF_BUDGET,symmetry=False):
        self.n=n;self.k=k;self.m=m;self.budget=conf_budget;self.top=0;self.symmetry=symmetry
        self.unknown=0;self.witness_failures=0;self.queries=0;self.layers_built=0;self.rebuilds=0
        self.s=None;self._reset()

    # ---- infrastructure ----
    def _v(self):
        self.top+=1;return self.top

    def _add(self,C):
        for c in C:self.s.add_clause(c)

    def _reset(self):
        if self.s is not None:self.s.delete()
        self.top=0;self.s=Solver(name=SOLVER);n,k,m=self.n,self.k,self.m;v=self._v;C=[]
        self.F=v();C.append([-self.F])  # constant false
        self.Tq=[[[v() for _ in range(n)] for _ in range(k)] for _ in range(n)]
        self.E=[[v() for _ in range(m)] for _ in range(n)]
        for row in self.E:
            C.append(list(row));C.extend([-a,-b] for a,b in combinations(row,2))
        for q in range(n):
            for a in range(k):
                row=self.Tq[q][a];C.append(list(row));self._seq_amo(row,C)
        self._add(C);self.main=None;self.ext={}

    def _seq_amo(self,xs,C):
        """Sinz sequential-counter at-most-one (as XRegion)."""
        if len(xs)<2:return
        s=[self._v() for _ in xs[:-1]]
        C.append([-xs[0],s[0]])
        for i in range(1,len(xs)-1):
            C.append([-xs[i],s[i]]);C.append([-s[i-1],s[i]]);C.append([-xs[i],-s[i-1]])
        C.append([-xs[-1],-s[-1]])

    def _layer(self,parent,mask,action):
        """New layer at position T=parent.T+1 (or T=0 if parent is None), all clauses guarded by a fresh g."""
        n,k,m=self.n,self.k,self.m;v=self._v;L=_Layer();g=v();L.g=g;G=lambda cl:[-g]+cl;C=[]
        L.T=0 if parent is None else parent.T+1
        L.masks=(mask,) if parent is None else parent.masks+(mask,)
        L.actions=() if parent is None else parent.actions+(action,)
        S=[v() for _ in range(n)];L.rows=[S] if parent is None else parent.rows+[S]
        C.append(G(list(S)));C.extend(G([-a,-b]) for a,b in combinations(S,2))
        for q in range(n):
            C.append(G([-S[q]]+[self.E[q][c] for c in range(m) if mask>>c&1]))
            if parent is not None:
                P=parent.rows[-1]
                for p in range(n):C.append(G([-P[p],-self.Tq[p][action][q],S[q]]))
        if self.symmetry:
            # first-visit state naming (satisfiability-preserving for every query here: all queries are invariant under
            # renaming states): S_0[0], and S_t[q] -> V_{t-1}[q-1] (state q-1 was visited before t)
            if parent is None:C.append(G([S[0]]))
            else:C.extend(G([-S[q],parent.V[q-1]]) for q in range(1,n))
        # chained derived variables
        L.Ac=[[None]*m for _ in range(n)];L.V=[None]*n;L.Tr=[[None]*k for _ in range(n)]
        for q in range(n):
            for c in range(m):
                prev=parent.Ac[q][c] if parent is not None else -self.F  # true
                if mask>>c&1:L.Ac[q][c]=prev;continue
                x=v();L.Ac[q][c]=x  # x <-> prev and not S[q]
                C.append(G([-x,prev]));C.append(G([-x,-S[q]]));C.append(G([x,-prev,S[q]]))
            prev=parent.V[q] if parent is not None else self.F
            x=v();L.V[q]=x  # x <-> prev or S[q]
            C.append(G([x,-prev]));C.append(G([x,-S[q]]));C.append(G([-x,prev,S[q]]))
            for a in range(k):
                if parent is None:L.Tr[q][a]=self.F;continue
                prev=parent.Tr[q][a]
                if action!=a:L.Tr[q][a]=prev;continue
                y=parent.rows[-1][q];x=v();L.Tr[q][a]=x  # x <-> prev or S_{T-1}[q]
                C.append(G([x,-prev]));C.append(G([x,-y]));C.append(G([-x,prev,y]))
        L.NX={};L.TrR={};L.W={};L.sat=None;L.committed=False;L.dead=False
        self._add(C);self.layers_built+=1
        return L

    def _commit(self,L):
        self.s.add_clause([L.g]);L.committed=True
        for M in self.ext.values():
            if M is not L and not M.dead:self.s.add_clause([-M.g]);M.dead=True
        self.ext={};self.main=L

    def _build_main(self,masks,actions):
        self.rebuilds+=1;self._reset();L=None
        for t,mk in enumerate(masks):
            L=self._layer(L,mk,actions[t-1] if t else None);self.s.add_clause([L.g]);L.committed=True
        self.main=L

    def layer(self,masks,actions):
        """The layer for evidence (masks, actions): main, a one-step extension of main, or advance/rebuild main."""
        masks=tuple(masks);actions=tuple(actions);assert len(masks)==len(actions)+1
        M=self.main
        if M is not None:
            T=M.T
            if len(masks)==T+1 and masks==M.masks and actions==M.actions:return M
            if len(masks)>T+1 and masks[:T+1]==M.masks and actions[:T]==M.actions:
                # advance main to masks[:-1] (commit the cached extension when it exists), then extend by one
                while self.main.T<len(masks)-2:
                    t=self.main.T+1;key=(masks[t],actions[t-1])
                    nxt=self.ext.get(key) or self._layer(self.main,*key)
                    self._commit(nxt)
                key=(masks[-1],actions[-1])
                if key not in self.ext:self.ext[key]=self._layer(self.main,*key)
                return self.ext[key]
        self._build_main(masks,actions);return self.main

    def close(self):
        if self.s is not None:self.s.delete();self.s=None

    # ---- solving ----
    def _solve(self,assume):
        self.queries+=1;self.s.conf_budget(self.budget);r=self.s.solve_limited(assumptions=assume)
        if r is None:self.unknown+=1
        return r

    def decode(self,model):
        pos=set(x for x in model if x>0);n,k,m=self.n,self.k,self.m
        def one(row):
            hits=[i for i,x in enumerate(row) if x in pos]
            if len(hits)!=1:raise WitnessFailure('not one-hot')
            return hits[0]
        return [[one(self.Tq[q][a]) for a in range(k)] for q in range(n)],[one(self.E[q]) for q in range(n)],one(self._S0)

    def _witness(self,L,pred):
        try:
            self._S0=L.rows[0];mach=self.decode(self.s.get_model());path=replay(mach,L.masks,L.actions)
            if not pred(mach,path):raise WitnessFailure('predicate')
        except WitnessFailure:
            self.witness_failures+=1

    def feasible(self,L):
        if L.sat is None:
            r=self._solve([L.g])
            if r:self._witness(L,lambda mach,path:True)
            L.sat=r
        return L.sat

    def _guarded(self,L,C_fn,pred):
        g=self._v();C=C_fn(g);self._add(C);r=self._solve([L.g,g])
        if r:self._witness(L,pred)
        self.s.add_clause([-g]);return r

    def _nx(self,L,b):
        if b not in L.NX:
            n=self.n;NX=[self._v() for _ in range(n)];S=L.rows[-1];C=[]
            for q in range(n):
                for r in range(n):C.append([-L.g,-S[q],-self.Tq[q][b][r],NX[r]])
            C.extend([-L.g,-x,-y] for x,y in combinations(NX,2));self._add(C);L.NX[b]=NX
        return L.NX[b]

    def _w(self,L,j,c):
        if (j,c) not in L.W:
            w=self._v();L.W[(j,c)]=w
            self._add([[-L.g,-w,L.V[j]],[-L.g,-w,L.Ac[j][c]],[-L.g,w,-L.V[j],-L.Ac[j][c]]])
        return L.W[(j,c)]

    def _trr(self,L,b,t0):
        if (b,t0) not in L.TrR:
            n=self.n;TrR=[self._v() for _ in range(n)];C=[]
            for j in range(n):
                xs=[L.rows[t][j] for t in range(t0,L.T) if L.actions[t]==b]
                C.append([-L.g,-TrR[j]]+xs);C.extend([-L.g,TrR[j],-x] for x in xs)
            self._add(C);L.TrR[(b,t0)]=TrR
        return L.TrR[(b,t0)]

    # ---- queries (same semantics as XRegion) ----
    def support(self,L,b):
        f=self.feasible(L)
        if f is not True:return None,int(f is None)
        NX=self._nx(L,b);out=[];u=0;T=L.T
        for c in range(self.m):
            r=self._guarded(L,lambda g:[[-g,-NX[q],self.E[q][c]] for q in range(self.n)],
                            lambda mach,path,c=c:mach[1][mach[0][path[T]][b]]==c)
            if r is None:u+=1
            if r is not False:out.append(c)
        return tuple(out),u

    def saturated(self,L):
        f=self.feasible(L)
        if f is not True:return True,int(f is None)
        r=self._guarded(L,lambda g:[[-g]+[-x for x in L.V]],lambda mach,path:len(set(path))<self.n)
        return (r is not True),int(r is None)

    def y1k(self,L,b,mask,t0=None):
        f=self.feasible(L)
        if f is not True:return None,int(f is None)
        n,m,T=self.n,self.m,L.T;out=[];u=0
        TrR=self._trr(L,b,t0) if t0 is not None else None
        ST=L.rows[-1]
        for c in range(m):
            def cl(g,c=c):
                v=self._v;P=[v() for _ in range(n)];C=[[-g]+P]
                for j in range(n):
                    C.append([-P[j],L.V[j]])
                    C.append([-P[j]]+[L.Ac[j][cc] for cc in range(m) if mask>>cc&1])
                    k1,k2=v(),v();br=[k1,k2]
                    C.append([-k1,L.Tr[j][b]])
                    for r in range(n):C.append([-k1,-self.Tq[j][b][r],L.Ac[r][c]])
                    C.append([-k2,-L.Tr[j][b]]);C.append([-k2,ST[j]])
                    C.append([-k2]+[-x for x in L.V]+[self._w(L,j2,c) for j2 in range(n)])
                    if TrR is not None:
                        k3=v();br.append(k3);C.append([-k3,L.Tr[j][b]]);C.append([-k3,-TrR[j]])
                    C.append([-P[j]]+br)
                return C
            r=self._guarded(L,cl,lambda mach,path,c=c:py_y1k_has(mach,path,L.masks,L.actions,n,m,b,mask,c,t0))
            if r is None:u+=1
            if r is not False:out.append(c)
        return tuple(out),u
