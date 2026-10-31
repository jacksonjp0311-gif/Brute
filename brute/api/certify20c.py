"""Brute v0.52.0 embeddable certify interface, version 20c (BRUTE_PLAN_055; pre-run deviation #183 fixes the readings below).
Additive: brute/api/certify16e.py, certify16d.py, certify20t.py and every earlier module are untouched and imported only.

certify/20c is certify/16e (A16: first-visit symmetry clauses, apartness clauses, observe / propose / result interface, labels, K,
and its query sequence: least-machine sizes upward, then the 'future' and 'start' rival queries at every size up to N) with ONE
change, how a SAT query is solved once its first conflict chunk is capped:
  * first chunk: solve_limited with conf_budget(min(C, conflicts left in the case)), exactly certify/16e's first chunk; a query
    that answers here is answered as certify/16e answers it;
  * otherwise the query is split into cubes: the colours of the states reached at trace positions 0..d-1 (d = CUBE_DEPTH = 5,
    or fewer if the trace is shorter). Under first-visit symmetry these colourings are exactly the restricted-growth strings
    (RGS) of length d with every colour < n (at most Bell(5) = 52). A cube that gives one colour to two positions in the
    encoding's apartness relation (the pool's future_pairs, whose clauses -x[t][q] | -x[u][q] are in every instance) is pruned
    before solving: it is UNSAT by those clauses alone. Cube order is lexicographic in the RGS, fixed before solving.
  * conquer: the surviving cubes are solved under assumptions (the query's own assumptions plus x[t][c_t] for t < d) on the SAME
    incremental solver, in round-robin chunks of C conflicts in the fixed cube order. A cube that returns UNSAT is closed; the
    first SAT cube answers SAT for the query with that witness; UNSAT on every cube answers UNSAT; every chunk counts against
    the one case budget B; budget spent (or a host wall guard) -> unknown, as certify/16e.
Why the split is exact (Exact): every model of the query has x[0][0] and first-visit symmetry, so the colours (s_0..s_{d-1}) form an
RGS with values < n; the RGS cubes are pairwise disjoint and cover all of them; a pruned cube contradicts an apartness clause.
So SAT/UNSAT of the query equals the disjunction over the cubes, and labels follow certify/16e's rules unchanged.
    c = Certifier20C(initial, num_actions=3, family_bound=20, conflict_cap=C, budget_conflicts=B)
Guarantee (label 'ID' / 'IDF'): exact, CONDITIONAL on noise-free readings and on the true machine having at most family_bound
states (declared N <= 20). Every rival with at most N states consistent with the trace was ruled out by an UNSAT proof.
Why a size bound is needed (Inferred): a larger machine can copy the true machine on every visited state and differ only on
states the trace never reached, so no finite trace rules out every larger machine.
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from time import perf_counter
from brute.api.certify16 import S_BITS
from brute.api import certify16e as E
from brute.api.certify16d import A16D_MAX_BOUND,CCounted,counted16d
from brute.api.certify16e import Certifier16E,H16E,Pool16E

API='brute.certify/20c'
SEARCHES=('a20c',)
CUBE_DEPTH=5
__all__=['API','SEARCHES','A16D_MAX_BOUND','CUBE_DEPTH','Certifier20C','certify20c','soundness','rgs','cube_plan','H20C','Pool20C',
         'counted16d','CCounted']


def soundness(**kw):
    s=E.soundness();s['search']='a20c'
    s['split']=f'cube-and-conquer on capped queries: restricted-growth colourings of trace positions 0..{CUBE_DEPTH-1}, apartness-pruned, lexicographic, round-robin conflict chunks'
    return s


def rgs(d,n):
    """Restricted-growth strings of length d with values < n, lexicographic (a[0] = 0, a[i] <= max(a[:i]) + 1)."""
    out=[]
    def go(a,mx):
        if len(a)==d:out.append(tuple(a));return
        for c in range(min(mx+1,n-1)+1):go(a+[c],max(mx,c))
    if d>=1 and n>=1:go([0],0)
    return out


def cube_plan(n,T,pairs,depth=CUBE_DEPTH):
    """(positions, live cubes, pruned [(cube, (t, u))]) for an n-state instance over trace positions 0..T and apart pairs."""
    pos=list(range(min(depth,T+1)));live=[];pruned=[]
    P=sorted((t,u) for (t,u) in pairs if t<len(pos) and u<len(pos))
    for c in rgs(len(pos),n):
        hit=next(((t,u) for (t,u) in P if c[t]==c[u]),None)
        if hit is None:live.append(c)
        else:pruned.append((c,hit))
    return pos,live,pruned


def _chunk(R,o,assume):
    """One conflict chunk on R's solver under assume: (answer, conflicts, wall, why); why in (None, 'budget', 'wall_guard')."""
    c=o.case;left=c.budget-c.spent
    if left<=0:return None,0,0.0,'budget'
    if c.t0 is not None and perf_counter()-c.t0>=c.guard_case_s:c.wall_guard+=1;c.guard_events.append('case');return None,0,0.0,'wall_guard'
    cap=min(c.cap,left);h=c.hook;tok=None;b0=R.s.conflicts();t1=perf_counter();r=None
    if h is not None:tok=h.arm(R.s.interrupt,c.guard_call_s)
    try:
        R.s.conf_budget(cap);r=R.s.solve_limited(assumptions=assume,expect_interrupt=h is not None);o.chunks+=1
    finally:
        fired=False
        if h is not None:fired=bool(h.disarm(tok));R.s.clear_interrupt()
        used=R.s.conflicts()-b0;c.spent+=used
    if r is None and fired:c.wall_guard+=1;c.guard_events.append('call');return None,used,perf_counter()-t1,'wall_guard'
    return r,used,perf_counter()-t1,None


class H20C(H16E):
    """A16's instance (first-visit + apartness clauses); capped queries are conquered over prefix-colour cubes."""
    def query(self,o,deadline,assume):
        t=perf_counter();self._owner=o;self._dl=deadline;r=self._solve20c(o,list(assume))
        self._log('least' if not assume else 'rival',t,r);return r

    def _solve20c(self,o,assume):
        if self._skip:self._skip=False;return True
        c=o.case;self.calls+=1;o.solves+=1;t0=perf_counter();per=[];walls=[]
        def done(r,why):
            o.call_conflicts.append(sum(per));o.query_walls.append(perf_counter()-t0)
            if r is None:o.unknowns+=1;o.capped+=1;o.call_capped.append(why)
            else:o.call_capped.append(None)
            c.calls_log.append((len(per),per,walls));return r
        r,u,w,why=_chunk(self,o,assume)
        if why is None or u:per.append(u);walls.append(w)
        if r is not None:return done(r,None)
        if why is not None:return done(None,why)
        pos,live,pruned=cube_plan(self.n,self.T,self.pool.future_pairs)
        q={'n':self.n,'phase':'least' if not assume else 'rival','T':self.T,'positions':pos,'first':u,
           'cubes':[list(x) for x in live],'pruned':[[list(x),list(p)] for x,p in pruned],'cube_conflicts':[0]*len(live),
           'cube_chunks':[0]*len(live),'closed':[],'sat':None,'open':None,'why':None}
        self.pool.cube_log.append(q);self.cubes+=len(live);openi=list(range(len(live)));res=None;why=None
        lits=[[self.x[p][x[p]] for p in pos] for x in live]
        while openi and why is None and res is None:
            keep=[]
            for j,i in enumerate(openi):
                if c.max_chunks is not None and len(per)>=c.max_chunks:why='cap';keep+=openi[j:];break
                r,u,w,why=_chunk(self,o,assume+lits[i])
                if why is None or u:per.append(u);walls.append(w);q['cube_conflicts'][i]+=u;q['cube_chunks'][i]+=1
                if why is not None:keep+=openi[j:];break
                if r is True:res=True;q['sat']=i;self.cube_sat+=1;keep+=openi[j+1:];break
                if r is False:q['closed'].append(i);self.cube_unsat+=1
                else:keep.append(i)
            openi=keep
        if res is None and why is None:res=False
        q['open']=[] if res is not None else openi;q['why']=why
        return done(res,None if res is not None else why)


class Pool20C(Pool16E):
    def __init__(self,*a,**kw):super().__init__(*a,**kw);self.cube_log=[]

    def get(self,n,masks,acts):
        self._update(masks,acts)
        if n not in self.inc:self.inc[n]=H20C(n,self.k,self.m,self,self.solver)
        return self.inc[n].sync(masks,acts)

    def cube_counts(self):
        d=super().cube_counts();d['depth']=CUBE_DEPTH;d['queries']=[dict(q) for q in self.cube_log];return d


class Certifier20C(Certifier16E):
    def __init__(self,initial=None,num_actions=None,family_bound=None,search='a20c',max_chunks=None,**kw):
        if search!='a20c':raise ValueError('search must be a20c')
        super().__init__(initial,num_actions,family_bound,'a16d',max_chunks,**kw);self.search='a20c'

    def propose(self):
        if self.stop is None and self._pending is None and self.P is None:
            self.case.t0=perf_counter();self.P=Pool20C(self.k,1<<S_BITS,self.solver,self.factory);self.n_lo=self.P.lower(self.masks,self.acts)
        return super().propose()

    def current(self):
        d=super().current();d['api']=API;d['search']='a20c';return d

    def result(self):
        d=super().result();d['api']=API;d['search']='a20c';d['soundness']=soundness();return d


def certify20c(initial,actions,observations,num_actions=None,family_bound=None,**kw):
    """One stop check on the given trace (K=0: an ambiguous trace ends 'AMB' with no experiment)."""
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    c=Certifier20C(initial,num_actions,family_bound,'a20c',K=0,**kw)
    try:
        for a,o in zip(acts,obs):c.observe(a,o)
        c.propose();return c.result()
    finally:c.close()
