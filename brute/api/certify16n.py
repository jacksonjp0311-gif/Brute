"""Brute v0.47.0 embeddable certify interface, version 16n (BRUTE_PLAN_050; pre-run deviation #173 fixes the readings below).
Additive: brute/api/certify16e.py and every earlier module are untouched and imported only.

certify/16n is a repeated-reading majority front end on an UNCHANGED certify/16e instance. Each observation is read k times; each
output bit is set to its majority over the k readings (k odd, so no ties) and the majority reading is passed to certify/16e.
k rule (plan design.api, deviation #173): observation t (t = 1 for the initial reading) gets the smallest odd k with
    bits * exp(-2 k (1/2 - eps_bar)^2) <= delta * 6 / (pi^2 t^2),
so by Hoeffding per bit and a union bound over bits and over every t (sum of 6/(pi^2 t^2) = 1) the chance that ANY majority bit
of the whole trace is wrong is at most delta, for any trace length (Exact, conditional on the iid model below). This is the
plan's 'T * exp(-2 k (0.5 - eps_bar)^2) <= delta' rule made anytime, because the trace length T is not known in advance.
    c = Certifier16N(initial_reads, num_actions=3, family_bound=12, eps_bar=0.10, delta=0.001, conflict_cap=C, budget_conflicts=B)
    k = c.reads_needed(); c.observe(action, [reading_1, ..., reading_k])
reads=<odd int> fixes k for every observation instead (reads=1 with noise-free readings reproduces certify/16e exactly).
Guarantee (label 'ID' / 'IDF'): exact, CONDITIONAL on every majority reading being correct and on the true machine having at most
family_bound states. If each reading bit is flipped independently with probability eps <= eps_bar (the attested noise model) and
re-reading the current observation does not change the hidden state, every majority is correct with probability >= 1 - delta.
Why a size bound is needed (Inferred): a larger machine can copy the true machine on every visited state and differ only on
states the trace never reached, so no finite trace rules out every larger machine.
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
import math
from brute.api.certify8 import _int
from brute.api.certify16 import S_BITS
from brute.api import certify16e as E

API='brute.certify/16n'
__all__=['API','Certifier16N','reads_for','majority','soundness']


def reads_for(t,eps_bar,delta,bits=S_BITS):
    """Smallest odd k with bits*exp(-2k(1/2-eps_bar)^2) <= delta*6/(pi^2 t^2)."""
    if _int(t,'t')<1:raise ValueError('t must be a positive int')
    g=2.0*(0.5-eps_bar)**2;need=math.log(bits*math.pi**2*t*t/(6.0*delta))/g
    k=max(1,math.ceil(need-1e-12))
    if k%2==0:k+=1
    return k


def _bits(r):
    t=tuple(r)
    if len(t)!=S_BITS or any(b not in (0,1) or isinstance(b,bool) for b in t):raise ValueError(f'a reading is a tuple of {S_BITS} bits (0/1)')
    return t


def majority(readings):
    """Per-bit majority of an odd number of readings; returns (reading, per-bit one-counts)."""
    rs=[_bits(r) for r in readings];k=len(rs)
    if k<1 or k%2==0:raise ValueError('need an odd number of readings')
    ones=[sum(r[j] for r in rs) for j in range(S_BITS)];return tuple(1 if 2*o>k else 0 for o in ones),ones


def soundness(eps_bar,delta,reads):
    s=E.soundness();s['noise']=('per-bit majority of repeated readings; exact conditional on every majority being correct; under iid '
                               'flips with eps <= eps_bar and state-preserving re-reads all majorities are correct with probability '
                               '>= 1 - delta')
    s['eps_bar']=eps_bar;s['delta']=delta;s['reads']=reads;return s


class Certifier16N:
    def __init__(self,initial_reads=None,num_actions=None,family_bound=None,eps_bar=0.10,delta=0.001,reads=None,**kw):
        if isinstance(eps_bar,bool) or not isinstance(eps_bar,(int,float)) or not 0<=eps_bar<0.5:raise ValueError('eps_bar must be in [0, 0.5)')
        if isinstance(delta,bool) or not isinstance(delta,(int,float)) or not 0<delta<1:raise ValueError('delta must be in (0, 1)')
        if reads is not None and (_int(reads,'reads')<1 or reads%2==0):raise ValueError('reads must be None or a positive odd int')
        self.eps_bar=eps_bar;self.delta=delta;self.reads=reads;self.t=0;self.votes=[];self.ks=[]
        m=self._take(initial_reads);self.inner=E.Certifier16E(m,num_actions,family_bound,'a16d',**kw)

    def reads_needed(self):
        return self.reads if self.reads is not None else reads_for(self.t+1,self.eps_bar,self.delta)

    def _take(self,readings):
        rs=list(readings);k=self.reads_needed()
        if len(rs)!=k:raise ValueError(f'expected {k} readings for observation {self.t+1}, got {len(rs)}')
        m,ones=majority(rs);self.t+=1;self.ks.append(k);self.votes.append(ones);return m

    def observe(self,action,readings):
        if isinstance(action,bool) or not isinstance(action,int) or action not in range(self.inner.k):
            raise ValueError(f'action must be an int in 0..{self.inner.k-1}')
        if self.inner.stop is not None:raise RuntimeError('certifier has stopped; no further observations')
        m=self._take(readings);self.inner.observe(action,m)

    def propose(self):return self.inner.propose()

    def _extra(self,d):
        d['api']=API;d['inner_api']=E.API;d['eps_bar']=self.eps_bar;d['delta']=self.delta;d['reads']=self.reads
        d['observations']=self.t;d['reads_total']=sum(self.ks);d['reads_max']=max(self.ks);return d

    def current(self):return self._extra(self.inner.current())

    def result(self):
        d=self._extra(self.inner.result());d['soundness']=soundness(self.eps_bar,self.delta,self.reads);return d

    def record(self):
        r=dict(self.inner.record());r['reads_per_obs']=list(self.ks);r['votes']=[list(v) for v in self.votes]
        r['eps_bar']=self.eps_bar;r['delta']=self.delta;r['reads']=self.reads;return r

    @property
    def stop(self):return self.inner.stop

    @property
    def k(self):return self.inner.k

    def close(self):self.inner.close()

    def __enter__(self):return self

    def __exit__(self,*a):self.close();return False
