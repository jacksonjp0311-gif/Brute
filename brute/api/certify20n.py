"""Brute v0.56.0 embeddable certify interface, version 20n (BRUTE_PLAN_059).
Additive: brute/api/certify16n.py, certify20b.py and every earlier module are untouched and imported only.

certify/20n is certify/16n's repeated-reading per-bit majority front end on an UNCHANGED certify/20b instance, with the reading
width as a parameter (read_bits 2, 3 or 4). Each observation is read k times; each output bit is set to its majority over the k
readings (k odd, no ties) and the majority reading is passed to certify/20b.
k rule (certify/16n's anytime rule with bits = read_bits): observation t (t = 1 for the initial reading) gets the smallest odd k with
    read_bits * exp(-2 k (1/2 - eps_bar)^2) <= delta * 6 / (pi^2 t^2),
so by Hoeffding per bit and a union bound over bits and every t the chance that ANY majority bit of the whole trace is wrong is at
most delta, for any trace length (Exact, conditional on the iid model below).
    c = Certifier20N(initial_reads, num_actions=3, family_bound=20, read_bits=4, eps_bar=0.15, delta=0.001, conflict_cap=C, budget_conflicts=B)
    k = c.reads_needed(); c.observe(action, [reading_1, ..., reading_k])
reads=<odd int> fixes k for every observation (reads=1 on noise-free readings reproduces certify/20b exactly).
Guarantee (label 'ID' / 'IDF'): exact, CONDITIONAL on every majority reading being correct and on the true machine having at most
family_bound states. If each reading bit is flipped independently with probability eps <= eps_bar and re-reading the current
observation does not change the hidden state, every majority is correct with probability >= 1 - delta.
Why a size bound is needed (Inferred): a larger machine can copy the true machine on every visited state and differ only on states
the trace never reached, so no finite trace rules out every larger machine.
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
from brute.api.certify8 import _int
from brute.api import certify16n as N
from brute.api import certify20b as B

API='brute.certify/20n'
READ_BITS=B.READ_BITS
__all__=['API','READ_BITS','Certifier20N','reads_for','majority','soundness']


def reads_for(t,eps_bar,delta,read_bits):
    """Smallest odd k with read_bits*exp(-2k(1/2-eps_bar)^2) <= delta*6/(pi^2 t^2)."""
    return N.reads_for(t,eps_bar,delta,bits=read_bits)


def _bits(r,sb):
    if not isinstance(r,(tuple,list)) or len(r)!=sb or any(isinstance(b,bool) or b not in (0,1) for b in r):
        raise ValueError(f'a reading is a tuple of {sb} bits (0/1)')
    return tuple(r)


def majority(readings,read_bits):
    """Per-bit majority of an odd number of read_bits-wide readings; returns (reading, per-bit one-counts)."""
    rs=[_bits(r,read_bits) for r in readings];k=len(rs)
    if k<1 or k%2==0:raise ValueError('need an odd number of readings')
    ones=[sum(r[j] for r in rs) for j in range(read_bits)];return tuple(1 if 2*o>k else 0 for o in ones),ones


def soundness(eps_bar,delta,reads,read_bits):
    s=N.soundness(eps_bar,delta,reads);s['readings']=B.soundness()['readings'];s['read_bits']=read_bits;return s


class Certifier20N:
    def __init__(self,initial_reads=None,num_actions=None,family_bound=None,read_bits=4,eps_bar=0.10,delta=0.001,reads=None,**kw):
        if isinstance(read_bits,bool) or not isinstance(read_bits,int) or read_bits not in READ_BITS:raise ValueError('read_bits must be 2, 3 or 4')
        if isinstance(eps_bar,bool) or not isinstance(eps_bar,(int,float)) or not 0<eps_bar<0.5:raise ValueError('eps_bar must be in (0, 0.5)')
        if isinstance(delta,bool) or not isinstance(delta,(int,float)) or not 0<delta<1:raise ValueError('delta must be in (0, 1)')
        if reads is not None and (isinstance(reads,bool) or _int(reads,'reads')<1 or reads%2==0):raise ValueError('reads must be None or a positive odd int')
        self.sb=read_bits;self.eps_bar=eps_bar;self.delta=delta;self.reads=reads;self.t=0;self.votes=[];self.ks=[]
        m=self._take(initial_reads);self.inner=B.Certifier20B(m,num_actions,family_bound,'a16d',read_bits=read_bits,**kw)

    def reads_needed(self):
        return self.reads if self.reads is not None else reads_for(self.t+1,self.eps_bar,self.delta,self.sb)

    def _take(self,readings):
        if not isinstance(readings,(tuple,list)):raise ValueError('readings must be a list of readings')
        rs=list(readings);k=self.reads_needed()
        if len(rs)!=k:raise ValueError(f'expected {k} readings for observation {self.t+1}, got {len(rs)}')
        m,ones=majority(rs,self.sb);self.t+=1;self.ks.append(k);self.votes.append(ones);return m

    def observe(self,action,readings):
        if isinstance(action,bool) or not isinstance(action,int) or action not in range(self.inner.k):
            raise ValueError(f'action must be an int in 0..{self.inner.k-1}')
        if self.inner.stop is not None:raise RuntimeError('certifier has stopped; no further observations')
        m=self._take(readings);self.inner.observe(action,m)

    def propose(self):return self.inner.propose()

    def _extra(self,d):
        d['api']=API;d['inner_api']=B.API;d['read_bits']=self.sb;d['eps_bar']=self.eps_bar;d['delta']=self.delta;d['reads']=self.reads
        d['observations']=self.t;d['reads_total']=sum(self.ks);d['reads_max']=max(self.ks);return d

    def current(self):return self._extra(self.inner.current())

    def result(self):
        d=self._extra(self.inner.result());d['soundness']=soundness(self.eps_bar,self.delta,self.reads,self.sb);return d

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
