"""Brute v0.43.0 embeddable certify interface, version 16 (BRUTE_PLAN_046; pre-run deviation #165 fixes the readings below).
Additive: brute/api/certify14.py and every earlier module are untouched and imported only.

search='a16' (default): the A16 declared-N exact identifier (brute.scalesearch16: Pool16 instances with first-visit and apartness
clauses, cube split on capped queries; least machine, rival searches at every size n_min..N, shortest separating word, K, case
budget, per-call cap) exposed step by step. The host owns the world and the clock; this module only proposes experiments:
    c = Certifier16(initial, num_actions=3, family_bound=16)       # initial: the first reading, a pair of bits 0 / 1 / None
    c.observe(action, reading)                                       # passive prefix, one call per step
    w = c.propose()                                                  # next experiment word (list of actions) or None when stopped
    for a in w: c.observe(a, world.step(a))                          # the host executes the word action by action
    c.result()                                                       # {'api': 'brute.certify/16', 'label', 'model', 'n_min', ...}
    certify16(initial, actions, observations, ...)                   # one-shot: one stop check on a fixed trace (no experiments)
The loop is active16's loop split at its observe calls, in the same order (stop check; on AMB the separating word, the K check,
the predicted outputs; then the word's observations; then n_lo = max(n_min, n_lo)), so a host that executes every proposed word
reproduces active16 on the same trace and clock.
search='region', 's2', 's3', 's4': brute.api.certify14 unchanged; Certifier16 and certify16 return certify14's objects and outputs
as they are (their 'api' field stays 'brute.certify/14', the API that computed them). certify16's default search is 'a16', so
certify14's default 'region' must be named explicitly; for delegated searches the other defaults are certify14's.

Guarantee (label 'ID' / 'IDF'): exact, CONDITIONAL on noise-free readings and on the true machine having at most family_bound
states (the declared size N). Every rival with at most N states consistent with the trace was ruled out by an UNSAT proof; a
capped call or a passed deadline gives 'IDU' (unknown), never a certificate. Why a size bound is needed (Inferred): from finite
data a larger machine can always copy the true machine on every visited state and differ only on states the trace never
reached, so no finite trace rules out every larger machine; some size bound is inherent (study 045: the n_min+delta bound
was sound but decided 0/12 16-state worlds).
Host-agnostic: no I/O, network, threads, child processes or global state. The per-call cap is the solver's chunked conflict
budget checked against the clock; a host may pass `hook` (interrupt at the cap) and `factory` (solver supplier).
"""
from __future__ import annotations
from time import perf_counter
from brute.api.certify import _obs
from brute.api.certify8 import _int,_num
from brute.api.certify14 import Certifier14,certify14,SEARCHES as SEARCHES14
from brute.region import codes_mask
from brute.scalesearch4 import SOLVER4
from brute.scalesearch8 import distinguishing_word,run_word
from brute.scalesearch10 import _Owner10
from brute.scalesearch14 import QUERY_S14,K14,BUDGET14,stop_check14
from brute.scalesearch16 import Pool16,_ex,native

API='brute.certify/16'
SEARCHES=('a16',)+tuple(SEARCHES14)
A16_MAX_BOUND=16
S_BITS=2
LABEL_OF_STOP={'ID':'ID','IDF':'IDF','AMB':'AMB','K_spent':'AMB','unknown':'IDU'}
__all__=['API','SEARCHES','A16_MAX_BOUND','LABEL_OF_STOP','Certifier16','certify16','soundness']


def soundness(search='a16',**kw):
    if search!='a16':
        from brute.api.certify14 import soundness as s14
        return s14(kw.get('delta',0.01),kw.get('method','betting'),search)
    return {'kind':'exact','method':'exact','search':'a16','anytime':False,
            'conditional_on':'noise-free readings and true size <= family_bound (the declared N)',
            'why_bounded':'Inferred: a larger machine can copy the true machine on every visited state, so finite data never rules out all larger machines'}


class Certifier16:
    def __new__(cls,initial=None,num_actions=None,family_bound=None,search='a16',**kw):
        """search != 'a16' returns brute.api.certify14.Certifier14(initial, search=search, **given arguments) with certify14's
        own defaults for anything not given (num_actions 2, family_bound 4)."""
        if not isinstance(search,str) or search not in SEARCHES:raise ValueError('search must be one of '+', '.join(SEARCHES))
        if search!='a16':return Certifier14(initial,search=search,**_given(num_actions,family_bound,kw))
        return object.__new__(cls)

    def __init__(self,initial=None,num_actions=None,family_bound=None,search='a16',K=K14,budget_s=BUDGET14,query_s=QUERY_S14,
                 deadline=None,solver=SOLVER4,hook=None,factory=None):
        num_actions=3 if num_actions is None else num_actions;family_bound=16 if family_bound is None else family_bound
        if _int(num_actions,'num_actions') not in (2,3,4):raise ValueError('num_actions must be 2, 3 or 4')
        if _int(family_bound,'family_bound')<1 or family_bound>A16_MAX_BOUND:raise ValueError(f'family_bound must be in 1..{A16_MAX_BOUND}')
        if _int(K,'K')<0:raise ValueError('K must be a non-negative int')
        _num(budget_s,'budget_s');_num(query_s,'query_s')
        if not query_s>0:raise ValueError('query_s must be positive')
        if not budget_s>0:raise ValueError('budget_s must be positive')
        if deadline is not None:_num(deadline,'deadline')
        self.search='a16';self.k=num_actions;self.N=family_bound;self.K=K;self.budget_s=budget_s;self.query_s=query_s
        self.deadline=deadline;self.solver=solver;self.hook=hook;self.factory=factory or native
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

    def propose(self):
        """Run the stop check on the current trace. Returns the next word to execute, or None once stopped."""
        if self.stop is not None:return None
        if self._pending is not None:raise RuntimeError('the proposed word is not fully observed yet')
        if self.P is None:
            if self.deadline is None:self.deadline=perf_counter()+self.budget_s
            self.P=Pool16(self.k,1<<S_BITS,self.solver,self.factory);self.n_lo=self.P.lower(self.masks,self.acts)
        o=_Owner10(self.query_s,self.hook)
        r=stop_check14(self.masks,self.acts,self.k,1<<S_BITS,self.N,self.deadline,self.n_lo,self.query_s,self.solver,o,self.P)
        rec={'T':len(self.acts),'n_min':r['n_min'],'M1':r['model'],'s1':r['s1'],'future':r['future'],'start':r['start'],
             'query_walls':list(o.query_walls),'capped':o.capped,'check':r['stop']};self.rounds.append(rec)
        if r['stop']!='AMB':return self._finish(r['stop'],r)
        F=r['future'];M1=r['model'];M2=F['M2'];s1=r['s1'];s2=F['s2']
        w=distinguishing_word(M1[0],M1[1],s1,M2[0],M2[1],s2);rec.update(word=w,M2=M2,s2=s2)
        if w is None:raise AssertionError('certify16: SAT M2 has no distinguishing word')
        if len(w)>self.K-self.used:return self._finish('K_spent',r)
        rec['pred1']=run_word(M1[0],M1[1],s1,w);rec['pred2']=run_word(M2[0],M2[1],s2,w)
        self._pending=list(w);self._rec=rec;self._r=r;self._obs=[];return list(w)

    def _finish(self,stop,r):
        self.stop=stop;self.final=r;ex=_ex(self.P)
        self._record={'stop':stop,'masks':list(self.masks),'acts':list(self.acts),'used':self.used,'rounds':self.rounds,'final':r,
                      'guards':self.P.guards(),'sizes':sorted(self.P.inc),'clique':ex.get('clique'),'cube':ex.get('cube'),'audit':ex}
        self.P.close();return None

    def record(self):
        """active16's return dict for a stopped certifier (same keys), for hosts that audit the run."""
        if self.stop is None:raise RuntimeError('not stopped')
        return self._record

    def result(self):
        if self.stop is None:raise RuntimeError('not stopped: call propose() until it returns None')
        f=self.final
        return {'api':API,'search':'a16','label':LABEL_OF_STOP[self.stop],'stop':self.stop,'model':f['model'],'s1':f['s1'],
                'n_min':f['n_min'],'family_bound':self.N,'used':self.used,'steps':len(self.acts),'rounds':len(self.rounds),
                'calls':sum(len(r['query_walls']) for r in self.rounds),'unknown':self.stop=='unknown','soundness':soundness('a16')}

    def close(self):
        if self.P is not None and self.stop is None:self.P.close();self.stop='closed'

    def __enter__(self):return self

    def __exit__(self,*a):self.close();return False


def _given(num_actions,family_bound,kw):
    d=dict(kw)
    if num_actions is not None:d['num_actions']=num_actions
    if family_bound is not None:d['family_bound']=family_bound
    return d


def certify16(initial,actions,observations,num_actions=None,family_bound=None,search='a16',**kw):
    """search='a16': one stop check on the given trace (K=0, so an ambiguous trace ends 'AMB' with no experiment).
    Other searches: brute.api.certify14.certify14 unchanged (same arguments and certify14's defaults, same output).
    a16 defaults: num_actions 3, family_bound 16."""
    if not isinstance(search,str) or search not in SEARCHES:raise ValueError('search must be one of '+', '.join(SEARCHES))
    if search!='a16':return certify14(initial,actions,observations,search=search,**_given(num_actions,family_bound,kw))
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    c=Certifier16(initial,num_actions,family_bound,'a16',K=0,**kw)
    try:
        for a,o in zip(acts,obs):c.observe(a,o)
        c.propose();return c.result()
    finally:c.close()
