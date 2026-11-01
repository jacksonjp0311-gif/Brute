"""Brute v0.53.0 embeddable certify interface, version 20l (BRUTE_PLAN_056; pre-run deviation #185 fixes the readings below).
Additive: brute/api/certify16e.py, certify16d.py, certify20c.py and every earlier module are untouched and imported only.

certify/20l is a no-reset, table-driven (L*-style) active learner over certify/16e's machinery:
  * Table (pure bookkeeping, no SAT). Rows are trace positions chosen as the BASIS: position 0, then (scanning positions in order)
    every position that is apart on the trace from every basis row (apart = scalesearch15.apart_matrix: the same action word from
    both positions gives disjoint readings). Columns are the separating witness words (shortest common action word ending in
    disjoint readings) used so far. Basis rows are pairwise apart, so EVERY machine consistent with the trace has at least
    len(basis) states (Exact); that is the size lower bound and the hypothesis size. More than N rows: stop AMB, table published.
  * Identification: a position's candidate rows are the rows it is not apart from; then (#185, HYP_ROUNDS = 3 passes) the rows
    whose partial H reproduces its next 2 x rows readings, and forward propagation from an identified predecessor along a known,
    conflict-free cell. One candidate left = identified. Identification only chooses actions and H; it is never trusted.
  * Hypothesis H: state i = basis row i; emission = lowest code of the row's reading; delta(i, a) = identity of t + 1 for the
    first position t identified with i that took action a and whose successor is identified (shortest-lex = trace order);
    a missing cell defaults to a self-loop. H only proposes; it is never trusted.
  * Cell filling from the current position T (the walk has no reset; #185 reads the plan's homing word as the adaptive homing
    sequence below, fixed before data): (1) if T matches two or more rows, propose the witness word of the first two (rows in
    basis order); (2) else if T is identified with i and a cell (i, a) is missing, propose [a] (lowest a); (3) else the
    shortest-lex path in H's known cells from i to the nearest row with a missing cell, then that action; (4) else none.
    A filling word that does not fit in K goes straight to the equivalence check.
  * Equivalence check (no least-machine SAT search): certify/16e's rival query, scalesearch14.search14 on the same Pool16E
    incremental instances and chunked conflict-counted solve, at sizes len(basis)..N with M1 = H and s1 = H's state after the
    trace. If H contradicts the trace, M1 is instead the least SAT machine consistent with the trace at sizes len(basis)..N
    (#185 repair, conflicts counted; M1_source 'sat_repair'; no machine or budget spent -> unknown; n_min is then least14's size, the
    least consistent size, and the rival searches start there; with a consistent H, n_min = len(basis) exactly), so every round's M1 and
    every published model is consistent with the trace. 'future' SAT -> AMB round; the counterexample is distinguishing_word(H, s1, M2, s2), proposed next (it counts against
    K; too long -> K_spent); its observations add apartness and so rows or cells. 'future' UNSAT at every size and 'start'
    UNSAT -> ID; 'start' SAT -> IDF; budget spent -> unknown (IDU). Labels are certify/16e's (LABEL_OF_STOP).
Soundness (Exact argument): an ID / IDF is issued only when every machine with at most N states consistent with the full trace
agrees with H from s1 (and, for ID, from state 0); sizes below len(basis) admit no consistent machine. A wrong or inconsistent H
can only make a rival exist (cost), never a WRONG label. The guarantee is CONDITIONAL on noise-free readings and on the true
machine having at most N states (declared N <= 20). Inferred reason: a larger machine can copy the true machine on every visited
state and differ only on states the trace never reached, so no finite trace rules out every larger machine.
Host-agnostic: no I/O, network, threads, child processes or global state; the world is reached only via observe/propose.
"""
from __future__ import annotations
from collections import deque
from time import perf_counter
from brute.api.certify16 import LABEL_OF_STOP,S_BITS
from brute.api import certify16e as E
from brute.api.certify16d import _Owner16D,INF,A16D_MAX_BOUND
from brute.api.certify16e import Certifier16E,Pool16E,counted16d
from brute.scalesearch8 import distinguishing_word,run_word
from brute.scalesearch import simulate
from brute.scalesearch14 import search14,least14
from brute.scalesearch15 import apart_matrix
from brute.scalesearch16 import _ex

API='brute.certify/20l'
SEARCHES=('a20l',)
HYP_ROUNDS=3
__all__=['API','SEARCHES','A16D_MAX_BOUND','Certifier20L','certify20l','soundness','table_of','fill_word','hypothesis','counted16d']


def soundness(**kw):
    s=E.soundness();s.update(search='a20l',learner='no-reset table (L*-style); H proposes only',
                             proof='certify/16e rival query at sizes len(basis)..N; no least-machine search');return s


def _ap(A,t,u):return A[t][u] if t<u else A[u][t]


def _low(mk):return (mk&-mk).bit_length()-1


def witness(masks,acts,t,u):
    """Shortest common action word from positions t and u ending in disjoint readings (len >= 0), or None."""
    T=len(acts);j=0
    while True:
        if not masks[t+j]&masks[u+j]:return list(acts[t:t+j])
        if t+j>=T or u+j>=T or acts[t+j]!=acts[u+j]:return None
        j+=1


def table_of(masks,acts,basis=None):
    """Pure table from the trace: basis rows (extending the given basis in trace order), per-position candidate rows."""
    A=apart_matrix(masks,acts);T1=len(acts)+1;B=list(basis or [0])
    for t in range(T1):
        if t not in B and all(_ap(A,t,b) for b in B):B.append(t)
    cand=[[i for i,b in enumerate(B) if t==b or not _ap(A,t,b)] for t in range(T1)]
    return {'A':A,'basis':B,'cand':cand}


def _cells(acts,k,n,cand):
    d=[[None]*k for _ in range(n)];conf=set()
    for t,a in enumerate(acts):
        if len(cand[t])==1 and len(cand[t+1])==1:
            i,j=cand[t][0],cand[t+1][0]
            if d[i][a] is None:d[i][a]=j
            elif d[i][a]!=j:conf.add((i,a))
    return d,conf


def _agrees(d,e,masks,acts,t,i,L):
    """H from state i reproduces the readings from position t for up to L steps (a missing cell ends the check: agrees)."""
    q=i
    if not masks[t]>>e[q]&1:return False
    for j in range(t,min(len(acts),t+L)):
        q=d[q][acts[j]]
        if q is None:return True
        if not masks[j+1]>>e[q]&1:return False
    return True


def hypothesis(masks,acts,k,tab,L=None,rounds=None):
    """(H = (d, e), missing cells, conflict cells) from the table; refines tab['cand'] in place.
    Cells: first sample (trace order) of a position identified with row i, action a, successor identified. Identification starts
    from trace apartness against the rows, then (#185) is narrowed for `rounds` passes to the rows whose partial H reproduces the
    position's next L readings (2 x rows by default; a narrowing that would leave no row is not applied), then forward along a
    known conflict-free cell from an identified predecessor (trace order). Missing cells -> self-loop."""
    B=tab['basis'];n=len(B);e=[_low(masks[b]) for b in B];L=2*n if L is None else L;cand=tab['cand']
    rounds=HYP_ROUNDS if rounds is None else rounds;d,conf=_cells(acts,k,n,cand)
    for _ in range(rounds):
        new=[]
        for t,c in enumerate(cand):
            if len(c)<2:new.append(c);continue
            c2=[i for i in c if _agrees(d,e,masks,acts,t,i,L)];new.append(c2 if c2 else c)
        for t in range(1,len(new)):
            p_=new[t-1]
            if len(new[t])>1 and len(p_)==1 and (p_[0],acts[t-1]) not in conf and d[p_[0]][acts[t-1]] in new[t]:new[t]=[d[p_[0]][acts[t-1]]]
        if new==cand:break
        cand=new;d,conf=_cells(acts,k,n,cand)
    tab['cand']=cand
    miss=sorted((i,a) for i in range(n) for a in range(k) if d[i][a] is None)
    for i,a in miss:d[i][a]=i
    return (d,e),miss,sorted(conf)


def fill_word(masks,acts,k,tab,H,miss):
    """The next table-filling word from the current position (rules (1)-(3) of the module docstring), with its kind; or (None, None)."""
    T=len(acts);c=tab['cand'][T];B=tab['basis']
    if len(c)>=2:
        for x in range(len(c)):
            for y in range(x+1,len(c)):
                w=witness(masks,acts,B[c[x]],B[c[y]])
                if w:return w,'home'
        return None,None
    if not c:return None,None
    i=c[0];ms=set(miss)
    for a in range(k):
        if (i,a) in ms:return [a],'cell'
    d=H[0];known=lambda q,a:(q,a) not in ms;prev={i:None};dq=deque([i])
    while dq:
        q=dq.popleft()
        for a in range(k):
            if not known(q,a):
                w=[a];x=q
                while prev[x] is not None:x,b=prev[x];w.append(b)
                return w[::-1],'route'
        for a in range(k):
            r=d[q][a]
            if r not in prev:prev[r]=(q,a);dq.append(r)
    return None,None


class Certifier20L(Certifier16E):
    def __init__(self,initial=None,num_actions=None,family_bound=None,search='a20l',max_chunks=None,**kw):
        if search!='a20l':raise ValueError('search must be a20l')
        super().__init__(initial,num_actions,family_bound,'a16d',max_chunks,**kw);self.search='a20l'
        self.basis=[0];self.table=[];self.columns=[];self.hyps=0;self.cex=0;self.fill_steps=0;self.H=None

    def _tab(self):
        tab=table_of(self.masks,self.acts,self.basis);self.basis=list(tab['basis']);return tab

    def propose(self):
        if self.stop is not None:return None
        if self._pending is not None:raise RuntimeError('the proposed word is not fully observed yet')
        if self.P is None:
            self.case.t0=perf_counter();self.P=Pool16E(self.k,1<<S_BITS,self.solver,self.factory);self.n_lo=self.P.lower(self.masks,self.acts)
        tab=self._tab();n=len(self.basis);self.n_lo=n
        if n>self.N:
            r={'stop':'AMB','n_min':None,'model':None,'s1':None,'future':None,'start':None,'table_rows':n}
            self.table.append({'T':len(self.acts),'kind':'rows_exceed_N','rows':n});return self._finish20('AMB',r)
        H,miss,conf=hypothesis(self.masks,self.acts,self.k,tab);self.H=H
        w,kind=fill_word(self.masks,self.acts,self.k,tab,H,miss)
        if w is not None and len(w)<=self.K-self.used:
            ent={'T':len(self.acts),'kind':kind,'word':list(w),'rows':n,'missing':len(miss),'conflicts':len(conf)}
            if kind=='home' and w not in self.columns:self.columns.append(list(w))
            self.table.append(ent);self.fill_steps+=len(w)
            self._pending=list(w);self._rec=ent;self._r={'n_min':n};self._obs=[];return list(w)
        return self._check(H,n,miss,conf)

    def _check(self,H,n,miss,conf):
        nc=len(self.case.calls_log);o=_Owner16D(self.case);self.hyps+=1
        ok,s1,_=simulate(H[0],H[1],self.acts,self.masks);src='table'
        if not ok:
            # #185 repair: H contradicts the trace, so it may not stand as a round's M1 (the recount contract needs M1 consistent).
            # M1 = the least SAT machine consistent with the trace at sizes len(basis)..N, conflicts counted in the same budget.
            st0,n2,M=least14(o,self.P,self.masks,self.acts,self.N,INF,n);src='sat_repair'
            if st0!='ok':
                r={'stop':'unknown','n_min':n,'model':None,'s1':None,'future':None,'start':None,'repair':st0}
                self.rounds.append({'T':len(self.acts),'n_min':n,'M1':None,'s1':None,'future':None,'start':None,'M1_source':src,'repair':st0,
                                    'query_walls':list(o.query_walls),'call_conflicts':list(o.call_conflicts),'call_capped':list(o.call_capped),
                                    'capped':o.capped,'check':'unknown','table_rows':n,'table_missing':len(miss),'table_conflicts':len(conf)})
                log=self.case.calls_log[nc:];rec=self.rounds[-1]
                rec['call_chunks']=[x[0] for x in log];rec['chunk_conflicts']=[list(x[1]) for x in log];rec['chunk_walls']=[list(x[2]) for x in log]
                self.table.append({'T':len(self.acts),'kind':'check','rows':n,'missing':len(miss),'conflicts':len(conf),'check':'unknown','M1_source':src})
                return self._finish20('unknown',r)
            H=M;s1=simulate(H[0],H[1],self.acts,self.masks)[1];nm=n2   # least14 searched up from len(basis): n2 is the least size
        else:nm=n   # H itself is consistent with len(basis) states, the lower bound: n_min = len(basis) exactly
        d,e=H
        r={'stop':None,'n_min':nm,'model':H,'s1':s1,'future':None,'start':None}
        F=search14(o,self.P,self.masks,self.acts,nm,self.N,H,s1,'future',INF);r['future']=F
        if F['unknown']:st='unknown'
        elif F['found']:st='AMB'
        else:
            S=search14(o,self.P,self.masks,self.acts,nm,self.N,H,s1,'start',INF);r['start']=S
            st='unknown' if S['unknown'] else ('IDF' if S['found'] else 'ID')
        r['stop']=st
        rec={'T':len(self.acts),'n_min':nm,'M1':H,'s1':s1,'future':F,'start':r['start'],'query_walls':list(o.query_walls),
             'call_conflicts':list(o.call_conflicts),'call_capped':list(o.call_capped),'capped':o.capped,'check':st,
             'table_rows':n,'table_missing':len(miss),'table_conflicts':len(conf),'M1_source':src}
        log=self.case.calls_log[nc:]
        rec['call_chunks']=[x[0] for x in log];rec['chunk_conflicts']=[list(x[1]) for x in log];rec['chunk_walls']=[list(x[2]) for x in log]
        self.rounds.append(rec);self.table.append({'T':len(self.acts),'kind':'check','rows':n,'missing':len(miss),'conflicts':len(conf),'check':st,'M1_source':src})
        if st!='AMB':return self._finish20(st,r)
        M2=F['M2'];s2=F['s2'];w=distinguishing_word(d,e,s1,M2[0],M2[1],s2);rec.update(word=w,M2=M2,s2=s2)
        if w is None:raise AssertionError('certify20l: SAT M2 has no distinguishing word')
        if len(w)>self.K-self.used:return self._finish20('K_spent',r)
        rec['pred1']=run_word(d,e,s1,w);rec['pred2']=run_word(M2[0],M2[1],s2,w);self.cex+=1
        self.table[-1]['counterexample']=list(w)
        self._pending=list(w);self._rec=rec;self._r=r;self._obs=[];return list(w)

    def _finish20(self,stop,r):
        self._finish(stop,r);self._record['table']=self.table_summary();self._extend();return None

    def table_summary(self):
        return {'basis':list(self.basis),'rows':len(self.basis),'columns':[list(c) for c in self.columns],'n_columns':len(self.columns),
                'hypotheses':self.hyps,'counterexamples':self.cex,'fill_steps':self.fill_steps,'log':[dict(x) for x in self.table]}

    def current(self):
        d=super().current();d['api']=API;d['search']='a20l';d['rows']=len(self.basis);return d

    def result(self):
        d=super().result();d['api']=API;d['search']='a20l';d['soundness']=soundness();d['table']=self.table_summary();return d


def certify20l(initial,actions,observations,num_actions=None,family_bound=None,**kw):
    """One table + equivalence check on the given trace (K=0: no experiment)."""
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    c=Certifier20L(initial,num_actions,family_bound,'a20l',K=0,**kw)
    try:
        for a,o in zip(acts,obs):c.observe(a,o)
        c.propose();return c.result()
    finally:c.close()
