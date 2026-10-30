"""A8 active experiments for Brute v0.30.0 (BRUTE_PLAN_033; deviation #138 fixes the readings below). New file;
brute/region.py (S1), brute/scalesearch4.py, brute/scalesearch5.py and brute/scalesearch6.py are untouched and imported
only.

identify8: the 031 identify probe (brute.scalesearch6.identify6: least n from a start bound, the frozen S1 RegionK with
first-visit symmetry so a minimum machine has canonical state names, then a second solve with the first model blocked)
with two additions: (1) the search starts at max(n_lo, greedy clique bound), where n_lo is the n_min of an earlier,
shorter prefix of the same trace (n_min never decreases as readings are added, so no smaller n is skipped); (2) every
SAT query is hard-capped at query_s seconds inside the case deadline (a capped query counts as UNKNOWN). It also returns
the second machine, and the wall time of each query.
distinguishing_word: BFS over the product of two complete machines from given states; the shortest action word on
which their emitted codes first differ (None if no reachable pair of states emits differently).
active8: the A8 loop. Each round runs identify8 on the trace so far; UNKNOWN stops (IDU); a unique class stops (the
runner scores ID or WRONG against the truth); otherwise the shortest word that separates the two machines is executed
on the world through observe(action) -> reading mask, its readings are appended and the loop repeats, until a single
class remains, the two machines are indistinguishable from their current states, the word no longer fits in the K
extra actions left, or the deadline passes. A machine is ruled out only by real readings (hard masks).
Host-agnostic: no I/O, network, threads, child processes or global state; the world is reached only via observe."""
from __future__ import annotations
from collections import deque
from time import perf_counter
from brute.scalesearch import simulate
from brute.scalesearch4 import _Region as _Region4,_lower_bound,CHUNK0,CHUNK_MIN,CHUNK_MAX,CHUNK_TARGET_S,SOLVER4

__all__=['QUERY_S8','K8','identify8','distinguishing_word','active8']
QUERY_S8=10.0;K8=64


class _Owner8:
    def __init__(self,query_s):self.solves=0;self.unknowns=0;self.chunks=0;self.chunk=CHUNK0;self.query_s=query_s;self.query_walls=[];self.capped=0


class _RegionQ(_Region4):
    """The frozen S1 RegionK with first-visit symmetry; chunked solve bounded by min(deadline, query start + query_s)."""
    def _solve(self,assume):
        if self._skip:self._skip=False;return True
        o=self._owner;self.calls+=1;o.solves+=1;t0=perf_counter();dl=min(self._dl,t0+o.query_s)
        try:
            while True:
                if perf_counter()>=dl:
                    o.unknowns+=1
                    if dl<self._dl:o.capped+=1
                    return None
                ch=o.chunk;t=perf_counter();self.s.conf_budget(ch);r=self.s.solve_limited(assumptions=assume)
                dt=perf_counter()-t;o.chunks+=1
                o.chunk=int(max(CHUNK_MIN,min(CHUNK_MAX,ch*CHUNK_TARGET_S/max(dt,1e-3))))
                if r is not None:return r
        finally:o.query_walls.append(perf_counter()-t0)


def identify8(masks,acts,k,m,n_max,deadline,n_lo=1,query_s=QUERY_S8,solver=SOLVER4):
    """{'n_min', 'unique', 'unknown', 'model', 'model2', 'second_found', 'query_walls', 'capped', 'n_start'}; unknown True iff
    the deadline or the per-query cap stopped it. model and model2 are (transitions, emissions) with start state 0."""
    o=_Owner8(query_s);n0=n=max(n_lo,_lower_bound(masks))
    out=lambda **kw:{'n_min':None,'unique':False,'unknown':False,'model':None,'model2':None,'second_found':False,
                     'query_walls':o.query_walls,'capped':o.capped,'n_start':n0,**kw}
    while n<=n_max:
        if perf_counter()>=deadline:return out(unknown=True)
        R=_RegionQ(o,n,k,m,masks,acts,solver);R._dl=deadline
        try:
            r=R._solve([])
            if r is None:return out(unknown=True)
            if r is False:n+=1;continue
            d,e=R.machine()
            R.s.add_clause([-R.d[q][a][d[q][a]] for q in range(n) for a in range(k)]+[-R.e[q][e[q]] for q in range(n)])
            u=R._solve([]);m2=R.machine() if u is True else None
            return out(n_min=n,unique=u is False,unknown=u is None,model=(d,e),model2=m2,second_found=u is True)
        finally:R.close()
    return out()


def distinguishing_word(d1,e1,s1,d2,e2,s2):
    """Shortest action word w with e1[d1*(s1,w)] != e2[d2*(s2,w)] at its last step and equal codes before it; None if none."""
    k=len(d1[0]);start=(s1,s2);prev={start:None};dq=deque([start])
    while dq:
        p=dq.popleft()
        for a in range(k):
            q=(d1[p[0]][a],d2[p[1]][a])
            if e1[q[0]]!=e2[q[1]]:
                w=[a];x=p
                while prev[x] is not None:x,b=prev[x];w.append(b)
                return w[::-1]
            if q in prev:continue
            prev[q]=(p,a);dq.append(q)
    return None


def run_word(d,e,s,word):
    """Codes emitted by machine (d, e) from state s after each action of word."""
    out=[]
    for a in word:s=d[s][a];out.append(e[s])
    return out


def active8(masks,acts,k,m,n_max,observe,deadline,K=K8,query_s=QUERY_S8,solver=SOLVER4):
    """The A8 loop on a copy of the passive trace (masks, acts). Returns {'stop', 'masks', 'acts', 'used', 'rounds', 'final'}
    with stop in 'unique', 'unknown', 'none' (no machine <= n_max), 'indistinguishable', 'K_spent'; final is the last
    identify8 result; each round records n_min, the word, both machines' predicted codes and the real reading masks."""
    masks=list(masks);acts=list(acts);used=0;rounds=[];n_lo=1
    while True:
        r=identify8(masks,acts,k,m,n_max,deadline,n_lo,query_s,solver)
        rec={'T':len(acts),'n_min':r['n_min'],'n_start':r['n_start'],'unique':r['unique'],'unknown':r['unknown'],
             'second_found':r['second_found'],'query_walls':list(r['query_walls']),'capped':r['capped']}
        rounds.append(rec)
        if r['unknown']:stop='unknown';break
        if r['n_min'] is None:stop='none';break
        if not r['second_found']:stop='unique';break
        (d1,e1),(d2,e2)=r['model'],r['model2'];s1=simulate(d1,e1,acts,masks)[1];s2=simulate(d2,e2,acts,masks)[1]
        w=distinguishing_word(d1,e1,s1,d2,e2,s2);rec['word']=w;rec['M1']=r['model'];rec['M2']=r['model2'];rec['s1']=s1;rec['s2']=s2
        if w is None:stop='indistinguishable';break
        if len(w)>K-used:stop='K_spent';break
        rec['pred1']=run_word(d1,e1,s1,w);rec['pred2']=run_word(d2,e2,s2,w);obs=[]
        for a in w:mk=observe(a);acts.append(a);masks.append(mk);obs.append(mk)
        used+=len(w);rec['obs']=obs;n_lo=r['n_min']
    return {'stop':stop,'masks':masks,'acts':acts,'used':used,'rounds':rounds,'final':r}
