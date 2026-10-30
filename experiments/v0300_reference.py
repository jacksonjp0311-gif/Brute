"""Independent reference for study-033 GS_ref (deviation #138). New file; shares no code with brute/scalesearch*.
A plain CNF (state-per-step variables, exactly-one transitions and emissions, first-visit state introduction, every state
visited) solved with CaDiCaL ('cd'), not the solver's region encoding. For an eps-0 trace it computes n_min (with the
n_min-1 UNSAT proof), whether a second rooted machine exists at n_min (blocking clause on the transition/emission table),
and an independent product BFS for shortest distinguishing words. Host-agnostic apart from the SAT library."""
from collections import deque
from pysat.solvers import Solver


class _V:
    def __init__(self):self.n=0
    def new(self):self.n+=1;return self.n


def _eo(cl,xs):
    cl.append(list(xs))
    for i in range(len(xs)):
        for j in range(i+1,len(xs)):cl.append([-xs[i],-xs[j]])


def encode(acts,codes,n,k,m):
    v=_V();T=len(codes);x=[[v.new() for _ in range(n)] for _ in range(T)]
    d=[[[v.new() for _ in range(n)] for _ in range(k)] for _ in range(n)];e=[[v.new() for _ in range(m)] for _ in range(n)];cl=[]
    for t in range(T):_eo(cl,x[t])
    for q in range(n):
        _eo(cl,e[q])
        for a in range(k):_eo(cl,d[q][a])
    cl.append([x[0][0]])
    for t in range(T):
        for q in range(n):cl.append([-x[t][q],e[q][codes[t]]])
    for t,a in enumerate(acts):
        for q in range(n):
            for r in range(n):cl.append([-x[t][q],-d[q][a][r],x[t+1][r]])
    for q in range(1,n):
        for t in range(T):cl.append([-x[t][q]]+[x[u][q-1] for u in range(t)])
        cl.append([x[t][q] for t in range(T)])
    return cl,d,e


def _decode(model,d,e,n,k,m):
    s=set(l for l in model if l>0)
    D=[[next(r for r in range(n) if d[q][a][r] in s) for a in range(k)] for q in range(n)]
    E=[next(c for c in range(m) if e[q][c] in s) for q in range(n)];return D,E


def solve(acts,codes,n,k,m,two=False):
    cl,d,e=encode(acts,codes,n,k,m)
    with Solver(name='cd',bootstrap_with=cl) as s:
        if not s.solve():return None,None
        M1=_decode(s.get_model(),d,e,n,k,m)
        if not two:return M1,None
        blk=[-d[q][a][M1[0][q][a]] for q in range(n) for a in range(k)]+[-e[q][M1[1][q]] for q in range(n)]
        s.add_clause(blk)
        return M1,(_decode(s.get_model(),d,e,n,k,m) if s.solve() else None)


def reference_identify(acts,codes,k,m,n_max):
    """n_min, unique, M1, M2, unsat_below (n_min-1 proven UNSAT, or n_min == 1)."""
    for n in range(1,n_max+1):
        M1,_=solve(acts,codes,n,k,m)
        if M1 is not None:
            _,M2=solve(acts,codes,n,k,m,two=True)
            return {'n_min':n,'unique':M2 is None,'M1':M1,'M2':M2,'unsat_below':True}
    return {'n_min':None,'unique':False,'M1':None,'M2':None,'unsat_below':True}


def shortest_word_len(D1,E1,s1,D2,E2,s2):
    """Length of the shortest action word after which the two machines' readings differ (None if never)."""
    k=len(D1[0]);seen={(s1,s2)};dq=deque([(s1,s2,0)])
    while dq:
        p,q,L=dq.popleft()
        for a in range(k):
            p2,q2=D1[p][a],D2[q][a]
            if E1[p2]!=E2[q2]:return L+1
            if (p2,q2) not in seen:seen.add((p2,q2));dq.append((p2,q2,L+1))
    return None
