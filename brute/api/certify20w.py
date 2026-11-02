"""Brute v0.59.0 embeddable certify interface, version 20w (BRUTE_PLAN_062; pre-run deviation #198 fixes the readings below).
Additive: brute/api/certify20b.py, certify16e.py, certify16d.py and every earlier module are untouched and imported only.

certify/20w is certify/20b (conflict-counted A16 declared-N exact identifier at read_bits 2, 3 or 4) with ONE change, the action
policy: after each word w that the frozen certify/20b proposes (a word separating the two fitted rival machines), a fixed probe
word p is appended, so the proposal is w + p. Default p = (0, 1) (plan 062, declared without tuning). K counts every executed
action, probe actions included: if fewer than len(p) actions are left after w, only the first K - used - len(w) actions of p are
appended (none if no action is left). The solver, the encoding, observe(), the stop rule and result() are the frozen certify/20b
ones, so every trace is a valid certify/20b trace and the round record keeps the separating word w in 'word' (pred1 / pred2 cover
w only; 'obs' holds the readings of w + p). probe_word=() gives certify/20b record-for-record.
    c = Certifier20W(initial, num_actions=3, family_bound=20, read_bits=2, probe_word=(0, 1), conflict_cap=C, budget_conflicts=B)
Guarantee (label 'ID' / 'IDF'): exact, CONDITIONAL on noise-free readings and on the true machine having at most family_bound
states (declared N <= 20). Every rival with at most N states consistent with the trace was ruled out by an UNSAT proof.
Why a size bound is needed (Inferred): a larger machine can copy the true machine on every visited state and differ only on
states the trace never reached, so no finite trace rules out every larger machine.
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from brute.api.certify8 import _int
from brute.api import certify20b as B
from brute.api.certify20b import Certifier20B,counted16d,READ_BITS

API='brute.certify/20w'
SEARCHES=('a16d',)
PROBE_WORD=(0,1)
__all__=['API','SEARCHES','PROBE_WORD','READ_BITS','Certifier20W','certify20w','soundness','counted16d']


def soundness(**kw):
    s=B.soundness();s['policy']='probe-word windows: each proposed separating word is followed by a fixed probe word (K counts it)';return s


class Certifier20W(Certifier20B):
    def __init__(self,initial=None,num_actions=None,family_bound=None,search='a16d',read_bits=2,max_chunks=None,probe_word=PROBE_WORD,**kw):
        super().__init__(initial,num_actions,family_bound,search,read_bits=read_bits,max_chunks=max_chunks,**kw)
        if isinstance(probe_word,(str,bytes)) or not isinstance(probe_word,(tuple,list)):raise ValueError('probe_word must be a tuple of actions')
        p=tuple(probe_word)
        for a in p:
            if _int(a,'probe_word action') not in range(self.k):raise ValueError(f'probe_word actions must be ints in 0..{self.k-1}')
        self.probe_word=p

    def propose(self):
        w=super().propose()
        if w is None:return None
        tail=list(self.probe_word[:max(0,self.K-self.used-len(w))])
        if tail:self._pending=list(w)+tail;self._rec['probe']=tail
        return list(self._pending)

    def current(self):
        d=super().current();d['api']=API;d['probe_word']=list(self.probe_word);return d

    def result(self):
        d=super().result();d['api']=API;d['probe_word']=list(self.probe_word);d['soundness']=soundness();return d


def certify20w(initial,actions,observations,num_actions=None,family_bound=None,read_bits=2,**kw):
    """One stop check on the given trace (K=0: an ambiguous trace ends 'AMB' with no experiment); the probe word never runs."""
    acts=list(actions);obs=list(observations)
    if len(obs)!=len(acts):raise ValueError('need one observation per action')
    c=Certifier20W(initial,num_actions,family_bound,'a16d',read_bits=read_bits,K=0,**kw)
    try:
        for a,o in zip(acts,obs):c.observe(a,o)
        c.propose();return c.result()
    finally:c.close()
