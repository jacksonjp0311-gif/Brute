"""Brute v0.7.0 planning arm P7: the frozen A5 learner with a count-based ACTION CHOICE (BRUTE_PLAN_009 planning_rule).

New file. CountPlanLearner subclasses the frozen brute.region_learner.RegionBruteLearner and overrides ONLY
experiment() (the action choice). Certification, status, reason, probabilities, surprise, alarm and resume are the
frozen A5 code paths run on P7's own (action, observation) history. Nothing is monkeypatched in this process: every
count runs in a forked child process (the frozen brute/modelcount.regionk_cnf temporarily swaps brute.region.Solver to
capture the CNF; doing that only inside the child keeps the parent's A5 objects untouched).

Applicable steps: family and margin supported, no active alarm (the A5 LU-R score is computed) and t >= burn_in
(t = observations so far). Elsewhere: the A5 LU-R choice a_L, planner record None.

Counts n_{a,c} = (machine, fibre state) pairs of the current RegionK region predicting code c under action a, as defined by
the frozen brute/modelcount.count_jobs (fibre jobs). Source order:
  (1) 'enumeration': blocking-clause enumeration of the region's canonical machines projected on (d, e) of the RegionK CNF,
      used iff it completes with <= 10^4 machines within 3 s; pairs then counted in plain Python by replaying the evidence;
      the 2-step branch counts counts2['a,c'][b][c'] (pairs (M, d[P][a]) with e[d[P][a]] = c, deduplicated, predicting c'
      under b) are recorded;
  (2) 'ganak': pyganak projected counts of the 8 fibre jobs via the frozen brute/modelcount.ganak_counts, 2 s per count.
Objective: E1(a) = sum_c n_ac^2 / N_a (Fraction); E2(a) = sum_c (n_ac/N_a) min_b E1(b | a, c) (source 1 only).
Choice: argmin E2 (ties: E1, then a_L) if E2 exists, else argmin E1 (ties: a_L). Any UNKNOWN count, a child failure, the
15 s decision budget or the 150 s per-case counting budget -> fallback to a_L with a reason (never imputed).
"""
from __future__ import annotations
import multiprocessing as mp
import time
from fractions import Fraction
from brute.region_learner import RegionBruteLearner

ENUM_CAP=10_000
ENUM_SECONDS=3.0
PER_COUNT_S=2.0
PER_DECISION_S=15.0
PER_CASE_S=150.0
BURN_IN=8


def e1(counts):
    N=sum(counts);return None if N==0 else Fraction(sum(n*n for n in counts),N)


def fr(x):return None if x is None else f'{x.numerator}/{x.denominator}'


def enumerate_pairs(n,masks,acts,cap=ENUM_CAP,seconds=ENUM_SECONDS,k=2,m=4):
    """(counts, counts2, machines) or (None, None, reason). Runs regionk_cnf: call only in a child process."""
    from pysat.solvers import Solver
    from brute.modelcount import regionk_cnf
    R,base=regionk_cnf(n,k,m,masks,acts);dv=R.d;ev=R.e;R.close()
    proj=[v for q in range(n) for a in range(k) for v in dv[q][a]]+[v for q in range(n) for v in ev[q]]
    t0=time.perf_counter();Ms=[]
    with Solver(name='g3',bootstrap_with=base) as S:
        while True:
            if time.perf_counter()-t0>seconds:return None,None,f'enumeration did not complete within {seconds:g} s'
            if not S.solve():break
            pos=set(x for x in S.get_model() if x>0)
            d=[[next(r for r in range(n) if dv[q][a][r] in pos) for a in range(k)] for q in range(n)]
            e=[next(c for c in range(m) if ev[q][c] in pos) for q in range(n)]
            Ms.append((d,e))
            if len(Ms)>cap:return None,None,f'enumeration exceeded {cap} machines'
            S.add_clause([-v if v in pos else v for v in proj])
    last=masks[-1];counts=[[0]*m for _ in range(k)];br={}
    for mi,(d,e) in enumerate(Ms):
        x=0;A={0:masks[0]}
        for t,a in enumerate(acts):
            x=d[x][a];A[x]=A.get(x,(1<<m)-1)&masks[t+1]
        for j,Aj in A.items():
            if not Aj&last:continue
            for a in range(k):
                p=d[j][a];c=e[p];counts[a][c]+=1;br.setdefault((a,c),set()).add((mi,p))
    counts2={}
    for a in range(k):
        for c in range(m):
            if not counts[a][c]:continue
            nn=[[0]*m for _ in range(k)]
            for mi,p in br[(a,c)]:
                d,e=Ms[mi]
                for b in range(k):nn[b][e[d[p][b]]]+=1
            counts2[f'{a},{c}']=nn
    return counts,counts2,len(Ms)


def ganak_fibres(n,masks,acts,deadline,per_count=PER_COUNT_S,k=2,m=4):
    """(counts, reason). The frozen modelcount jobs and counter; run only in a child process."""
    from brute.modelcount import count_jobs,ganak_counts
    jobs=[j for j in count_jobs(n,k,m,masks,acts) if j[0][0]=='fibre']
    out=ganak_counts(jobs,per_count=per_count,deadline=deadline);counts=[[None]*m for _ in range(k)]
    for (_,a,c),r in ((j[0],out[j[0]]) for j in jobs):
        if r['count'] is None:return None,f"counter UNKNOWN at fibre({a},{c}): {r['reason']}"
        counts[a][c]=int(r['count'])
    return counts,None


def _child(conn,n,masks,acts,deadline):
    try:
        c,c2,info=enumerate_pairs(n,masks,acts)
        if c is not None:conn.send(('enumeration',c,c2,None,info));return
        why=info;c,r=ganak_fibres(n,masks,acts,deadline)
        conn.send(('ganak',c,None,r,why))
    except Exception as exc:
        conn.send((None,None,None,f'error: {type(exc).__name__}: {exc}',None))
    finally:conn.close()


def count_decision(n,masks,acts,budget):
    """{'source', 'counts', 'counts2', 'reason', 'enumeration_note'} computed in a forked, non-daemonic child."""
    ctx=mp.get_context('fork');a,b=ctx.Pipe(duplex=False);deadline=time.time()+budget
    p=ctx.Process(target=_child,args=(b,n,list(masks),list(acts),deadline),daemon=False);p.start();b.close()
    try:
        if a.poll(budget+5.):
            try:src,c,c2,r,note=a.recv()
            except EOFError:src,c,c2,r,note=None,None,None,'error: counting child died',None
        else:src,c,c2,r,note=None,None,None,f'decision counting budget ({budget:.1f} s) exhausted',None
    finally:
        if p.is_alive():p.kill()
        p.join();a.close()
    return {'source':src,'counts':c,'counts2':c2,'reason':r,'enumeration_note':note}


def choose(counts,counts2,a_l):
    E1=[e1(counts[a]) for a in (0,1)]
    if any(x is None for x in E1):return None,E1,None
    if counts2 is not None:
        E2=[]
        for a in (0,1):
            N=sum(counts[a]);tot=Fraction(0)
            for c,nac in enumerate(counts[a]):
                if nac:tot+=Fraction(nac,N)*min(x for x in (e1(counts2[f'{a},{c}'][b]) for b in (0,1)) if x is not None)
            E2.append(tot)
        if E2[0]!=E2[1]:return (0 if E2[0]<E2[1] else 1),E1,E2
        if E1[0]!=E1[1]:return (0 if E1[0]<E1[1] else 1),E1,E2
        return a_l,E1,E2
    if E1[0]!=E1[1]:return (0 if E1[0]<E1[1] else 1),E1,None
    return a_l,E1,None


class CountPlanLearner(RegionBruteLearner):
    """P7. RegionBruteLearner (A5, policy LU-R) constructor plus burn_in and the counting budgets."""
    def __init__(self,*args,burn_in=BURN_IN,per_decision=PER_DECISION_S,per_case=PER_CASE_S,**kwargs):
        super().__init__(*args,**kwargs)
        if self.policy!='LU-R':raise ValueError('P7 replaces the LU-R choice only')
        self.burn_in=burn_in;self.per_decision=per_decision;self.per_case=per_case
        self.counting_seconds=0.;self.planner_decisions=0;self.planner_planned=0;self.planner_fallbacks=0

    def experiment(self,default_action,counts=False):
        out=super().experiment(default_action,counts);a_l=out['action'];out['lur_action']=a_l;out['planner']=None
        live=self.support.status=='supported' and self.margin.status=='supported' and self.alarm_step is None
        if not (live and self.steps>=self.burn_in):return out
        self.planner_decisions+=1
        P={'applicable':True,'source':None,'counts':None,'counts2':None,'E1':None,'E2':None,'choice':a_l,'lur_action':a_l,
           'planned':False,'fallback_reason':None,'enumeration_note':None}
        left=self.per_case-self.counting_seconds
        if left<=0:P['fallback_reason']=f'per-case counting budget ({self.per_case:g} s) exhausted'
        else:
            n,ms,acts=self.support.max_states,list(self.support.region.masks),list(self.support.region.actions)
            P['region']={'n':n,'masks':ms,'actions':acts}
            t0=time.perf_counter();r=count_decision(n,ms,acts,min(self.per_decision,left))
            dt=time.perf_counter()-t0;self.counting_seconds+=dt;P['seconds_informational']=round(dt,3)
            P['source']=r['source'];P['enumeration_note']=r['enumeration_note']
            if r['counts'] is None or r['reason']:P['fallback_reason']=r['reason'] or 'no counts'
            else:
                a,E1,E2=choose(r['counts'],r['counts2'],a_l);P.update(counts=r['counts'],counts2=r['counts2'],E1=[fr(x) for x in E1],
                                                                   E2=[fr(x) for x in E2] if E2 else None)
                if a is None:P['fallback_reason']='N_a = 0'
                else:P.update(choice=a,planned=True)
        if P['planned']:self.planner_planned+=1
        else:self.planner_fallbacks+=1;P['choice']=a_l
        out['planner']=P;out.update(action=P['choice'],score=out['scores'][P['choice']]);return out

    def diagnostics(self):
        d=super().diagnostics()
        d.update({'planner_decisions':self.planner_decisions,'planner_planned':self.planner_planned,
                  'planner_fallbacks':self.planner_fallbacks,'counting_seconds_informational':round(self.counting_seconds,3)})
        return d
