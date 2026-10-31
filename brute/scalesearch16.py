"""A16 for Brute v0.39.0 (BRUTE_PLAN_042; pre-run deviation #157 fixes the readings below). New file; brute/scalesearch14.py
(A14), brute/scalesearch15.py, brute/encaudit16.py and every earlier module are untouched and imported only.

A16 = A14 (least machine, rival search at every size n_min..N, shortest separating word, stop rule, labels, K, budgets, query
cap, incremental per-size instances, first-visit symmetry clauses, size search from 1) with two declared changes, both
taken from frozen code:
 (i) the apartness clauses of encaudit16 E1 (-x[t][q] | -x[u][q] for every apart pair with intersecting own masks; Exact:
     apart positions cannot share a state, so no consistent machine is excluded); NO fixed colours (the plan-041 audit tied
     the decision loss and most of the cost to the fixed-colour clique);
 (ii) the per-size cube split of scalesearch15 / encaudit16 E4: when a size-n query (least or rival) returns capped, it is
     re-solved as cubes q = 0..n-1 under the extra assumption x[t*][q], t* = Pool15.cube_pos (the first trace position
     outside the greedy clique Pool15 computes; here the clique only chooses t* and fixes no colour). Each cube is one capped
     call; SAT at the first SAT cube, UNSAT if every cube is UNSAT, unknown otherwise (also when the case deadline passes).
     Exactly-one on x[t*] makes the cubes cover the query, so verdicts other than unknown are unchanged.
The solver comes from a factory (default: pysat behind a clause counter), so a host may supply a hard-killable solver; every
call is logged on the pool (size, phase least / rival / cube, wall, capped, clauses, vars).
Host-agnostic: no I/O, network, threads, child processes or global state; the world is reached only via observe."""
from __future__ import annotations
from time import perf_counter
from brute.scalesearch4 import SOLVER4
from brute.scalesearch8 import distinguishing_word,run_word
from brute.scalesearch10 import _Owner10
from brute.scalesearch14 import QUERY_S14,K14,BUDGET14,stop_check14
from brute.encaudit16 import H14Apart,PoolE1,native,_extra

__all__=['QUERY_S14','K14','BUDGET14','H16','Pool16','stop_check16','active16','native']


class H16(H14Apart):
    """E1's instance (first-visit + apartness clauses) with the E4 cube split on capped queries."""
    def __init__(self,*a,**kw):self.cubes=0;self.cube_sat=0;self.cube_unsat=0;H14Apart.__init__(self,*a,**kw)

    def query(self,o,deadline,assume):
        t=perf_counter();self._owner=o;self._dl=deadline;r=self._solve(assume);self._log('least' if not assume else 'rival',t,r)
        if r is not None:return r
        ts=self.pool.cube_pos(self.T)
        if ts is None:return None
        allu=True
        for q in range(self.n):
            if perf_counter()>=deadline:return None
            t=perf_counter();self._owner=o;self._dl=deadline;self.cubes+=1;rq=self._solve(list(assume)+[self.x[ts][q]]);self._log('cube',t,rq)
            if rq is True:self.cube_sat+=1;return True
            if rq is None:allu=False
            else:self.cube_unsat+=1
        return False if allu else None


class Pool16(PoolE1):
    """PoolE1's bookkeeping (apartness pairs; the clique only picks the cube position) with H16 instances."""
    def get(self,n,masks,acts):
        self._update(masks,acts)
        if n not in self.inc:self.inc[n]=H16(n,self.k,self.m,self,self.solver)
        return self.inc[n].sync(masks,acts)

    def cube_counts(self):
        return {'cubes':sum(i.cubes for i in self.inc.values()),'cube_sat':sum(i.cube_sat for i in self.inc.values()),
                'cube_unsat':sum(i.cube_unsat for i in self.inc.values())}


def _ex(P):
    out=_extra(P);out['cube']=P.cube_counts();return out


def stop_check16(masks,acts,k,m,N,deadline,n_lo=1,query_s=QUERY_S14,solver=SOLVER4,o=None,hook=None,factory=native):
    """stop_check14 on a fresh Pool16 (closed on return). Returns stop_check14's dict plus 'audit'."""
    P=Pool16(k,m,solver,factory);o=o or _Owner10(query_s,hook)
    try:
        r=stop_check14(masks,acts,k,m,N,deadline,max(n_lo,P.lower(masks,acts)),query_s,solver,o,P);r['audit']=_ex(P);return r
    finally:P.close()


def active16(masks,acts,k,m,N,observe,deadline,K=K14,query_s=QUERY_S14,solver=SOLVER4,hook=None,factory=native):
    """active14's loop on one Pool16. Returns active14's keys plus 'clique', 'cube' and 'audit'."""
    masks=list(masks);acts=list(acts);used=0;rounds=[];P=Pool16(k,m,solver,factory);n_lo=P.lower(masks,acts)
    try:
        while True:
            o=_Owner10(query_s,hook);r=stop_check14(masks,acts,k,m,N,deadline,n_lo,query_s,solver,o,P)
            rec={'T':len(acts),'n_min':r['n_min'],'M1':r['model'],'s1':r['s1'],'future':r['future'],'start':r['start'],
                 'query_walls':list(o.query_walls),'capped':o.capped,'check':r['stop']};rounds.append(rec)
            if r['stop']!='AMB':stop=r['stop'];break
            F=r['future'];M1=r['model'];M2=F['M2'];s1=r['s1'];s2=F['s2']
            w=distinguishing_word(M1[0],M1[1],s1,M2[0],M2[1],s2);rec.update(word=w,M2=M2,s2=s2)
            if w is None:raise AssertionError('active16: SAT M2 has no distinguishing word')
            if len(w)>K-used:stop='K_spent';break
            rec['pred1']=run_word(M1[0],M1[1],s1,w);rec['pred2']=run_word(M2[0],M2[1],s2,w);obs=[]
            for a in w:mk=observe(a);acts.append(a);masks.append(mk);obs.append(mk)
            used+=len(w);rec['obs']=obs;n_lo=max(r['n_min'],n_lo)
        ex=_ex(P)
        return {'stop':stop,'masks':masks,'acts':acts,'used':used,'rounds':rounds,'final':r,'guards':P.guards(),'sizes':sorted(P.inc),
                'clique':ex.get('clique'),'cube':ex.get('cube'),'audit':ex}
    finally:P.close()
