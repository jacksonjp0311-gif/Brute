"""S7 noise-tolerant exact search for Brute v0.29.0 (BRUTE_PLAN_032). New file; brute/region.py (S1), brute/scalesearch4.py
(S4) and brute/scalesearch5.py (S5) are untouched and imported only.

S7 = S5 (symmetry-free, hard per-query cap, witness pool, multi-code queries) with a noise-tolerant encoding:
  * the frozen S1 transition encoding (one-hot state per position, one-hot transitions and emissions, start state 0, no
    symmetry clauses), but the hard emission-matches-reading clause is replaced by one flip literal f[t][j] per sensor
    reading (bit j of reading t): x[t][q] and e[q][c] imply f[t][j] whenever bit j of code c differs from the reading;
  * a sequential-counter cardinality constraint: at most B flipped sensor readings over the trace so far, with
    B(t) = ceil(eps * t + 2 * sqrt(eps * t)), eps = EPS_ASSUMED = 0.05, t = number of sensor readings observed so far
    (S bits per reading); B is applied on every trace, including clean ones.
A code is reported impossible only by an UNSAT proof over that CNF; a code is reported possible only from a concrete <= n
machine whose total flips (mismatched sensor readings over the trace) are <= B, or as UNKNOWN. So S7 is sound against the
true machine whenever the realised flips are <= B (the true machine is then one of the machines in the CNF).
Witness pool: as S4, with each pooled machine carrying its flip count; it is dropped once the count exceeds B.
ScaleRegion5C (S7_contra, descriptive ablation): S5 plus, once per step before the first query, the S1-style whole-trace
grammar check (frozen RegionK with first-visit symmetry, chunked under the same per-query cap; skipped when a pooled
machine already matches every reading); UNSAT sets grammar_contradicted as S1 does; its solves count in the arm's counters.
Host-agnostic: no I/O, network, threads, child processes or global state."""
from __future__ import annotations
from math import ceil,sqrt
from time import perf_counter
from pysat.card import CardEnc,EncType
from pysat.solvers import Solver
from brute.region import RegionK,codes_mask
from brute.scalesearch4 import _Machine,POOL_MAX
from brute.scalesearch5 import ScaleRegion5,_Region5,QUERY_S,SOLVER4,MARGIN_S,BUILD_SAFETY

EPS_ASSUMED=0.05
__all__=['ScaleRegion7','ScaleRegion5C','flip_budget','machine_flips','EPS_ASSUMED','QUERY_S','SOLVER4']


def flip_budget(t,eps=EPS_ASSUMED):
    """B(t) = ceil(eps*t + 2*sqrt(eps*t)) for t sensor readings (0 when t = 0)."""
    if t<=0:return 0
    x=eps*t;return int(ceil(x+2.0*sqrt(x)-1e-12))


def _bit(c,j,s):return (c>>(s-1-j))&1


def _cost(c,obs,s):
    return sum(1 for j,b in enumerate(obs) if b is not None and _bit(c,j,s)!=b)


def machine_flips(d,e,acts,readings,s):
    """Total flipped sensor readings needed for machine (d, e) started in state 0 to emit the readings."""
    q=0;f=_cost(e[0],readings[0],s)
    for a,o in zip(acts,readings[1:]):q=d[q][a];f+=_cost(e[q],o,s)
    return f


class _NMachine(_Machine):
    __slots__=('flips','s')
    def __init__(self,d,e,acts,readings,s):
        _Machine.__init__(self,d,e,acts,None);self.s=s;self.flips=machine_flips(d,e,acts,readings,s)

    def nstep(self,a,obs,bound):
        self.exercised.add((self.q,a));self.q=self.d[self.q][a];self.visited.add(self.q)
        self.flips+=_cost(self.e[self.q],obs,self.s);return self.flips<=bound


class _Region7(_Region5):
    """The S1 transition encoding (symmetry off) with flip literals and a sequential-counter flip budget."""
    def __init__(self,owner,n,k,m,s,readings,actions,bound,solver):
        self._owner=owner;self._skip=False;self._dl=None;self.calls=0;self.unknown=0
        self.n=n;self.k=k;self.m=m;self.T=T=len(actions);self.nv=0;self.cl=[];v=self._v;K=range(k);M=range(m)
        self.x=[[v() for _ in range(n)] for _ in range(T+1)]
        self.d=[[[v() for _ in range(n)] for _ in K] for _ in range(n)]
        self.e=[[v() for _ in M] for _ in range(n)]
        for row in self.x:self._one(row)
        for q in range(n):
            for a in K:self._one(self.d[q][a])
            self._one(self.e[q])
        self.cl.append([self.x[0][0]])
        for t in range(1,T+1):
            a=actions[t-1]
            for q in range(n):
                for r in range(n):self.cl.append([-self.x[t-1][q],-self.d[q][a][r],self.x[t][r]])
        self.f=[]
        for t,o in enumerate(readings):
            for j,b in enumerate(o):
                if b is None:continue
                fv=v();self.f.append(fv)
                bad=[c for c in M if _bit(c,j,s)!=b]
                for q in range(n):
                    for c in bad:self.cl.append([-self.x[t][q],-self.e[q][c],fv])
        self.bound=bound
        if bound<len(self.f):
            enc=CardEnc.atmost(lits=self.f,bound=bound,top_id=self.nv,encoding=EncType.seqcounter)
            self.cl.extend(enc.clauses);self.nv=max(self.nv,enc.nv)
        self.nx=[[v() for _ in range(n)] for _ in K];self.nc=[[v() for _ in M] for _ in K]
        for b in K:
            for q in range(n):
                for r in range(n):self.cl.append([-self.x[T][q],-self.d[q][b][r],self.nx[b][r]])
            self._amo(self.nx[b])
            for r in range(n):
                for c in M:self.cl.append([-self.nx[b][r],-self.e[r][c],self.nc[b][c]])
            self._amo(self.nc[b])
        self.base_vars=self.nv;self.base_clauses=len(self.cl)
        self.s=Solver(name=solver,bootstrap_with=self.cl);self.cl=None

    _v=RegionK._v;_amo=RegionK._amo;_one=RegionK._one;close=RegionK.close


class ScaleRegion7(ScaleRegion5):
    def __init__(self,n_max,k,s=2,query_s=QUERY_S,witness=True,solver=SOLVER4,hard_cap=True,eps_assumed=EPS_ASSUMED):
        ScaleRegion5.__init__(self,n_max,k,s,query_s,witness,solver,hard_cap)
        self.eps_assumed=eps_assumed;self.readings=[];self.sensor_readings=0;self.bound=0

    def _count(self,obs):
        self.readings.append(tuple(obs));self.sensor_readings+=sum(1 for b in obs if b is not None)
        self.bound=flip_budget(self.sensor_readings,self.eps_assumed)

    def initialize(self,obs,deadline=None):
        if self.masks:raise ValueError('already initialized')
        mk=codes_mask(obs,self.s_bits);self._count(obs);self.masks=[mk];self.status='supported';self._new_step()

    def observe(self,action,obs,deadline=None):
        if not self.masks:raise ValueError('not initialized')
        if action not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        mk=codes_mask(obs,self.s_bits);self.masks.append(mk);self.acts.append(action);self._count(obs)
        if self.status=='grammar_contradicted':return
        t=perf_counter();B=self.bound;self.pool=[P for P in self.pool if P.nstep(action,obs,B)];self.timing['pool']+=perf_counter()-t
        self._new_step()

    def _harvest(self,R,b,cset):
        d,e=R.machine();P=_NMachine(d,e,self.acts,self.readings,self.s_bits)
        if P.flips>self.bound:raise AssertionError('S7 model exceeds the flip budget')
        if self.witness:
            for bb in range(self.k):self.wit[bb]|=P.codes(bb,self.n,self.m)
            self.pool.append(P)
            if len(self.pool)>POOL_MAX:self.pool.pop(0)
        else:self.wit[b].add(e[d[P.q][b]])

    def _region(self,dl=None):
        if self.region is None:
            size=(len(self.acts)+1)*self.n*self.n
            if self.hard_cap and dl is not None and self._build_rate is not None:
                if BUILD_SAFETY*self._build_rate*size>dl-perf_counter()-MARGIN_S:self.build_skips+=1;return None
            t=perf_counter()
            self.region=_Region7(self,self.n,self.k,self.m,self.s_bits,self.readings,self.acts,self.bound,self.solver)
            dt=perf_counter()-t;self.builds+=1;self.timing['build']+=dt;self._build_rate=dt/size
        return self.region

    def identify(self,deadline):raise NotImplementedError('S7 has no identify routine (no identify gate in study 032)')


class ScaleRegion5C(ScaleRegion5):
    """S7_contra: S5 plus a per-step symmetry-on whole-trace grammar check (descriptive ablation)."""
    def __init__(self,*a,**kw):
        ScaleRegion5.__init__(self,*a,**kw);self._checked=False;self.contra_checks=0;self.contra_unknown=0

    def _new_step(self):
        ScaleRegion5._new_step(self);self._checked=False

    def _contra(self,dl):
        self._checked=True;self.contra_checks+=1
        R=_Region5(self,self.n,self.k,self.m,self.masks,self.acts,self.solver,True)
        try:
            R._dl=dl;r=R._solve([])
        finally:R.close()
        if r is None:self.contra_unknown+=1
        if r is False:self.status='grammar_contradicted';self.memo={x:(None,0) for x in range(self.k)}

    def support(self,b,deadline=None):
        if b not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        if self.status!='grammar_contradicted' and not self._checked:
            if self.pool:self._checked=True      # a pooled machine matches every reading: the trace is not contradicted
            else:
                dl=perf_counter()+self.query_s;dl=min(dl,deadline) if deadline is not None else dl;t=perf_counter()
                self._contra(dl);self.timing['solve']+=perf_counter()-t
                if self.status=='grammar_contradicted':return None,0
                return ScaleRegion5.support(self,b,dl)
        return ScaleRegion5.support(self,b,deadline)
