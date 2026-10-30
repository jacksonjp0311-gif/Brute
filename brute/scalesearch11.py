"""A11 repeated-read sound active identification for Brute v0.33.0 (BRUTE_PLAN_036; deviation #144 fixes the readings
below). New file; brute/scalesearch10.py (A10) and every earlier search module are untouched and imported only.

The trace the solver sees holds majority readings only: the host reads each base-trace position r times (one step read
plus r - 1 re-reads of the same state) and passes the per-bit majorities; during the loop every reading of an executed
separating word is taken r times through observe / reread and only the majority is appended. Raw reads never reach the
solver.
bmin11: the least B in lo..B_max with some machine of <= N states, found by bisection: B_max first (UNSAT -> 'none'),
then midpoints of [lo, hi) with hi the least B known SAT (SAT -> hi = mid, UNSAT -> lo = mid + 1); the first capped query
returns 'unknown' (no unproven B is ever used). search 'up' uses scalesearch10.bmin10 (the A10 upward chain; ablation).
active11: the A10 loop (stop check under B; on 'none' B rises to bmin(B + 1, B_max) and never falls) with r reads per
word reading at every B, and K counted in world steps (a re-read costs a read, not a step). Stops: ID, IDF, K_spent,
unknown, none.
Host-agnostic: no I/O, network, threads, child processes or global state; the world is reached only via observe/reread."""
from __future__ import annotations
from math import comb
from time import perf_counter
from brute.scalesearch4 import SOLVER4
from brute.scalesearch7 import flip_budget
from brute.scalesearch8 import distinguishing_word,run_word
from brute import scalesearch10 as S10
from brute.scalesearch10 import Trace10,_Owner10,_region,stop_check10,majority,final_state,fits,bmin10,QUERY_S10,K10

__all__=['R11','majority_rate','b_max11','bmin11','active11','majority','final_state','fits','Trace10']
R11=(3,5)


def majority_rate(eps,r):
    """Probability that a per-bit majority of r independent reads (r odd) is flipped."""
    if r%2==0 or r<1:raise ValueError('r must be odd')
    return sum(comb(r,i)*eps**i*(1-eps)**(r-i) for i in range(r//2+1,r+1))


def b_max11(n_bits,eps,r):
    """The declared-rate B_end rule (scalesearch7.flip_budget) applied to the majority flip rate."""
    return flip_budget(n_bits,majority_rate(eps,r))


def _sat(o,tr,k,m,N,B,deadline,solver):
    R=_region(o,N,k,m,tr,B,solver);R._dl=deadline
    try:return R._solve([])
    finally:R.close()


def bmin11(o,tr,k,m,N,lo,B_max,deadline,solver=SOLVER4,probes=None):
    """('ok', B) | ('none', None) | ('unknown', None); probes (optional list) records [B, True|False|None] per query."""
    probes=probes if probes is not None else []
    if lo>B_max:return 'none',None
    if perf_counter()>=deadline:return 'unknown',None
    r=_sat(o,tr,k,m,N,B_max,deadline,solver);probes.append([B_max,r])
    if r is None:return 'unknown',None
    if r is False:return 'none',None
    hi=B_max
    while lo<hi:
        if perf_counter()>=deadline:return 'unknown',None
        mid=(lo+hi)//2;r=_sat(o,tr,k,m,N,mid,deadline,solver);probes.append([mid,r])
        if r is None:return 'unknown',None
        if r:hi=mid
        else:lo=mid+1
    return 'ok',hi


def active11(readings,acts,k,s,N,observe,reread,deadline,K,B_max,r=3,search='bisect',query_s=QUERY_S10,solver=SOLVER4,hook=None):
    """readings: majority base readings. Returns {'stop', 'trace', 'used', 'reads', 'B', 'B_history', 'rounds', 'final'}."""
    if search not in ('bisect','up'):raise ValueError(search)
    m=1<<s;tr=Trace10(readings,acts,s);used=0;reads=0;rounds=[];n_lo=1;B=0;hist=[[len(tr.acts),B,'start']]
    while True:
        o=_Owner10(query_s,hook);x=stop_check10(tr,B,k,m,N,deadline,n_lo,query_s,solver,o)
        rec={'T':len(tr.acts),'B':B,'n_min':x['n_min'],'M1':x['model'],'s1':x['s1'],'future':x['future'],'start':x['start'],
             'check':x['stop']};rounds.append(rec)
        if x['stop']=='none' and B<B_max:
            pr=[]
            if search=='bisect':st,Bn=bmin11(o,tr,k,m,N,B+1,B_max,deadline,solver,pr)
            else:st,Bn=bmin10(o,tr,k,m,N,B+1,B_max,deadline,solver)
            rec.update(query_walls=list(o.query_walls),capped=o.capped,raise_to=Bn,raise_status=st,probes=pr)
            if st!='ok':stop='unknown' if st=='unknown' else 'none';break
            B=Bn;hist.append([len(tr.acts),B,'raise']);n_lo=1;continue
        rec.update(query_walls=list(o.query_walls),capped=o.capped)
        if x['stop']!='AMB':stop=x['stop'];break
        F=x['future'];M1=x['model'];M2=F['M2'];s1=x['s1'];s2=F['s2']
        w=distinguishing_word(M1[0],M1[1],s1,M2[0],M2[1],s2);rec.update(word=w,M2=M2,s2=s2)
        if w is None:raise AssertionError('active11: SAT M2 has no distinguishing word')
        if len(w)>K-used:stop='K_spent';break
        rec['pred1']=run_word(M1[0],M1[1],s1,w);rec['pred2']=run_word(M2[0],M2[1],s2,w);obs=[];raw=[]
        for a in w:
            rr=[tuple(observe(a))]+[tuple(reread()) for _ in range(r-1)]
            o_=majority(rr) if r>1 else rr[0];tr.add(a,o_);obs.append(o_);raw.append(rr)
        used+=len(w);reads+=r*len(w);rec['obs']=obs;rec['raw']=raw;rec['reps']=r;n_lo=x['n_min']
    return {'stop':stop,'trace':tr,'used':used,'reads':reads,'B':B,'B_history':hist,'rounds':rounds,'final':x}
