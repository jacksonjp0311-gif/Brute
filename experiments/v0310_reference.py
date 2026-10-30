"""Independent reference for study-034 GS_ref (deviation #140). New file; shares no code with brute/scalesearch*.
Plain CNF solved with CaDiCaL ('cd'): state-per-step variables, exactly-one transitions and emissions, first-visit
order along the trace (state q > 0 may appear at step t only if q-1 appeared earlier; states never visited by the trace
take the highest labels, so this is a relabelling and loses no machine) and no 'every state visited' constraint (so
machines with unvisited states are included). For the bounded
'is there a consistent <= n machine that behaves differently from M1' question it unrolls the pair (M2 state, M1 state)
for L steps under a symbolic word, with a monotone 'already differed' flag g_j (g_0 = codes differ at step 0;
g_j = g_{j-1} or codes differ at step j) and asserts g_L. n_min comes from experiments.v0300_reference (frozen)."""
from pysat.solvers import Solver
from experiments.v0300_reference import reference_identify,solve as solve_min


class _V:
    def __init__(self):self.n=0
    def new(self):self.n+=1;return self.n


def _eo(cl,xs):
    cl.append(list(xs))
    for i in range(len(xs)):
        for j in range(i+1,len(xs)):cl.append([-xs[i],-xs[j]])


def exists_different(acts,codes,n,k,m,M1,s1,mode,L):
    """True iff some complete machine with n states (start 0) is consistent with (acts, codes) and differs from M1 within
    L steps from (M2's state after the trace, s1) in mode 'future' or (0, 0) in mode 'start'."""
    D1,E1=M1;n1=len(D1);v=_V();T=len(codes);cl=[]
    x=[[v.new() for _ in range(n)] for _ in range(T)];d=[[[v.new() for _ in range(n)] for _ in range(k)] for _ in range(n)]
    e=[[v.new() for _ in range(m)] for _ in range(n)]
    for t in range(T):_eo(cl,x[t])
    for q in range(n):
        _eo(cl,e[q])
        for a in range(k):_eo(cl,d[q][a])
    cl.append([x[0][0]])
    for q in range(1,n):
        for t in range(T):cl.append([-x[t][q]]+[x[u][q-1] for u in range(t)])
    for t in range(T):
        for q in range(n):cl.append([-x[t][q],e[q][codes[t]]])
    for t,a in enumerate(acts):
        for q in range(n):
            for r in range(n):cl.append([-x[t][q],-d[q][a][r],x[t+1][r]])
    y=[[v.new() for _ in range(n)] for _ in range(L+1)];z=[[v.new() for _ in range(n1)] for _ in range(L+1)]
    w=[[v.new() for _ in range(k)] for _ in range(L)];g=[v.new() for _ in range(L+1)];c2=[[v.new() for _ in range(m)] for _ in range(L+1)]
    for j in range(L+1):_eo(cl,y[j]);_eo(cl,z[j]);_eo(cl,c2[j])
    for j in range(L):_eo(cl,w[j])
    if mode=='future':
        for q in range(n):cl.append([-x[T-1][q],y[0][q]])
        cl.append([z[0][s1]])
    else:cl+= [[y[0][0]],[z[0][0]]]
    for j in range(L+1):
        for q in range(n):
            for c in range(m):cl.append([-y[j][q],-e[q][c],c2[j][c]])
    for j in range(1,L+1):
        for b in range(k):
            for q in range(n):
                for r in range(n):cl.append([-y[j-1][q],-w[j-1][b],-d[q][b][r],y[j][r]])
            for p in range(n1):cl.append([-z[j-1][p],-w[j-1][b],z[j][D1[p][b]]])
    for j in range(L+1):
        for p in range(n1):
            # g_j -> (g_{j-1} or c2_j != E1[p] when z_j = p)
            cl.append([-g[j],-z[j][p],-c2[j][E1[p]]]+([g[j-1]] if j else []))
    cl.append([g[L]])
    with Solver(name='cd',bootstrap_with=cl) as s:return bool(s.solve())
