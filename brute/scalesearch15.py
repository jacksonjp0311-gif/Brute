"""A15 / A15_cube for Brute v0.37.0 (BRUTE_PLAN_040; deviation #152 fixes the readings below). New file;
brute/scalesearch14.py (A14) and every earlier search module are untouched and imported only.

A15 is A14 (least machine, rival search at every size n_min..N, shortest separating word, stop rule, labels, K, budgets,
query cap and the incremental per-size instances) with ONE declared change to the per-size CNF: the trace first-visit symmetry
clauses of Inc14 are replaced by
 (i) apartness clauses: for every pair of trace positions t < u that are apart on the trace (a common action continuation
     acts[t..t+j-1] == acts[u..u+j-1] after which masks[t+j] & masks[u+j] == 0) and whose own masks intersect (pairs with
     disjoint own masks are already separated by the emission clauses), the clauses -x[t][q] | -x[u][q] for every q. Exact:
     apart positions cannot share a state in any consistent deterministic machine, so no consistent machine is excluded;
 (ii) fixed colours: a greedy clique C = [c_0 = 0, c_1, ...] of pairwise-apart positions (position 0 first, then positions
     by decreasing apartness degree, ties by position) gets x[c_i] = state i. Any consistent machine visits pairwise
     distinct states at C, so a relabelling with C's states 0..|C|-1 in that order exists and is consistent; position 0 keeps
     state 0, so the 'start' rival mode (state 0) means the same as in A14. If |C| > n the size-n instance is UNSAT.
C is computed once per pool from the trace at pool creation (apartness only grows as the trace grows, so C stays a clique);
apartness clauses for new pairs are added as the trace grows. The size search starts at max(A14's lower bound, |C|), Exact.
A15_cube adds a per-size cube split: when a size-n query (least or rival) returns capped, it is re-solved as cubes q = 0..n-1
under the extra assumption x[t*][q], t* = the first trace position outside C; each cube is one capped call (QUERY_S14);
verdict SAT at the first SAT cube (its model is the instance model), UNSAT if every cube is UNSAT, unknown otherwise
(including when the case deadline passes). Exactly-one on x[t*] makes the cubes cover the query.
least14, differ14, search14 and stop_check14 are reused unchanged on Pool15 (they use only get/query/machine/x/d/e/s).
Host-agnostic: no I/O, network, threads, child processes or global state; the world is reached only via observe."""
from __future__ import annotations
from time import perf_counter
from pysat.solvers import Solver
from brute.region import RegionK
from brute.scalesearch4 import SOLVER4
from brute.scalesearch8 import distinguishing_word,run_word
from brute.scalesearch10 import _Owner10,_capped_solve
from brute.scalesearch14 import QUERY_S14,K14,BUDGET14,word_len9,stop_check14,least14,differ14,search14

__all__=['QUERY_S14','K14','BUDGET14','apart_matrix','greedy_clique','Inc15','Pool15','active15','stop_check15',
         'least14','differ14','search14','word_len9']


def apart_matrix(masks,acts):
    """A[t][u] (t < u) = 1 iff positions t and u are apart on the trace. A[t] is a bytearray of length T + 1."""
    T=len(acts);A=[bytearray(T+1) for _ in range(T+1)]
    for dl in range(1,T+1):
        prev=0
        for t in range(T-dl,-1,-1):
            u=t+dl;v=1 if not (masks[t]&masks[u]) else (1 if (u<T and acts[t]==acts[u] and prev) else 0)
            A[t][u]=v;prev=v
    return A


def _ap(A,t,u):return A[t][u] if t<u else A[u][t]


def greedy_clique(A):
    T1=len(A);deg=[sum(_ap(A,t,u) for u in range(T1) if u!=t) for t in range(T1)]
    C=[0]
    for t in sorted(range(1,T1),key=lambda t:(-deg[t],t)):
        if all(_ap(A,t,c) for c in C):C.append(t)
    return C


class Inc15:
    """Incremental n-state region: Inc14's core with apartness clauses and clique fixed colours (no first-visit clauses)."""
    def __init__(self,n,k,m,pool,solver=SOLVER4,cube=False):
        self._owner=None;self._skip=False;self._dl=None;self.calls=0;self.n=n;self.k=k;self.m=m;self.pool=pool;self.cube=cube
        self.nv=0;self.x=[];self.T=-1;self.acts=[];self.masks=[];self.s=Solver(name=solver);self.guards=0;self.cl=[];v=self._v
        self.pairs=set();self.cubes=0;self.cube_sat=0;self.cube_unsat=0
        self.d=[[[v() for _ in range(n)] for _ in range(k)] for _ in range(n)];self.e=[[v() for _ in range(m)] for _ in range(n)]
        for q in range(n):
            for a in range(k):self._one(self.d[q][a])
            self._one(self.e[q])
        if len(pool.clique)>n:z=v();self.cl.append([z]);self.cl.append([-z])
        self._flush()

    _v=RegionK._v;_amo=RegionK._amo;_one=RegionK._one;_solve=_capped_solve

    def _flush(self):
        for c in self.cl:self.s.add_clause(c)
        self.cl=[]

    def close(self):
        if self.s is not None:self.s.delete();self.s=None

    def sync(self,masks,acts):
        if len(masks)!=len(acts)+1:raise ValueError('need one more mask than actions')
        if self.T>=0 and (list(acts[:self.T])!=self.acts or list(masks[:self.T+1])!=self.masks):raise ValueError('Inc15: trace prefix changed')
        n=self.n;cl=self.cl;v=self._v;col=self.pool.colour
        for t in range(self.T+1,len(acts)+1):
            row=[v() for _ in range(n)];self.x.append(row);self._one(row)
            if t in col and col[t]<n:cl.append([row[col[t]]])
            if t>0:
                a=acts[t-1]
                for q in range(n):
                    for r in range(n):cl.append([-self.x[t-1][q],-self.d[q][a][r],row[r]])
            mk=masks[t]
            for q in range(n):cl.append([-row[q]]+[self.e[q][c] for c in range(self.m) if mk>>c&1])
        self.T=len(acts);self.acts=list(acts);self.masks=list(masks)
        for (t,u) in self.pool.future_pairs-self.pairs:
            for q in range(n):cl.append([-self.x[t][q],-self.x[u][q]])
        self.pairs|=self.pool.future_pairs;self._flush();return self

    def query(self,o,deadline,assume):
        self._owner=o;self._dl=deadline;r=self._solve(assume)
        if r is not None or not self.cube:return r
        ts=self.pool.cube_pos(self.T)
        if ts is None:return None
        allu=True
        for q in range(self.n):
            if perf_counter()>=deadline:return None
            self._owner=o;self._dl=deadline;self.cubes+=1;rq=self._solve(list(assume)+[self.x[ts][q]])
            if rq is True:self.cube_sat+=1;return True
            if rq is None:allu=False
            else:self.cube_unsat+=1
        return False if allu else None

    def machine(self,mod):
        n,K,M=self.n,range(self.k),range(self.m)
        return ([[next(r for r in range(n) if self.d[q][a][r] in mod) for a in K] for q in range(n)],
                [next(c for c in M if self.e[q][c] in mod) for q in range(n)])


class Pool15:
    """One Inc15 per size n; the clique is fixed from the trace at the first get; apartness recomputed as the trace grows."""
    def __init__(self,k,m,solver=SOLVER4,cube=False):
        self.k=k;self.m=m;self.solver=solver;self.cube=cube;self.inc={};self.clique=None;self.colour={};self.future_pairs=set();self._T=None

    def _update(self,masks,acts):
        if self._T==len(acts):return
        A=apart_matrix(masks,acts);T1=len(acts)+1
        if self.clique is None:self.clique=greedy_clique(A);self.colour={t:i for i,t in enumerate(self.clique)}
        else:
            for i,a in enumerate(self.clique):
                for b in self.clique[i+1:]:
                    if not _ap(A,a,b):raise AssertionError('Pool15: clique lost apartness')
        self.future_pairs|={(t,u) for t in range(T1) for u in range(t+1,T1) if A[t][u] and masks[t]&masks[u]};self._T=len(acts)

    def cube_pos(self,T):
        return next((t for t in range(T+1) if t not in self.colour),None)

    def lower(self,masks,acts):self._update(masks,acts);return len(self.clique)

    def get(self,n,masks,acts):
        self._update(masks,acts)
        if n not in self.inc:self.inc[n]=Inc15(n,self.k,self.m,self,self.solver,self.cube)
        return self.inc[n].sync(masks,acts)

    def guards(self):return sum(i.guards for i in self.inc.values())
    def cube_counts(self):
        return {'cubes':sum(i.cubes for i in self.inc.values()),'cube_sat':sum(i.cube_sat for i in self.inc.values()),
                'cube_unsat':sum(i.cube_unsat for i in self.inc.values())}

    def close(self):
        for i in self.inc.values():i.close()
        self.inc={}


def stop_check15(masks,acts,k,m,N,deadline,n_lo=1,query_s=QUERY_S14,solver=SOLVER4,o=None,P=None,hook=None,cube=False):
    """stop_check14 on a Pool15 (fresh unless given; a fresh pool is closed on return); n_lo raised to the clique size."""
    own=P is None;P=P or Pool15(k,m,solver,cube)
    try:return stop_check14(masks,acts,k,m,N,deadline,max(n_lo,P.lower(masks,acts)),query_s,solver,o or _Owner10(query_s,hook),P)
    finally:
        if own:P.close()


def active15(masks,acts,k,m,N,observe,deadline,K=K14,query_s=QUERY_S14,solver=SOLVER4,hook=None,cube=False):
    """active14 on one Pool15. Returns active14's keys plus 'clique' and 'cube' counts."""
    masks=list(masks);acts=list(acts);used=0;rounds=[];P=Pool15(k,m,solver,cube);n_lo=P.lower(masks,acts)
    try:
        while True:
            o=_Owner10(query_s,hook);r=stop_check14(masks,acts,k,m,N,deadline,n_lo,query_s,solver,o,P)
            rec={'T':len(acts),'n_min':r['n_min'],'M1':r['model'],'s1':r['s1'],'future':r['future'],'start':r['start'],
                 'query_walls':list(o.query_walls),'capped':o.capped,'check':r['stop']};rounds.append(rec)
            if r['stop']!='AMB':stop=r['stop'];break
            F=r['future'];M1=r['model'];M2=F['M2'];s1=r['s1'];s2=F['s2']
            w=distinguishing_word(M1[0],M1[1],s1,M2[0],M2[1],s2);rec.update(word=w,M2=M2,s2=s2)
            if w is None:raise AssertionError('active15: SAT M2 has no distinguishing word')
            if len(w)>K-used:stop='K_spent';break
            rec['pred1']=run_word(M1[0],M1[1],s1,w);rec['pred2']=run_word(M2[0],M2[1],s2,w);obs=[]
            for a in w:mk=observe(a);acts.append(a);masks.append(mk);obs.append(mk)
            used+=len(w);rec['obs']=obs;n_lo=max(r['n_min'],n_lo)
        return {'stop':stop,'masks':masks,'acts':acts,'used':used,'rounds':rounds,'final':r,'guards':P.guards(),'sizes':sorted(P.inc),
                'clique':len(P.clique),'cube':P.cube_counts()}
    finally:P.close()
