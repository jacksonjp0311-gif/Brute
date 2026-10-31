"""Brute v0.51.0 embeddable certify interface, version 20t (BRUTE_PLAN_054 as amended pre-data by BRUTE_PLAN_054a; pre-run
deviation #181 fixes the readings below). Additive: brute/api/certify16e.py, certify16d.py and every earlier module are untouched
and imported only.

certify/20t is certify/16e (A16: first-visit symmetry clauses, apartness clauses, the cube split on capped queries, chunked
conflict resume, conflict-only stop) with ONE change to the search: the rival queries ('future', then 'start') are asked ONCE,
on the size-N instance, instead of at every size n_min..N. The least-machine search (sizes upward from n_lo) is unchanged.
There is NO fixed-colour clique (amendment 054a: study-041 GAUD_loc isolated the fixed-colour clique, encaudit16 E2, as the cause
of the GINC15 decision loss, 3/3 repeats, and of a 4.18x [2.53, 6.46] call-wall cost; A16 dropped it).
Why one query at N is enough (Exact): a rival with n' <= N states that is consistent with the trace and separates from M1 becomes an
N-state rival by adding N - n' states the trace never visits; first-visit numbering and apartness only constrain visited states, so
the padded rival satisfies the size-N instance and separates on the same word. Hence the size-N rival query is UNSAT iff every
size n_min..N rival query is UNSAT, and a SAT model is a rival with at most N states. Stop-check verdicts equal certify/16e's;
the rival model M2, and so the next experiment, may differ.
    c = Certifier20T(initial, num_actions=3, family_bound=20, conflict_cap=C, budget_conflicts=B, max_chunks=None)
Guarantee (label 'ID' / 'IDF'): exact, CONDITIONAL on noise-free readings and on the true machine having at most family_bound
states (declared N <= 20). Every rival with at most N states consistent with the trace was ruled out by an UNSAT proof.
Why a size bound is needed (Inferred): a larger machine can copy the true machine on every visited state and differ only on
states the trace never reached, so no finite trace rules out every larger machine.
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from time import perf_counter
from brute.api.certify16 import LABEL_OF_STOP,S_BITS
from brute.api import certify16e as E
from brute.api.certify16d import _Owner16D,INF,A16D_MAX_BOUND,CCounted,counted16d
from brute.api.certify16e import Certifier16E,Pool16E
from brute.scalesearch import simulate
from brute.scalesearch8 import distinguishing_word,run_word
from brute.scalesearch9 import word_len9
from brute.scalesearch14 import least14,differ14

API='brute.certify/20t'
SEARCHES=('a20t',)
__all__=['API','SEARCHES','A16D_MAX_BOUND','Certifier20T','certify20t','soundness','search20t','stop_check20t','counted16d','CCounted']


def soundness(**kw):
    s=E.soundness();s['search']='a20t';s['rival']='once at size N (padding argument; verdict equal to sizes n_min..N)';s['clique']='none'
    return s


def search20t(o,P,masks,acts,n_min,N,M1,s1,mode,deadline):
    """search14's result shape with ONE differ14 query at size N (n_min <= N)."""
    L=word_len9(N,len(M1[0]));ver=[]
    res=lambda **kw:{'found':False,'unknown':False,'n':None,'M2':None,'s2':None,'word_sat':None,'verdicts':ver,'L':L,**kw}
    if n_min>N:return res()
    f,M2,s2,w=differ14(o,P,masks,acts,N,M1,s1,mode,L,deadline)
    if f is None:ver.append([N,'UNKNOWN']);return res(unknown=True)
    if f:ver.append([N,'SAT']);return res(found=True,n=N,M2=M2,s2=s2,word_sat=w)
    ver.append([N,'UNSAT']);return res()


def stop_check20t(masks,acts,k,N,deadline,n_lo,o,P):
    """stop_check14 on the given pool with search20t in place of search14."""
    res={'n_min':None,'model':None,'s1':None,'future':None,'start':None}
    out=lambda stop:{'stop':stop,**res,'query_walls':o.query_walls,'capped':o.capped}
    st,n,M1=least14(o,P,masks,acts,N,deadline,n_lo)
    if st!='ok':return out(st)
    s1=simulate(M1[0],M1[1],acts,masks)[1];res.update(n_min=n,model=M1,s1=s1)
    F=search20t(o,P,masks,acts,n,N,M1,s1,'future',deadline);res['future']=F
    if F['unknown']:return out('unknown')
    if F['found']:return out('AMB')
    S=search20t(o,P,masks,acts,n,N,M1,s1,'start',deadline);res['start']=S
    if S['unknown']:return out('unknown')
    return out('IDF' if S['found'] else 'ID')


class Certifier20T(Certifier16E):
    def __init__(self,initial=None,num_actions=None,family_bound=None,search='a20t',max_chunks=None,**kw):
        if search!='a20t':raise ValueError('search must be a20t')
        super().__init__(initial,num_actions,family_bound,'a16d',max_chunks,**kw);self.search='a20t'

    def _round(self):
        """certify/16d's propose body with stop_check20t."""
        if self.stop is not None:return None
        if self._pending is not None:raise RuntimeError('the proposed word is not fully observed yet')
        if self.P is None:
            self.case.t0=perf_counter();self.P=Pool16E(self.k,1<<S_BITS,self.solver,self.factory);self.n_lo=self.P.lower(self.masks,self.acts)
        o=_Owner16D(self.case)
        r=stop_check20t(self.masks,self.acts,self.k,self.N,INF,self.n_lo,o,self.P)
        rec={'T':len(self.acts),'n_min':r['n_min'],'M1':r['model'],'s1':r['s1'],'future':r['future'],'start':r['start'],
             'query_walls':list(o.query_walls),'call_conflicts':list(o.call_conflicts),'call_capped':list(o.call_capped),
             'capped':o.capped,'check':r['stop']};self.rounds.append(rec)
        if r['stop']!='AMB':return self._finish(r['stop'],r)
        F=r['future'];M1=r['model'];M2=F['M2'];s1=r['s1'];s2=F['s2']
        w=distinguishing_word(M1[0],M1[1],s1,M2[0],M2[1],s2);rec.update(word=w,M2=M2,s2=s2)
        if w is None:raise AssertionError('certify20t: SAT M2 has no distinguishing word')
        if len(w)>self.K-self.used:return self._finish('K_spent',r)
        rec['pred1']=run_word(M1[0],M1[1],s1,w);rec['pred2']=run_word(M2[0],M2[1],s2,w)
        self._pending=list(w);self._rec=rec;self._r=r;self._obs=[];return list(w)

    def propose(self):
        if self.stop is None and self._pending is None and self.P is None:
            self.case.t0=perf_counter();self.P=Pool16E(self.k,1<<S_BITS,self.solver,self.factory);self.n_lo=self.P.lower(self.masks,self.acts)
        nr=len(self.rounds);nc=len(self.case.calls_log);w=self._round()
        if len(self.rounds)>nr:
            log=self.case.calls_log[nc:];rec=self.rounds[-1]
            rec['call_chunks']=[x[0] for x in log];rec['chunk_conflicts']=[list(x[1]) for x in log];rec['chunk_walls']=[list(x[2]) for x in log]
        if self.stop is not None and getattr(self,'_record',None) is not None:self._extend()
        return w

    def current(self):
        d=super().current();d['api']=API;d['search']='a20t';return d

    def result(self):
        d=super().result();d['api']=API;d['search']='a20t';d['soundness']=soundness();return d


def certify20t(initial,actions,observations,num_actions=None,family_bound=None,**kw):
    """One stop check on the given trace (K=0: an ambiguous trace ends 'AMB' with no experiment)."""
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    c=Certifier20T(initial,num_actions,family_bound,'a20t',K=0,**kw)
    try:
        for a,o in zip(acts,obs):c.observe(a,o)
        c.propose();return c.result()
    finally:c.close()
