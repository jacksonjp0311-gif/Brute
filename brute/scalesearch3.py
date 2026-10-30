"""Brute v0.25.0 S3 exact search (BRUTE_PLAN_028 arm S3; deviation #128). New file; brute/scalesearch.py (S2) is imported
unchanged and S3 is a subclass with four changes, each aimed at per-step solver cost:
  (1) hard per-query budget: every solve runs in small conflict chunks (CHUNK0 = 2000 conflicts, shrunk adaptively from
      the measured seconds per conflict so one chunk fits in the time left) with a wall check BEFORE each chunk; a query
      whose deadline has passed starts no further chunk, chain or solve (no threads, signals or child processes);
  (2) the suffix-chain witness search (_chain) takes the query deadline and stops when it passes;
  (3) per-step n_lo deepening is off the per-step path: an observe step that needs a new model makes ONE capped
      attempt (DEEPEN_S seconds in total, not per level) at the cheapest proven bound, max(n_lo, greedy clique of
      pairwise-distinguishable trace positions), and otherwise goes straight to the full <= n_max search; the full
      deepening runs only in identify (started from the same cheap bound);
  (4) informational per-phase timing in self.timing (seconds): repair, add_step, feasible, chain, solve_support.
Solvers: an interleaved MiniSat 2.2 + Maple-ChronoBT portfolio ('m22+mcb') by default. Glucose ('g3', 'g4', S2's
default) checks its conflict budget only at restarts and overran a 2000-conflict chunk by up to 115x (18 s) on smoke
seeds, so it cannot give a hard budget; cd195, m22, mcb and mgh kept every chunk under 1 s there. Selection rule (fixed
before the freeze, smoke seeds only): 0 UNKNOWN on the control smoke seeds, then the lowest summed UNKNOWN on scale8 and
scale12 smoke seeds. cd195 alone, m22 alone, m22+cd195 and mcb+cd195 each left an UNKNOWN on a 3-state control; mcb
alone (23) and m22+mcb (22) did not, so m22+mcb (results/diag-028/S2_ABLATION_028.json, S3_PORTFOLIO_028.json;
deviation #128). On the same smoke seeds S2 summed 10, so S3 is not expected to beat S2 (Inferred).
Observe shares one query deadline across chain repair and feasibility, so one observe call is one query.
Soundness is S2's: every SAT answer has a concrete machine checked by simulation; every 'impossible' is an UNSAT proof
of the full <= n_max region; the clique bound is a proven lower bound (pairwise-distinguishable positions occupy
pairwise distinct states in every consistent deterministic machine). Host-agnostic: no I/O, threads or child processes.
"""
from __future__ import annotations
from time import perf_counter
from pysat.solvers import Solver
from brute.scalesearch import _Skeleton,ScaleRegion,simulate,greedy_fold,canonical_bfs,QUERY_S,FRESH

__all__=['SOLVER','QUERY_S','CHUNK0','CHUNK_MIN','DEEPEN_S','ScaleRegion3','clique_lb']
SOLVER='m22+mcb';CHUNK0=2000;CHUNK_MIN=50;DEEPEN_S=1.0;SAFETY=0.5


def clique_lb(pairs,T):
    """Greedy clique size in the conflict graph on positions 0..T with edges `pairs` (a proven lower bound on states)."""
    if not pairs:return 1
    adj={}
    for t,u in pairs:adj.setdefault(t,set()).add(u);adj.setdefault(u,set()).add(t)
    best=1
    for v in sorted(adj,key=lambda x:-len(adj[x]))[:32]:
        C=[v];cand=set(adj[v])
        while cand:
            w=max(cand,key=lambda x:len(adj[x]&cand));C.append(w);cand&=adj[w]
        best=max(best,len(C))
    return best


class _Skeleton3(_Skeleton):
    """S2 skeleton with a hard budget and an interleaved portfolio: `solver` is one pysat name or several joined by '+'
    (default 'm22+mcb'); every solver holds the same clauses, and a query runs one chunk on each solver in turn (no
    threads) with a wall check before every chunk; the first solver to finish answers. Chunk size per solver adapts to
    its measured seconds per conflict so a chunk fits in SAFETY x the time left."""
    def __init__(self,n,k,m,solver=SOLVER):
        names=solver.split('+');super().__init__(n,k,m,names[0])
        self.names=names;self.ss=[self.s]+[Solver(name=x,bootstrap_with=self.base) for x in names[1:]]
        self.spc=[None]*len(names);self.chunks=0;self.wins=[0]*len(names)

    def add(self,clauses,keep=True):
        for c in clauses:
            for x in self.ss:x.add_clause(c)
        if keep:self.base.extend(clauses)
        self.clauses+=len(clauses)

    def restart(self):
        for x in self.ss:x.delete()
        self.ss=[Solver(name=x,bootstrap_with=self.base) for x in self.names];self.s=self.ss[0]

    @staticmethod
    def _conflicts(x):
        try:return x.accum_stats().get('conflicts',0)
        except Exception:return None

    def solve(self,assume,deadline):
        while True:
            for i,x in enumerate(self.ss):
                rem=deadline-perf_counter()
                if rem<=0:return None
                spc=self.spc[i];c=CHUNK0 if spc is None else int(max(CHUNK_MIN,min(CHUNK0,SAFETY*rem/max(spc,1e-7))))
                c0=self._conflicts(x);t=perf_counter();x.conf_budget(c);r=x.solve_limited(assumptions=assume)
                dt=perf_counter()-t;c1=self._conflicts(x);self.chunks+=1
                if c0 is not None and c1 is not None and c1>c0:
                    v=dt/(c1-c0);self.spc[i]=v if spc is None else max(v,0.7*spc+0.3*v)
                if r is not None:self.s=x;self.wins[i]+=1;return r

    def phases(self,d,e):
        keep=self.s
        for x in self.ss:self.s=x;super().phases(d,e)
        self.s=keep

    def close(self):
        for x in getattr(self,'ss',[]):x.delete()
        self.ss=[];self.s=None


class ScaleRegion3(ScaleRegion):
    """S3 region (same interface as ScaleRegion)."""
    def __init__(self,n_max,k=2,s=2,query_s=QUERY_S,solver=SOLVER,hint=True,distinct=True,fresh=FRESH):
        super().__init__(n_max,k,s,query_s,solver.split('+')[0],hint,distinct,fresh)
        self.S.close();self.S=_Skeleton3(n_max,k,self.m,solver)
        self.timing={'repair':0.0,'add_step':0.0,'feasible':0.0,'chain':0.0,'solve_support':0.0}

    def _add_step(self,mask,action=None):
        t=perf_counter()
        try:return super()._add_step(mask,action)
        finally:self.timing['add_step']+=perf_counter()-t

    def cheap_lb(self):
        return clique_lb(self._dist,len(self.masks)-1) if self.distinct else 1

    def _chain(self,b,c,models=8,deadline=None):
        t0=perf_counter()
        try:
            acts=self.actions;T=len(acts)
            for P in self.pool[:models]:
                if deadline is not None and perf_counter()>=deadline:return False
                d0,e0=P['d'],P['e'];r=len(e0);path=[P['start']]
                for a in acts:path.append(d0[path[-1]][a])
                for L in range(0,min(T,self.n-r-1)+1):
                    if deadline is not None and perf_counter()>=deadline:return False
                    base=r+L+1
                    if base>self.n:break
                    d=[list(x) for x in d0]+[list(d0[path[T-L+i]]) for i in range(L+1)];e=list(e0)+[e0[path[T-L+i]] for i in range(L+1)]
                    for i in range(L):d[r+i][acts[T-L+i]]=r+i+1
                    start=P['start']
                    if T-L==0:start=r
                    else:d[path[T-L-1]][acts[T-L-1]]=r
                    fL=r+L;tg=d0[path[T]][b];cands=[q for q in range(base) if e[q]==c]
                    if base<self.n:cands.append(base)
                    for t in cands:
                        dd=[list(x) for x in d];ee=list(e)
                        if t==base:dd.append(list(d0[tg]));ee.append(c)
                        dd[fL][b]=t
                        ok,q,_=simulate(dd,ee,acts,self.masks,start)
                        if ok and q==fL:self._pool_add(dd,ee,start);return True
            return False
        finally:self.timing['chain']+=perf_counter()-t0

    def initialize(self,obs):
        super().initialize(obs)

    def observe(self,action,obs,deadline=None):
        from brute.region import codes_mask
        if not self.masks:raise ValueError('not initialized')
        if action not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        mk=codes_mask(tuple(obs),self.s_bits)
        if self.status=='grammar_contradicted':self.masks.append(mk);self.actions.append(action);return
        dl=self._deadline(deadline)
        if self.pool and not any(mk>>P['e'][P['d'][P['q']][action]]&1 for P in self.pool):
            t=perf_counter()
            for c in range(self.m):
                if mk>>c&1 and self._chain(action,c,deadline=dl):break
            self.timing['repair']+=perf_counter()-t
        if self.fresh:self.S.restart()
        self.masks.append(mk);self.actions.append(action);self._add_step(mk,action);self._memo={}
        keep=[];self._dropped=self.pool[-1] if self.pool else self._dropped
        for P in self.pool:
            q2=P['d'][P['q']][action]
            if mk>>P['e'][q2]&1:P['used'].add((P['q'],action));P['q']=q2;keep.append(P)
        self.pool=keep;self._feasible(dl)

    def _feasible(self,deadline=None):
        if self.pool:self.status='supported';return True
        t0=perf_counter()
        try:
            if self.hint and len(self.masks)>1 and all(bin(mk).count('1')==1 for mk in self.masks):
                f=greedy_fold(self.actions,[mk.bit_length()-1 for mk in self.masks],self.n,self.k)
                if f is not None:self.S.phases(*canonical_bfs(*f))
                elif self._dropped is not None:
                    P=self._dropped;self.S.phases(*canonical_bfs(P['d'],P['e'],P['start']))
            dl=self._deadline(deadline);self.calls+=1
            self.n_lo=max(self.n_lo,min(self.cheap_lb(),self.n))
            dd=min(dl,perf_counter()+DEEPEN_S)
            while self.n_lo<self.n and perf_counter()<dd:   # one capped attempt from the cheap bound (total DEEPEN_S)
                r=self.S.solve([-self.S.u[self.n_lo]],dd);self.solves+=1
                if r is None:break
                if r:self._pool_add(*self.S.model());self.status='supported';return True
                self.n_lo+=1
            r=self.S.solve([],dl);self.solves+=1
            if r is None:self.status='budget_exhausted';self.unknown_total+=1;return None
            if r:self._pool_add(*self.S.model());self.status='supported';return True
            self.n_lo=self.n+1;self.status='grammar_contradicted';return False
        finally:self.timing['feasible']+=perf_counter()-t0

    def support(self,b,deadline=None):
        """(sorted tuple of possible next codes after action b, unknowns); (None, 0|1) if not supported. Hard budget."""
        if b not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        if ('sup',b) in self._memo:return self._memo[('sup',b)]
        if self.status=='budget_exhausted':self._feasible(deadline)
        if self.status!='supported':return None,int(self.status=='budget_exhausted')
        S=self.S;T=len(self.x)-1;dl=self._deadline(deadline);self.calls+=1
        have=self._witness_codes(b);u=0
        todo=[c for c in range(self.m) if c not in have]
        if todo:
            y=[S._v() for _ in range(self.n)];cl=[]
            for q in range(self.n):
                for r in range(self.n):cl.append([-self.x[T][q],-S.d[q][b][r],y[r]])
            S.add(cl,keep=False)
        for c in todo:
            if c in have:continue
            if perf_counter()>=dl:u+=1;have.add(c);continue
            if self._chain(b,c,deadline=dl):have.add(c);have|=self._witness_codes(b);continue
            g=S._v();S.add([[-g,-y[r],S.e[r][c]] for r in range(self.n)],keep=False)
            t=perf_counter();res=S.solve([g],dl);self.timing['solve_support']+=perf_counter()-t;self.solves+=1
            if res is True:
                d,e=S.model();self._pool_add(d,e);have|=self._witness_codes(b);have.add(c)
            elif res is None:u+=1;have.add(c)
            S.add([[-g]],keep=False)
        self.unknown_total+=u;out=(tuple(sorted(have)),u);self._memo[('sup',b)]=out
        return out

    def identify(self,deadline=None):
        if self.status=='supported':self.n_lo=max(self.n_lo,min(self.cheap_lb(),self.n))
        return super().identify(deadline)
