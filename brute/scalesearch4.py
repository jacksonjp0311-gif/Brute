"""S4 exact search for Brute v0.26.0 (BRUTE_PLAN_029 as amended by BRUTE_PLAN_029_A1): the S1 lineage plus throughput.
New file; brute/region.py (S1), brute/scalesearch.py (S2) and brute/scalesearch3.py (S3) are untouched and imported only.

S1 (frozen) per step: one fresh RegionK (<= n complete Moore machines consistent with the masks, first-visit symmetry), one
feasibility solve, then one solve per (action, code) with a 100000-conflict budget; a query past 10 s of wall is discarded.
S4 keeps the S1 encoding exactly (it builds the frozen brute.region.RegionK) and changes only how queries are answered:
  1. one solver per step, built lazily, answers every query of the step through assumptions (as S1, but lazily: a step
     whose supports are fully witnessed builds nothing);
  2. witness reuse: every SAT model is a complete <= n machine consistent with the trace; it is kept in a pool, re-simulated
     on each new reading (dropped on the first inconsistency) and, from its current state q, witnesses for every action b
     the code of d[q][b]; if (q, b) is not yet exercised by the trace it also witnesses the code of every visited state,
     and every code if the machine has an unvisited state (redirect / recode an unconstrained part; still <= n states);
  3. several queries in one solve: for action b, with R = codes not yet witnessed, assume OR(nc[b][c] : c in R) under a
     fresh selector; UNSAT proves every code in R impossible at once; SAT witnesses one code (and harvests its model);
     repeat until R is empty or UNSAT; out of budget leaves the rest UNKNOWN (counted possible, never certified);
  4. a hard per-query wall cap (QUERY_S, as S3) by conflict chunks with a wall check before each chunk, plus the S1
     per-solve conflict budget (CONF, 100000) kept.
Soundness: a code is reported impossible only by an UNSAT proof over the frozen S1 CNF; a code is reported possible only
from a concrete consistent <= n machine (or as UNKNOWN). So exact answers equal S1's exact answers.
S4_nowit (ablation): 1 and 3 and 4 only: no pool, no harvesting beyond the one code a SAT answer witnesses.
Host-agnostic: no I/O, network, threads, child processes or global state."""
from __future__ import annotations
from time import perf_counter
from brute.region import RegionK,codes_mask

QUERY_S=10.0
CONF=100000
SOLVER4='g3'
CHUNK0=2000;CHUNK_MIN=200;CHUNK_MAX=20000;CHUNK_TARGET_S=0.25
POOL_MAX=32
__all__=['ScaleRegion4','QUERY_S','CONF','SOLVER4','identify_trace']


class _Region(RegionK):
    """The frozen S1 RegionK, with the initial feasibility solve skipped and a wall-capped chunked solve."""
    def __init__(self,owner,n,k,m,masks,actions,solver,symmetry=True):
        self._owner=owner;self._skip=True;self._dl=None
        RegionK.__init__(self,n,k,m,masks,actions,CONF,solver,symmetry)
        self._sat=True    # placeholder; S4 never reads RegionK.feasible

    def _solve(self,assume):
        if self._skip:self._skip=False;return True
        o=self._owner;self.calls+=1;o.solves+=1;used=0
        while True:
            if perf_counter()>=self._dl:o.unknowns+=1;return None
            ch=min(o.chunk,CONF-used);t=perf_counter();self.s.conf_budget(ch);r=self.s.solve_limited(assumptions=assume)
            dt=perf_counter()-t;o.chunks+=1;used+=ch
            o.chunk=int(max(CHUNK_MIN,min(CHUNK_MAX,ch*CHUNK_TARGET_S/max(dt,1e-3))))
            if r is not None:return r
            if used>=CONF:o.unknowns+=1;return None

    def machine(self):
        mod=set(x for x in self.s.get_model() if x>0);n,K,M=self.n,range(self.k),range(self.m)
        d=[[next(r for r in range(n) if self.d[q][a][r] in mod) for a in K] for q in range(n)]
        e=[next(c for c in M if self.e[q][c] in mod) for q in range(n)]
        return d,e


class _Machine:
    __slots__=('d','e','q','visited','exercised')
    def __init__(self,d,e,acts,masks):
        self.d=d;self.e=e;q=0;self.visited={0};self.exercised=set()
        for a in acts:self.exercised.add((q,a));q=d[q][a];self.visited.add(q)
        self.q=q

    def step(self,a,mask):
        self.exercised.add((self.q,a));self.q=self.d[self.q][a];self.visited.add(self.q);return mask>>self.e[self.q]&1

    def codes(self,b,n,m):
        out={self.e[self.d[self.q][b]]}
        if (self.q,b) not in self.exercised:
            out.update(self.e[r] for r in self.visited)
            if len(self.visited)<n:out.update(range(m))
        return out


class ScaleRegion4:
    def __init__(self,n_max,k,s=2,query_s=QUERY_S,witness=True,solver=SOLVER4,symmetry=True):
        self.symmetry=symmetry;self.n=n_max;self.k=k;self.m=1<<s;self.s_bits=s;self.query_s=query_s;self.witness=witness;self.solver=solver
        self.masks=[];self.acts=[];self.status='uninitialized';self.pool=[];self.region=None;self.memo={};self.wit=None
        self.solves=0;self.unknowns=0;self.chunks=0;self.chunk=CHUNK0;self.builds=0;self.solve_free_steps=0
        self.timing={'build':0.0,'solve':0.0,'pool':0.0};self.queries_by_solve=0;self.queries_by_witness=0

    # ---- evidence -----------------------------------------------------------------------------------------------------
    def initialize(self,obs,deadline=None):
        if self.masks:raise ValueError('already initialized')
        self.masks=[codes_mask(obs,self.s_bits)];self.status='supported';self._new_step()

    def observe(self,action,obs,deadline=None):
        if not self.masks:raise ValueError('not initialized')
        if action not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        mk=codes_mask(obs,self.s_bits);self.masks.append(mk);self.acts.append(action)
        if self.status=='grammar_contradicted':return
        t=perf_counter();self.pool=[M for M in self.pool if M.step(action,mk)];self.timing['pool']+=perf_counter()-t
        self._new_step()

    def _new_step(self):
        if self.region is not None:self.region.close();self.region=None
        self.memo={};self.wit=[set() for _ in range(self.k)]
        if self.witness:
            for M in self.pool:
                for b in range(self.k):self.wit[b]|=M.codes(b,self.n,self.m)

    def _harvest(self,R,b,cset):
        d,e=R.machine();M=_Machine(d,e,self.acts,self.masks)
        if self.witness:
            for bb in range(self.k):self.wit[bb]|=M.codes(bb,self.n,self.m)
            self.pool.append(M)
            if len(self.pool)>POOL_MAX:self.pool.pop(0)
        else:self.wit[b].add(e[d[M.q][b]])

    def _region(self):
        if self.region is None:
            t=perf_counter();self.region=_Region(self,self.n,self.k,self.m,self.masks,self.acts,self.solver,self.symmetry)
            self.builds+=1;self.timing['build']+=perf_counter()-t
        return self.region

    # ---- queries ------------------------------------------------------------------------------------------------------
    def support(self,b,deadline=None):
        """(sorted tuple of possible next codes after action b, UNKNOWN count); None, 0 if no machine is consistent."""
        if b not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        if self.status=='grammar_contradicted':return None,0
        if b in self.memo:return self.memo[b]
        dl=perf_counter()+self.query_s;dl=min(dl,deadline) if deadline is not None else dl
        rest=[c for c in range(self.m) if c not in self.wit[b]];unk=0
        if not rest:self.queries_by_witness+=1
        solved=False
        while rest:
            if perf_counter()>=dl:unk=len(rest);break
            R=self._region();R._dl=dl;g=R._v();R.s.add_clause([-g]+[R.nc[b][c] for c in rest])
            solved=True;t=perf_counter();r=R._solve([g]);self.timing['solve']+=perf_counter()-t;R.s.add_clause([-g])
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
        return identify_trace(self.masks,self.acts,self.k,self.m,self.n,deadline,self.solver)

    def close(self):
        if self.region is not None:self.region.close();self.region=None


class _Plain:
    """Owner stub so identify_trace can reuse _Region's chunked solve."""
    def __init__(self):self.solves=0;self.unknowns=0;self.chunks=0;self.chunk=CHUNK0


def _lower_bound(masks):
    """Greedy clique of trace positions with pairwise disjoint masks (each must be a distinct state)."""
    reps=[]
    for mk in masks:
        if all(mk&r==0 for r in reps):reps.append(mk)
    return max(1,len(reps))


def identify_trace(masks,acts,k,m,n_max,deadline,solver=SOLVER4):
    """Least n <= n_max with a consistent complete machine, and whether it is unique (first-visit naming makes every
    all-visited machine's state names canonical; a minimum machine visits every state). Returns {'n_min', 'unique',
    'unknown', 'model': (transitions, emissions) or None}."""
    o=_Plain();n=_lower_bound(masks)
    while n<=n_max:
        R=_Region(o,n,k,m,masks,acts,solver);R._dl=deadline
        try:
            r=R._solve([])
            if r is None:return {'n_min':None,'unique':False,'unknown':True,'model':None}
            if r is False:n+=1;continue
            d,e=R.machine()
            R.s.add_clause([-R.d[q][a][d[q][a]] for q in range(n) for a in range(k)]+[-R.e[q][e[q]] for q in range(n)])
            u=R._solve([])
            return {'n_min':n,'unique':u is False,'unknown':u is None,'model':(d,e)}
        finally:R.close()
    return {'n_min':None,'unique':False,'unknown':False,'model':None}
