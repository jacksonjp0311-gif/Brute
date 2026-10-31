"""A13 incremental least-B and B_max confirmation for Brute v0.35.0 (BRUTE_PLAN_038; deviation #148 fixes the readings
below). New file; brute/scalesearch12.py (A12), brute/scalesearch11.py (A11), brute/scalesearch10.py (A10) and every
earlier search module are untouched and imported only.

One change against A12 (stop check under B, stop rule and labels are A12's): the least-B search and the B_max confirmation
run on ONE incremental SAT instance per active13 call (Inc13), the scalesearch10._RegionN10 encoding at n = N (S1
transitions, first-visit symmetry, one S7 flip literal per sensor reading) with a pysat ITotalizer over the flip literals
(upper bound B_max). 'At most b flips' is the assumption -rhs[b]; nothing is retracted, so learned clauses persist across
budgets and across steps. When the trace grows, Inc13.sync adds the new rows, transition and flip clauses and extends the
totalizer (clauses only added).
bmin13: least B in lo..B_max by unit increments (b = lo, lo + 1, ...; the first SAT b is the least); B_max UNSAT -> 'none';
the first capped query -> 'unknown'. Probes recorded as [b, True|False|None] (as bmin12).
confirm13: A12's confirm12 verdict rule, each mode one query at n = N (an N-state region holds every machine of <= N states,
so the verdict equals search10's n = 1..N loop; the rival found may differ): the rival clauses of scalesearch10.differ10
are added guarded by a fresh activation literal g (every clause gets -g), solved under [g, -rhs[B_max]], then g is
retired by the unit clause [-g]. Decoded rivals are re-checked exactly as differ10 (fits at B_max, the word separates).
Every solve is scalesearch10._capped_solve (chunked, host interrupt at the query cap); one call is one query.
Host-agnostic: no I/O, network, threads, child processes or global state; the world is reached only via observe/reread."""
from __future__ import annotations
from time import perf_counter
from pysat.card import ITotalizer
from pysat.solvers import Solver
from brute.region import RegionK
from brute.scalesearch4 import SOLVER4
from brute.scalesearch7 import _bit
from brute.scalesearch8 import distinguishing_word,run_word
from brute.scalesearch9 import word_len9
from brute.scalesearch10 import Trace10,_Owner10,_capped_solve,stop_check10,majority,final_state,fits,QUERY_S10
from brute.scalesearch11 import b_max11,majority_rate

__all__=['Inc13','bmin13','confirm13','active13','b_max11','majority_rate','majority','final_state','fits','Trace10']


class Inc13:
    """Incremental N-state flip region over a growing trace with a totalizer (ubound B_max) on the flip literals."""
    def __init__(self,N,k,m,s,B_max,solver=SOLVER4):
        self._owner=None;self._skip=False;self._dl=None;self.calls=0;self.n=N;self.k=k;self.m=m;self.s_bits=s;self.B_max=B_max
        self.nv=0;self.x=[];self.f=[];self.T=-1;self.acts=[];self.tot=None;self.s=Solver(name=solver);self.guards=0
        n=N;K=range(k);M=range(m);v=self._v;self.cl=[]
        self.d=[[[v() for _ in range(n)] for _ in K] for _ in range(n)];self.e=[[v() for _ in M] for _ in range(n)]
        for q in range(n):
            for a in K:self._one(self.d[q][a])
            self._one(self.e[q])
        self._flush()

    _v=RegionK._v;_amo=RegionK._amo;_one=RegionK._one;_solve=_capped_solve

    def _flush(self):
        for c in self.cl:self.s.add_clause(c)
        self.cl=[]

    def close(self):
        if self.tot is not None:self.tot.delete();self.tot=None
        if self.s is not None:self.s.delete();self.s=None

    def __del__(self):
        try:self.close()
        except Exception:pass

    def sync(self,tr):
        """Add trace positions T + 1 .. len(tr.acts) (the trace only grows; earlier positions must be unchanged)."""
        if self.T>=0 and (tr.acts[:self.T]!=self.acts or tr.readings[:self.T+1]!=self.readings):
            raise ValueError('Inc13: trace prefix changed')
        n=self.n;cl=self.cl;v=self._v;M=range(self.m);new=[]
        for t in range(self.T+1,len(tr.acts)+1):
            row=[v() for _ in range(n)];self.x.append(row);self._one(row)
            if t==0:cl.append([row[0]])
            for q in range(1,n):cl.append([-row[q]]+[self.x[u][q-1] for u in range(t)])
            if t>0:
                a=tr.acts[t-1]
                for q in range(n):
                    for r in range(n):cl.append([-self.x[t-1][q],-self.d[q][a][r],row[r]])
            for j,b in enumerate(tr.readings[t]):
                if b is None:continue
                fv=v();new.append(fv);bad=[c for c in M if _bit(c,j,self.s_bits)!=b]
                for q in range(n):
                    for c in bad:cl.append([-row[q],-self.e[q][c],fv])
        self.T=len(tr.acts);self.acts=list(tr.acts);self.readings=list(tr.readings)
        if new:
            self.f.extend(new)
            if self.tot is None:self.tot=ITotalizer(lits=new,ubound=self.B_max,top_id=self.nv);cl.extend(self.tot.cnf.clauses)
            else:
                self.tot.extend(lits=new,ubound=self.B_max,top_id=self.nv)
                if self.tot.nof_new:cl.extend(self.tot.cnf.clauses[-self.tot.nof_new:])
            self.nv=max(self.nv,self.tot.top_id)
        self._flush();return self

    def budget(self,b):
        """Assumptions for 'at most b flips' (none when b >= the number of flip literals)."""
        if b>self.B_max:raise ValueError('b > B_max')
        return [] if b>=len(self.f) else [-self.tot.rhs[b]]

    def query(self,o,deadline,assume):
        self._owner=o;self._dl=deadline;return self._solve(assume)

    def machine(self,mod):
        n,K,M=self.n,range(self.k),range(self.m)
        return ([[next(r for r in range(n) if self.d[q][a][r] in mod) for a in K] for q in range(n)],
                [next(c for c in M if self.e[q][c] in mod) for q in range(n)])


def bmin13(o,inc,tr,lo,B_max,deadline,probes=None):
    """('ok', B) | ('none', None) | ('unknown', None) by unit increments on the incremental instance."""
    probes=probes if probes is not None else []
    if lo>B_max:return 'none',None
    inc.sync(tr)
    for b in range(lo,B_max+1):
        if perf_counter()>=deadline:return 'unknown',None
        r=inc.query(o,deadline,inc.budget(b));probes.append([b,r])
        if r is None:return 'unknown',None
        if r:return 'ok',b
    return 'none',None


def differ13(o,inc,tr,M1,s1,mode,B,deadline):
    """differ10 at n = N on the incremental instance: (True, M2, s2, word) | (False, None, None, None) | (None, ...)."""
    inc.sync(tr);d1,e1=M1;n1=len(d1);n=inc.n;k=inc.k;L=word_len9(n,n1);T=inc.T;v=inc._v;g=v();cl=[]
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
        for q in range(n):add([-inc.x[T][q],y[0][q]]);add([inc.x[T][q],-y[0][q]])
        add([z[0][s1]])
    elif mode=='start':add([y[0][0]]);add([z[0][0]])
    else:raise ValueError(mode)
    for j in range(1,L+1):
        for b in range(k):
            for p in range(n1):add([-z[j-1][p],-A[j][b],z[j][d1[p][b]]])
            for q in range(n):
                for r in range(n):add([-y[j-1][q],-A[j][b],-inc.d[q][b][r],y[j][r]])
    for j in range(L+1):
        for p in range(n1):
            for q in range(n):add([-D[j],-z[j][p],-y[j][q],-inc.e[q][e1[p]]])
    add(D)
    for c in cl:inc.s.add_clause(c)
    inc.guards+=1
    try:
        r=inc.query(o,deadline,[g]+inc.budget(B))
        if r is None:return None,None,None,None
        if r is False:return False,None,None,None
        mod=set(x for x in inc.s.get_model() if x>0);M2=inc.machine(mod)
        word=[next(b for b in range(k) if A[j][b] in mod) for j in range(1,L+1)]
        jd=min(j for j in range(L+1) if D[j] in mod);word=word[:jd]
        if not fits(M2,tr,B):raise AssertionError('differ13: decoded M2 does not fit')
        s2=final_state(M2[0],tr.acts)
        q1,q2=(s1,s2) if mode=='future' else (0,0);p1=[e1[q1]]+run_word(d1,e1,q1,word);p2=[M2[1][q2]]+run_word(M2[0],M2[1],q2,word)
        if p1==p2:raise AssertionError('differ13: decoded word does not separate')
        return True,M2,s2,word
    finally:inc.s.add_clause([-g])


def search13(o,inc,tr,M1,s1,mode,B,deadline):
    """search10-shaped result from one n = N query: verdicts [[N, 'SAT'|'UNSAT'|'UNKNOWN']]."""
    N=inc.n;L=word_len9(N,len(M1[0]));ver=[]
    res=lambda **kw:{'found':False,'unknown':False,'n':None,'M2':None,'s2':None,'word_sat':None,'verdicts':ver,'L':L,'B':B,**kw}
    if perf_counter()>=deadline:ver.append([N,'UNKNOWN']);return res(unknown=True)
    f,M2,s2,w=differ13(o,inc,tr,M1,s1,mode,B,deadline)
    if f is None:ver.append([N,'UNKNOWN']);return res(unknown=True)
    if f:ver.append([N,'SAT']);return res(found=True,n=N,M2=M2,s2=s2,word_sat=w)
    ver.append([N,'UNSAT']);return res()


def confirm13(o,inc,tr,M1,s1,claim,B_max,deadline):
    """confirm12's verdict rule on the incremental instance: {'verdict', 'future', 'start'}."""
    F=search13(o,inc,tr,M1,s1,'future',B_max,deadline);out={'future':F,'start':None}
    if F['unknown']:return {'verdict':'unknown',**out}
    if F['found']:return {'verdict':'AMB',**out}
    if claim=='IDF':return {'verdict':'IDF',**out}
    S=search13(o,inc,tr,M1,s1,'start',B_max,deadline);out['start']=S
    if S['unknown']:return {'verdict':'unknown',**out}
    return {'verdict':'IDF' if S['found'] else 'ID',**out}


def active13(readings,acts,k,s,N,observe,reread,deadline,K,B_max,r=3,query_s=QUERY_S10,solver=SOLVER4,hook=None):
    """active12 (sound stop) with bmin13 / confirm13 on one Inc13 instance. Same return shape as active12."""
    m=1<<s;tr=Trace10(readings,acts,s);used=0;reads=0;rounds=[];n_lo=1;B=0;hist=[[len(tr.acts),B,'start']]
    inc=Inc13(N,k,m,s,B_max,solver)
    try:
        while True:
            o=_Owner10(query_s,hook);x=stop_check10(tr,B,k,m,N,deadline,n_lo,query_s,solver,o)
            rec={'T':len(tr.acts),'B':B,'n_min':x['n_min'],'M1':x['model'],'s1':x['s1'],'future':x['future'],'start':x['start'],
                 'check':x['stop']};rounds.append(rec)
            if x['stop']=='none' and B<B_max:
                pr=[];st,Bn=bmin13(o,inc,tr,B+1,B_max,deadline,pr)
                rec.update(query_walls=list(o.query_walls),capped=o.capped,raise_to=Bn,raise_status=st,probes=pr)
                if st!='ok':stop_='unknown' if st=='unknown' else 'none';break
                B=Bn;hist.append([len(tr.acts),B,'raise']);n_lo=1;continue
            M1=x['model'];s1=x['s1']
            if x['stop'] in ('ID','IDF') and B<B_max:
                C=confirm13(o,inc,tr,M1,s1,x['stop'],B_max,deadline)
                rec.update(confirm={'verdict':C['verdict'],'future':C['future'],'start':C['start'],'B_max':B_max})
                if C['verdict']!='AMB':
                    rec.update(query_walls=list(o.query_walls),capped=o.capped);stop_=C['verdict'];break
                F=C['future']
            elif x['stop']!='AMB':
                rec.update(query_walls=list(o.query_walls),capped=o.capped);stop_=x['stop'];break
            else:F=x['future']
            rec.update(query_walls=list(o.query_walls),capped=o.capped)
            M2=F['M2'];s2=F['s2']
            w=distinguishing_word(M1[0],M1[1],s1,M2[0],M2[1],s2);rec.update(word=w,M2=M2,s2=s2)
            if w is None:raise AssertionError('active13: SAT M2 has no distinguishing word')
            if len(w)>K-used:stop_='K_spent';break
            rec['pred1']=run_word(M1[0],M1[1],s1,w);rec['pred2']=run_word(M2[0],M2[1],s2,w);obs=[];raw=[]
            for a in w:
                rr=[tuple(observe(a))]+[tuple(reread()) for _ in range(r-1)]
                o_=majority(rr) if r>1 else rr[0];tr.add(a,o_);obs.append(o_);raw.append(rr)
            used+=len(w);reads+=r*len(w);rec['obs']=obs;rec['raw']=raw;rec['reps']=r;n_lo=x['n_min']
    finally:inc.close()
    return {'stop':stop_,'trace':tr,'used':used,'reads':reads,'B':B,'B_history':hist,'rounds':rounds,'final':x,
            'inc_guards':inc.guards,'inc_flip_lits':len(inc.f)}
