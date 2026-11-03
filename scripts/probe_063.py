"""Capability probe for plan 063 (v0.60.0; run BEFORE the plan is locked, so the plan can say whether the step decides anything;
NOT a study, never gated). New file.
Question: on 2-bit 20-state worlds (worlds_058 'scale20', original emissions), does a stronger use of the APARTNESS CLIQUE decide
any world that the frozen certify/20b (B2) left undecided at the same budget? The frozen pool (PoolE1 via Pool16E) computes a greedy
clique but uses it only as the cube position: its lower bound is 1 and its symmetry breaking is first-visit only, so every size
below the clique must be refuted by the solver (a pigeonhole-like proof). Diagnostic results/diag-063/CLIQUE_DIAG_063.json
(Observed, sealed 062 seeds): the exact maximum clique on the sealed traces is 17-18; the greedy one is 13-17.
Two arms, each the frozen certify/20b with ONE change (policy, solver, apartness clauses, proposals, stop rule, labels, K, budgets
unchanged):
  L2  n_lo is raised, before every round, to the size of the exact maximum apartness clique containing position 0 (deterministic
      branch and bound with a greedy-colouring bound, node cap NODE_CAP; Exact lower bound: apart positions need distinct states).
  P2  clique-anchored symmetry breaking (Pool63/H63 below): the max clique C (sorted, position 0 first) is pinned x[c_i]=i, the
      first-visit clauses are kept for the non-clique positions and states > |C| only, sizes < |C| are UNSAT at once; when the max
      clique grows the pool is rebuilt on the larger clique (learnt clauses lost). Exact (Inferred): any consistent machine can
      be relabelled with clique states 0..|C|-1 in clique order and the other states by first visit off the clique.
Seeds are NON-FRESH: sealed study-062 main seeds 12620101-12620103 (B2 and W2 IDU at 8M there) and sealed 058 seed 12530003
(probe_062 W2 decided it at 8M; B2 did not). Grid: {P2, L2} x 4 seeds at B 8M (B2 at 8M on all 4 is already sealed: 062 main and BUDGET_PROBE_062, all IDU);
C 50000, K 400, read_bits 2, bound 20; WORKERS workers, max_tasks_per_child=1; probe-only wall guard 2400 s per case.
Output: results/diag-063/CAPABILITY_PROBE_063.json (refuses overwrite). Labels against the true machine (Observed).
  PYTHONPATH=. python scripts/probe_063.py"""
from __future__ import annotations
import hashlib,json,sys,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import worlds_058 as W58
from experiments.brute_study_058 import truth_label,_Step
from brute.api import certify20b as C20B
from brute.api.certify16e import Pool16E,H16E
from brute.scalesearch15 import apart_matrix,greedy_clique
from brute.scalesearch4 import SOLVER4
from experiments.brute_common import dumps

SEEDS=(12620101,12620102,12620103,12530003);B=8000000;C=50000;K=400;N=20;NODE_CAP=200000;WORKERS=6
GUARD_CASE_S=2400.0;GUARD_CALL_S=30.0
OUT=ROOT/'results/diag-063/CAPABILITY_PROBE_063.json'


def max_clique0(A,floor,cap=NODE_CAP):
    """Largest clique containing position 0 (exact unless the node cap is hit; never smaller than floor). Deterministic."""
    n=len(A);ap=lambda t,u:A[t][u] if t<u else A[u][t]
    adj=[{u for u in range(n) if u!=t and ap(t,u)} for t in range(n)]
    best=sorted(floor);nodes=[0]
    def colour_sort(P):
        P=sorted(P,key=lambda v:(-len(adj[v]),v));cls=[];order=[];bounds=[]
        for v in P:
            for c in cls:
                if not (adj[v]&c):c.add(v);break
            else:cls.append({v})
        for i,c in enumerate(cls):
            for v in sorted(c):order.append(v);bounds.append(i+1)
        return order,bounds
    def expand(R,P):
        nonlocal best
        nodes[0]+=1
        if nodes[0]>cap:return
        order,bounds=colour_sort(P)
        for i in range(len(order)-1,-1,-1):
            if len(R)+bounds[i]<=len(best):return
            v=order[i];R2=R+[v];P2=[u for u in order[:i] if u in adj[v]]
            if not P2:
                if len(R2)>len(best):best=sorted(R2)
            else:expand(R2,P2)
    expand([0],sorted(adj[0]))
    return best,nodes[0]<=cap


class H63(H16E):
    """H16E with clique-anchored symmetry breaking: pinned positions get x[c_i]=i (no first-visit clause); every other position
    keeps a first-visit clause only for states q > |C| (state q may be used off the clique only after state q-1 was, among
    non-clique positions). Exact (Inferred): relabel clique states 0..|C|-1 in clique order, the rest by first visit."""
    def sync(self,masks,acts):
        if len(masks)!=len(acts)+1:raise ValueError('need one more mask than actions')
        if self.T>=0 and (list(acts[:self.T])!=self.acts or list(masks[:self.T+1])!=self.masks):raise ValueError('H63: trace prefix changed')
        n=self.n;cl=self.cl;v=self._v;col=self.pool.colour;c=len(self.pool.clique)
        if c>n and not getattr(self,'_dead',False):z=v();cl.append([z]);cl.append([-z]);self._dead=True
        for t in range(self.T+1,len(acts)+1):
            row=[v() for _ in range(n)];self.x.append(row);self._one(row)
            if t in col:
                if col[t]<n:cl.append([row[col[t]]])
            else:
                for q in range(c+1,n):cl.append([-row[q]]+[self.x[u][q-1] for u in range(t) if u not in col])
            if t>0:
                a=acts[t-1]
                for q in range(n):
                    for r in range(n):cl.append([-self.x[t-1][q],-self.d[q][a][r],row[r]])
            mk=masks[t]
            for q in range(n):cl.append([-row[q]]+[self.e[q][cc] for cc in range(self.m) if mk>>cc&1])
        self.T=len(acts);self.acts=list(acts);self.masks=list(masks)
        for (t,u) in sorted(self.pool.future_pairs-self.pairs):
            for q in range(n):cl.append([-self.x[t][q],-self.x[u][q]])
        self.pairs|=self.pool.future_pairs;self._flush();return self


class Pool63(Pool16E):
    """Pool16E pinned to a preset clique (must contain position 0, sorted), H63 instances, lower bound |C| (Exact)."""
    def __init__(self,k,m,solver,factory,clique):
        Pool16E.__init__(self,k,m,solver,factory);self.clique=sorted(clique);self.colour={t:i for i,t in enumerate(self.clique)}
        assert self.clique[0]==0
    def lower(self,masks,acts):self._update(masks,acts);return len(self.clique)
    def get(self,n,masks,acts):
        self._update(masks,acts)
        if n not in self.inc:self.inc[n]=H63(n,self.k,self.m,self,self.solver)
        return self.inc[n].sync(masks,acts)


class _ProbeBase(C20B.Certifier20B):
    def _clique(self,floor):
        A=apart_matrix(self.masks,self.acts);mc,exact=max_clique0(A,floor);return mc,exact


class _L2Probe(_ProbeBase):
    """Frozen pool and encoding; only n_lo is raised to the exact max apartness clique size before every round (Exact bound)."""
    def propose(self):
        if self.stop is not None or self._pending is not None:return super().propose()
        if not hasattr(self,'repins'):self.repins=[]
        mc,exact=self._clique([0])
        if self.P is None:
            self.case.t0=perf_counter();self.P=Pool16E(self.k,self.m,self.solver,self.factory);self.n_lo=self.P.lower(self.masks,self.acts)
        if len(mc)>self.n_lo:self.repins.append((len(self.acts),self.n_lo,len(mc),exact));self.n_lo=len(mc)
        return super().propose()


class _P2Probe(_ProbeBase):
    """Clique-anchored pinning (Pool63) re-pinned to a strictly larger max clique (pool rebuilt, learnt clauses lost)."""
    def propose(self):
        if self.stop is not None or self._pending is not None:return super().propose()
        if not hasattr(self,'repins'):self.repins=[];self.guards_closed=0
        A=apart_matrix(self.masks,self.acts);cur=None if self.P is None else self.P.clique
        mc,exact=max_clique0(A,greedy_clique(A) if cur is None else cur)
        if self.P is None:
            self.case.t0=perf_counter();self.P=Pool63(self.k,self.m,self.solver,self.factory,mc);self.n_lo=self.P.lower(self.masks,self.acts)
            self.repins.append((len(self.acts),None,len(mc),exact))
        elif len(mc)>len(cur):
            self.guards_closed+=self.P.guards();self.P.close()
            self.P=Pool63(self.k,self.m,self.solver,self.factory,mc);self.n_lo=max(self.n_lo,self.P.lower(self.masks,self.acts))
            self.repins.append((len(self.acts),len(cur),len(mc),exact))
        return super().propose()


ARMS={'L2':_L2Probe,'P2':_P2Probe}


def job(seed,arm):
    fam='scale20';w=W58.world(seed,fam);sw=_Step(w);acts=list(W58.actions(seed,0.0,w.k));t0=time.perf_counter()
    c=ARMS[arm](sw.read(),w.k,N,'a16d',read_bits=2,max_chunks=None,K=K,conflict_cap=C,budget_conflicts=B,
               wall_guard_case_s=GUARD_CASE_S,wall_guard_call_s=GUARD_CALL_S,solver=SOLVER4,hook=None,factory=C20B.counted16d)
    try:
        for a in acts:c.observe(a,sw.step(a))
        while True:
            x=c.propose()
            if x is None:break
            for a in x:c.observe(a,sw.step(a))
        R=c.record()
    finally:c.close()
    f=R['final']
    return {'seed':seed,'arm':arm,'B':B,'stop':R['stop'],'label':truth_label(R['stop'],f['model'],f['s1'],w,sw.q),'n_min':f['n_min'],
            'used':R['used'],'n_rounds':len(R['rounds']),'conflicts_spent':R['conflicts_spent'],'wall_guard':R['wall_guard'],
            'repins':getattr(c,'repins',[]),'final_clique':len(c.P.clique) if c.P is not None else None,
            'wall_s_informational':round(time.perf_counter()-t0,1)}


def main():
    if OUT.exists():raise SystemExit('refusing overwrite '+str(OUT))
    t0=time.time();out=[]
    with ProcessPoolExecutor(WORKERS,max_tasks_per_child=1) as ex:
        fs={ex.submit(job,s,a):(s,a) for a in ('P2','L2') for s in SEEDS}
        for f in as_completed(fs):
            r=f.result();out.append(r);print(dumps(r),flush=True)
    out.sort(key=lambda r:(r['arm'],r['seed']))
    d={'schema':'brute.probe.v60_0','label':'Observed','purpose':'capability probe for plan 063 before locking; not evidence for any gate',
       'seeds_non_fresh':list(SEEDS),'seed_note':'sealed study-062 main seeds 12620101-03 and sealed 058 seed 12530003; spent, never fresh',
       'api':'probe-local _L2Probe/_P2Probe around '+C20B.API,'C':C,'K':K,'N':N,'B':B,'node_cap':NODE_CAP,'guard_case_s':GUARD_CASE_S,'records':out,
       'summary':{a:{'decided':sum(r['label'] in ('ID','IDF') for r in out if r['arm']==a),'of':sum(r['arm']==a for r in out),'labels':[r['label'] for r in out if r['arm']==a],'n_min':[r['n_min'] for r in out if r['arm']==a]} for a in ARMS},
       'decided':sum(r['label'] in ('ID','IDF') for r in out),'of':len(out),'wrong':sum(r['label']=='WRONG' for r in out),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'elapsed_informational':round(time.time()-t0,1)}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(d,indent=1,sort_keys=True)+'\n')
    print(json.dumps({k:d[k] for k in ('decided','of','wrong','elapsed_informational')}))


if __name__=='__main__':main()
