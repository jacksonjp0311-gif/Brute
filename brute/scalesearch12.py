"""A12 sound noisy stop for Brute v0.34.0 (BRUTE_PLAN_037; deviation #146 items 2-3 fix the readings below). New file;
brute/scalesearch11.py (A11), brute/scalesearch10.py (A10) and every earlier search module are untouched and imported only.

bmin12: the least B in lo..B_max with some machine of <= N states, by upward doubling then bisection. Candidates are lo,
then max(c + 1, 2c), ... capped at B_max (B_max itself is always a candidate); the first SAT candidate c ends the doubling
and the least B is bisected in (previous UNSAT candidate, c]. B_max UNSAT -> 'none'; the first capped query -> 'unknown'
(no unproven B is ever used). Every query is recorded in probes as [B, True|False|None].
Sound stop (stop='sound'): when the stop check under the current B < B_max says ID or IDF, the claim is confirmed at B_max:
  1. search10 'future' at B_max with n = 1..N: SAT -> the separating word is executed as a rival pair (r reads per action,
     majority appended) and the loop continues; capped -> 'unknown';
  2. (ID only) search10 'start' at B_max with n = 1..N: SAT -> IDF, UNSAT -> ID, capped -> 'unknown'.
  An IDF claim under B needs only step 1 (a start-distinct rival is already known). When B == B_max the ordinary check is
  the confirmation. A start-mode word cannot be executed (the world has no reset), so a start-distinct rival at B_max
  yields IDF, never a probe.
stop='a11': the A11 stop (no confirmation); with search 'double' this is the A12_r3_nostop ablation.
Host-agnostic: no I/O, network, threads, child processes or global state; the world is reached only via observe/reread."""
from __future__ import annotations
from time import perf_counter
from brute.scalesearch4 import SOLVER4
from brute.scalesearch8 import distinguishing_word,run_word
from brute.scalesearch10 import Trace10,_Owner10,stop_check10,search10,majority,final_state,fits,QUERY_S10
from brute.scalesearch11 import _sat,bmin11,b_max11,majority_rate

__all__=['bmin12','confirm12','active12','b_max11','majority_rate','majority','final_state','fits','Trace10']


def doubling_candidates(lo,B_max):
    """lo, max(c + 1, 2c), ... strictly increasing, capped at and including B_max (empty if lo > B_max)."""
    out=[];c=lo
    while c<=B_max:
        out.append(c)
        if c==B_max:break
        c=min(B_max,max(c+1,2*c))
    return out


def bmin12(o,tr,k,m,N,lo,B_max,deadline,solver=SOLVER4,probes=None):
    """('ok', B) | ('none', None) | ('unknown', None); probes (optional list) records [B, True|False|None] per query."""
    probes=probes if probes is not None else []
    if lo>B_max:return 'none',None
    prev=lo-1;hi=None
    for c in doubling_candidates(lo,B_max):
        if perf_counter()>=deadline:return 'unknown',None
        r=_sat(o,tr,k,m,N,c,deadline,solver);probes.append([c,r])
        if r is None:return 'unknown',None
        if r:hi=c;break
        prev=c
    if hi is None:return 'none',None
    a=prev+1
    while a<hi:
        if perf_counter()>=deadline:return 'unknown',None
        mid=(a+hi)//2;r=_sat(o,tr,k,m,N,mid,deadline,solver);probes.append([mid,r])
        if r is None:return 'unknown',None
        if r:hi=mid
        else:a=mid+1
    return 'ok',hi


def confirm12(o,tr,k,m,N,M1,s1,claim,B_max,deadline,solver=SOLVER4):
    """{'verdict': 'AMB'|'ID'|'IDF'|'unknown', 'future', 'start'} for an ID / IDF claim made under some B < B_max."""
    F=search10(o,tr,B_max,k,m,1,N,M1,s1,'future',deadline,solver);out={'future':F,'start':None}
    if F['unknown']:return {'verdict':'unknown',**out}
    if F['found']:return {'verdict':'AMB',**out}
    if claim=='IDF':return {'verdict':'IDF',**out}
    S=search10(o,tr,B_max,k,m,1,N,M1,s1,'start',deadline,solver);out['start']=S
    if S['unknown']:return {'verdict':'unknown',**out}
    return {'verdict':'IDF' if S['found'] else 'ID',**out}


def active12(readings,acts,k,s,N,observe,reread,deadline,K,B_max,r=3,search='double',stop='sound',query_s=QUERY_S10,solver=SOLVER4,hook=None):
    """readings: majority base readings. Returns {'stop', 'trace', 'used', 'reads', 'B', 'B_history', 'rounds', 'final'}."""
    if search not in ('double','bisect'):raise ValueError(search)
    if stop not in ('sound','a11'):raise ValueError(stop)
    m=1<<s;tr=Trace10(readings,acts,s);used=0;reads=0;rounds=[];n_lo=1;B=0;hist=[[len(tr.acts),B,'start']]
    while True:
        o=_Owner10(query_s,hook);x=stop_check10(tr,B,k,m,N,deadline,n_lo,query_s,solver,o)
        rec={'T':len(tr.acts),'B':B,'n_min':x['n_min'],'M1':x['model'],'s1':x['s1'],'future':x['future'],'start':x['start'],
             'check':x['stop']};rounds.append(rec)
        if x['stop']=='none' and B<B_max:
            pr=[]
            if search=='double':st,Bn=bmin12(o,tr,k,m,N,B+1,B_max,deadline,solver,pr)
            else:st,Bn=bmin11(o,tr,k,m,N,B+1,B_max,deadline,solver,pr)
            rec.update(query_walls=list(o.query_walls),capped=o.capped,raise_to=Bn,raise_status=st,probes=pr)
            if st!='ok':stop_='unknown' if st=='unknown' else 'none';break
            B=Bn;hist.append([len(tr.acts),B,'raise']);n_lo=1;continue
        M1=x['model'];s1=x['s1']
        if x['stop'] in ('ID','IDF') and stop=='sound' and B<B_max:
            C=confirm12(o,tr,k,m,N,M1,s1,x['stop'],B_max,deadline,solver)
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
        if w is None:raise AssertionError('active12: SAT M2 has no distinguishing word')
        if len(w)>K-used:stop_='K_spent';break
        rec['pred1']=run_word(M1[0],M1[1],s1,w);rec['pred2']=run_word(M2[0],M2[1],s2,w);obs=[];raw=[]
        for a in w:
            rr=[tuple(observe(a))]+[tuple(reread()) for _ in range(r-1)]
            o_=majority(rr) if r>1 else rr[0];tr.add(a,o_);obs.append(o_);raw.append(rr)
        used+=len(w);reads+=r*len(w);rec['obs']=obs;rec['raw']=raw;rec['reps']=r;n_lo=x['n_min']
    return {'stop':stop_,'trace':tr,'used':used,'reads':reads,'B':B,'B_history':hist,'rounds':rounds,'final':x}
