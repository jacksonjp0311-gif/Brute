"""Brute v0.69.0 embeddable certify interface, version 33h (BRUTE_PLAN_073). New file; certify32h.py and every earlier module are untouched
and imported only.

certify/33h is certify/32h with ONE change, a memory and time fix in the trace preprocessing and nothing in the logic: before every round
certify/20p computes the apartness of all trace positions, a greedy clique, the exact maximum apartness clique through position 0 and the
apart pair set. certify/20p holds each position's apart neighbours as a Python set, about T/1.4 integers per position, so at about 5,700
trace steps it needs about 1.4 GB of Python objects and a 1.8 GiB process dies there (study 072: 8 of 8 jobs at N = true+3 and 2 of 16 at
true+1 were killed, 7 + 2 of them by the memory cap). certify/33h holds the same relation as one big integer (bitset) per position
(brute/apart33.py, proven equal to the old functions on random traces in tests) and builds it by the same recurrence on whole rows.
The clique, the pins, the encoding, the policy, the stop rule, the labels and the guarantee are certify/32h's; the answer of every
preprocessing function is identical, so a run that finished under certify/32h gives the same trace and label here.
    c = Certifier33H(initial, num_actions=3, family_bound=12, read_bits=2, conflict_cap=C, budget_conflicts=B, K=40000, seed=s)
    w = c.propose(); for a in w: c.observe(a, reading); ...; c.result()          # as certify/32h
Guarantee (label 'ID' / 'IDF'): certify/32h's, exact, CONDITIONAL on noise-free readings and on the true machine having at most
family_bound states. No reset is used or assumed.
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from brute.api import certify20b as B20
from brute.api.certify20b import Certifier20B
from brute.api.certify20p import Pool63,NODE_CAP
from brute.api import certify32h as H32
from brute.api.certify32h import Certifier32H,homing_sequence,char_set,MAX_BOUND,BATCH_STEPS
from brute.apart33 import apart_bitsets,greedy_clique33,max_clique33,apart_pairs33

API='brute.certify/33h'
__all__=['API','MAX_BOUND','NODE_CAP','BATCH_STEPS','Certifier33H','Pool73','soundness']


def soundness():
    s=H32.soundness();s.update(api=API,preprocessing='bitset apartness, clique and pairs (identical answers to certify/32h)');return s


class Pool73(Pool63):
    """Pool63 whose per-round bookkeeping (clique validity check and apart pair set) uses bitsets."""
    def _update(self,masks,acts):
        if self._T==len(acts):return
        adj=apart_bitsets(masks,acts)
        if self.clique is None:self.clique=greedy_clique33(adj);self.colour={t:i for i,t in enumerate(self.clique)}
        else:
            for i,a in enumerate(self.clique):
                for b in self.clique[i+1:]:
                    if not (adj[a]>>b)&1:raise AssertionError('Pool73: clique lost apartness')
        self.future_pairs|=apart_pairs33(adj,masks);self._T=len(acts)


class Certifier33H(Certifier32H):
    def _p20(self):
        """Certifier20P.propose with bitset preprocessing (same clique, same pool lifecycle)."""
        if self.stop is not None or self._pending is not None:return Certifier20B.propose(self)
        adj=apart_bitsets(self.masks,self.acts);cur=None if self.P is None else self.P.clique
        mc,exact=max_clique33(adj,greedy_clique33(adj) if cur is None else cur,self.node_cap)
        if self.P is None:
            self.case.t0=B20.perf_counter();self.P=Pool73(self.k,self.m,self.solver,self.factory,mc);self.n_lo=self.P.lower(self.masks,self.acts)
            self.repins.append([len(self.acts),None,len(mc),exact]);self.clique=list(mc)
        elif len(mc)>len(cur):
            self.guards_closed+=self.P.guards();self.P.close()
            self.P=Pool73(self.k,self.m,self.solver,self.factory,mc);self.n_lo=max(self.n_lo,self.P.lower(self.masks,self.acts))
            self.repins.append([len(self.acts),len(cur),len(mc),exact]);self.clique=list(mc)
        return Certifier20B.propose(self)

    def propose(self):
        # certify/32h.propose with the base proposal taken from _p20 (the one changed call)
        w=self._p20()
        if w is None:return None
        return self._batch_after(w)

    def _batch_after(self,w):
        import itertools
        from brute.api.certify32h import _norm,_path
        r=self._r;T,E=_norm(r['model']);s=r['s1']
        for a in w:s=T[s][a]
        key=(tuple(map(tuple,T)),tuple(E))
        if self.cursor is None or self.cursor[0]!=key:self.cursor=(key,self._suite(T,E),homing_sequence(T,E))
        _,gen,h=self.cursor;h=list(h or [])
        room=self.K-self.used-len(w);batch=[];depths=[]
        while len(batch)<self.batch_steps:
            d,(t,u,e)=next(gen)
            q=s
            for a in h:q=T[q][a]
            p=_path(T,q,t)
            if p is None:continue
            seg=h+p+list(u)+list(e)
            if len(batch)+len(seg)>room:break
            batch+=seg;depths.append(d)
            for a in seg:s=T[s][a]
        self.batches.append({'round':len(self.rounds),'h':h,'steps':len(batch),'segments':len(depths),'max_depth':max(depths) if depths else None})
        self._pending=list(w)+batch;return list(self._pending)

    def current(self):
        d=super().current();d['api']=API;return d

    def result(self):
        d=super().result();d['api']=API;d['soundness']=soundness();return d
