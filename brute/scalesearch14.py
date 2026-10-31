"""A14 incremental sound active identification for Brute v0.36.0 (BRUTE_PLAN_039; deviation #150 fixes the readings below).
New file; brute/scalesearch9.py (A9), brute/scalesearch10.py and every earlier search module are untouched and imported only.

Two declared changes against A9 (least machine, rival search at every size n_min..N, shortest separating word, stop rule and
labels are A9's, B = 0, hard reading masks):
(1) Pool14 keeps ONE incremental SAT instance (Inc14) per candidate size n for the whole active14 call, kept across rounds
and executed actions. Inc14 holds the satisfiability core of the frozen S1 RegionK at size n: one-hot state rows x[t],
one-hot transitions d and emissions e, x[0] = state 0, first-visit symmetry, transition clauses and hard reading-mask
clauses. RegionK's extra variables (A, V, Tr, nx, nc) are definitional (each fully defined by, and never restricting, x/d/e),
so the set of (d, e) admitted is RegionK's and every SAT/UNSAT verdict is the same (GINC14 tests this on the sealed study-034
A9 traces). Inc14.sync adds the rows of new trace positions (clauses only added). least14 solves the instance with no
assumptions. differ14 adds scalesearch9.differ9's rival clauses (symbolic word of length L = N + n_M1 - 1, mode 'future'
from the current state or 'start' from state 0) guarded by a fresh activation literal g (every clause gets -g), solves under
[g], then retires g with the unit clause [-g]; learned clauses on d/e/x persist. Decoded rivals are re-checked exactly as
differ9 (consistent with the trace, the decoded word separates).
(2) Budgets are parameters: A14 runs with K = 128 extra actions and a 240 s case budget, A14_k64 with K = 64 and 120 s.
Every solve is scalesearch10._capped_solve (chunked, optional host interrupt at the query cap, QUERY_S14 = 9.0 s); one call
is one query. stop_check14 is the same stop decision on a fixed trace with no actions (A14_random).
Host-agnostic: no I/O, network, threads, child processes or global state; the world is reached only via observe."""
from __future__ import annotations
from time import perf_counter
from pysat.solvers import Solver
from brute.region import RegionK
from brute.scalesearch import simulate
from brute.scalesearch4 import _lower_bound,SOLVER4
from brute.scalesearch8 import distinguishing_word,run_word
from brute.scalesearch9 import word_len9
from brute.scalesearch10 import _Owner10,_capped_solve

__all__=['QUERY_S14','K14','BUDGET14','K14_64','BUDGET14_64','Inc14','Pool14','least14','differ14','search14','stop_check14',
         'active14','word_len9']
QUERY_S14=9.0;K14=128;BUDGET14=240.0;K14_64=64;BUDGET14_64=120.0


class Inc14:
    """Incremental n-state region (the S1 RegionK satisfiability core) over a growing hard-mask trace."""
    def __init__(self,n,k,m,solver=SOLVER4):
        self._owner=None;self._skip=False;self._dl=None;self.calls=0;self.n=n;self.k=k;self.m=m
        self.nv=0;self.x=[];self.T=-1;self.acts=[];self.masks=[];self.s=Solver(name=solver);self.guards=0;self.cl=[];v=self._v
        self.d=[[[v() for _ in range(n)] for _ in range(k)] for _ in range(n)];self.e=[[v() for _ in range(m)] for _ in range(n)]
        for q in range(n):
            for a in range(k):self._one(self.d[q][a])
            self._one(self.e[q])
        self._flush()

    _v=RegionK._v;_amo=RegionK._amo;_one=RegionK._one;_solve=_capped_solve

    def _flush(self):
        for c in self.cl:self.s.add_clause(c)
        self.cl=[]

    def close(self):
        if self.s is not None:self.s.delete();self.s=None

    def sync(self,masks,acts):
        """Add trace positions T + 1 .. len(acts) (the trace only grows; earlier positions must be unchanged)."""
        if len(masks)!=len(acts)+1:raise ValueError('need one more mask than actions')
        if self.T>=0 and (list(acts[:self.T])!=self.acts or list(masks[:self.T+1])!=self.masks):raise ValueError('Inc14: trace prefix changed')
        n=self.n;cl=self.cl;v=self._v
        for t in range(self.T+1,len(acts)+1):
            row=[v() for _ in range(n)];self.x.append(row);self._one(row)
            if t==0:cl.append([row[0]])
            for q in range(1,n):cl.append([-row[q]]+[self.x[u][q-1] for u in range(t)])
            if t>0:
                a=acts[t-1]
                for q in range(n):
                    for r in range(n):cl.append([-self.x[t-1][q],-self.d[q][a][r],row[r]])
            mk=masks[t]
            for q in range(n):cl.append([-row[q]]+[self.e[q][c] for c in range(self.m) if mk>>c&1])
        self.T=len(acts);self.acts=list(acts);self.masks=list(masks);self._flush();return self

    def query(self,o,deadline,assume):
        self._owner=o;self._dl=deadline;return self._solve(assume)

    def machine(self,mod):
        n,K,M=self.n,range(self.k),range(self.m)
        return ([[next(r for r in range(n) if self.d[q][a][r] in mod) for a in K] for q in range(n)],
                [next(c for c in M if self.e[q][c] in mod) for q in range(n)])


class Pool14:
    """One Inc14 per candidate size n, created on first use, kept until close()."""
    def __init__(self,k,m,solver=SOLVER4):self.k=k;self.m=m;self.solver=solver;self.inc={}

    def get(self,n,masks,acts):
        if n not in self.inc:self.inc[n]=Inc14(n,self.k,self.m,self.solver)
        return self.inc[n].sync(masks,acts)

    def guards(self):return sum(i.guards for i in self.inc.values())

    def close(self):
        for i in self.inc.values():i.close()
        self.inc={}


def least14(o,P,masks,acts,N,deadline,n_lo=1):
    """('ok', n, (d, e)) | ('none', None, None) | ('unknown', None, None); least9 on the pooled instances."""
    n=max(n_lo,_lower_bound(masks))
    while n<=N:
        if perf_counter()>=deadline:return 'unknown',None,None
        R=P.get(n,masks,acts);r=R.query(o,deadline,[])
        if r is None:return 'unknown',None,None
        if r is False:n+=1;continue
        return 'ok',n,R.machine(set(x for x in R.s.get_model() if x>0))
    return 'none',None,None


def differ14(o,P,masks,acts,n,M1,s1,mode,L,deadline):
    """differ9 on the pooled size-n instance: (True, M2, s2, word) | (False, None, None, None) | (None, ...) unknown."""
    R=P.get(n,masks,acts);d1,e1=M1;n1=len(d1);k=R.k;T=R.T;v=R._v;g=v();cl=[]
    add=lambda c:cl.append([-g]+list(c))
    def eo(xs):
        add(xs)
        for i in range(len(xs)):
            for j in range(i+1,len(xs)):add([-xs[i],-xs[j]])
    y=[[v() for _ in range(n)] for _ in range(L+1)];z=[[v() for _ in range(n1)] for _ in range(L+1)]
    A=[None]+[[v() for _ in range(k)] for _ in range(L)];D=[v() for _ in range(L+1)]
    for j in range(L+1):eo(y[j]);eo(z[j])
    for j in range(1,L+1):eo(A[j])
    if mode=='future':
        for q in range(n):add([-R.x[T][q],y[0][q]]);add([R.x[T][q],-y[0][q]])
        add([z[0][s1]])
    elif mode=='start':add([y[0][0]]);add([z[0][0]])
    else:raise ValueError(mode)
    for j in range(1,L+1):
        for b in range(k):
            for p in range(n1):add([-z[j-1][p],-A[j][b],z[j][d1[p][b]]])
            for q in range(n):
                for r in range(n):add([-y[j-1][q],-A[j][b],-R.d[q][b][r],y[j][r]])
    for j in range(L+1):
        for p in range(n1):
            for q in range(n):add([-D[j],-z[j][p],-y[j][q],-R.e[q][e1[p]]])
    add(D)
    for c in cl:R.s.add_clause(c)
    R.guards+=1
    try:
        r=R.query(o,deadline,[g])
        if r is None:return None,None,None,None
        if r is False:return False,None,None,None
        mod=set(x for x in R.s.get_model() if x>0);M2=R.machine(mod)
        word=[next(b for b in range(k) if A[j][b] in mod) for j in range(1,L+1)]
        jd=min(j for j in range(L+1) if D[j] in mod);word=word[:jd]
        ok,s2,_=simulate(M2[0],M2[1],acts,masks)
        if not ok:raise AssertionError('differ14: decoded M2 inconsistent')
        q1,q2=(s1,s2) if mode=='future' else (0,0);p1=[e1[q1]]+run_word(d1,e1,q1,word);p2=[M2[1][q2]]+run_word(M2[0],M2[1],q2,word)
        if p1==p2:raise AssertionError('differ14: decoded word does not separate')
        return True,M2,s2,word
    finally:R.s.add_clause([-g])


def search14(o,P,masks,acts,n_min,N,M1,s1,mode,deadline):
    """search9 on the pooled instances: n = n_min..N in order; same result shape."""
    L=word_len9(N,len(M1[0]));ver=[]
    res=lambda **kw:{'found':False,'unknown':False,'n':None,'M2':None,'s2':None,'word_sat':None,'verdicts':ver,'L':L,**kw}
    for n in range(n_min,N+1):
        if perf_counter()>=deadline:ver.append([n,'UNKNOWN']);return res(unknown=True)
        f,M2,s2,w=differ14(o,P,masks,acts,n,M1,s1,mode,L,deadline)
        if f is None:ver.append([n,'UNKNOWN']);return res(unknown=True)
        if f:ver.append([n,'SAT']);return res(found=True,n=n,M2=M2,s2=s2,word_sat=w)
        ver.append([n,'UNSAT'])
    return res()


def stop_check14(masks,acts,k,m,N,deadline,n_lo=1,query_s=QUERY_S14,solver=SOLVER4,o=None,P=None,hook=None):
    """stop_check9 on pooled instances (a fresh pool unless P is given; a fresh pool is closed on return)."""
    o=o or _Owner10(query_s,hook);own=P is None;P=P or Pool14(k,m,solver)
    res={'n_min':None,'model':None,'s1':None,'future':None,'start':None}
    out=lambda stop:{'stop':stop,**res,'query_walls':o.query_walls,'capped':o.capped}
    try:
        st,n,M1=least14(o,P,masks,acts,N,deadline,n_lo)
        if st!='ok':return out(st)
        s1=simulate(M1[0],M1[1],acts,masks)[1];res.update(n_min=n,model=M1,s1=s1)
        F=search14(o,P,masks,acts,n,N,M1,s1,'future',deadline);res['future']=F
        if F['unknown']:return out('unknown')
        if F['found']:return out('AMB')
        S=search14(o,P,masks,acts,n,N,M1,s1,'start',deadline);res['start']=S
        if S['unknown']:return out('unknown')
        return out('IDF' if S['found'] else 'ID')
    finally:
        if own:P.close()


def active14(masks,acts,k,m,N,observe,deadline,K=K14,query_s=QUERY_S14,solver=SOLVER4,hook=None):
    """active9 on one Pool14. Returns {'stop', 'masks', 'acts', 'used', 'rounds', 'final', 'guards', 'sizes'}."""
    masks=list(masks);acts=list(acts);used=0;rounds=[];n_lo=1;P=Pool14(k,m,solver)
    try:
        while True:
            o=_Owner10(query_s,hook);r=stop_check14(masks,acts,k,m,N,deadline,n_lo,query_s,solver,o,P)
            rec={'T':len(acts),'n_min':r['n_min'],'M1':r['model'],'s1':r['s1'],'future':r['future'],'start':r['start'],
                 'query_walls':list(o.query_walls),'capped':o.capped,'check':r['stop']};rounds.append(rec)
            if r['stop']!='AMB':stop=r['stop'];break
            F=r['future'];M1=r['model'];M2=F['M2'];s1=r['s1'];s2=F['s2']
            w=distinguishing_word(M1[0],M1[1],s1,M2[0],M2[1],s2);rec.update(word=w,M2=M2,s2=s2)
            if w is None:raise AssertionError('active14: SAT M2 has no distinguishing word')
            if len(w)>K-used:stop='K_spent';break
            rec['pred1']=run_word(M1[0],M1[1],s1,w);rec['pred2']=run_word(M2[0],M2[1],s2,w);obs=[]
            for a in w:mk=observe(a);acts.append(a);masks.append(mk);obs.append(mk)
            used+=len(w);rec['obs']=obs;n_lo=r['n_min']
        return {'stop':stop,'masks':masks,'acts':acts,'used':used,'rounds':rounds,'final':r,'guards':P.guards(),'sizes':sorted(P.inc)}
    finally:P.close()
