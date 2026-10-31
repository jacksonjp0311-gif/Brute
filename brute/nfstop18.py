"""A16_nf for Brute v0.42.0 (BRUTE_PLAN_045; pre-run deviation #163 fixes the readings below). New file; brute/scalesearch14.py,
brute/scalesearch16.py and every earlier module are untouched and imported only.

A16_nf = A16 (Pool16 instances: first-visit + apartness clauses, cube split on capped queries; least machine; shortest
separating word; K, budgets, query cap) with ONE declared change to the stop check:
  the least-model search runs n = n_lo..CEIL (CEIL = 16, a compute ceiling only, never claimed); once n_min is found, the future
  and start rival searches run at sizes n_min..n_min+delta (search14 with N replaced by n_min+delta; separating-word length
  L = word_len9(n_min+delta, n_min)), instead of n_min..N. The rival bound is NOT clipped at CEIL.
A stop 'ID' / 'IDF' from this module is a BOUNDED claim (plan labels ID_d / IDF_d): the returned model is unique (from the start,
or in its future behaviour) among machines with at most n_min+delta states that are consistent with the trace. It is not
full N-freedom: a larger true machine is not ruled out, and the least-model search still uses the ceiling CEIL.
Host-agnostic: no I/O, network, threads, child processes or global state; the world is reached only via observe."""
from __future__ import annotations
from brute.scalesearch4 import SOLVER4
from brute.scalesearch8 import distinguishing_word,run_word
from brute.scalesearch10 import _Owner10
from brute.scalesearch14 import QUERY_S14,K14,BUDGET14,least14,search14
from brute.scalesearch16 import Pool16,_ex,native
from brute.scalesearch import simulate

CEIL18=16
__all__=['CEIL18','QUERY_S14','K14','BUDGET14','stop_check18','active18']


def stop_check18(masks,acts,k,m,delta,deadline,n_lo=1,query_s=QUERY_S14,o=None,P=None,ceil=CEIL18):
    """stop_check14 with least14 up to ceil and both rival searches over n_min..n_min+delta. Adds 'bound' (n_min+delta or None)."""
    res={'n_min':None,'model':None,'s1':None,'future':None,'start':None,'bound':None}
    out=lambda stop:{'stop':stop,**res,'query_walls':o.query_walls,'capped':o.capped}
    st,n,M1=least14(o,P,masks,acts,ceil,deadline,n_lo)
    if st!='ok':return out(st)
    B=n+delta;s1=simulate(M1[0],M1[1],acts,masks)[1];res.update(n_min=n,model=M1,s1=s1,bound=B)
    F=search14(o,P,masks,acts,n,B,M1,s1,'future',deadline);res['future']=F
    if F['unknown']:return out('unknown')
    if F['found']:return out('AMB')
    S=search14(o,P,masks,acts,n,B,M1,s1,'start',deadline);res['start']=S
    if S['unknown']:return out('unknown')
    return out('IDF' if S['found'] else 'ID')


def active18(masks,acts,k,m,delta,observe,deadline,K=K14,query_s=QUERY_S14,solver=SOLVER4,hook=None,factory=native,ceil=CEIL18):
    """active16's loop on one Pool16 with stop_check18. Returns active16's keys plus 'delta', 'ceil' and 'bound'."""
    if delta<0:raise ValueError('delta must be >= 0')
    masks=list(masks);acts=list(acts);used=0;rounds=[];P=Pool16(k,m,solver,factory);n_lo=P.lower(masks,acts)
    try:
        while True:
            o=_Owner10(query_s,hook);r=stop_check18(masks,acts,k,m,delta,deadline,n_lo,query_s,o,P,ceil)
            rec={'T':len(acts),'n_min':r['n_min'],'M1':r['model'],'s1':r['s1'],'future':r['future'],'start':r['start'],'bound':r['bound'],
                 'query_walls':list(o.query_walls),'capped':o.capped,'check':r['stop']};rounds.append(rec)
            if r['stop']!='AMB':stop=r['stop'];break
            F=r['future'];M1=r['model'];M2=F['M2'];s1=r['s1'];s2=F['s2']
            w=distinguishing_word(M1[0],M1[1],s1,M2[0],M2[1],s2);rec.update(word=w,M2=M2,s2=s2)
            if w is None:raise AssertionError('active18: SAT M2 has no distinguishing word')
            if len(w)>K-used:stop='K_spent';break
            rec['pred1']=run_word(M1[0],M1[1],s1,w);rec['pred2']=run_word(M2[0],M2[1],s2,w);obs=[]
            for a in w:mk=observe(a);acts.append(a);masks.append(mk);obs.append(mk)
            used+=len(w);rec['obs']=obs;n_lo=max(r['n_min'],n_lo)
        ex=_ex(P)
        return {'stop':stop,'masks':masks,'acts':acts,'used':used,'rounds':rounds,'final':r,'guards':P.guards(),'sizes':sorted(P.inc),
                'clique':ex.get('clique'),'cube':ex.get('cube'),'audit':ex,'delta':delta,'ceil':ceil,'bound':r['bound']}
    finally:P.close()
