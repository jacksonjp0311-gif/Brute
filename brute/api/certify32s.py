"""Brute v0.63.0 embeddable certify interface, version 32s (BRUTE_PLAN_066).
Additive: brute/api/certify20s.py, certify32p.py and every earlier module are untouched and imported only.

certify/32s is the certify/20s SEQUENTIAL per-bit re-read front end (random-walk / SPRT stopping rule, threshold and settle imported
unchanged from certify/20s) on an UNCHANGED certify/32p instance, so the declared size bound may be 1..32 (certify/20s allows <= 20).
At family_bound <= 20 the inner certify/32p is certify/20p exactly, so certify/32s is certify/20s exactly (inner record equal).
    c = Certifier32S(initial_reads, num_actions=3, family_bound=24, read_bits=2, eps_bar=0.35, delta=0.001, conflict_cap=C, budget_conflicts=B)
    need = c.more(readings_so_far); c.observe(action, readings); c.propose(); c.result()     # as certify/20s
Guarantee (label 'ID' / 'IDF'): exact, CONDITIONAL on every settled reading being correct and on the true machine having at most
family_bound states (N <= 32). Under iid flips with eps <= eps_bar and state-preserving re-reads, every settled reading is correct
with probability >= 1 - delta (the certify/20s gambler's ruin bound, union over bits and observations).
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from brute.api import certify20s as S20
from brute.api import certify32p as P32
from brute.api.certify20s import Certifier20S,threshold,settle,READ_CAP
from brute.api.certify32p import Certifier32P,NODE_CAP,MAX_BOUND

API='brute.certify/32s'
__all__=['API','READ_CAP','NODE_CAP','MAX_BOUND','Certifier32S','threshold','settle','soundness']


def soundness(eps_bar,delta,read_bits):
    s=S20.soundness(eps_bar,delta,read_bits);s['family_bound']=P32.soundness()['family_bound'];return s


class Certifier32S(Certifier20S):
    def __init__(self,initial_reads=None,num_actions=None,family_bound=None,read_bits=2,eps_bar=0.15,delta=0.001,max_chunks=None,node_cap=NODE_CAP,**kw):
        if isinstance(read_bits,bool) or not isinstance(read_bits,int) or read_bits not in (2,3,4):raise ValueError('read_bits must be 2, 3 or 4')
        if isinstance(eps_bar,bool) or not isinstance(eps_bar,(int,float)) or not 0<=eps_bar<0.5:raise ValueError('eps_bar must be in [0, 0.5)')
        if isinstance(delta,bool) or not isinstance(delta,(int,float)) or not 0<delta<1:raise ValueError('delta must be in (0, 1)')
        self.sb=read_bits;self.eps_bar=eps_bar;self.delta=delta;self.t=0;self.ks=[];self.ms=[];self.settle_at=[]
        m=self._take(initial_reads)
        self.inner=Certifier32P(m,num_actions,family_bound,'a16d',read_bits=read_bits,max_chunks=max_chunks,node_cap=node_cap,**kw)

    def _extra(self,d):
        d=super()._extra(d);d['api']=API;d['inner_api']=P32.API;return d

    def result(self):
        d=self._extra(self.inner.result());d['soundness']=soundness(self.eps_bar,self.delta,self.sb);return d
