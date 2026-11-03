"""Brute v0.62.0 embeddable certify interface, version 20s (BRUTE_PLAN_065).
Additive: brute/api/certify20p.py, certify20n.py and every earlier module are untouched and imported only.

certify/20s is a SEQUENTIAL per-bit re-read front end (a random-walk / SPRT stopping rule) on an UNCHANGED certify/20p instance
(clique-anchored symmetry breaking). Each observation is re-read until every output bit is settled: for bit j keep a lead
L_j = (#ones - #zeros) over the readings so far and settle the bit the first time |L_j| >= m_t; the settled value is the sign.
Later readings of a settled bit are ignored. The settled reading is passed to certify/20p.
m rule: observation t (t = 1 for the initial reading) uses the smallest m >= 1 with
    read_bits * r^m / (1 + r^m) <= delta * 6 / (pi^2 t^2),     r = eps_bar / (1 - eps_bar).
Why (Exact, gambler's ruin): with iid flips at eps <= eps_bar the lead is a +-1 walk with drift toward the true bit; the chance it
hits the wrong barrier -m before +m is r_eps^m / (1 + r_eps^m) <= r^m / (1 + r^m) (monotone in eps), and the walk stops with
probability 1. A union bound over bits and every t gives P(any settled bit of the whole trace wrong) <= delta, any trace length.
Expected reads per observation grow like m / (1 - 2 eps) instead of the fixed rule's log(.)/(2 (1/2 - eps_bar)^2) (certify/20n).
    c = Certifier20S(initial_reads, num_actions=3, family_bound=20, read_bits=2, eps_bar=0.15, delta=0.001, conflict_cap=C, budget_conflicts=B)
    need = c.more(readings_so_far)      # True while some bit is unsettled for the NEXT observation
    c.observe(action, readings)         # readings must be exactly a stopping sequence (more(readings[:-1]) True, more(readings) False)
Guarantee (label 'ID' / 'IDF'): exact, CONDITIONAL on every settled reading being correct and on the true machine having at most
family_bound states (N <= 20). Under iid flips with eps <= eps_bar and state-preserving re-reads, every settled reading is correct
with probability >= 1 - delta. A hard cap of READ_CAP readings per observation raises ValueError (no silent truncation).
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
import math
from brute.api.certify8 import _int
from brute.api import certify20p as P
from brute.api.certify20p import Certifier20P,NODE_CAP

API='brute.certify/20s'
READ_CAP=100000
__all__=['API','READ_CAP','NODE_CAP','Certifier20S','threshold','settle','soundness']


def threshold(t,eps_bar,delta,read_bits=2):
    """Smallest m >= 1 with read_bits * r^m/(1+r^m) <= delta*6/(pi^2 t^2), r = eps_bar/(1-eps_bar)."""
    if _int(t,'t')<1:raise ValueError('t must be a positive int')
    if eps_bar==0:return 1
    r=eps_bar/(1.0-eps_bar);x=delta*6.0/(math.pi**2*t*t)/read_bits;m=1
    while r**m/(1.0+r**m)>x:m+=1
    return m


def _bits(r,sb):
    if not isinstance(r,(tuple,list)) or len(r)!=sb or any(isinstance(b,bool) or b not in (0,1) for b in r):
        raise ValueError(f'a reading is a tuple of {sb} bits (0/1)')
    return tuple(r)


def settle(readings,m,read_bits):
    """Returns (settled reading or None, per-bit settle index or None, leads). Bit j settles at the first prefix with |lead| >= m."""
    lead=[0]*read_bits;at=[None]*read_bits;val=[None]*read_bits
    for i,r in enumerate(readings,1):
        r=_bits(r,read_bits)
        for j in range(read_bits):
            if at[j] is not None:continue
            lead[j]+=1 if r[j] else -1
            if abs(lead[j])>=m:at[j]=i;val[j]=1 if lead[j]>0 else 0
    if any(a is None for a in at):return None,at,lead
    return tuple(val),at,lead


def soundness(eps_bar,delta,read_bits):
    s=P.soundness();s['noise']=('sequential per-bit re-reads (random-walk stopping rule); exact conditional on every settled bit being '
                                'correct; under iid flips with eps <= eps_bar and state-preserving re-reads all settled bits are correct '
                                'with probability >= 1 - delta (gambler\'s ruin bound r^m/(1+r^m) per bit, union over bits and t)')
    s['eps_bar']=eps_bar;s['delta']=delta;s['read_bits']=read_bits;return s


class Certifier20S:
    def __init__(self,initial_reads=None,num_actions=None,family_bound=None,read_bits=2,eps_bar=0.15,delta=0.001,max_chunks=None,node_cap=NODE_CAP,**kw):
        if isinstance(read_bits,bool) or not isinstance(read_bits,int) or read_bits not in (2,3,4):raise ValueError('read_bits must be 2, 3 or 4')
        if isinstance(eps_bar,bool) or not isinstance(eps_bar,(int,float)) or not 0<=eps_bar<0.5:raise ValueError('eps_bar must be in [0, 0.5)')
        if isinstance(delta,bool) or not isinstance(delta,(int,float)) or not 0<delta<1:raise ValueError('delta must be in (0, 1)')
        self.sb=read_bits;self.eps_bar=eps_bar;self.delta=delta;self.t=0;self.ks=[];self.ms=[];self.settle_at=[]
        m=self._take(initial_reads)
        self.inner=Certifier20P(m,num_actions,family_bound,'a16d',read_bits=read_bits,max_chunks=max_chunks,node_cap=node_cap,**kw)

    def threshold_next(self):return threshold(self.t+1,self.eps_bar,self.delta,self.sb)

    def more(self,readings):
        """True while some bit of the NEXT observation is unsettled after these readings."""
        rs=list(readings)
        if len(rs)>READ_CAP:raise ValueError(f'more than READ_CAP={READ_CAP} readings for one observation')
        v,_,_=settle(rs,self.threshold_next(),self.sb);return v is None

    def _take(self,readings):
        if not isinstance(readings,(tuple,list)):raise ValueError('readings must be a list of readings')
        rs=list(readings)
        if not rs:raise ValueError('need at least one reading')
        if len(rs)>READ_CAP:raise ValueError(f'more than READ_CAP={READ_CAP} readings for one observation')
        m=self.threshold_next();v,at,_=settle(rs,m,self.sb)
        if v is None:raise ValueError(f'observation {self.t+1}: readings do not settle every bit at threshold {m}')
        if max(at)!=len(rs):raise ValueError(f'observation {self.t+1}: {len(rs)} readings given but every bit settled after {max(at)}')
        self.t+=1;self.ks.append(len(rs));self.ms.append(m);self.settle_at.append(list(at));return v

    def observe(self,action,readings):
        if isinstance(action,bool) or not isinstance(action,int) or action not in range(self.inner.k):
            raise ValueError(f'action must be an int in 0..{self.inner.k-1}')
        if self.inner.stop is not None:raise RuntimeError('certifier has stopped; no further observations')
        m=self._take(readings);self.inner.observe(action,m)

    def propose(self):return self.inner.propose()

    def _extra(self,d):
        d['api']=API;d['inner_api']=P.API;d['read_bits']=self.sb;d['eps_bar']=self.eps_bar;d['delta']=self.delta
        d['observations']=self.t;d['reads_total']=sum(self.ks);d['reads_max']=max(self.ks);return d

    def current(self):return self._extra(self.inner.current())

    def result(self):
        d=self._extra(self.inner.result());d['soundness']=soundness(self.eps_bar,self.delta,self.sb);return d

    def record(self):
        r=dict(self.inner.record());r['reads_per_obs']=list(self.ks);r['thresholds']=list(self.ms);r['settle_at']=[list(a) for a in self.settle_at]
        r['eps_bar']=self.eps_bar;r['delta']=self.delta;return r

    @property
    def stop(self):return self.inner.stop

    @property
    def k(self):return self.inner.k

    def close(self):self.inner.close()

    def __enter__(self):return self

    def __exit__(self,*a):self.close();return False
