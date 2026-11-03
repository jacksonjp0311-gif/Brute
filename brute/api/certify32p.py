"""Brute v0.61.0 embeddable certify interface, version 32p (BRUTE_PLAN_064). Additive: brute/api/certify20p.py, certify32b.py and
every earlier module are untouched and imported only.

certify/32p is certify/20p (clique-anchored symmetry breaking: the exact maximum apartness clique through position 0 is pinned to
states 0..|C|-1 and re-pinned when it grows) with ONE change, the certify/32b one: this module owns the declared size bound and
accepts family_bound in 1..32. The certify/20p constructor is called with min(family_bound, 20) so the certify/16d argument check
passes, then the declared bound self.N is set to family_bound before any query is built (self.N is read only at query time; no
global is changed). At family_bound <= 20 it is certify/20p exactly.
    c = Certifier32P(initial, num_actions=3, family_bound=24, read_bits=2, conflict_cap=C, budget_conflicts=B)
    c.observe(a, reading); w = c.propose(); ...; c.result()        # as certify/20p
Guarantee (label 'ID' / 'IDF'): exact, CONDITIONAL on noise-free readings and on the true machine having at most family_bound
states (declared N <= 32). Every rival with at most N states consistent with the trace was ruled out by an UNSAT proof; the
pinning loses no machine (Exact: pairwise apart positions need distinct states; any machine can be relabelled into the pinned form).
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from brute.api.certify8 import _int
from brute.api import certify20p as P20
from brute.api.certify20p import Certifier20P,NODE_CAP
from brute.api.certify16d import A16D_MAX_BOUND

API='brute.certify/32p'
SEARCHES=('a16d',)
MAX_BOUND=32
__all__=['API','SEARCHES','MAX_BOUND','NODE_CAP','Certifier32P','certify32p','soundness']


def soundness(**kw):
    s=P20.soundness();s['family_bound']='declared N in 1..32 (this module owns the bound)';return s


class Certifier32P(Certifier20P):
    def __init__(self,initial=None,num_actions=None,family_bound=None,search='a16d',read_bits=2,max_chunks=None,node_cap=NODE_CAP,**kw):
        fb=16 if family_bound is None else family_bound
        if _int(fb,'family_bound')<1 or fb>MAX_BOUND:raise ValueError(f'family_bound must be in 1..{MAX_BOUND}')
        super().__init__(initial,num_actions,min(fb,A16D_MAX_BOUND),search,read_bits=read_bits,max_chunks=max_chunks,node_cap=node_cap,**kw)
        self.N=fb

    def current(self):
        d=super().current();d['api']=API;return d

    def result(self):
        d=super().result();d['api']=API;d['soundness']=soundness();return d


def certify32p(initial,actions,observations,num_actions=None,family_bound=None,read_bits=2,**kw):
    """One stop check on the given trace (K=0: an ambiguous trace ends 'AMB' with no experiment)."""
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    c=Certifier32P(initial,num_actions,family_bound,'a16d',read_bits=read_bits,K=0,**kw)
    try:
        for a,o in zip(acts,obs):c.observe(a,o)
        c.propose();return c.result()
    finally:c.close()
