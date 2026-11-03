"""Brute v0.60.0 embeddable certify interface, version 20p (BRUTE_PLAN_063; clique-anchored symmetry breaking).
Additive: brute/api/certify20b.py, certify16e.py and every earlier module are untouched and imported only.

certify/20p is certify/20b (conflict-counted A16 declared-N exact identifier at read_bits 2, 3 or 4) with ONE change, the
encoding's symmetry breaking. Before every round the exact maximum apartness clique C of the observed positions that contains
position 0 is computed (deterministic branch and bound with a greedy-colouring bound; node cap NODE_CAP, after which the best
clique found so far is used: still sound, only weaker). C is sorted (position 0 first) and pinned: x[c_i] = i. First-visit
clauses are kept only for positions outside C and states q > |C|, over earlier positions outside C. Sizes below |C| are never
queried (lower bound |C|, Exact: pairwise apart positions need distinct states) and are UNSAT by one contradiction clause if
asked. Apartness pair clauses are kept. When the maximum clique grows, the pool is rebuilt on the larger clique (learnt
clauses are lost; conflicts keep counting against the same budget). The policy (separating words), observe(), the stop rule,
K, the conflict ledger and the labels are certify/20b's. record() adds 'repins' (step, old size, new size, exact) and
'guards_closed' (chunk guards of rebuilt pools) and 'final_clique' (the pinned positions).
Exactness of the pinning (Inferred, relabelling argument): any machine consistent with the trace can be relabelled so the
clique positions get states 0..|C|-1 in clique order (they are pairwise distinct) and the remaining states appear in first-visit
order off the clique; so the pinned encoding is satisfiable iff the unpinned one is, at every size n >= |C|.
    c = Certifier20P(initial, num_actions=3, family_bound=20, read_bits=2, conflict_cap=C, budget_conflicts=B)
Guarantee (label 'ID' / 'IDF'): exact, CONDITIONAL on noise-free readings and on the true machine having at most family_bound
states (declared N <= 20). Every rival with at most N states consistent with the trace was ruled out by an UNSAT proof.
Why a size bound is needed (Inferred): a larger machine can copy the true machine on every visited state and differ only on
states the trace never reached, so no finite trace rules out every larger machine.
Host-agnostic: no I/O, network, threads, child processes or global state. The case clock for the wall guard is certify/20b's
(the same perf_counter the frozen module uses), so this file imports no host module itself.
"""
from __future__ import annotations
from brute.api import certify20b as B
from brute.api.certify20b import Certifier20B,counted16d,READ_BITS
from brute.api.certify16e import Pool16E,H16E
from brute.scalesearch15 import apart_matrix,greedy_clique

API='brute.certify/20p'
SEARCHES=('a16d',)
NODE_CAP=200000
__all__=['API','SEARCHES','READ_BITS','NODE_CAP','Certifier20P','certify20p','soundness','counted16d','max_clique0','H63','Pool63']


def soundness(**kw):
    s=B.soundness();s['symmetry']='clique-anchored: the exact max apartness clique is pinned to states 0..|C|-1 (re-pinned when it grows)';return s


def max_clique0(A,floor,cap=NODE_CAP):
    """(clique, exact): the largest clique of the apartness matrix A containing position 0, never smaller than floor (a clique
    containing 0); exact unless the node cap is hit. Deterministic."""
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
    non-clique positions); n < |C| gets a contradiction clause."""
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
    """Pool16E pinned to a preset clique (sorted, must contain position 0), H63 instances, lower bound |C| (Exact)."""
    def __init__(self,k,m,solver,factory,clique):
        Pool16E.__init__(self,k,m,solver,factory);self.clique=sorted(clique);self.colour={t:i for i,t in enumerate(self.clique)}
        if not self.clique or self.clique[0]!=0:raise ValueError('Pool63: the clique must contain position 0')
    def lower(self,masks,acts):self._update(masks,acts);return len(self.clique)
    def get(self,n,masks,acts):
        self._update(masks,acts)
        if n not in self.inc:self.inc[n]=H63(n,self.k,self.m,self,self.solver)
        return self.inc[n].sync(masks,acts)


class Certifier20P(Certifier20B):
    def __init__(self,initial=None,num_actions=None,family_bound=None,search='a16d',read_bits=2,max_chunks=None,node_cap=NODE_CAP,**kw):
        if isinstance(node_cap,bool) or not isinstance(node_cap,int) or node_cap<1:raise ValueError('node_cap must be a positive int')
        super().__init__(initial,num_actions,family_bound,search,read_bits=read_bits,max_chunks=max_chunks,**kw)
        self.node_cap=node_cap;self.repins=[];self.guards_closed=0;self.clique=None

    def propose(self):
        if self.stop is not None or self._pending is not None:return super().propose()
        A=apart_matrix(self.masks,self.acts);cur=None if self.P is None else self.P.clique
        mc,exact=max_clique0(A,greedy_clique(A) if cur is None else cur,self.node_cap)
        if self.P is None:
            self.case.t0=B.perf_counter();self.P=Pool63(self.k,self.m,self.solver,self.factory,mc);self.n_lo=self.P.lower(self.masks,self.acts)
            self.repins.append([len(self.acts),None,len(mc),exact]);self.clique=list(mc)
        elif len(mc)>len(cur):
            self.guards_closed+=self.P.guards();self.P.close()
            self.P=Pool63(self.k,self.m,self.solver,self.factory,mc);self.n_lo=max(self.n_lo,self.P.lower(self.masks,self.acts))
            self.repins.append([len(self.acts),len(cur),len(mc),exact]);self.clique=list(mc)
        return super().propose()

    def record(self):
        d=dict(super().record());d['repins']=[list(x) for x in self.repins];d['guards_closed']=self.guards_closed;d['final_clique']=list(self.clique or []);return d

    def current(self):
        d=super().current();d['api']=API;d['clique_size']=None if self.P is None else len(self.P.clique);d['repins']=len(self.repins);return d

    def result(self):
        d=super().result();d['api']=API;d['clique_size']=None if self.P is None else len(self.P.clique);d['repins']=len(self.repins)
        d['soundness']=soundness();return d


def certify20p(initial,actions,observations,num_actions=None,family_bound=None,read_bits=2,**kw):
    """One stop check on the given trace (K=0: an ambiguous trace ends 'AMB' with no experiment)."""
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    c=Certifier20P(initial,num_actions,family_bound,'a16d',read_bits=read_bits,K=0,**kw)
    try:
        for a,o in zip(acts,obs):c.observe(a,o)
        c.propose();return c.result()
    finally:c.close()
