"""Brute v0.55.0 embeddable certify interface, version 20b (BRUTE_PLAN_058; the pre-run deviation fixes the readings below).
Additive: brute/api/certify16e.py, certify16d.py and every earlier module are untouched and imported only.

certify/20b is certify/16e (conflict-counted, chunked-resume A16 declared-N exact identifier) with ONE change: the reading width is
a parameter. A reading is a tuple of read_bits entries, each 0, 1 or None (unknown bit); the machine emits one of m = 2**read_bits
codes (bit j of code c is (c >> (read_bits-1-j)) & 1). read_bits 2 is exactly certify/16e. Encoding, clauses, cube split, rival
query, separating word, K, conflict ledger, wall guards and labels are certify/16e's.
    c = Certifier20B(initial, num_actions=3, family_bound=20, read_bits=4, conflict_cap=C, budget_conflicts=B)
    c.observe(a, reading); w = c.propose(); ...; c.result()        # as certify/16e
Guarantee (label 'ID' / 'IDF'): exact, CONDITIONAL on noise-free readings and on the true machine having at most family_bound
states (declared N <= 20). Every rival with at most N states consistent with the trace was ruled out by an UNSAT proof.
Why a size bound is needed (Inferred): a larger machine can copy the true machine on every visited state and differ only on
states the trace never reached, so no finite trace rules out every larger machine.
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from time import perf_counter
from brute.api.certify8 import _int
from brute.api import certify16e as E
from brute.api.certify16d import _Owner16D,INF,A16D_MAX_BOUND,CCounted,counted16d
from brute.api.certify16e import Certifier16E,Pool16E
from brute.region import codes_mask
from brute.scalesearch8 import distinguishing_word,run_word
from brute.scalesearch14 import stop_check14

API='brute.certify/20b'
SEARCHES=('a16d',)
READ_BITS=(2,3,4)
__all__=['API','SEARCHES','READ_BITS','A16D_MAX_BOUND','Certifier20B','certify20b','soundness','reading_of','counted16d','CCounted']


def soundness(**kw):
    s=E.soundness();s['readings']='read_bits-wide bit tuples (2, 3 or 4 bits)';return s


def reading_of(code,read_bits):
    """The bit tuple of a code (bit j = (code >> (read_bits-1-j)) & 1)."""
    return tuple((code>>(read_bits-1-j))&1 for j in range(read_bits))


def _obs_b(o,sb):
    if not isinstance(o,(tuple,list)) or len(o)!=sb or any(isinstance(x,bool) or x not in (0,1,None) for x in o):
        raise ValueError(f'observation must be a tuple of {sb} bits 0 / 1 / None')
    return tuple(o)


class Certifier20B(Certifier16E):
    def __init__(self,initial=None,num_actions=None,family_bound=None,search='a16d',read_bits=2,max_chunks=None,**kw):
        if isinstance(read_bits,bool) or not isinstance(read_bits,int) or read_bits not in READ_BITS:
            raise ValueError('read_bits must be 2, 3 or 4')
        sb=read_bits;ini=_obs_b(initial,sb)
        super().__init__((0,0),num_actions,family_bound,search,max_chunks=max_chunks,**kw)
        self.sb=sb;self.m=1<<sb;self.masks=[codes_mask(ini,sb)]

    def observe(self,action,reading):
        if isinstance(action,bool) or not isinstance(action,int) or action not in range(self.k):
            raise ValueError(f'action must be an int in 0..{self.k-1}')
        mk=codes_mask(_obs_b(reading,self.sb),self.sb)
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

    def _propose_d(self):
        """certify/16d's propose() with m = 2**read_bits (the pool is built in propose() below)."""
        if self.stop is not None:return None
        if self._pending is not None:raise RuntimeError('the proposed word is not fully observed yet')
        o=_Owner16D(self.case)
        r=stop_check14(self.masks,self.acts,self.k,self.m,self.N,INF,self.n_lo,INF,self.solver,o,self.P)
        rec={'T':len(self.acts),'n_min':r['n_min'],'M1':r['model'],'s1':r['s1'],'future':r['future'],'start':r['start'],
             'query_walls':list(o.query_walls),'call_conflicts':list(o.call_conflicts),'call_capped':list(o.call_capped),
             'capped':o.capped,'check':r['stop']};self.rounds.append(rec)
        if r['stop']!='AMB':return self._finish(r['stop'],r)
        F=r['future'];M1=r['model'];M2=F['M2'];s1=r['s1'];s2=F['s2']
        w=distinguishing_word(M1[0],M1[1],s1,M2[0],M2[1],s2);rec.update(word=w,M2=M2,s2=s2)
        if w is None:raise AssertionError('certify20b: SAT M2 has no distinguishing word')
        if len(w)>self.K-self.used:return self._finish('K_spent',r)
        rec['pred1']=run_word(M1[0],M1[1],s1,w);rec['pred2']=run_word(M2[0],M2[1],s2,w)
        self._pending=list(w);self._rec=rec;self._r=r;self._obs=[];return list(w)

    def propose(self):
        """certify/16e's propose() (chunk log per round) around _propose_d."""
        if self.stop is not None:return None
        if self._pending is not None:raise RuntimeError('the proposed word is not fully observed yet')
        if self.P is None:
            self.case.t0=perf_counter();self.P=Pool16E(self.k,self.m,self.solver,self.factory);self.n_lo=self.P.lower(self.masks,self.acts)
        nr=len(self.rounds);nc=len(self.case.calls_log);w=self._propose_d()
        if len(self.rounds)>nr:
            log=self.case.calls_log[nc:];rec=self.rounds[-1]
            rec['call_chunks']=[x[0] for x in log];rec['chunk_conflicts']=[list(x[1]) for x in log];rec['chunk_walls']=[list(x[2]) for x in log]
        if self.stop is not None and getattr(self,'_record',None) is not None:self._extend();self._record['read_bits']=self.sb
        return w

    def current(self):
        d=super().current();d['api']=API;d['read_bits']=self.sb;return d

    def result(self):
        d=super().result();d['api']=API;d['read_bits']=self.sb;d['soundness']=soundness();return d


def certify20b(initial,actions,observations,num_actions=None,family_bound=None,read_bits=2,**kw):
    """One stop check on the given trace (K=0: an ambiguous trace ends 'AMB' with no experiment)."""
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    c=Certifier20B(initial,num_actions,family_bound,'a16d',read_bits=read_bits,K=0,**kw)
    try:
        for a,o in zip(acts,obs):c.observe(a,o)
        c.propose();return c.result()
    finally:c.close()
