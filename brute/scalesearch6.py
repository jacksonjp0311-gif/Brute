"""S6 exact search for Brute v0.28.0 (BRUTE_PLAN_031; deviation #134 fixes the readings below). New file;
brute/region.py (S1), brute/scalesearch4.py (S4) and brute/scalesearch5.py (S5) are untouched and imported only.

S6 = S5 (no symmetry-breaking clauses, hard per-query cap, witness pool, several queries in one solve) plus:
  1. one incremental solver for the whole trace instead of one fresh RegionK per step: the base variables x[t][q],
     d[q][a][r], e[q][c] and the S1 base clauses (exactly-one rows, start state, transitions, emission masks) are added
     step by step and never removed, so clauses learned on earlier steps carry to later steps and no step rebuilds its
     CNF; the S1 "next code" clauses (nx, nc for the current last reading) are guarded by a fresh activation literal per
     step, solved under that literal as an assumption and switched off for good (unit -act) when the next reading
     arrives. The S1 auxiliary definitions A, V and Tr are not encoded: each is a definitional extension (every
     assignment of x, d, e extends to exactly one assignment of them) and support queries never read them, so the
     projected solution set over x, d, e, and hence every exact answer, equals S5's;
  2. query ordering (order()): the actions of a step are answered in ascending order of the number of next codes not
     yet witnessed by the pool (ties by action index), so cheap queries spend the arm budget first.
S6_noorder (ablation): 1 only (actions in index order, as S5).
Identify probe (identify6): as the frozen brute.scalesearch4.identify_trace (least n from the greedy clique bound,
first-visit symmetry so a minimum machine has canonical state names, then a second-machine solve with the first model
blocked) but bounded by the deadline only, not by the S1 per-solve conflict budget; labels are assigned by the runner.
Soundness: a code is reported impossible only by an UNSAT proof over the S1 base clauses; a code is reported possible
only from a concrete consistent <= n machine (or as UNKNOWN).
Host-agnostic: no I/O, network, threads, child processes or global state."""
from __future__ import annotations
from itertools import combinations
from time import perf_counter
from pysat.solvers import Solver
from brute.scalesearch4 import _Region as _Region4,_lower_bound,CHUNK0,CHUNK_MIN,CHUNK_MAX,CHUNK_TARGET_S
from brute.scalesearch5 import ScaleRegion5,_Region5,QUERY_S,CONF,SOLVER4

__all__=['ScaleRegion6','QUERY_S','CONF','SOLVER4','identify6']


class _Inc:
    """Incremental S1 base encoding (symmetry off) over masks[0..T], with guarded next-code variables for the last T."""
    _solve=_Region5._solve
    machine=_Region4.machine

    def __init__(self,owner,n,k,m,solver):
        self._owner=owner;self._skip=False;self._dl=None;self.calls=0;self.clauses=0;self.n=n;self.k=k;self.m=m;self.nv=0
        self.s=Solver(name=solver);K=range(k);M=range(m);v=self._v
        self.d=[[[v() for _ in range(n)] for _ in K] for _ in range(n)];self.e=[[v() for _ in M] for _ in range(n)]
        for q in range(n):
            for a in K:self._one(self.d[q][a])
            self._one(self.e[q])
        self.x=[];self.act=None;self.nc=None;self.T=-1

    def _v(self):
        self.nv+=1;return self.nv

    def _add(self,c):self.s.add_clause(c);self.clauses+=1

    def _one(self,lits):
        self._add(list(lits))
        for a,b in combinations(lits,2):self._add([-a,-b])

    def extend(self,masks,acts):
        """Add readings T+1..len(masks)-1 and re-guard the next-code clauses on the new last reading."""
        if len(masks)!=len(acts)+1:raise ValueError('need one more mask than actions')
        if len(masks)-1==self.T:return False
        n,k,m=self.n,self.k,self.m
        for t in range(self.T+1,len(masks)):
            row=[self._v() for _ in range(n)];self.x.append(row);self._one(row)
            if t==0:self._add([row[0]])
            else:
                a=acts[t-1];prev=self.x[t-1]
                for q in range(n):
                    for r in range(n):self._add([-prev[q],-self.d[q][a][r],row[r]])
            mk=masks[t]
            for q in range(n):self._add([-row[q]]+[self.e[q][c] for c in range(m) if mk>>c&1])
        self.T=len(masks)-1
        if self.act is not None:self._add([-self.act])
        g=self.act=self._v();xT=self.x[self.T]
        nx=[[self._v() for _ in range(n)] for _ in range(k)];self.nc=nc=[[self._v() for _ in range(m)] for _ in range(k)]
        for b in range(k):
            for q in range(n):
                for r in range(n):self._add([-g,-xT[q],-self.d[q][b][r],nx[b][r]])
            for a_,b_ in combinations(nx[b],2):self._add([-g,-a_,-b_])
            for r in range(n):
                for c in range(m):self._add([-g,-nx[b][r],-self.e[r][c],nc[b][c]])
            for a_,b_ in combinations(nc[b],2):self._add([-g,-a_,-b_])
        return True

    def close(self):
        if self.s is not None:self.s.delete();self.s=None


class ScaleRegion6(ScaleRegion5):
    def __init__(self,n_max,k,s=2,query_s=QUERY_S,witness=True,solver=SOLVER4,ordered=True):
        ScaleRegion5.__init__(self,n_max,k,s,query_s,witness,solver,hard_cap=True)
        self.ordered=ordered;self.extends=0

    def _new_step(self):
        self.memo={};self.wit=[set() for _ in range(self.k)]
        if self.witness:
            for M in self.pool:
                for b in range(self.k):self.wit[b]|=M.codes(b,self.n,self.m)

    def _region(self,dl=None):
        t=perf_counter()
        if self.region is None:self.region=_Inc(self,self.n,self.k,self.m,self.solver);self.builds+=1
        if self.region.extend(self.masks,self.acts):self.extends+=1
        self.timing['build']+=perf_counter()-t
        return self.region

    def order(self):
        """Actions of the current step, cheapest first (fewest next codes not yet witnessed); index order if not ordered."""
        if not self.ordered or self.wit is None:return list(range(self.k))
        return sorted(range(self.k),key=lambda b:(0 if b in self.memo else sum(1 for c in range(self.m) if c not in self.wit[b]),b))

    def support(self,b,deadline=None):
        """As ScaleRegion5.support, over the incremental solver (assumptions: query selector and the step literal)."""
        if b not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        if self.status=='grammar_contradicted':return None,0
        if b in self.memo:return self.memo[b]
        dl=perf_counter()+self.query_s;dl=min(dl,deadline) if deadline is not None else dl
        rest=[c for c in range(self.m) if c not in self.wit[b]];unk=0
        if not rest:self.queries_by_witness+=1
        solved=False
        while rest:
            if perf_counter()>=dl:unk=len(rest);break
            R=self._region(dl)
            R._dl=dl;g=R._v();R.s.add_clause([-g]+[R.nc[b][c] for c in rest])
            solved=True;t=perf_counter();r=R._solve([g,R.act]);self.timing['solve']+=perf_counter()-t;R.s.add_clause([-g])
            if r is None:unk=len(rest);break
            if r is False:
                if len(rest)==self.m:
                    self.status='grammar_contradicted';self.memo={x:(None,0) for x in range(self.k)};return None,0
                break
            self._harvest(R,b,rest);rest=[c for c in rest if c not in self.wit[b]]
        if unk==0 and solved:self.queries_by_solve+=1
        res=(tuple(c for c in range(self.m) if c in self.wit[b] or (unk and c in rest)),unk)
        if unk==0:self.memo[b]=res
        return res

    def identify(self,deadline):
        return identify6(self.masks,self.acts,self.k,self.m,self.n,deadline,self.solver)


class _IdOwner:
    def __init__(self):self.solves=0;self.unknowns=0;self.chunks=0;self.chunk=CHUNK0


class _RegionID(_Region4):
    """The frozen S1 RegionK with first-visit symmetry; chunked solve bounded by the deadline only."""
    def _solve(self,assume):
        if self._skip:self._skip=False;return True
        o=self._owner;self.calls+=1;o.solves+=1
        while True:
            if perf_counter()>=self._dl:o.unknowns+=1;return None
            ch=o.chunk;t=perf_counter();self.s.conf_budget(ch);r=self.s.solve_limited(assumptions=assume)
            dt=perf_counter()-t;o.chunks+=1
            o.chunk=int(max(CHUNK_MIN,min(CHUNK_MAX,ch*CHUNK_TARGET_S/max(dt,1e-3))))
            if r is not None:return r


def identify6(masks,acts,k,m,n_max,deadline,solver=SOLVER4):
    """Least n <= n_max with a consistent complete machine and whether a second (non-isomorphic) one exists at that n.
    Returns {'n_min', 'unique', 'unknown', 'model', 'second_found'}; unknown True iff the deadline stopped it."""
    o=_IdOwner();n=_lower_bound(masks)
    while n<=n_max:
        if perf_counter()>=deadline:return {'n_min':None,'unique':False,'unknown':True,'model':None,'second_found':False}
        R=_RegionID(o,n,k,m,masks,acts,solver);R._dl=deadline
        try:
            r=R._solve([])
            if r is None:return {'n_min':None,'unique':False,'unknown':True,'model':None,'second_found':False}
            if r is False:n+=1;continue
            d,e=R.machine()
            R.s.add_clause([-R.d[q][a][d[q][a]] for q in range(n) for a in range(k)]+[-R.e[q][e[q]] for q in range(n)])
            u=R._solve([])
            return {'n_min':n,'unique':u is False,'unknown':u is None,'model':(d,e),'second_found':u is True}
        finally:R.close()
    return {'n_min':None,'unique':False,'unknown':False,'model':None,'second_found':False}
