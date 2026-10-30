"""Brute v0.23.0 S2 exact search (BRUTE_PLAN_026 arm S2; deviation #123). New file; brute/region.py is imported unchanged.

ScaleRegion(n_max, k, s) is the exact region of complete deterministic Moore machines with at most n_max states, k actions
and m = 2**s codes, consistent with a hard-masked trace (the RegionK semantics), answered with four changes:
  (i)   incremental SAT: one solver for the whole trace; each observation only ADDS clauses; queries use assumptions
        (one fresh selector per (step, action, code), retired by a unit clause after use);
  (ii)  BFS-canonical symmetry breaking (Ulyantsev et al. 2015): used states 0..r-1 are numbered in breadth-first order
        from the start state 0 over actions 0..k-1; unused states are fixed (all transitions to 0, code 0) and never
        entered; every reachable machine with r <= n_max states has exactly one model;
  (iii) iterative state-count deepening for feasibility: assumption (not u[n]) restricts to <= n states, DEEPEN_S
        seconds per level from n_lo upward, then the full <= n_max search; n_lo (a proven lower bound on the least state
        count) is monotone in the trace length; support queries always solve the full <= n_max region;
  (iv)  a passive greedy state-merging fold (RPNI-style) of the trace, or the last refuted pool model, used ONLY as solver
        phases, never as an answer;
  (v)   implied distinguishability clauses: trace positions whose observed futures along a common action word conflict
        cannot share a state (sound for every deterministic machine).
Exact witnesses: every model found is kept (pool, at most POOL_MAX) and simulated forward; a surviving model answers
"code c possible" without a solve, and so does any machine obtained from it by redirecting a transition that the trace
never exercised (to an existing state, or to a fresh state when it has fewer than n_max states), and so does a
"suffix chain" machine (_chain). Every SAT answer
therefore has a concrete machine behind it; every "impossible" answer is an UNSAT proof of the full <= n_max region.
Answers equal RegionK(n_max) supports (projection on the next code) wherever both finish (GSC a).

Budget: each query (feasibility, or one support(b)) gets query_s seconds of wall time, spent in conflict-budget chunks
of CHUNK conflicts (no threads, no signals; granularity one chunk). A query out of time is UNKNOWN; UNKNOWN codes count
as possible (conservative, as brute.region). An UNKNOWN feasibility is not sticky: the next step tries again.
ScaleTolerant is the same skeleton with fully open masks, one flip variable per observed bit and sum(flips) <= m
(the brute.noisyregion RGN_n(m) semantics), rebuilt per step; it backs RGB6_on_S2.
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from itertools import combinations
from time import perf_counter
from pysat.solvers import Solver
from pysat.card import CardEnc,EncType
from brute.region import codes_mask

__all__=['SOLVER','QUERY_S','CHUNK','POOL_MAX','DEEPEN_S','ScaleRegion','ScaleTolerant','greedy_fold','canonical_bfs','simulate']
SOLVER='g4';QUERY_S=10.0;CHUNK=20000;POOL_MAX=64;DEEPEN_S=1.0;FRESH=False


def canonical_bfs(d,e,start=0):
    """BFS renumbering of the part reachable from `start`: (d', e') as tuples (evaluator and test helper)."""
    k=len(d[0]);order=[start];idx={start:0};i=0
    while i<len(order):
        q=order[i];i+=1
        for a in range(k):
            r=d[q][a]
            if r not in idx:idx[r]=len(order);order.append(r)
    return (tuple(tuple(idx[d[q][a]] for a in range(k)) for q in order),tuple(e[q] for q in order))


def simulate(d,e,actions,masks,start=0):
    """(consistent, final state, exercised transition set) of machine (d, e) on a hard-masked trace."""
    q=start;used=set()
    if not masks[0]>>e[q]&1:return False,None,used
    for a,mk in zip(actions,masks[1:]):
        used.add((q,a));q=d[q][a]
        if not mk>>e[q]&1:return False,None,used
    return True,q,used


def greedy_fold(actions,codes,n_max,k=None):
    """Passive greedy merge of the trace path (positions 0..T, single code per position): each position joins the
    earliest earlier block with its code if the deterministic fold stays consistent, else opens a block. (d, e) or None
    if more than n_max blocks are needed. Phase hint only."""
    T=len(actions);blk=[None]*(T+1);trans={};code={}
    def try_assign(i,b,blk,trans,code):
        blk=list(blk);trans=dict(trans);code=dict(code);stack=[(i,b)]
        while stack:
            j,b=stack.pop()
            if blk[j] is not None:
                if blk[j]!=b:return None
                continue
            if code.get(b,codes[j])!=codes[j]:return None
            blk[j]=b;code[b]=codes[j]
            if j<T:
                a=actions[j];t=trans.get((b,a))
                if t is None and blk[j+1] is not None:trans[(b,a)]=blk[j+1]
                elif t is not None:stack.append((j+1,t))
            if j>0 and blk[j-1] is not None:
                a=actions[j-1];t=trans.get((blk[j-1],a))
                if t is None:trans[(blk[j-1],a)]=b
                elif t!=b:return None
        return blk,trans,code
    nb=0
    for i in range(T+1):
        if blk[i] is not None:continue
        done=False
        for b in range(nb):
            if code[b]!=codes[i]:continue
            r=try_assign(i,b,blk,trans,code)
            if r is not None:blk,trans,code=r;done=True;break
        if not done:
            if nb>=n_max:return None
            r=try_assign(i,nb,blk,trans,code)
            if r is None:return None
            blk,trans,code=r;nb+=1
    k=k or (1+max(actions) if actions else 1)
    d=[[trans.get((q,a),0) for a in range(k)] for q in range(nb)];e=[code[q] for q in range(nb)]
    ok=simulate(d,e,actions,[1<<c for c in codes])[0]
    return (d,e) if ok else None


class _Skeleton:
    """BFS-canonical <= n machine skeleton on a pysat solver (variables d, e, u, plus BFS auxiliaries)."""
    def __init__(self,n,k,m,solver=SOLVER):
        self.n=n;self.k=k;self.m=m;self.nv=0;cl=[];v=self._v;N=range(n);K=range(k);M=range(m)
        self.d=[[[v() for _ in N] for _ in K] for _ in N];self.e=[[v() for _ in M] for _ in N];self.u=[v() for _ in N]
        for q in N:
            for a in K:cl+=self._one(self.d[q][a])
            cl+=self._one(self.e[q])
        cl.append([self.u[0]])
        for q in range(1,n):
            cl.append([-self.u[q],self.u[q-1]])
            for a in K:cl.append([self.u[q],self.d[q][a][0]])
            cl.append([self.u[q],self.e[q][0]])
            for i in N:
                for a in K:cl.append([-self.d[i][a][q],self.u[q]])
        t={};p={}
        for j in range(1,n):
            for i in range(j):
                t[i,j]=v();ors=[self.d[i][a][j] for a in K]
                cl.append([-t[i,j]]+ors);cl+=[[-x,t[i,j]] for x in ors]
            for i in range(j):
                p[j,i]=v();prev=[t[kk,j] for kk in range(i)]
                cl.append([-p[j,i],t[i,j]]);cl+=[[-p[j,i],-x] for x in prev];cl.append([p[j,i],-t[i,j]]+prev)
            cl.append([-self.u[j]]+[p[j,i] for i in range(j)])
        for j in range(1,n-1):
            for i in range(j):
                for kk in range(i):cl.append([-p[j,i],-p[j+1,kk]])
        mm={}
        for i in N:
            for j in range(1,n):
                for a in K:
                    mm[i,a,j]=x=v();prev=[self.d[i][b][j] for b in range(a)]
                    cl.append([-x,self.d[i][a][j]]);cl+=[[-x,-y] for y in prev];cl.append([x,-self.d[i][a][j]]+prev)
        for j in range(1,n-1):
            for i in range(j):
                for a in K:
                    for b in range(a+1,k):cl.append([-p[j,i],-p[j+1,i],-mm[i,a,j+1],-mm[i,b,j]])
        self.solver_name=solver;self.base=cl;self.s=Solver(name=solver,bootstrap_with=cl);self.clauses=len(cl)

    def _v(self):
        self.nv+=1;return self.nv

    def _one(self,lits):
        return [list(lits)]+[[-a,-b] for a,b in combinations(lits,2)]

    def add(self,clauses,keep=True):
        """Add clauses; keep=False marks query-local clauses (selectors) that a restart drops."""
        for c in clauses:self.s.add_clause(c)
        if keep:self.base.extend(clauses)
        self.clauses+=len(clauses)

    def restart(self):
        """Fresh solver on the kept clauses (no learned clauses, no retired selectors)."""
        self.s.delete();self.s=Solver(name=self.solver_name,bootstrap_with=self.base)

    def solve(self,assume,deadline):
        """True / False / None (out of time), in CHUNK-conflict slices until `deadline` (perf_counter seconds)."""
        while True:
            self.s.conf_budget(CHUNK);r=self.s.solve_limited(assumptions=assume)
            if r is not None:return r
            if perf_counter()>=deadline:return None

    def model(self):
        pos={l for l in self.s.get_model() if l>0};n,k,m=self.n,self.k,self.m
        r=sum(self.u[q] in pos for q in range(n))
        d=[[next(x for x in range(n) if self.d[q][a][x] in pos) for a in range(k)] for q in range(r)]
        e=[next(c for c in range(m) if self.e[q][c] in pos) for q in range(r)]
        return d,e

    def phases(self,d,e):
        lits=[]
        for q in range(self.n):
            used=q<len(d);lits.append(self.u[q] if used else -self.u[q])
            for a in range(self.k):
                for r in range(self.n):lits.append(self.d[q][a][r] if (used and d[q][a]==r) else -self.d[q][a][r])
            for c in range(self.m):lits.append(self.e[q][c] if (used and e[q]==c) else -self.e[q][c])
        try:self.s.set_phases(lits)
        except NotImplementedError:pass

    def close(self):
        if self.s is not None:self.s.delete();self.s=None


class ScaleRegion:
    """S2 region (RegionSpace-shaped: status, initialize, observe, support(b) -> (tuple | None, unknowns), close)."""
    def __init__(self,n_max,k=2,s=2,query_s=QUERY_S,solver=SOLVER,hint=True,distinct=True,fresh=FRESH):
        if not (isinstance(n_max,int) and n_max>=1):raise ValueError('n_max must be a positive int')
        if not (isinstance(k,int) and k>=1):raise ValueError('k must be a positive int')
        self.n=n_max;self.k=k;self.s_bits=s;self.m=1<<s;self.query_s=query_s;self.hint=hint;self.distinct=distinct;self._dist=set();self._dropped=None;self.fresh=fresh
        self.S=_Skeleton(n_max,k,self.m,solver);self.x=[];self.masks=[];self.actions=[];self.pool=[];self.n_lo=1
        self.status='uninitialized';self._memo={};self.calls=0;self.unknown_total=0;self.solves=0;self._hinted=False

    # ---- trace ------------------------------------------------------------------------------------------------------
    def _add_step(self,mask,action=None):
        S=self.S;xt=[S._v() for _ in range(self.n)];cl=[]
        if action is None:cl.append([xt[0]])
        else:
            xp=self.x[-1]
            for q in range(self.n):
                for r in range(self.n):cl.append([-xp[q],-S.d[q][action][r],xt[r]])
        full=(1<<self.m)-1
        if mask!=full:
            for q in range(self.n):cl.append([-xt[q]]+[S.e[q][c] for c in range(self.m) if mask>>c&1])
        S.add(cl);self.x.append(xt)
        if self.distinct:self._distinguish()

    def _distinguish(self):
        """Implied clauses (sound for every deterministic machine): positions t < t' of the trace whose observed futures
        along a common action word conflict cannot share a state. Path rule: (t, t') conflict if their masks are disjoint,
        or a_t == a_t' and (t+1, t'+1) conflict. Only pairs that become conflicting at this step are added."""
        T=len(self.masks)-1;new=[]
        for t in range(T):
            if not self.masks[t]&self.masks[T]:new.append((t,T))
        out=[];seen=self._dist
        while new:
            t,u=new.pop()
            if (t,u) in seen:continue
            seen.add((t,u));out.append((t,u))
            if t>0 and self.actions[t-1]==self.actions[u-1]:new.append((t-1,u-1))
        cl=[]
        for t,u in out:
            for q in range(self.n):cl.append([-self.x[t][q],-self.x[u][q]])
        self.S.add(cl)

    def _pool_add(self,d,e,start=0):
        ok,q,used=simulate(d,e,self.actions,self.masks,start)
        if ok:
            if len(self.pool)>=POOL_MAX:self.pool.pop(0)   # oldest out: the newest witness always enters
            self.pool.append({'d':d,'e':e,'q':q,'used':used,'start':start})
        return ok

    def _chain(self,b,c,models=8):
        """Constructive exact witness for 'code c after action b now': for a pool machine M with path q_0..q_T, copy the
        last L+1 path states into fresh states f_0..f_L (same codes and transitions, except f_i --a_{T-L+i}--> f_{i+1}),
        enter the copy through the edge used at step T-L-1 (or start in it if L = T), and send f_L --b--> a state with code
        c (an existing one, or one more fresh copy of M's b-successor of q_T recoded to c). Accepted only if the whole
        machine (at most n_max states) is consistent with the trace by direct simulation; then it joins the pool."""
        acts=self.actions;T=len(acts)
        for P in self.pool[:models]:
            d0,e0=P['d'],P['e'];r=len(e0);path=[P['start']]
            for a in acts:path.append(d0[path[-1]][a])
            for L in range(0,min(T,self.n-r-1)+1):
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

    def initialize(self,obs):
        if self.masks:raise ValueError('already initialized')
        mk=codes_mask(tuple(obs),self.s_bits);self.masks.append(mk);self._add_step(mk);self._feasible()

    def observe(self,action,obs,deadline=None):
        if not self.masks:raise ValueError('not initialized')
        if action not in range(self.k):raise ValueError(f'action must be in 0..{self.k-1}')
        mk=codes_mask(tuple(obs),self.s_bits)
        if self.status=='grammar_contradicted':self.masks.append(mk);self.actions.append(action);return
        if self.pool and not any(mk>>P['e'][P['d'][P['q']][action]]&1 for P in self.pool):
            for c in range(self.m):   # repair before the step: a chain witness for an observed code keeps the pool alive
                if mk>>c&1 and self._chain(action,c):break
        if self.fresh:self.S.restart()
        self.masks.append(mk);self.actions.append(action);self._add_step(mk,action);self._memo={}
        keep=[];self._dropped=self.pool[-1] if self.pool else self._dropped
        for P in self.pool:
            q2=P['d'][P['q']][action]
            if mk>>P['e'][q2]&1:P['used'].add((P['q'],action));P['q']=q2;keep.append(P)
        self.pool=keep;self._feasible(deadline)

    def _deadline(self,deadline):
        t=perf_counter()+self.query_s
        return t if deadline is None else min(t,deadline)

    def _feasible(self,deadline=None):
        if self.pool:self.status='supported';return True
        if self.hint and len(self.masks)>1 and all(bin(mk).count('1')==1 for mk in self.masks):
            f=greedy_fold(self.actions,[mk.bit_length()-1 for mk in self.masks],self.n,self.k)
            if f is not None:self.S.phases(*canonical_bfs(*f))
            elif self._dropped is not None:
                P=self._dropped;self.S.phases(*canonical_bfs(P['d'],P['e'],P['start']))
        dl=self._deadline(deadline);self.calls+=1
        while self.n_lo<self.n:   # deepening, DEEPEN_S per level; a level out of time hands over to the full search
            r=self.S.solve([-self.S.u[self.n_lo]],min(dl,perf_counter()+DEEPEN_S));self.solves+=1
            if r is None:break
            if r:self._pool_add(*self.S.model());self.status='supported';return True
            self.n_lo+=1
        r=self.S.solve([],dl);self.solves+=1
        if r is None:self.status='budget_exhausted';self.unknown_total+=1;return None
        if r:self._pool_add(*self.S.model());self.status='supported';return True
        self.n_lo=self.n+1;self.status='grammar_contradicted';return False

    # ---- queries ----------------------------------------------------------------------------------------------------
    def _witness_codes(self,b):
        out=set()
        for P in self.pool:
            q=P['q'];out.add(P['e'][P['d'][q][b]])
            if (q,b) not in P['used']:
                out.update(P['e'])
                if len(P['e'])<self.n:return set(range(self.m))
        return out

    def support(self,b,deadline=None):
        """(sorted tuple of possible next codes after action b, unknowns); (None, 0|1) if not supported."""
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
            if self._chain(b,c):have.add(c);have|=self._witness_codes(b);continue
            g=S._v();S.add([[-g,-y[r],S.e[r][c]] for r in range(self.n)],keep=False);res=S.solve([g],dl);self.solves+=1
            if res is True:
                d,e=S.model();self._pool_add(d,e);have|=self._witness_codes(b);have.add(c)
            elif res is None:u+=1;have.add(c)
            S.add([[-g]],keep=False)
        self.unknown_total+=u;out=(tuple(sorted(have)),u);self._memo[('sup',b)]=out
        return out

    def identify(self,deadline=None):
        """End-of-trace identification: {'n_min', 'unique', 'model' (BFS-canonical (d, e)) , 'unknown'}. unique is True iff
        the least-state model is the only BFS-canonical model with n_min states (unexercised transitions included)."""
        if self.status=='budget_exhausted':self._feasible(deadline)
        if self.status!='supported':return {'n_min':None,'unique':False,'model':None,'unknown':self.status=='budget_exhausted'}
        S=self.S;dl=self._deadline(deadline)
        while True:
            n=self.n_lo;base=[-S.u[n]] if n<self.n else [];r=S.solve(base,dl);self.solves+=1
            if r is not False or n>=self.n:break
            self.n_lo+=1
        if r is not True:return {'n_min':n,'unique':False,'model':None,'unknown':r is None}
        d,e=S.model();g=S._v()
        S.add([[-g]+[-S.d[q][a][d[q][a]] for q in range(len(d)) for a in range(self.k)]+[-S.e[q][e[q]] for q in range(len(e))]])
        r2=S.solve([g]+base,dl);self.solves+=1;S.add([[-g]])
        return {'n_min':n,'unique':r2 is False,'model':(d,e),'unknown':r2 is None}

    def close(self):
        if self.S is not None:self.S.close();self.S=None

    def __enter__(self):return self

    def __exit__(self,*exc):self.close()


class ScaleTolerant:
    """RGN_n(m) on the S2 skeleton: masks open, flip variable per observed bit, sum(flips) <= m. Built once per step."""
    def __init__(self,n,readings,actions,m,k=2,s=2,query_s=QUERY_S,solver=SOLVER,deadline=None):
        if len(readings)!=len(actions)+1:raise ValueError('need one more reading than actions')
        self.n=n;self.k=k;self.mcodes=1<<s;self.query_s=query_s;S=self.S=_Skeleton(n,k,1<<s,solver);cl=[]
        self.x=[[S._v() for _ in range(n)] for _ in readings];cl.append([self.x[0][0]])
        for t,a in enumerate(actions):
            for q in range(n):
                for r in range(n):cl.append([-self.x[t][q],-S.d[q][a][r],self.x[t+1][r]])
        for t in range(len(readings)):cl.append(list(self.x[t]))
        for t in range(len(readings)):
            for q,r in combinations(range(n),2):cl.append([-self.x[t][q],-self.x[t][r]])
        fs=[]
        for t,o in enumerate(readings):
            if len(o)!=s:raise ValueError(f'reading must have {s} entries')
            for j,bit in enumerate(o):
                if bit is None:continue
                if bit not in (0,1):raise ValueError('reading entries must be 0, 1 or None')
                f=S._v();fs.append(f)
                for q in range(n):
                    for c in range(1<<s):
                        same=((c>>(s-1-j))&1)==bit
                        cl.append([-self.x[t][q],-S.e[q][c],-f] if same else [-self.x[t][q],-S.e[q][c],f])
        if fs and m<len(fs):
            card=CardEnc.atmost(lits=fs,bound=m,top_id=S.nv,encoding=EncType.seqcounter);S.nv=max(S.nv,card.nv);cl+=card.clauses
        S.add(cl);self.T=len(actions);self.m_bound=m;self.flip_vars=len(fs)
        dl=perf_counter()+query_s if deadline is None else min(deadline,perf_counter()+query_s)
        self._sat=S.solve([],dl);self.unknown=int(self._sat is None)

    @property
    def feasible(self):return self._sat

    def support(self,b,deadline=None):
        if self._sat is not True:return None,int(self._sat is None)
        S=self.S;n=self.n;dl=perf_counter()+self.query_s if deadline is None else min(deadline,perf_counter()+self.query_s)
        y=[S._v() for _ in range(n)]
        S.add([[-self.x[self.T][q],-S.d[q][b][r],y[r]] for q in range(n) for r in range(n)])
        out=[];u=0
        for c in range(self.mcodes):
            g=S._v();S.add([[-g,-y[r],S.e[r][c]] for r in range(n)]);r_=S.solve([g],dl);S.add([[-g]])
            if r_ is None:u+=1
            if r_ is not False:out.append(c)
        self.unknown+=u;return tuple(out),u

    def close(self):
        if self.S is not None:self.S.close();self.S=None
