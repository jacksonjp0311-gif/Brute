"""Brute v0.46.0 embeddable certify interface, version 16e (BRUTE_PLAN_049; pre-run deviation #171 fixes the readings below).
Additive: brute/api/certify16d.py, certify16.py, certify14.py and every earlier module are untouched and imported only.

certify/16e is certify/16d (conflict-counted A16 declared-N exact identifier) with ONE change, chunked resume: a SAT call runs
solve_limited with conf_budget(min(C, conflicts left in the case)); if it returns no answer and the case budget is not spent,
the SAME incremental solver (learned clauses kept) is called again with the same assumptions and a fresh chunk, until it
answers, the case budget B is spent, max_chunks chunks have run, or a host wall guard fires. Chunk boundaries are conflict counts;
the wall guards are host safety only (as certify/16d): the 600 s case guard is checked before every chunk, and the 30 s guard is
passed to the host hook for every chunk (deviation #171: the plan's '30 s per call' is read as per solve_limited chunk; GQB24
bounds the chunk wall). max_chunks=None (default) = resume until B; max_chunks=1 = certify/16d behaviour.
    c = Certifier16E(initial, num_actions=3, family_bound=16, conflict_cap=C, budget_conflicts=B, max_chunks=None)
Guarantee (label 'ID' / 'IDF'): exact, CONDITIONAL on noise-free readings and on the true machine having at most family_bound
states (declared N <= 20). Every rival with at most N states consistent with the trace was ruled out by an UNSAT proof.
Why a size bound is needed (Inferred): a larger machine can copy the true machine on every visited state and differ only on
states the trace never reached, so no finite trace rules out every larger machine.
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from time import perf_counter
from brute.api.certify8 import _int
from brute.api.certify16 import S_BITS
from brute.api import certify16d as D
from brute.api.certify16d import (Certifier16D,H16D,Pool16D,_Case,CCounted,counted16d,A16D_MAX_BOUND,GUARD_CASE_S,GUARD_CALL_S,INF)

API='brute.certify/16e'
SEARCHES=('a16d',)
__all__=['API','SEARCHES','A16D_MAX_BOUND','Certifier16E','certify16e','soundness','counted16d','CCounted']


def soundness(**kw):
    s=D.soundness();s['resume']='chunked (fixed conflict chunks on one incremental solver until the case budget)';return s


class _Case16E(_Case):
    """certify/16d's conflict ledger plus max_chunks and the per-call chunk log."""
    def __init__(self,cap,budget,guard_case_s,guard_call_s,hook,max_chunks):
        super().__init__(cap,budget,guard_case_s,guard_call_s,hook);self.max_chunks=max_chunks;self.calls_log=[]


def _chunk_solve(R,assume):
    if R._skip:R._skip=False;return True
    o=R._owner;c=o.case;R.calls+=1;o.solves+=1;t0=perf_counter();n=0;used_all=0;per=[];walls=[];r=None;why=None
    while True:
        left=c.budget-c.spent
        if left<=0:why='budget';break
        if c.t0 is not None and perf_counter()-c.t0>=c.guard_case_s:
            c.wall_guard+=1;c.guard_events.append('case');why='wall_guard';break
        if c.max_chunks is not None and n>=c.max_chunks:why='cap';break
        cap=min(c.cap,left);h=c.hook;tok=None;b0=R.s.conflicts();t1=perf_counter()
        if h is not None:tok=h.arm(R.s.interrupt,c.guard_call_s)
        try:
            R.s.conf_budget(cap);r=R.s.solve_limited(assumptions=assume,expect_interrupt=h is not None);o.chunks+=1
        finally:
            fired=False
            if h is not None:fired=bool(h.disarm(tok));R.s.clear_interrupt()
            used=R.s.conflicts()-b0;c.spent+=used;used_all+=used;n+=1;per.append(used);walls.append(perf_counter()-t1)
        if r is not None:break
        if fired:c.wall_guard+=1;c.guard_events.append('call');why='wall_guard';break
    o.call_conflicts.append(used_all);o.query_walls.append(perf_counter()-t0 if n else 0.0)
    if r is None:o.unknowns+=1;o.capped+=1;o.call_capped.append(why)
    else:o.call_capped.append(None)
    c.calls_log.append((n,per,walls));return r


class H16E(H16D):
    """A16's instance with the chunked conflict-counted solve."""
    _solve=_chunk_solve


class Pool16E(Pool16D):
    def get(self,n,masks,acts):
        self._update(masks,acts)
        if n not in self.inc:self.inc[n]=H16E(n,self.k,self.m,self,self.solver)
        return self.inc[n].sync(masks,acts)


class Certifier16E(Certifier16D):
    def __init__(self,initial=None,num_actions=None,family_bound=None,search='a16d',max_chunks=None,**kw):
        super().__init__(initial,num_actions,family_bound,search,**kw)
        if max_chunks is not None and _int(max_chunks,'max_chunks')<1:raise ValueError('max_chunks must be None or a positive int')
        c=self.case;self.case=_Case16E(c.cap,c.budget,c.guard_case_s,c.guard_call_s,c.hook,max_chunks);self.max_chunks=max_chunks

    def propose(self):
        if self.stop is None and self._pending is None and self.P is None:
            self.case.t0=perf_counter();self.P=Pool16E(self.k,1<<S_BITS,self.solver,self.factory);self.n_lo=self.P.lower(self.masks,self.acts)
        nr=len(self.rounds);nc=len(self.case.calls_log);w=super().propose()
        if len(self.rounds)>nr:
            log=self.case.calls_log[nc:];rec=self.rounds[-1]
            rec['call_chunks']=[x[0] for x in log];rec['chunk_conflicts']=[list(x[1]) for x in log];rec['chunk_walls']=[list(x[2]) for x in log]
        if self.stop is not None and getattr(self,'_record',None) is not None:self._extend()
        return w

    def _extend(self):
        L=self.case.calls_log;cw=[t for x in L for t in x[2]]
        self._record.update(max_chunks=self.max_chunks,chunks_total=sum(x[0] for x in L),
                            chunk_wall_max=max(cw) if cw else None,
                            case_wall=None if self.case.t0 is None else perf_counter()-self.case.t0)

    def current(self):
        d=super().current();d['api']=API;d['max_chunks']=self.max_chunks;d['chunks']=sum(x[0] for x in self.case.calls_log);return d

    def result(self):
        d=super().result();d['api']=API;d['max_chunks']=self.max_chunks;d['chunks']=sum(x[0] for x in self.case.calls_log)
        d['soundness']=soundness();return d


def certify16e(initial,actions,observations,num_actions=None,family_bound=None,**kw):
    """One stop check on the given trace (K=0: an ambiguous trace ends 'AMB' with no experiment)."""
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    c=Certifier16E(initial,num_actions,family_bound,'a16d',K=0,**kw)
    try:
        for a,o in zip(acts,obs):c.observe(a,o)
        c.propose();return c.result()
    finally:c.close()
