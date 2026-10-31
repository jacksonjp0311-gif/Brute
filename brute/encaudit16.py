"""Encoding audit variants E0-E4 for Brute v0.38.0 (BRUTE_PLAN_041; deviation #154 fixes the readings below). New file;
brute/scalesearch14.py (A14), brute/scalesearch15.py (A15, A15_cube) and every earlier module are untouched and imported only.

Every variant runs the frozen least14 / differ14 / search14 / stop_check14 on a pool of per-size incremental instances; the
variants differ ONLY in the per-size CNF and the size-search start:
  E0  Inc14 (first-visit symmetry clauses), start = A14's lower bound          (= A14, brute.scalesearch14)
  E1  E0 plus apartness clauses -x[t][q] | -x[u][q] for every apart pair (Pool15's future_pairs); first-visit clauses kept;
      no fixed colours; start = A14's lower bound
  E2  Inc15's fixed-colour greedy clique only (x[c_i] = i); no first-visit clauses and no pair clauses beyond those the
      colours imply (clique members already differ); start = max(A14 bound, |C|)
  E3  Inc15 as frozen, no cube split                                           (= A15)
  E4  Inc15 as frozen, cube split                                              (= A15_cube)
The only code differences against the frozen classes: (i) the SAT solver comes from a factory (default: pysat Solver(name)
behind a clause counter), so a host may supply a hard-killable solver; (ii) every query is logged per call (size n, phase
'least' / 'rival' / 'cube', wall, capped, clause and variable counts) on the pool. Both leave every clause and every verdict
unchanged (tested against the frozen active14 / active15 / stop_check14 / stop_check15).
Host-agnostic: no I/O, network, threads, child processes or global state; the world is reached only via observe."""
from __future__ import annotations
from time import perf_counter
from pysat.solvers import Solver
from brute.region import RegionK
from brute.scalesearch4 import SOLVER4
from brute.scalesearch8 import distinguishing_word,run_word
from brute.scalesearch10 import _Owner10,_capped_solve
from brute.scalesearch14 import QUERY_S14,K14,BUDGET14,Inc14,Pool14,stop_check14
from brute.scalesearch15 import Inc15,Pool15

__all__=['VARIANTS','ARM_VARIANT','QUERY_S14','K14','BUDGET14','Counted','native','make_pool','stop_check_audit','active_audit']
VARIANTS=('E0','E1','E2','E3','E4')
ARM_VARIANT={'A14':'E0','A15':'E3','A15_cube':'E4'}


class Counted:
    """A pysat solver with a clause counter (the default factory)."""
    def __init__(self,name=SOLVER4):self.s=Solver(name=name);self.n_clauses=0

    def add_clause(self,c):self.n_clauses+=1;self.s.add_clause(c)
    def conf_budget(self,b):self.s.conf_budget(b)
    def solve_limited(self,assumptions=(),expect_interrupt=False):return self.s.solve_limited(assumptions=assumptions,expect_interrupt=expect_interrupt)
    def interrupt(self):self.s.interrupt()
    def clear_interrupt(self):self.s.clear_interrupt()
    def get_model(self):return self.s.get_model()
    def delete(self):self.s.delete()


def native(name=SOLVER4):return Counted(name)


class _Log:
    def _log(self,phase,t,r):
        P=self.pool;P.calls.append({'n':self.n,'phase':phase,'wall':perf_counter()-t,'capped':r is None,
                                    'clauses':getattr(self.s,'n_clauses',None),'vars':self.nv})


class H14(_Log,Inc14):
    """Inc14 with the solver from the pool's factory; queries logged."""
    def __init__(self,n,k,m,pool,solver=SOLVER4):
        self.pool=pool
        self._owner=None;self._skip=False;self._dl=None;self.calls=0;self.n=n;self.k=k;self.m=m
        self.nv=0;self.x=[];self.T=-1;self.acts=[];self.masks=[];self.s=pool.factory(solver);self.guards=0;self.cl=[];v=self._v
        self.d=[[[v() for _ in range(n)] for _ in range(k)] for _ in range(n)];self.e=[[v() for _ in range(m)] for _ in range(n)]
        for q in range(n):
            for a in range(k):self._one(self.d[q][a])
            self._one(self.e[q])
        self._flush()

    def query(self,o,deadline,assume):
        t=perf_counter();self._owner=o;self._dl=deadline;r=self._solve(assume);self._log('least' if not assume else 'rival',t,r);return r


class H14Apart(H14):
    """E1: Inc14 plus the apartness pair clauses of every apart pair (first-visit clauses kept, no colours)."""
    def __init__(self,*a,**kw):self.pairs=set();H14.__init__(self,*a,**kw)

    def sync(self,masks,acts):
        Inc14.sync(self,masks,acts);n=self.n
        for (t,u) in sorted(self.pool.future_pairs-self.pairs):
            for q in range(n):self.cl.append([-self.x[t][q],-self.x[u][q]])
        self.pairs|=self.pool.future_pairs;self._flush();return self


class H15(_Log,Inc15):
    """Inc15 with the solver from the pool's factory; queries (and cube sub-calls) logged."""
    def __init__(self,n,k,m,pool,solver=SOLVER4,cube=False):
        self._owner=None;self._skip=False;self._dl=None;self.calls=0;self.n=n;self.k=k;self.m=m;self.pool=pool;self.cube=cube
        self.nv=0;self.x=[];self.T=-1;self.acts=[];self.masks=[];self.s=pool.factory(solver);self.guards=0;self.cl=[];v=self._v
        self.pairs=set();self.cubes=0;self.cube_sat=0;self.cube_unsat=0
        self.d=[[[v() for _ in range(n)] for _ in range(k)] for _ in range(n)];self.e=[[v() for _ in range(m)] for _ in range(n)]
        for q in range(n):
            for a in range(k):self._one(self.d[q][a])
            self._one(self.e[q])
        if len(pool.clique)>n:z=v();self.cl.append([z]);self.cl.append([-z])
        self._flush()

    def query(self,o,deadline,assume):
        t=perf_counter();self._owner=o;self._dl=deadline;r=self._solve(assume);self._log('least' if not assume else 'rival',t,r)
        if r is not None or not self.cube:return r
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


class PoolE0(Pool14):
    def __init__(self,k,m,solver=SOLVER4,factory=native):Pool14.__init__(self,k,m,solver);self.factory=factory;self.calls=[]

    def lower(self,masks,acts):return 1

    def get(self,n,masks,acts):
        if n not in self.inc:self.inc[n]=H14(n,self.k,self.m,self,self.solver)
        return self.inc[n].sync(masks,acts)


class PoolE1(Pool15):
    """E1: Pool15's apartness bookkeeping (clique computed, never used as colours) with H14Apart instances."""
    def __init__(self,k,m,solver=SOLVER4,factory=native):Pool15.__init__(self,k,m,solver,False);self.factory=factory;self.calls=[]

    def lower(self,masks,acts):self._update(masks,acts);return 1

    def get(self,n,masks,acts):
        self._update(masks,acts)
        if n not in self.inc:self.inc[n]=H14Apart(n,self.k,self.m,self,self.solver)
        return self.inc[n].sync(masks,acts)


class PoolE15(Pool15):
    """E2 (colours only: future_pairs kept empty), E3 (A15), E4 (A15_cube)."""
    def __init__(self,k,m,solver=SOLVER4,factory=native,cube=False,pairs=True):
        Pool15.__init__(self,k,m,solver,cube);self.factory=factory;self.calls=[];self.use_pairs=pairs

    def _update(self,masks,acts):
        Pool15._update(self,masks,acts)
        if not self.use_pairs:self.future_pairs=set()

    def get(self,n,masks,acts):
        self._update(masks,acts)
        if n not in self.inc:self.inc[n]=H15(n,self.k,self.m,self,self.solver,self.cube)
        return self.inc[n].sync(masks,acts)


def make_pool(variant,k,m,solver=SOLVER4,factory=native):
    if variant=='E0':return PoolE0(k,m,solver,factory)
    if variant=='E1':return PoolE1(k,m,solver,factory)
    if variant=='E2':return PoolE15(k,m,solver,factory,cube=False,pairs=False)
    if variant=='E3':return PoolE15(k,m,solver,factory,cube=False)
    if variant=='E4':return PoolE15(k,m,solver,factory,cube=True)
    raise ValueError(variant)


def _extra(P):
    out={'calls':list(P.calls)}
    if isinstance(P,Pool15):
        out['clique']=len(P.clique)
        if isinstance(P,PoolE15):out['cube']=P.cube_counts()
        out['pairs']=len(P.future_pairs)
    return out


def stop_check_audit(variant,masks,acts,k,m,N,deadline,n_lo=1,query_s=QUERY_S14,solver=SOLVER4,o=None,hook=None,factory=native):
    """stop_check14 on a fresh variant pool (closed on return); n_lo raised to P.lower (|C| for E2-E4, unchanged for E0/E1).
    Returns stop_check14's dict plus 'audit' (per-call log, clique, cube counts)."""
    P=make_pool(variant,k,m,solver,factory);o=o or _Owner10(query_s,hook)
    try:
        r=stop_check14(masks,acts,k,m,N,deadline,max(n_lo,P.lower(masks,acts)),query_s,solver,o,P);r['audit']=_extra(P);return r
    finally:P.close()


def active_audit(variant,masks,acts,k,m,N,observe,deadline,K=K14,query_s=QUERY_S14,solver=SOLVER4,hook=None,factory=native):
    """active15's loop on one variant pool (E0: active14's; n_lo = max(n_min, n_lo) equals active14's n_lo = n_min since
    n_min >= n_lo). Returns active14's keys plus 'clique', 'cube' (E2-E4) and 'audit'."""
    masks=list(masks);acts=list(acts);used=0;rounds=[];P=make_pool(variant,k,m,solver,factory);n_lo=P.lower(masks,acts)
    try:
        while True:
            o=_Owner10(query_s,hook);r=stop_check14(masks,acts,k,m,N,deadline,n_lo,query_s,solver,o,P)
            rec={'T':len(acts),'n_min':r['n_min'],'M1':r['model'],'s1':r['s1'],'future':r['future'],'start':r['start'],
                 'query_walls':list(o.query_walls),'capped':o.capped,'check':r['stop']};rounds.append(rec)
            if r['stop']!='AMB':stop=r['stop'];break
            F=r['future'];M1=r['model'];M2=F['M2'];s1=r['s1'];s2=F['s2']
            w=distinguishing_word(M1[0],M1[1],s1,M2[0],M2[1],s2);rec.update(word=w,M2=M2,s2=s2)
            if w is None:raise AssertionError('active_audit: SAT M2 has no distinguishing word')
            if len(w)>K-used:stop='K_spent';break
            rec['pred1']=run_word(M1[0],M1[1],s1,w);rec['pred2']=run_word(M2[0],M2[1],s2,w);obs=[]
            for a in w:mk=observe(a);acts.append(a);masks.append(mk);obs.append(mk)
            used+=len(w);rec['obs']=obs;n_lo=max(r['n_min'],n_lo)
        ex=_extra(P)
        return {'stop':stop,'masks':masks,'acts':acts,'used':used,'rounds':rounds,'final':r,'guards':P.guards(),'sizes':sorted(P.inc),
                'clique':ex.get('clique'),'cube':ex.get('cube'),'audit':ex}
    finally:P.close()
