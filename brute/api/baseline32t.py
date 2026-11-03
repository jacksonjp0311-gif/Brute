"""Brute v0.66.0 TEXTBOOK BASELINE (BRUTE_PLAN_070), NOT Brute's engine: reset-free learning in the style of Rivest and Schapire
(1993), homing sequence + one L* / Vasilevskii-Chow learner per homing output, using the unchanged certify/32r learner. New file.

A homing word h (starts empty) replaces the reset: before each query the host applies h and the learner keyed by the readings sigma
seen along h (the reading before h included) asks one word from 'its' start state. When a learner's tree is contradicted (the same
prefix, read from an origin with the same sigma, gives a different reading), h is proved NOT homing; h := h . (query prefix up to
the contradiction) and every learner restarts (Rivest-Schapire). No SAT and no version space are used.
    c = Baseline32T(initial_reading, num_actions=3, family_bound=8, read_bits=2, seed=s, step_cap=3000000)
    while (w := c.propose()) is not None:
        for a in w: c.observe(a, reading_after(a))
    c.result()
Labels: 'ID' (one learner passed its N-complete suite), 'EXCEEDS_N' (that learner saw more than N distinct rows), 'QCAP' (step cap).
Guarantee for 'ID' (textbook, CONDITIONAL): if the target is a deterministic Moore machine with <= N states AND h is a homing
sequence for it, the target state at the end of h with output sigma is equivalent to H. That h homes the target is NOT checked,
so the label can be wrong when h is not homing. Clean readings only.
Host-agnostic: no I/O, network, threads, child processes or global state."""
from __future__ import annotations
from brute.api.certify32r import Certifier32R,canonical

API='brute.baseline/32t'
STEP_CAP=3000000
__all__=['API','STEP_CAP','Baseline32T','soundness']


def soundness():
    return {'api':API,'engine':'textbook (Rivest-Schapire homing + L* + Vasilevskii-Chow), not Brute SAT','sat':False,'resets':False,
            'label_ID':'conditional on: <= family_bound states, h homing for the target (unchecked), clean readings'}


def _code(r):
    c=0
    for b in r:c=2*c+int(b)
    return c


class Baseline32T:
    def __init__(self,initial,num_actions=3,family_bound=8,read_bits=2,seed=0,step_cap=STEP_CAP,query_cap=10**9):
        self.k=num_actions;self.N=family_bound;self.sb=read_bits;self.seed=seed;self.cap=step_cap;self.qcap=query_cap
        self.last=tuple(initial);self.steps=0;self.h=[];self.L={};self.label=None;self.win=None
        self.h_history=[];self.restarts=0;self.queries=0;self.origin_step=None;self._plan=None;self._buf=[];self.H=None

    def _new(self):return Certifier32R(self.k,self.N,self.sb,None,None,seed=self.seed,query_cap=self.qcap)

    def propose(self):
        if self.label is not None:return None
        if self.steps>=self.cap:self.label='QCAP';return None
        self._plan=('h',);self._buf=[self.last];return list(self.h) if self.h else self._after_h()

    def _after_h(self):
        sig=tuple(_code(r) for r in self._buf);L=self.L.get(sig)
        if L is None:L=self.L[sig]=self._new()
        w=L.propose()
        if w is None:
            self.label=L.label;self.win=sig;self.H=L.H;self.origin_step=self.steps;self._plan=None;return None
        self.queries+=1;self._plan=('w',sig,tuple(w),self.steps);self._buf=[self.last];return list(w) if w else self._finish_word()

    def _finish_word(self):
        _,sig,w,o=self._plan;L=self.L[sig];rs=self._buf
        for i in range(len(w)+1):
            p=w[:i]
            if L.wants(p):L.take(p,[rs[i]])
            elif L.tree[p]!=_code(rs[i]):
                self.h=self.h+list(p);self.h_history.append({'step':self.steps,'h':list(self.h)});self.L={};self.restarts+=1
                break
        self.last_origin=o;return self.propose()

    def observe(self,a,reading):
        if self._plan is None:raise ValueError('nothing proposed')
        self.steps+=1;self.last=tuple(reading);self._buf.append(self.last)

    def next(self):
        """Call after the host has run every action of the proposed word; returns the next word or None."""
        if self._plan[0]=='h':
            if len(self._buf)!=len(self.h)+1:raise ValueError('homing word not complete')
            return self._after_h()
        if len(self._buf)!=len(self._plan[2])+1:raise ValueError('query word not complete')
        return self._finish_word()

    def result(self):
        if self.label is None:raise ValueError('not finished')
        d={'api':API,'label':self.label,'family_bound':self.N,'steps':self.steps,'h':list(self.h),'restarts':self.restarts,
           'queries':self.queries,'soundness':soundness()}
        if self.label=='ID':
            ct,ce=canonical(*self.H);d.update(n=len(ct),transitions=ct,emissions=ce,origin_step=self.origin_step,sigma=list(self.win))
        return d

    def record(self):
        d=self.result();d.update(seed=self.seed,step_cap=self.cap,h_history=self.h_history,learners=len(self.L),
            learner_queries={','.join(map(str,s)):L.queries for s,L in self.L.items()});return d
