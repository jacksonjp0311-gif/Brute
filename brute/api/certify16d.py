"""Brute v0.44.0 embeddable certify interface, version 16d (BRUTE_PLAN_047; the pre-run deviation fixes the readings below).
Additive: brute/api/certify16.py, brute/api/certify14.py and every earlier module are untouched and imported only.

certify/16d is certify/16 (the A16 declared-N exact identifier, brute.scalesearch16) with ONE change: the per-call cap and the
case budget are counted in solver CONFLICTS, not wall seconds, so the same trace gives the same calls, the same answers and the
same record on any host (Simulated until study 047's GDET; Observed after it):
  * each SAT call gets  conf_budget(min(conflict_cap, conflicts left in the case))  in ONE solve_limited call (no adaptive
    chunking, no clock check); a call that returns no answer is 'capped' (unknown, never a certificate);
  * the case budget is budget_conflicts in all; when it is spent every further call is unknown at once;
  * the case and per-call wall clocks are kept only as a HOST GUARD (wall_guard_case_s, default 600 s, checked before each call;
    wall_guard_call_s, default 30 s, passed to the host's hook). A guard that fires makes the call unknown and sets
    record['wall_guard'] (the run is then no longer host-independent; study 047 counts it as a GDET failure).
The frozen A16 functions are called with deadline = +inf, so their own clock checks never fire; only this module's conflict
counter decides when a case runs out. Encoding, clauses, cube split, rival query, separating word, K and labels are A16's.
    c = Certifier16D(initial, num_actions=3, family_bound=16, conflict_cap=C, budget_conflicts=B)
    c.observe(a, reading); w = c.propose(); ...; c.result()        # as certify/16
Guarantee (label 'ID' / 'IDF'): exact, CONDITIONAL on noise-free readings and on the true machine having at most family_bound
states (declared N <= 20 here). Every rival with at most N states consistent with the trace was ruled out by an UNSAT proof.
Why a size bound is needed (Inferred): a larger machine can copy the true machine on every visited state and differ only on
states the trace never reached, so no finite trace rules out every larger machine.
Host-agnostic: no I/O, network, threads, child processes or global state. The default solver factory is pysat behind a clause and
conflict counter; a host factory must offer conflicts() (cumulative conflicts) besides the certify/16 solver methods.
"""
from __future__ import annotations
from time import perf_counter
from brute.api.certify import _obs
from brute.api.certify8 import _int,_num
from brute.api.certify16 import LABEL_OF_STOP,S_BITS
from brute.encaudit16 import Counted
from brute.region import codes_mask
from brute.scalesearch4 import SOLVER4
from brute.scalesearch8 import distinguishing_word,run_word
from brute.scalesearch14 import K14,stop_check14
from brute.scalesearch16 import H16,Pool16,_ex

API='brute.certify/16d'
SEARCHES=('a16d',)
A16D_MAX_BOUND=20
INF=float('inf')
GUARD_CASE_S=600.0
GUARD_CALL_S=30.0
__all__=['API','SEARCHES','A16D_MAX_BOUND','Certifier16D','certify16d','soundness','counted16d','CCounted']


class CCounted(Counted):
    """Counted (pysat behind a clause counter) plus conflicts(): the solver's cumulative conflict count."""
    def conflicts(self):return int(self.s.accum_stats().get('conflicts',0))


def counted16d(name=SOLVER4):return CCounted(name)


def soundness(**kw):
    return {'kind':'exact','method':'exact','search':'a16d','anytime':False,'cap':'conflicts',
            'conditional_on':'noise-free readings and true size <= family_bound (the declared N)',
            'why_bounded':'Inferred: a larger machine can copy the true machine on every visited state, so finite data never rules out all larger machines'}


class _Case:
    """Conflict ledger shared by every call of one case."""
    def __init__(self,cap,budget,guard_case_s,guard_call_s,hook):
        self.cap=cap;self.budget=budget;self.spent=0;self.guard_case_s=guard_case_s;self.guard_call_s=guard_call_s;self.hook=hook
        self.t0=None;self.wall_guard=0;self.guard_events=[]


class _Owner16D:
    """Per-round call owner (the fields stop_check14 and the record read) plus the per-call conflict log."""
    def __init__(self,case):
        self.case=case;self.solves=0;self.unknowns=0;self.capped=0;self.query_walls=[];self.call_conflicts=[];self.call_capped=[]
        self.query_s=INF;self.hook=None;self.chunks=0


def _conflict_solve(R,assume):
    if R._skip:R._skip=False;return True
    o=R._owner;c=o.case;R.calls+=1;o.solves+=1;t0=perf_counter();left=c.budget-c.spent
    if left<=0:
        o.unknowns+=1;o.capped+=1;o.call_conflicts.append(0);o.call_capped.append('budget');o.query_walls.append(0.0);return None
    if c.t0 is not None and t0-c.t0>=c.guard_case_s:
        c.wall_guard+=1;c.guard_events.append('case');o.unknowns+=1;o.capped+=1
        o.call_conflicts.append(0);o.call_capped.append('wall_guard');o.query_walls.append(0.0);return None
    cap=min(c.cap,left);h=c.hook;tok=None;b0=R.s.conflicts()
    if h is not None:tok=h.arm(R.s.interrupt,c.guard_call_s)
    try:
        R.s.conf_budget(cap);r=R.s.solve_limited(assumptions=assume,expect_interrupt=h is not None);o.chunks+=1
    finally:
        fired=False
        if h is not None:fired=bool(h.disarm(tok));R.s.clear_interrupt()
        used=R.s.conflicts()-b0;c.spent+=used;o.call_conflicts.append(used);o.query_walls.append(perf_counter()-t0)
    if r is None:
        o.unknowns+=1;o.capped+=1
        if fired:c.wall_guard+=1;c.guard_events.append('call');o.call_capped.append('wall_guard')
        else:o.call_capped.append('budget' if c.spent>=c.budget else 'cap')
    else:o.call_capped.append(None)
    return r


class H16D(H16):
    """A16's instance with the conflict-counted solve."""
    _solve=_conflict_solve


class Pool16D(Pool16):
    def get(self,n,masks,acts):
        self._update(masks,acts)
        if n not in self.inc:self.inc[n]=H16D(n,self.k,self.m,self,self.solver)
        return self.inc[n].sync(masks,acts)


class Certifier16D:
    def __init__(self,initial=None,num_actions=None,family_bound=None,search='a16d',K=K14,conflict_cap=None,budget_conflicts=None,
                 wall_guard_case_s=GUARD_CASE_S,wall_guard_call_s=GUARD_CALL_S,solver=SOLVER4,hook=None,factory=None):
        if search!='a16d':raise ValueError('search must be a16d')
        num_actions=3 if num_actions is None else num_actions;family_bound=16 if family_bound is None else family_bound
        if _int(num_actions,'num_actions') not in (2,3,4):raise ValueError('num_actions must be 2, 3 or 4')
        if _int(family_bound,'family_bound')<1 or family_bound>A16D_MAX_BOUND:raise ValueError(f'family_bound must be in 1..{A16D_MAX_BOUND}')
        if _int(K,'K')<0:raise ValueError('K must be a non-negative int')
        if conflict_cap is None or budget_conflicts is None:raise ValueError('conflict_cap and budget_conflicts are required')
        if _int(conflict_cap,'conflict_cap')<1:raise ValueError('conflict_cap must be positive')
        if _int(budget_conflicts,'budget_conflicts')<1:raise ValueError('budget_conflicts must be positive')
        _num(wall_guard_case_s,'wall_guard_case_s');_num(wall_guard_call_s,'wall_guard_call_s')
        self.search='a16d';self.k=num_actions;self.N=family_bound;self.K=K;self.solver=solver;self.factory=factory or counted16d
        self.case=_Case(conflict_cap,budget_conflicts,wall_guard_case_s,wall_guard_call_s,hook)
        self.masks=[codes_mask(_obs(initial),S_BITS)];self.acts=[];self.used=0;self.rounds=[];self.P=None;self.n_lo=None
        self.stop=None;self.final=None;self._pending=None;self._rec=None;self._r=None;self._obs=[]

    def observe(self,action,reading):
        if isinstance(action,bool) or not isinstance(action,int) or action not in range(self.k):
            raise ValueError(f'action must be an int in 0..{self.k-1}')
        mk=codes_mask(_obs(reading),S_BITS)
        if self.stop is not None:raise RuntimeError('certifier has stopped; no further observations')
        if self._pending is not None:
            i=len(self._obs)
            if action!=self._pending[i]:raise ValueError(f'expected action {self._pending[i]} (step {i} of the proposed word)')
            self.acts.append(action);self.masks.append(mk);self._obs.append(mk)
            if len(self._obs)==len(self._pending):
                self.used+=len(self._pending);self._rec['obs']=list(self._obs);self.n_lo=max(self._r['n_min'],self.n_lo)
                self._pending=None;self._obs=[];self._rec=None;self._r=None
            return
        if self.P is not None:raise ValueError('after the first propose() only the proposed word may be observed')
        self.acts.append(action);self.masks.append(mk)

    def current(self):
        c=self.case
        return {'api':API,'search':'a16d','steps':len(self.acts),'used':self.used,'family_bound':self.N,'K':self.K,
                'pending':None if self._pending is None else list(self._pending),'pending_seen':len(self._obs),'n_lo':self.n_lo,
                'stopped':self.stop is not None,'stop':self.stop,'rounds':len(self.rounds),'conflicts_spent':c.spent,
                'conflict_cap':c.cap,'budget_conflicts':c.budget,'wall_guard':c.wall_guard}

    def propose(self):
        if self.stop is not None:return None
        if self._pending is not None:raise RuntimeError('the proposed word is not fully observed yet')
        if self.P is None:
            self.case.t0=perf_counter();self.P=Pool16D(self.k,1<<S_BITS,self.solver,self.factory);self.n_lo=self.P.lower(self.masks,self.acts)
        o=_Owner16D(self.case)
        r=stop_check14(self.masks,self.acts,self.k,1<<S_BITS,self.N,INF,self.n_lo,INF,self.solver,o,self.P)
        rec={'T':len(self.acts),'n_min':r['n_min'],'M1':r['model'],'s1':r['s1'],'future':r['future'],'start':r['start'],
             'query_walls':list(o.query_walls),'call_conflicts':list(o.call_conflicts),'call_capped':list(o.call_capped),
             'capped':o.capped,'check':r['stop']};self.rounds.append(rec)
        if r['stop']!='AMB':return self._finish(r['stop'],r)
        F=r['future'];M1=r['model'];M2=F['M2'];s1=r['s1'];s2=F['s2']
        w=distinguishing_word(M1[0],M1[1],s1,M2[0],M2[1],s2);rec.update(word=w,M2=M2,s2=s2)
        if w is None:raise AssertionError('certify16d: SAT M2 has no distinguishing word')
        if len(w)>self.K-self.used:return self._finish('K_spent',r)
        rec['pred1']=run_word(M1[0],M1[1],s1,w);rec['pred2']=run_word(M2[0],M2[1],s2,w)
        self._pending=list(w);self._rec=rec;self._r=r;self._obs=[];return list(w)

    def _finish(self,stop,r):
        self.stop=stop;self.final=r;ex=_ex(self.P);c=self.case
        self._record={'stop':stop,'masks':list(self.masks),'acts':list(self.acts),'used':self.used,'rounds':self.rounds,'final':r,
                      'guards':self.P.guards(),'sizes':sorted(self.P.inc),'clique':ex.get('clique'),'cube':ex.get('cube'),'audit':ex,
                      'conflicts_spent':c.spent,'conflict_cap':c.cap,'budget_conflicts':c.budget,'wall_guard':c.wall_guard,
                      'guard_events':list(c.guard_events)}
        self.P.close();return None

    def record(self):
        if self.stop is None:raise RuntimeError('not stopped')
        return self._record

    def result(self):
        if self.stop is None:raise RuntimeError('not stopped: call propose() until it returns None')
        f=self.final;c=self.case
        return {'api':API,'search':'a16d','label':LABEL_OF_STOP[self.stop],'stop':self.stop,'model':f['model'],'s1':f['s1'],
                'n_min':f['n_min'],'family_bound':self.N,'used':self.used,'steps':len(self.acts),'rounds':len(self.rounds),
                'calls':sum(len(r['call_conflicts']) for r in self.rounds),'conflicts':c.spent,
                'capped':sum(r['capped'] for r in self.rounds),'unknown':self.stop=='unknown','wall_guard':c.wall_guard,
                'soundness':soundness()}

    def close(self):
        if self.P is not None and self.stop is None:self.P.close();self.stop='closed'

    def __enter__(self):return self

    def __exit__(self,*a):self.close();return False


def certify16d(initial,actions,observations,num_actions=None,family_bound=None,**kw):
    """One stop check on the given trace (K=0: an ambiguous trace ends 'AMB' with no experiment)."""
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    c=Certifier16D(initial,num_actions,family_bound,'a16d',K=0,**kw)
    try:
        for a,o in zip(acts,obs):c.observe(a,o)
        c.propose();return c.result()
    finally:c.close()
