"""Brute v0.70.0 embeddable certify interface, version 34h (BRUTE_PLAN_074). New file; certify33h.py and every earlier module are untouched
and imported only.

certify/34h is certify/33h with ONE change, the experiment policy: after every AMB stop check the proposed word is ONLY the engine's
separating word w (as certify/32p / the _p20 path of certify/33h). The 400-step homing-based test batch that certify/32h and
certify/33h append is NOT appended. The bitset trace preprocessing, clique pins, encoding, stop rule, labels and guarantee are
certify/33h's (hence certify/32h's). The batch was a heuristic only; the certificate never assumed the homing sequence was homing
for the target. Study 073's loose-N kills were dominated by SAT/memory at long traces; the batch added about 400 steps per round.
    c = Certifier34H(initial, num_actions=3, family_bound=12, read_bits=2, conflict_cap=C, budget_conflicts=B, K=40000, seed=s)
    w = c.propose(); for a in w: c.observe(a, reading); ...; c.result()
Guarantee (label 'ID' / 'IDF'): certify/33h's, exact, CONDITIONAL on noise-free readings and on the true machine having at most
family_bound states. No reset is used or assumed.
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from brute.api.certify33h import Certifier33H,Pool73,MAX_BOUND,NODE_CAP,soundness as soundness33
from brute.api.certify32h import BATCH_STEPS

API='brute.certify/34h'
__all__=['API','MAX_BOUND','NODE_CAP','BATCH_STEPS','Certifier34H','Pool73','soundness']


def soundness():
    s=soundness33();s.update(api=API,policy='separating word only (no homing-based test batch); bitset preprocess as certify/33h');return s


class Certifier34H(Certifier33H):
    def propose(self):
        """Separating word from the bitset-preprocessed pool; no homing batch."""
        return self._p20()

    def current(self):
        d=super().current();d['api']=API;return d

    def result(self):
        d=super().result();d['api']=API;d['soundness']=soundness();d['batches']=0;return d
