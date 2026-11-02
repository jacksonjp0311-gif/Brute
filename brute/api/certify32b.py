"""Brute v0.57.0 embeddable certify interface, version 32b (BRUTE_PLAN_060; the pre-run deviation fixes the readings below).
Additive: brute/api/certify20b.py, certify16e.py, certify16d.py and every earlier module are untouched and imported only.

certify/32b is certify/20b (certify/16e with a configurable reading width) with ONE change: this module owns the declared size
bound and accepts family_bound in 1..32 (certify/16d refuses > 20). Encoding, clauses, cube split, rival query, separating word,
K, conflict ledger, wall guards, reading widths and labels are certify/20b's; at family_bound <= 20 it is certify/20b exactly.
How: the certify/20b constructor is called with min(family_bound, 20) so its argument check passes, then the declared bound
self.N is set to family_bound before any query is built (self.N is read only at query time; no global is changed).
    c = Certifier32B(initial, num_actions=3, family_bound=24, read_bits=4, conflict_cap=C, budget_conflicts=B)
    c.observe(a, reading); w = c.propose(); ...; c.result()        # as certify/20b
Guarantee (label 'ID' / 'IDF'): exact, CONDITIONAL on noise-free readings and on the true machine having at most family_bound
states (declared N <= 32). Every rival with at most N states consistent with the trace was ruled out by an UNSAT proof.
Why a size bound is needed (Inferred): a larger machine can copy the true machine on every visited state and differ only on
states the trace never reached, so no finite trace rules out every larger machine.
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from brute.api.certify8 import _int
from brute.api import certify20b as B20
from brute.api.certify20b import Certifier20B,READ_BITS,reading_of,counted16d,CCounted
from brute.api.certify16d import A16D_MAX_BOUND

API='brute.certify/32b'
SEARCHES=('a16d',)
MAX_BOUND=32
__all__=['API','SEARCHES','READ_BITS','MAX_BOUND','Certifier32B','certify32b','soundness','reading_of','counted16d','CCounted']


def soundness(**kw):
    s=B20.soundness();s['family_bound']='declared N in 1..32 (this module owns the bound)';return s


class Certifier32B(Certifier20B):
    def __init__(self,initial=None,num_actions=None,family_bound=None,search='a16d',read_bits=2,max_chunks=None,**kw):
        fb=16 if family_bound is None else family_bound
        if _int(fb,'family_bound')<1 or fb>MAX_BOUND:raise ValueError(f'family_bound must be in 1..{MAX_BOUND}')
        super().__init__(initial,num_actions,min(fb,A16D_MAX_BOUND),search,read_bits=read_bits,max_chunks=max_chunks,**kw)
        self.N=fb

    def current(self):
        d=super().current();d['api']=API;return d

    def result(self):
        d=super().result();d['api']=API;d['soundness']=soundness();return d


def certify32b(initial,actions,observations,num_actions=None,family_bound=None,read_bits=2,**kw):
    """One stop check on the given trace (K=0: an ambiguous trace ends 'AMB' with no experiment)."""
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    c=Certifier32B(initial,num_actions,family_bound,'a16d',read_bits=read_bits,K=0,**kw)
    try:
        for a,o in zip(acts,obs):c.observe(a,o)
        c.propose();return c.result()
    finally:c.close()
