"""A9 sound active identification for Brute v0.31.0 (BRUTE_PLAN_034; deviation #140 fixes the readings below). New file;
brute/region.py (S1), brute/scalesearch4.py and brute/scalesearch8.py are untouched and imported only.

least9: the least n (from max(n_lo, greedy clique bound) up to N) with a complete Moore machine consistent with the trace
(the frozen S1 RegionK with first-visit symmetry, every SAT query hard-capped at query_s inside the deadline); returns M1.
differ9: is there a complete machine M2 with <= n states, consistent with the trace, whose behaviour differs from M1's from
a given pair of states? mode 'future': M1 at its current state s1, M2 at its own current state (after the trace); mode
'start': both at state 0. Encoding: the S1 region for M2 plus a symbolic word a_1..a_L (one-hot actions), M2's state
y_0..y_L under it, M1's state z_0..z_L (fixed table), and a disjunction over j = 0..L that M2's code at y_j differs from
M1's code at z_j. L = N + n_M1 - 1, which is at least n + n_M1 - 2, the longest shortest-distinguishing word of two Moore
machines with n and n_M1 states, so UNSAT proves that no <= n machine consistent with the trace differs from M1 (sound and
complete for that bound). A SAT model is decoded and re-checked by simulation (consistent, and the decoded word separates).
search9: n = n_min..N in order, stopping at the first n with an M2; 'none' only if every n is UNSAT.
active9: the A9 loop. Each round: M1 = least9; future search; if an M2 exists, the shortest word that separates M1 and M2
from their current states (product BFS, brute.scalesearch8.distinguishing_word) is executed through observe(action) ->
reading mask, readings appended, repeat (K extra actions in all); if none, the start search: none -> 'ID', else 'IDF'.
Stops: 'ID', 'IDF', 'K_spent' (word longer than the actions left), 'unknown' (deadline or capped query), 'none' (no machine
<= N). stop_check9 is the same stop decision on a fixed trace with no actions (used by A9_random).
Host-agnostic: no I/O, network, threads, child processes or global state; the world is reached only via observe."""
from __future__ import annotations
from time import perf_counter
from brute.scalesearch import simulate
from brute.scalesearch4 import _lower_bound,SOLVER4
from brute.scalesearch8 import _Owner8,_RegionQ,distinguishing_word,run_word,QUERY_S8,K8

__all__=['QUERY_S9','K9','least9','differ9','search9','stop_check9','active9','word_len9']
QUERY_S9=QUERY_S8;K9=K8


def word_len9(N,n1):return N+n1-1


def least9(o,masks,acts,k,m,N,deadline,n_lo=1,solver=SOLVER4):
    """('ok', n, (d, e)) | ('none', None, None) | ('unknown', None, None)."""
    n=max(n_lo,_lower_bound(masks))
    while n<=N:
        if perf_counter()>=deadline:return 'unknown',None,None
        R=_RegionQ(o,n,k,m,masks,acts,solver);R._dl=deadline
        try:
            r=R._solve([])
            if r is None:return 'unknown',None,None
            if r is False:n+=1;continue
            return 'ok',n,R.machine()
        finally:R.close()
    return 'none',None,None


def _eo(R,xs):
    R.s.add_clause(list(xs))
    for i in range(len(xs)):
        for j in range(i+1,len(xs)):R.s.add_clause([-xs[i],-xs[j]])


def differ9(o,masks,acts,k,m,n,M1,s1,mode,L,deadline,solver=SOLVER4):
    """(True, M2, s2, word) | (False, None, None, None) | (None, ...) unknown. M2 has n states, start state 0."""
    d1,e1=M1;n1=len(d1);R=_RegionQ(o,n,k,m,masks,acts,solver);R._dl=deadline;v=R._v;T=len(acts);add=R.s.add_clause
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
        ok,s2,_=simulate(M2[0],M2[1],acts,masks)
        if not ok:raise AssertionError('differ9: decoded M2 inconsistent')
        q1,q2=(s1,s2) if mode=='future' else (0,0);p1=[e1[q1]]+run_word(d1,e1,q1,word);p2=[M2[1][q2]]+run_word(M2[0],M2[1],q2,word)
        if p1==p2:raise AssertionError('differ9: decoded word does not separate')
        return True,M2,s2,word
    finally:R.close()


def search9(o,masks,acts,k,m,n_min,N,M1,s1,mode,deadline,solver=SOLVER4):
    """n = n_min..N in order. Returns {'found', 'unknown', 'n', 'M2', 's2', 'word_sat', 'verdicts': [[n, 'SAT'|'UNSAT'|'UNKNOWN']]}."""
    L=word_len9(N,len(M1[0]));ver=[]
    for n in range(n_min,N+1):
        if perf_counter()>=deadline:ver.append([n,'UNKNOWN']);return {'found':False,'unknown':True,'n':None,'M2':None,'s2':None,'word_sat':None,'verdicts':ver,'L':L}
        f,M2,s2,w=differ9(o,masks,acts,k,m,n,M1,s1,mode,L,deadline,solver)
        if f is None:ver.append([n,'UNKNOWN']);return {'found':False,'unknown':True,'n':None,'M2':None,'s2':None,'word_sat':None,'verdicts':ver,'L':L}
        if f:ver.append([n,'SAT']);return {'found':True,'unknown':False,'n':n,'M2':M2,'s2':s2,'word_sat':w,'verdicts':ver,'L':L}
        ver.append([n,'UNSAT'])
    return {'found':False,'unknown':False,'n':None,'M2':None,'s2':None,'word_sat':None,'verdicts':ver,'L':L}



def stop_check9(masks,acts,k,m,N,deadline,n_lo=1,query_s=QUERY_S9,solver=SOLVER4,o=None):
    """The A9 stop decision on a fixed trace. {'stop': 'ID'|'IDF'|'AMB'|'unknown'|'none', 'n_min', 'model', 's1', 'future',
    'start', 'query_walls', 'capped'}; 'AMB' means a future M2 exists (A9 would act)."""
    o=o or _Owner8(query_s);res={'n_min':None,'model':None,'s1':None,'future':None,'start':None}
    st,n,M1=least9(o,masks,acts,k,m,N,deadline,n_lo,solver)
    out=lambda stop:{'stop':stop,**res,'query_walls':o.query_walls,'capped':o.capped}
    if st!='ok':return out(st)
    s1=simulate(M1[0],M1[1],acts,masks)[1];res.update(n_min=n,model=M1,s1=s1)
    F=search9(o,masks,acts,k,m,n,N,M1,s1,'future',deadline,solver);res['future']=F
    if F['unknown']:return out('unknown')
    if F['found']:return out('AMB')
    S=search9(o,masks,acts,k,m,n,N,M1,s1,'start',deadline,solver);res['start']=S
    if S['unknown']:return out('unknown')
    return out('IDF' if S['found'] else 'ID')


def active9(masks,acts,k,m,N,observe,deadline,K=K9,query_s=QUERY_S9,solver=SOLVER4):
    """The A9 loop on a copy of the passive trace. Returns {'stop', 'masks', 'acts', 'used', 'rounds', 'final'}; final is the
    last round's stop_check9-style record; each round records n_min, M1, s1, the future and start searches, and for an
    executed word the word, both machines' predicted codes and the real reading masks."""
    masks=list(masks);acts=list(acts);used=0;rounds=[];n_lo=1
    while True:
        o=_Owner8(query_s);r=stop_check9(masks,acts,k,m,N,deadline,n_lo,query_s,solver,o)
        rec={'T':len(acts),'n_min':r['n_min'],'M1':r['model'],'s1':r['s1'],'future':r['future'],'start':r['start'],
             'query_walls':list(o.query_walls),'capped':o.capped,'check':r['stop']};rounds.append(rec)
        if r['stop']!='AMB':stop=r['stop'];break
        F=r['future'];M1=r['model'];M2=F['M2'];s1=r['s1'];s2=F['s2']
        w=distinguishing_word(M1[0],M1[1],s1,M2[0],M2[1],s2);rec.update(word=w,M2=M2,s2=s2)
        if w is None:raise AssertionError('active9: SAT M2 has no distinguishing word')
        if len(w)>K-used:stop='K_spent';break
        rec['pred1']=run_word(M1[0],M1[1],s1,w);rec['pred2']=run_word(M2[0],M2[1],s2,w);obs=[]
        for a in w:mk=observe(a);acts.append(a);masks.append(mk);obs.append(mk)
        used+=len(w);rec['obs']=obs;n_lo=r['n_min']
    return {'stop':stop,'masks':masks,'acts':acts,'used':used,'rounds':rounds,'final':r}
