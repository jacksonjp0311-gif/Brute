"""A10 noisy sound active identification for Brute v0.32.0 (BRUTE_PLAN_035; deviation #142 fixes the readings below).
New file; brute/scalesearch9.py (A9), brute/scalesearch8.py, brute/scalesearch7.py (S7 encoding) and brute/region.py (S1)
are untouched and imported only.

Trace: readings (tuples of s bits, fully observed), actions, and the derived reading masks.
Region under budget B: B = 0 is the frozen A9 region (S1 RegionK with first-visit symmetry, hard masks); B > 0 is the S1
transition encoding with first-visit symmetry and the S7 flip encoding (one flip literal per sensor reading; x[t][q] and
e[q][c] imply the flip when bit j of c differs from the reading) with a sequential-counter 'at most B flips'.
Query cap: every SAT query is chunked exactly as A9 (conflict chunks, wall check before each chunk) and, when the host
passes a hook, the host is asked to interrupt the solver at min(deadline, query start + query_s); an interrupted query is
UNKNOWN. hook is any object with arm(fn, seconds) -> token and disarm(token); the core never creates threads or timers.
least10 / differ10 / search10: least9 / differ9 / search9 under the current B (M2 must have <= B flips; decoded models are
re-checked by simulation: exact consistency at B = 0, machine_flips <= B at B > 0). bmin10: the least B in lo..B_max with
some machine of <= N states (binary search; SAT at N is monotone in B).
active10: each round runs the A9 stop check under B. If no machine <= N fits under B and the arm is adaptive, B rises to
bmin10(B + 1, B_max) and never falls (n search restarts at 1); a fixed arm stops 'none'. A rival M2 -> the shortest
separating word is executed; at B > 0 each reading of the word is read r times (the step's reading plus r - 1 re-reads of
the same state through reread()) and the per-bit majority is appended. Cost against K: len(word) at B = 0, r * len(word)
at B > 0. Stops: ID, IDF, K_spent, unknown, none.
identify10: the 031 identify probe (least n, then a second solve with the first table blocked) under the S7 flip encoding
with fixed B (n from 1: the greedy clique bound assumes exact masks).
Host-agnostic: no I/O, network, threads, child processes or global state; the world is reached only via observe/reread."""
from __future__ import annotations
from time import perf_counter
from pysat.card import CardEnc,EncType
from pysat.solvers import Solver
from brute.region import RegionK,codes_mask
from brute.scalesearch import simulate
from brute.scalesearch4 import _lower_bound,CHUNK_MIN,CHUNK_MAX,CHUNK_TARGET_S,SOLVER4
from brute.scalesearch7 import machine_flips,flip_budget,_bit
from brute.scalesearch8 import _Owner8,_RegionQ,distinguishing_word,run_word,QUERY_S8
from brute.scalesearch9 import word_len9

__all__=['QUERY_S10','K10','R10','Trace10','least10','differ10','search10','bmin10','stop_check10','active10','identify10',
         'majority','final_state','fits']
QUERY_S10=QUERY_S8;K10={8:64,12:64,16:128};R10=3


class _Owner10(_Owner8):
    def __init__(self,query_s,hook=None):_Owner8.__init__(self,query_s);self.hook=hook


def _capped_solve(R,assume):
    """A9's chunked solve (scalesearch8._RegionQ._solve) plus the optional host interrupt at the query cap."""
    if R._skip:R._skip=False;return True
    o=R._owner;R.calls+=1;o.solves+=1;t0=perf_counter();dl=min(R._dl,t0+o.query_s);h=o.hook;tok=None
    if h is not None:tok=h.arm(R.s.interrupt,max(0.0,dl-t0))
    try:
        while True:
            if perf_counter()>=dl:
                o.unknowns+=1
                if dl<R._dl:o.capped+=1
                return None
            ch=o.chunk;t=perf_counter();R.s.conf_budget(ch);r=R.s.solve_limited(assumptions=assume,expect_interrupt=h is not None)
            dt=perf_counter()-t;o.chunks+=1
            o.chunk=int(max(CHUNK_MIN,min(CHUNK_MAX,ch*CHUNK_TARGET_S/max(dt,1e-3))))
            if r is not None:return r
    finally:
        if h is not None:h.disarm(tok);R.s.clear_interrupt()
        o.query_walls.append(perf_counter()-t0)


class _RegionQ10(_RegionQ):
    """B = 0: the frozen A9 region with the host-interruptible solve."""
    _solve=_capped_solve


class _RegionN10:
    """B > 0: S1 transition encoding, first-visit symmetry, S7 flip literals, at most B flips."""
    def __init__(self,owner,n,k,m,s,readings,actions,bound,solver):
        self._owner=owner;self._skip=False;self._dl=None;self.calls=0
        self.n=n;self.k=k;self.m=m;self.T=T=len(actions);self.nv=0;cl=self.cl=[];v=self._v;K=range(k);M=range(m)
        self.x=[[v() for _ in range(n)] for _ in range(T+1)]
        self.d=[[[v() for _ in range(n)] for _ in K] for _ in range(n)]
        self.e=[[v() for _ in M] for _ in range(n)]
        for row in self.x:self._one(row)
        for q in range(n):
            for a in K:self._one(self.d[q][a])
            self._one(self.e[q])
        cl.append([self.x[0][0]])
        for t in range(T+1):
            for q in range(1,n):cl.append([-self.x[t][q]]+[self.x[u][q-1] for u in range(t)])
        for t in range(1,T+1):
            a=actions[t-1]
            for q in range(n):
                for r in range(n):cl.append([-self.x[t-1][q],-self.d[q][a][r],self.x[t][r]])
        f=[]
        for t,o in enumerate(readings):
            for j,b in enumerate(o):
                if b is None:continue
                fv=v();f.append(fv);bad=[c for c in M if _bit(c,j,s)!=b]
                for q in range(n):
                    for c in bad:cl.append([-self.x[t][q],-self.e[q][c],fv])
        self.f=f;self.bound=bound
        if bound<len(f):
            enc=CardEnc.atmost(lits=f,bound=bound,top_id=self.nv,encoding=EncType.seqcounter);cl.extend(enc.clauses);self.nv=max(self.nv,enc.nv)
        self.s=Solver(name=solver,bootstrap_with=cl);self.cl=None

    _v=RegionK._v;_amo=RegionK._amo;_one=RegionK._one;close=RegionK.close;_solve=_capped_solve

    def __del__(self):
        try:self.close()
        except Exception:pass

    def machine(self):
        mod=set(x for x in self.s.get_model() if x>0);n,K,M=self.n,range(self.k),range(self.m)
        return ([[next(r for r in range(n) if self.d[q][a][r] in mod) for a in K] for q in range(n)],
                [next(c for c in M if self.e[q][c] in mod) for q in range(n)])


class Trace10:
    """Readings (bit tuples), actions and masks of one arm's trace."""
    def __init__(self,readings,acts,s):
        self.s=s;self.readings=[tuple(o) for o in readings];self.acts=list(acts);self.masks=[codes_mask(o,s) for o in self.readings]
        if len(self.readings)!=len(self.acts)+1:raise ValueError('need one more reading than actions')

    def add(self,a,o):self.acts.append(a);o=tuple(o);self.readings.append(o);self.masks.append(codes_mask(o,self.s))


def final_state(d,acts,q=0):
    for a in acts:q=d[q][a]
    return q


def fits(M,tr,B):
    """M (start 0) is consistent with the trace: exactly at B = 0, with <= B flips otherwise."""
    if B==0:return simulate(M[0],M[1],tr.acts,tr.masks)[0]
    return machine_flips(M[0],M[1],tr.acts,tr.readings,tr.s)<=B


def majority(reads):
    return tuple(int(2*sum(o[j] for o in reads)>len(reads)) for j in range(len(reads[0])))


def _region(o,n,k,m,tr,B,solver):
    if B==0:return _RegionQ10(o,n,k,m,tr.masks,tr.acts,solver)
    return _RegionN10(o,n,k,m,tr.s,tr.readings,tr.acts,B,solver)


def least10(o,tr,B,k,m,N,deadline,n_lo=1,solver=SOLVER4):
    """('ok', n, (d, e)) | ('none', None, None) | ('unknown', None, None) under budget B."""
    n=max(n_lo,_lower_bound(tr.masks)) if B==0 else max(n_lo,1)
    while n<=N:
        if perf_counter()>=deadline:return 'unknown',None,None
        R=_region(o,n,k,m,tr,B,solver);R._dl=deadline
        try:
            r=R._solve([])
            if r is None:return 'unknown',None,None
            if r is False:n+=1;continue
            M1=R.machine()
            if not fits(M1,tr,B):raise AssertionError('least10: decoded M1 does not fit')
            return 'ok',n,M1
        finally:R.close()
    return 'none',None,None


def bmin10(o,tr,k,m,N,lo,B_max,deadline,solver=SOLVER4):
    """('ok', B) least B in lo..B_max with a machine of <= N states | ('none', None) | ('unknown', None)."""
    if lo>B_max:return 'none',None
    def sat(B):
        if perf_counter()>=deadline:return None
        R=_region(o,N,k,m,tr,B,solver);R._dl=deadline
        try:return R._solve([])
        finally:R.close()
    r=sat(B_max)
    if r is None:return 'unknown',None
    if r is False:return 'none',None
    a,b=lo,B_max
    while a<b:
        c=(a+b)//2;r=sat(c)
        if r is None:return 'unknown',None
        if r:b=c
        else:a=c+1
    return 'ok',a


def _eo(R,xs):
    R.s.add_clause(list(xs))
    for i in range(len(xs)):
        for j in range(i+1,len(xs)):R.s.add_clause([-xs[i],-xs[j]])


def differ10(o,tr,B,k,m,n,M1,s1,mode,L,deadline,solver=SOLVER4):
    """differ9 under budget B: (True, M2, s2, word) | (False, None, None, None) | (None, ...) unknown."""
    d1,e1=M1;n1=len(d1);R=_region(o,n,k,m,tr,B,solver);R._dl=deadline;v=R._v;T=len(tr.acts);add=R.s.add_clause
    try:
        y=[[v() for _ in range(n)] for _ in range(L+1)];z=[[v() for _ in range(n1)] for _ in range(L+1)]
        A=[None]+[[v() for _ in range(k)] for _ in range(L)];D=[v() for _ in range(L+1)]
        for j in range(L+1):_eo(R,y[j]);_eo(R,z[j])
        for j in range(1,L+1):_eo(R,A[j])
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
        r=R._solve([])
        if r is None:return None,None,None,None
        if r is False:return False,None,None,None
        mod=set(x for x in R.s.get_model() if x>0);M2=R.machine()
        word=[next(b for b in range(k) if A[j][b] in mod) for j in range(1,L+1)]
        jd=min(j for j in range(L+1) if D[j] in mod);word=word[:jd]
        if not fits(M2,tr,B):raise AssertionError('differ10: decoded M2 does not fit')
        s2=final_state(M2[0],tr.acts)
        q1,q2=(s1,s2) if mode=='future' else (0,0);p1=[e1[q1]]+run_word(d1,e1,q1,word);p2=[M2[1][q2]]+run_word(M2[0],M2[1],q2,word)
        if p1==p2:raise AssertionError('differ10: decoded word does not separate')
        return True,M2,s2,word
    finally:R.close()


def search10(o,tr,B,k,m,n_min,N,M1,s1,mode,deadline,solver=SOLVER4):
    L=word_len9(N,len(M1[0]));ver=[]
    res=lambda **kw:{'found':False,'unknown':False,'n':None,'M2':None,'s2':None,'word_sat':None,'verdicts':ver,'L':L,'B':B,**kw}
    for n in range(n_min,N+1):
        if perf_counter()>=deadline:ver.append([n,'UNKNOWN']);return res(unknown=True)
        f,M2,s2,w=differ10(o,tr,B,k,m,n,M1,s1,mode,L,deadline,solver)
        if f is None:ver.append([n,'UNKNOWN']);return res(unknown=True)
        if f:ver.append([n,'SAT']);return res(found=True,n=n,M2=M2,s2=s2,word_sat=w)
        ver.append([n,'UNSAT'])
    return res()


def stop_check10(tr,B,k,m,N,deadline,n_lo=1,query_s=QUERY_S10,solver=SOLVER4,o=None,hook=None):
    """stop_check9 under B: {'stop': 'ID'|'IDF'|'AMB'|'unknown'|'none', 'n_min', 'model', 's1', 'future', 'start', 'B', ...}."""
    o=o or _Owner10(query_s,hook);res={'n_min':None,'model':None,'s1':None,'future':None,'start':None,'B':B}
    st,n,M1=least10(o,tr,B,k,m,N,deadline,n_lo,solver)
    out=lambda stop:{'stop':stop,**res,'query_walls':o.query_walls,'capped':o.capped}
    if st!='ok':return out(st)
    s1=final_state(M1[0],tr.acts);res.update(n_min=n,model=M1,s1=s1)
    F=search10(o,tr,B,k,m,n,N,M1,s1,'future',deadline,solver);res['future']=F
    if F['unknown']:return out('unknown')
    if F['found']:return out('AMB')
    S=search10(o,tr,B,k,m,n,N,M1,s1,'start',deadline,solver);res['start']=S
    if S['unknown']:return out('unknown')
    return out('IDF' if S['found'] else 'ID')


def active10(readings,acts,k,s,N,observe,reread,deadline,K,B_max,B0=0,adaptive=True,r=R10,query_s=QUERY_S10,solver=SOLVER4,hook=None):
    """The A10 loop (adaptive) or A10_fixed (adaptive False, B0 = B_end). observe(a) -> reading tuple after action a;
    reread() -> a fresh reading of the current state. Returns {'stop', 'trace', 'used', 'B', 'B_history', 'rounds', 'final'}."""
    m=1<<s;tr=Trace10(readings,acts,s);used=0;rounds=[];n_lo=1;B=B0;hist=[[len(tr.acts),B,'start']]
    while True:
        o=_Owner10(query_s,hook);x=stop_check10(tr,B,k,m,N,deadline,n_lo,query_s,solver,o)
        rec={'T':len(tr.acts),'B':B,'n_min':x['n_min'],'M1':x['model'],'s1':x['s1'],'future':x['future'],'start':x['start'],
             'check':x['stop']};rounds.append(rec)
        if x['stop']=='none' and adaptive and B<B_max:
            st,Bn=bmin10(o,tr,k,m,N,B+1,B_max,deadline,solver);rec.update(query_walls=list(o.query_walls),capped=o.capped,raise_to=Bn,raise_status=st)
            if st!='ok':stop='unknown' if st=='unknown' else 'none';break
            B=Bn;hist.append([len(tr.acts),B,'raise']);n_lo=1;continue
        rec.update(query_walls=list(o.query_walls),capped=o.capped)
        if x['stop']!='AMB':stop=x['stop'];break
        F=x['future'];M1=x['model'];M2=F['M2'];s1=x['s1'];s2=F['s2']
        w=distinguishing_word(M1[0],M1[1],s1,M2[0],M2[1],s2);rec.update(word=w,M2=M2,s2=s2)
        if w is None:raise AssertionError('active10: SAT M2 has no distinguishing word')
        reps=r if B>0 else 1;cost=len(w)*reps
        if cost>K-used:stop='K_spent';break
        rec['pred1']=run_word(M1[0],M1[1],s1,w);rec['pred2']=run_word(M2[0],M2[1],s2,w);obs=[];raw=[]
        for a in w:
            reads=[tuple(observe(a))]+[tuple(reread()) for _ in range(reps-1)]
            o_=majority(reads) if reps>1 else reads[0];tr.add(a,o_);obs.append(o_);raw.append(reads)
        used+=cost;rec['obs']=obs;rec['raw']=raw;rec['reps']=reps;n_lo=x['n_min']
    return {'stop':stop,'trace':tr,'used':used,'B':B,'B_history':hist,'rounds':rounds,'final':x}


def identify10(readings,acts,k,s,n_max,B,deadline,query_s=QUERY_S10,solver=SOLVER4,hook=None):
    """{'n_min', 'unique', 'unknown', 'model', 'second_found', 'query_walls', 'capped', 'B'} under budget B (n from 1)."""
    m=1<<s;tr=Trace10(readings,acts,s);o=_Owner10(query_s,hook);n=1
    out=lambda **kw:{'n_min':None,'unique':False,'unknown':False,'model':None,'second_found':False,'query_walls':o.query_walls,
                     'capped':o.capped,'B':B,**kw}
    while n<=n_max:
        if perf_counter()>=deadline:return out(unknown=True)
        R=_region(o,n,k,m,tr,B,solver);R._dl=deadline
        try:
            r=R._solve([])
            if r is None:return out(unknown=True)
            if r is False:n+=1;continue
            d,e=R.machine()
            R.s.add_clause([-R.d[q][a][d[q][a]] for q in range(n) for a in range(k)]+[-R.e[q][e[q]] for q in range(n)])
            u=R._solve([])
            return out(n_min=n,unique=u is False,unknown=u is None,model=(d,e),second_found=u is True)
        finally:R.close()
    return out()
