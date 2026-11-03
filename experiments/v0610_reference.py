"""Clique-pinned independent reference for study-064 GS_ref64 (BRUTE_PLAN_064). New file; shares no code with brute/ (its own
apartness, its own clique check, its own CNF), solved with CaDiCaL ('cd'). Purpose: the plain-CNF reference of
experiments/v0300_reference.py / v0310_reference.py (frozen) proves every size below n_min UNSAT with first-visit symmetry
breaking only, a pigeonhole-like proof that did not finish within 1800 s on 5 of 7 decided 2-bit 20-state records in study-063
(GS_ref63 FAIL, deviation #201). Here:
  apart(acts, codes): trace apartness (positions t < u are apart iff codes differ there, or acts[t] == acts[u] and t+1, u+1 are
    apart); pairwise apart positions need distinct states in every consistent machine (Exact).
  clique: a HINT (the record's final_clique) is accepted only if this module's own apartness verifies it pairwise and it holds
    position 0; otherwise (or if smaller) this module's own greedy clique through position 0 is used. Soundness never depends on
    the hint (Exact: any verified clique is a valid lower bound and a valid pinning).
  pinning: sorted clique c_0 = 0 < c_1 < ... gets x[c_i] = i (so the start state is 0); states q >= |C| + 1 may first appear at
    step t only if q - 1 appeared earlier (first-visit over the rest). Any machine can be relabelled into this form (Exact:
    clique states are distinct; the rest are ordered by first visit, unvisited states take the highest labels), so no
    machine and no verdict is lost.
  nmin(acts, codes, k, m, N, clique): smallest n in |C|..N with a consistent n-state machine (n < |C| is impossible).
  exists_different(...): the frozen v0310 query (pair unroll, monotone 'already differed' flag, L steps) with the pinning above.
Host-agnostic apart from the SAT library."""
from pysat.solvers import Solver


class _V:
    def __init__(self):self.n=0
    def new(self):self.n+=1;return self.n


def _eo(cl,xs):
    cl.append(list(xs))
    for i in range(len(xs)):
        for j in range(i+1,len(xs)):cl.append([-xs[i],-xs[j]])


def apart(acts,codes):
    """set of (t, u), t < u, positions 0..len(codes)-1 that are apart on the trace."""
    T=len(codes);ap=set()
    for t in range(T-1,-1,-1):
        for u in range(T-1,t,-1):
            if codes[t]!=codes[u] or (u<len(acts) and acts[t]==acts[u] and (t+1,u+1) in ap):ap.add((t,u))
    return ap


def _is_ap(ap,a,b):return (min(a,b),max(a,b)) in ap


def own_clique(acts,codes,ap=None):
    """greedy clique through position 0 (highest apart-degree first, ties by position)."""
    ap=apart(acts,codes) if ap is None else ap;T=len(codes);deg=[0]*T
    for t,u in ap:deg[t]+=1;deg[u]+=1
    C=[0]
    for p in sorted(range(1,T),key=lambda p:(-deg[p],p)):
        if all(_is_ap(ap,p,c) for c in C):C.append(p)
    return sorted(C)


def verified_clique(acts,codes,hint=None):
    """(clique, source): the larger of the verified hint and this module's own greedy clique."""
    ap=apart(acts,codes);own=own_clique(acts,codes,ap);T=len(codes)
    ok=bool(hint) and 0 in hint and len(set(hint))==len(hint) and all(0<=p<T for p in hint) and \
        all(_is_ap(ap,a,b) for i,a in enumerate(hint) for b in hint[i+1:])
    if ok and len(hint)>=len(own):return sorted(hint),'hint_verified'
    return own,('own' if not ok else 'own_larger')


def _trace_cnf(v,cl,acts,codes,n,k,m,C):
    T=len(codes);x=[[v.new() for _ in range(n)] for _ in range(T)]
    d=[[[v.new() for _ in range(n)] for _ in range(k)] for _ in range(n)];e=[[v.new() for _ in range(m)] for _ in range(n)]
    for t in range(T):_eo(cl,x[t])
    for q in range(n):
        _eo(cl,e[q])
        for a in range(k):_eo(cl,d[q][a])
    for i,c in enumerate(C):cl.append([x[c][i]])
    c0=len(C)
    for q in range(c0+1,n):
        for t in range(T):cl.append([-x[t][q]]+[x[u][q-1] for u in range(t)])
    for t in range(T):
        for q in range(n):cl.append([-x[t][q],e[q][codes[t]]])
    for t,a in enumerate(acts):
        for q in range(n):
            for r in range(n):cl.append([-x[t][q],-d[q][a][r],x[t+1][r]])
    return x,d,e


def sat_at(acts,codes,n,k,m,C):
    if n<len(C):return False
    v=_V();cl=[];_trace_cnf(v,cl,acts,codes,n,k,m,C)
    with Solver(name='cd',bootstrap_with=cl) as s:return bool(s.solve())


def nmin(acts,codes,k,m,N,C):
    for n in range(max(1,len(C)),N+1):
        if sat_at(acts,codes,n,k,m,C):return n
    return None


def exists_different(acts,codes,n,k,m,M1,s1,mode,L,C):
    """True iff some n-state machine (start 0) consistent with (acts, codes) differs from M1 within L steps, from (its state
    after the trace, s1) in mode 'future' or (0, 0) in mode 'start'. Same query as experiments/v0310_reference.py, pinned."""
    if n<len(C):return False
    D1,E1=M1;n1=len(D1);v=_V();T=len(codes);cl=[]
    x,d,e=_trace_cnf(v,cl,acts,codes,n,k,m,C)
    y=[[v.new() for _ in range(n)] for _ in range(L+1)];z=[[v.new() for _ in range(n1)] for _ in range(L+1)]
    w=[[v.new() for _ in range(k)] for _ in range(L)];g=[v.new() for _ in range(L+1)];c2=[[v.new() for _ in range(m)] for _ in range(L+1)]
    for j in range(L+1):_eo(cl,y[j]);_eo(cl,z[j]);_eo(cl,c2[j])
    for j in range(L):_eo(cl,w[j])
    if mode=='future':
        for q in range(n):cl.append([-x[T-1][q],y[0][q]])
        cl.append([z[0][s1]])
    else:cl+=[[y[0][0]],[z[0][0]]]
    for j in range(L+1):
        for q in range(n):
            for c in range(m):cl.append([-y[j][q],-e[q][c],c2[j][c]])
    for j in range(1,L+1):
        for b in range(k):
            for q in range(n):
                for r in range(n):cl.append([-y[j-1][q],-w[j-1][b],-d[q][b][r],y[j][r]])
            for p in range(n1):cl.append([-z[j-1][p],-w[j-1][b],z[j][D1[p][b]]])
    for j in range(L+1):
        for p in range(n1):cl.append([-g[j],-z[j][p],-c2[j][E1[p]]]+([g[j-1]] if j else []))
    cl.append([g[L]])
    with Solver(name='cd',bootstrap_with=cl) as s:return bool(s.solve())
