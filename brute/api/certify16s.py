"""Brute v0.48.0 embeddable certify interface, version 16s (BRUTE_PLAN_051; pre-run deviation #175 fixes the readings below).
Additive: brute/api/certify16e.py, certify16d.py and every earlier module are untouched and imported only.

certify/16s is certify/16e (A16 declared-N exact identifier with chunked conflict resume) on an instance with ONE change, extra
symmetry-breaking clauses for the states the trace does not visit. The a16d variables (state rows x, transitions d, emissions e),
the first-visit clauses, the apartness clauses, the cube split, the rival encoding, the stop rule and the labels are unchanged.
Reading (#175): first-visit already numbers every trace-visited state canonically (by first visit time), so a BFS order over
ALL states would contradict it; the BFS-canonical part is therefore applied to the unvisited block only:
  vis[q]      <-> state q occurs in some trace row x[0..T][q] (exact under the current activation literal; the trace grows, so
                  the 'only if' half is guarded by a fresh literal per trace length T, passed as an assumption, old ones retired);
  f[j][r]     <-> some VISITED source pair (q, a) with index q*k + a <= r has d[q][a] = j (prefix OR; the minimum-parent key);
  for every adjacent pair j, j+1 that are both unvisited: emission(j) <= emission(j+1) (minimum symbol), and on equal emission
  minparent(j) <= minparent(j+1), i.e. f[j+1][r] -> f[j][r] for every r.
Soundness (Exact argument, checked by GCOMPAT16S and the CNF reference): permuting the unvisited states leaves every trace row,
first-visit, apartness, transition and reading clause satisfied (none mentions an unvisited state as a trace state), relabels
d targets, emissions and rival paths consistently, and leaves the (emission, minimum visited parent) key of each state attached
to it; sorting the unvisited block by that key is such a permutation, so every assignment of the certify/16e instance has a
renamed copy that satisfies the extra clauses. Verdicts (SAT / UNSAT) are therefore unchanged; models may differ by renaming.
    c = Certifier16S(initial, num_actions=3, family_bound=20, conflict_cap=C, budget_conflicts=B, max_chunks=None)
Guarantee (label 'ID' / 'IDF'): exact, CONDITIONAL on noise-free readings and on the true machine having at most family_bound
states (declared N <= 20). Why a size bound is needed (Inferred): a larger machine can copy the true machine on every visited
state and differ only on states the trace never reached, so no finite trace rules out every larger machine.
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from time import perf_counter
from brute.api.certify16 import S_BITS
from brute.api import certify16e as E
from brute.api.certify16e import Certifier16E,H16E,Pool16E,_chunk_solve,A16D_MAX_BOUND,counted16d,CCounted

API='brute.certify/16s'
ENCODING='a16d+unvisited_bfs_v1'
__all__=['API','ENCODING','A16D_MAX_BOUND','Certifier16S','certify16s','soundness','counted16d','CCounted','H16S','Pool16S']


def soundness(**kw):
    s=E.soundness();s['symmetry']=('first-visit numbering of trace states (unchanged) plus minimum-symbol and minimum-visited-parent '
                                   'ordering of the unvisited block (removes only renamed copies)');s['encoding']=ENCODING;return s


class H16S(H16E):
    """certify/16e's instance plus the unvisited-block symmetry clauses."""
    def __init__(self,*a,**kw):
        self.vis=None;self.f=None;self.act=None;self.act_T=None;self.xt=0;self.sym=0;H16E.__init__(self,*a,**kw)

    def _add(self,c):self.s.add_clause(c);self.sym+=1

    def _build(self):
        n,k,m,v=self.n,self.k,self.m,self._v;R=n*k;d=self.d;e=self.e
        self.vis=vis=[v() for _ in range(n)];self.f=f=[[v() for _ in range(R)] for _ in range(n)]
        for j in range(n):
            for r in range(R):
                q,a=divmod(r,k);prev=[f[j][r-1]] if r else []
                if r:self._add([-f[j][r-1],f[j][r]])
                self._add([-vis[q],-d[q][a][j],f[j][r]])
                self._add([-f[j][r]]+prev+[vis[q]]);self._add([-f[j][r]]+prev+[d[q][a][j]])
        for j in range(n-1):
            for c in range(m):
                for c2 in range(c):self._add([vis[j],vis[j+1],-e[j][c],-e[j+1][c2]])
                for r in range(R):self._add([vis[j],vis[j+1],-e[j][c],-e[j+1][c],-f[j+1][r],f[j][r]])
        self.pool.sym_total+=self.sym

    def sync(self,masks,acts):
        H16E.sync(self,masks,acts)
        if self.vis is None:self._build()
        if self.act_T!=self.T:
            s0=self.sym;n=self.n
            for t in range(self.xt,self.T+1):
                for q in range(n):self._add([-self.x[t][q],self.vis[q]])
            self.xt=self.T+1;old=self.act;self.act=a=self._v()
            for q in range(n):self._add([-a,-self.vis[q]]+[self.x[t][q] for t in range(self.T+1)])
            if old is not None:self._add([-old])
            self.act_T=self.T;self.pool.sym_total+=self.sym-s0
        return self

    def _solve(self,assume):return _chunk_solve(self,list(assume)+[self.act])


class Pool16S(Pool16E):
    def __init__(self,*a,**kw):Pool16E.__init__(self,*a,**kw);self.sym_total=0

    def get(self,n,masks,acts):
        self._update(masks,acts)
        if n not in self.inc:self.inc[n]=H16S(n,self.k,self.m,self,self.solver)
        return self.inc[n].sync(masks,acts)


class Certifier16S(Certifier16E):
    def propose(self):
        if self.stop is None and self._pending is None and self.P is None:
            self.case.t0=perf_counter();self.P=Pool16S(self.k,1<<S_BITS,self.solver,self.factory);self.n_lo=self.P.lower(self.masks,self.acts)
        P=self.P;w=Certifier16E.propose(self)
        if self.stop is not None and getattr(self,'_record',None) is not None:self._record.update(encoding=ENCODING,sym_clauses=P.sym_total)
        return w

    def current(self):
        d=Certifier16E.current(self);d['api']=API;d['encoding']=ENCODING;return d

    def result(self):
        d=Certifier16E.result(self);d['api']=API;d['encoding']=ENCODING;d['soundness']=soundness();return d


def certify16s(initial,actions,observations,num_actions=None,family_bound=None,**kw):
    """One stop check on the given trace (K=0: an ambiguous trace ends 'AMB' with no experiment)."""
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    c=Certifier16S(initial,num_actions,family_bound,'a16d',K=0,**kw)
    try:
        for a,o in zip(acts,obs):c.observe(a,o)
        c.propose();return c.result()
    finally:c.close()
