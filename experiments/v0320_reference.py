"""Independent reference for study-035 GS_ref (deviation #142). New file; shares no code with brute/scalesearch*.
Plain CNF solved with CaDiCaL 1.9.5 ('cd195') in conflict chunks up to a wall limit (undecided past it): state-per-step
variables, exactly-one transitions and emissions, first-visit order along the trace (as experiments/v0310_reference.py,
frozen, re-implemented here), and for a flip budget B > 0 one flip variable per sensor bit of every reading
(x[t][q] and e[q][c] imply the flip of bit j whenever bit j of c differs from the reading) with a totalizer 'at most B'
(pysat.card, a different encoding from the core's sequential counter). B = 0 has no flip variables (exact readings).
exists_machine: some complete n-state machine (start 0) fits the readings with <= B flips. exists_different: some such
machine differs from M1 within L steps from (its state after the trace, s1) ('future') or (0, 0) ('start'), with the
monotone 'already differed' flag of v0310_reference."""
from time import perf_counter
from pysat.solvers import Solver
from pysat.card import CardEnc,EncType
REF_SOLVER='cd195';CHUNK=20000


class _V:
    def __init__(self):self.n=0
    def new(self):self.n+=1;return self.n


def _eo(cl,xs):
    cl.append(list(xs))
    for i in range(len(xs)):
        for j in range(i+1,len(xs)):cl.append([-xs[i],-xs[j]])


def _bit(c,j,sb):return (c>>(sb-1-j))&1


def _trace(v,cl,acts,readings,n,k,m,B):
    sb=len(readings[0]);T=len(readings)
    x=[[v.new() for _ in range(n)] for _ in range(T)];d=[[[v.new() for _ in range(n)] for _ in range(k)] for _ in range(n)]
    e=[[v.new() for _ in range(m)] for _ in range(n)];f=[[v.new() for _ in range(sb)] for _ in range(T)] if B>0 else None
    for t in range(T):_eo(cl,x[t])
    for q in range(n):
        _eo(cl,e[q])
        for a in range(k):_eo(cl,d[q][a])
    cl.append([x[0][0]])
    for q in range(1,n):
        for t in range(T):cl.append([-x[t][q]]+[x[u][q-1] for u in range(t)])
    for t in range(T):
        for q in range(n):
            for c in range(m):
                diff=[j for j in range(sb) if _bit(c,j,sb)!=readings[t][j]]
                if diff:cl.append([-x[t][q],-e[q][c]]+([f[t][j] for j in diff] if B>0 else []))
    for t,a in enumerate(acts):
        for q in range(n):
            for r in range(n):cl.append([-x[t][q],-d[q][a][r],x[t+1][r]])
    return x,d,e,f


def _card(v,cl,f,B):
    if f is None:return
    lits=[z for row in f for z in row];enc=CardEnc.atmost(lits=lits,bound=B,top_id=v.n,encoding=EncType.totalizer)
    cl.extend(enc.clauses);v.n=max(v.n,enc.nv)


def _solve(cl,limit):
    t0=perf_counter()
    with Solver(name=REF_SOLVER,bootstrap_with=cl) as s:
        while True:
            if perf_counter()-t0>=limit:return None
            s.conf_budget(CHUNK);r=s.solve_limited()
            if r is not None:return bool(r)


def exists_machine(acts,readings,n,k,m,B,limit=30.0):
    """True / False, or None if undecided within limit seconds."""
    if n<1:return False
    v=_V();cl=[];x,d,e,f=_trace(v,cl,acts,readings,n,k,m,B);_card(v,cl,f,B);return _solve(cl,limit)


def exists_different(acts,readings,n,k,m,B,M1,s1,mode,L,limit=30.0):
    D1,E1=M1;n1=len(D1);v=_V();cl=[];x,d,e,f=_trace(v,cl,acts,readings,n,k,m,B);_card(v,cl,f,B);T=len(readings)
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
    cl.append([g[L]]);return _solve(cl,limit)
