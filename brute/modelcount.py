"""GMC model counting for BRUTE_PLAN_008 (reporting only: no count is ever used by a certification, policy, alarm or
experiment decision).

Quantities at a sampled step t (evidence = the initial mask plus the first t (action, mask) pairs of the learner's region):
* |R_t|: projected model count of the frozen RegionK CNF (brute/region.py, first-visit symmetry breaking, start state 0)
  onto the machine variables (d, e) = number of canonical complete <=n Moore machines consistent with the evidence;
* fibre(a, c): projected count onto (d, e, P) of (machine, fibre state P) pairs, P a visited state compatible with the
  last mask, whose successor under action a emits c; pairs(a): the same without the code constraint.
  Sum check: sum_c fibre(a, c) == pairs(a) >= |R_t| (every machine has its current state as a fibre state).

Counters:
* primary: pyganak==2.8.0 (documents itself as an exact model counter -> label Exact), run in a child process with a
  10 s wall-clock timeout per count (plan budget_rule_modelcount); timeout or error => UNKNOWN with a reason, never imputed;
* independent check: blocking-clause enumeration on the xcheck encoding (brute/xcheck_sat.XRegion, CaDiCaL) projected on
  its machine variables (T, E), capped at 10^4 models (">10000" = censored). For counting only, XRegion's optional
  first-visit naming (symmetry=True) is switched on so that both counters count the same canonical machines (disclosed);
* fallback: pyapproxmc==4.4.0 (epsilon=0.8, delta=0.2), label Inferred, used only for counts that are UNKNOWN.
The RegionK CNF is captured by temporarily substituting a recording Solver class in brute.region while a RegionK is built;
brute/region.py itself is not modified.
"""
from __future__ import annotations
import multiprocessing as mp
import time
from contextlib import contextmanager
from pysat.solvers import Solver
import brute.region as _region
from brute.region import RegionK
from brute.xcheck_sat import XRegion

PER_COUNT_S=10.0
PER_CASE_S=120.0
BLOCK_CAP=10_000
APPROX_EPS=0.8
APPROX_DELTA=0.2


class _Recorder(Solver):
    captured=None
    def __init__(self,name=None,bootstrap_with=None,**kw):
        _Recorder.captured=[list(c) for c in (bootstrap_with or [])]
        super().__init__(name=name,bootstrap_with=bootstrap_with,**kw)


@contextmanager
def _recording():
    old=_region.Solver;_region.Solver=_Recorder
    try:yield
    finally:_region.Solver=old


def regionk_cnf(n,k,m,masks,actions):
    """(RegionK object, captured clause list). The object keeps its solver; allocate extra vars with R._v()."""
    with _recording():
        R=RegionK(n,k,m,list(masks),list(actions),conf_budget=None)
        cl=_Recorder.captured;_Recorder.captured=None
    return R,cl


def count_jobs(n,k,m,masks,actions):
    """CNF jobs for one step: [('R',), ('pairs',a), ('fibre',a,c)...] each (key, nvars, clauses, projection)."""
    R,base=regionk_cnf(n,k,m,masks,actions)
    proj=[v for q in range(n) for a in range(k) for v in R.d[q][a]]+[v for q in range(n) for v in R.e[q]]
    jobs=[(('R',),R.nv,base,proj)];last=masks[-1]
    for a in range(k):
        P=[R._v() for _ in range(n)];C=[list(P)]+[[-x,-y] for i,x in enumerate(P) for y in P[i+1:]]
        for j in range(n):
            C.append([-P[j],R.V[j]]);C.append([-P[j]]+[R.A[j][cc] for cc in range(m) if last>>cc&1])
        jobs.append((('pairs',a),R.nv,base+C,proj+P))
        for c in range(m):
            D=[[-P[j],-R.d[j][a][r],R.e[r][c]] for j in range(n) for r in range(n)]
            jobs.append((('fibre',a,c),R.nv,base+C+D,proj+P))
    R.close()
    return jobs


def _child(conn,jobs):
    from pyganak import Counter
    for key,nv,cl,proj in jobs:
        try:
            c=Counter(verbose=0,seed=0)
            if nv:c.new_vars(nv)
            c.add_clauses(cl);c.set_sampling_set(proj);conn.send((key,str(c.count()),None))
        except Exception as exc:
            conn.send((key,None,f'error: {type(exc).__name__}: {exc}'))
    conn.close()


def ganak_counts(jobs,per_count=PER_COUNT_S,deadline=None):
    """{key: {'count': str|None, 'reason': str|None, 'seconds': float}} in job order; child process per batch with a
    per-count wall-clock limit; after a timeout the child is killed and a fresh one continues with the next job."""
    out={};todo=list(jobs);ctx=mp.get_context('fork')
    while todo:
        if deadline is not None and time.time()>=deadline:
            for j in todo:out[j[0]]={'count':None,'reason':'budget (per-case or total cap reached)','seconds':0.}
            break
        a,b=ctx.Pipe(duplex=False);p=ctx.Process(target=_child,args=(b,todo),daemon=True);p.start();b.close()
        while todo:
            key=todo[0][0];t0=time.time();lim=per_count
            if deadline is not None:lim=min(lim,max(0.,deadline-t0))
            if a.poll(lim):
                try:k_,cnt,err=a.recv()
                except EOFError:
                    out[key]={'count':None,'reason':'error: counter process died','seconds':round(time.time()-t0,3)};todo.pop(0);break
                out[k_]={'count':cnt,'reason':err,'seconds':round(time.time()-t0,3)};todo.pop(0)
            else:
                why='timeout (10 s per count)' if lim>=per_count else 'budget (per-case or total cap reached)'
                out[key]={'count':None,'reason':why,'seconds':round(time.time()-t0,3)};todo.pop(0)
                p.kill();break
        p.join(1)
        if p.is_alive():p.kill();p.join()
        a.close()
    return out


def blocking_count(n,k,m,masks,actions,cap=BLOCK_CAP,conf_budget=2_000_000):
    """Distinct (T, E) projections of the xcheck encoding with first-visit naming, by blocking clauses.
    Returns (count:int|None, censored:bool, reason)."""
    X=XRegion(n,k,m,masks,actions,conf_budget,symmetry=True)
    proj=[v for q in range(n) for a in range(k) for v in X.Tq[q][a]]+[v for q in range(n) for v in X.E[q]]
    cnt=0
    try:
        while True:
            r=X._solve([])
            if r is None:return None,False,'conflict budget'
            if not r:return cnt,False,None
            cnt+=1
            if cnt>cap:return None,True,f'>{cap}'
            pos=set(x for x in X.s.get_model() if x>0)
            X.s.add_clause([-v if v in pos else v for v in proj])
    finally:
        X.close()


def approx_count(nv,cl,proj,seed=0):
    """pyapproxmc fallback (Inferred): returns cells*2**hashes as a str."""
    import pyapproxmc
    c=pyapproxmc.Counter(seed=seed,epsilon=APPROX_EPS,delta=APPROX_DELTA)
    for x in cl:c.add_clause(x)
    if nv:c.add_clause([nv,-nv])
    a,b=c.count(proj);return str(a*2**b)
