"""Brute v0.65.0 embeddable certify interface, version 32r (BRUTE_PLAN_069): certification WITH RESETS. New file; every earlier
module is untouched (certify20s.threshold / settle are imported only).

RESETS MAKE THE PROBLEM EASIER than Brute's reset-free certifiers (certify/32p, /32s): every query word is run from the start
state. This module does not use Brute's SAT engine. It is an L*-style learner (observation tree, prefix-closed access words S,
suffix set E with the empty word first, Maler-Pnueli counterexample handling: all suffixes of a counterexample join E) whose stop
rule is the Vasilevskii-Chow N-complete test suite S . Sigma^{<= N-n+1} . E.
    c = Certifier32R(num_actions=3, family_bound=12, read_bits=2, eps_bar=None, delta=None, seed=0, query_cap=400000)
    while (w := c.propose()) is not None:          # w: tuple of actions, to be run from a FRESH start (reset)
        for i in range(len(w)+1):                   # after the reset (i = 0) and after each action w[i-1]
            if c.wants(w[:i]):
                rs = [one reading]; while c.more(rs): rs.append(one more reading)    # clean (eps_bar None): one reading
                c.take(w[:i], rs)
    c.result()
Labels: 'ID' (H has n <= N states and every suite word agrees with H), 'EXCEEDS_N' (more than N distinct rows: the target has
more than N states, exact), 'QCAP' (query cap, undecided).
Guarantee for 'ID' (Exact, Vasilevskii 1973 / Chow 1978, Moore form): if the target is a deterministic Moore machine with at most
N states, every query starts from its start state, and every recorded reading is correct, then the target is equivalent to H.
Rows of S are pairwise distinct over E, so E characterizes H and S is a state cover; a machine M with <= N states agreeing with H
on S . Sigma^{<= N-n+1} . E is equivalent to H. Noisy readings (eps_bar set): each NEW tree node is read until every bit settles
at certify20s.threshold(t, eps_bar, delta, read_bits) with t the 1-based index of the settled observation (union bound: all
correct with probability >= 1 - delta, iid flips eps <= eps_bar, state-preserving re-reads).
Host-agnostic: no I/O, network, threads, child processes or global state."""
from __future__ import annotations
import itertools,random
from brute.api.certify20s import threshold,settle

API='brute.certify/32r'
MAX_BOUND=64
READ_CAP=100000
__all__=['API','MAX_BOUND','READ_CAP','Certifier32R','canonical','equivalent','soundness']


def soundness():
    return {'api':API,'label_ID':'exact, conditional on: target has <= family_bound states, resets return the start state, every recorded reading correct (noisy: probability >= 1 - delta)',
            'method':'L* (Maler-Pnueli) + Vasilevskii-Chow N-complete suite S.Sigma^{<=N-n+1}.E','sat':False,'resets':True}


def canonical(trans,emis,start=0):
    """Relabel states in BFS order from start (actions in order); returns (transitions, emissions) of the reachable part."""
    order=[start];idx={start:0};i=0
    while i<len(order):
        for a in range(len(trans[order[i]])):
            t=trans[order[i]][a]
            if t not in idx:idx[t]=len(order);order.append(t)
        i+=1
    return [[idx[trans[s][a]] for a in range(len(trans[s]))] for s in order],[emis[s] for s in order]


def equivalent(t1,e1,t2,e2,s1=0,s2=0):
    """Moore equivalence of two machines from their starts (product BFS); returns (bool, shortest distinguishing word or None)."""
    seen={(s1,s2):()};q=[(s1,s2)];i=0
    while i<len(q):
        p=q[i];i+=1;w=seen[p]
        if e1[p[0]]!=e2[p[1]]:return False,list(w)
        for a in range(len(t1[p[0]])):
            r=(t1[p[0]][a],t2[p[1]][a])
            if r not in seen:seen[r]=w+(a,);q.append(r)
    return True,None


def _int(x,name):
    if isinstance(x,bool) or not isinstance(x,int):raise ValueError(f'{name} must be an int')
    return x


class Certifier32R:
    def __init__(self,num_actions=3,family_bound=12,read_bits=2,eps_bar=None,delta=None,seed=0,query_cap=400000):
        self.k=_int(num_actions,'num_actions');self.N=_int(family_bound,'family_bound');self.sb=_int(read_bits,'read_bits')
        if self.k<1 or not 1<=self.N<=MAX_BOUND or self.sb<1:raise ValueError('bad num_actions / family_bound / read_bits')
        if (eps_bar is None)!=(delta is None):raise ValueError('eps_bar and delta go together')
        if eps_bar is not None and not (0<=eps_bar<0.5 and 0<delta<1):raise ValueError('need 0 <= eps_bar < 0.5 and 0 < delta < 1')
        self.eps_bar=eps_bar;self.delta=delta;self.seed=_int(seed,'seed');self.cap=_int(query_cap,'query_cap')
        self.rng=random.Random(self.seed);self.tree={};self.t=0;self.reads=[];self.queries=0;self.rounds=0;self.cex=[]
        self.S=[()];self.E=[()];self.label=None;self.H=None;self.suite_words=0;self.pending=None
        self.gen=self._algo()

    # host side --------------------------------------------------------------------------------------------------------
    def propose(self):
        if self.label is not None:return None
        if self.pending is not None:raise ValueError('previous word not complete')
        w=next(self.gen)
        if w is None:return None
        self.queries+=1;self.pending=w;return w

    def wants(self,prefix):return tuple(prefix) not in self.tree

    def _m(self):return 1 if self.eps_bar is None else threshold(self.t+1,self.eps_bar,self.delta,self.sb)

    def more(self,readings):
        rs=list(readings)
        if len(rs)>READ_CAP:raise ValueError(f'more than READ_CAP={READ_CAP} readings for one observation')
        return settle(rs,self._m(),self.sb)[0] is None

    def take(self,prefix,readings):
        p=tuple(prefix);rs=list(readings)
        if self.pending is None or p!=self.pending[:len(p)]:raise ValueError('prefix is not a prefix of the proposed word')
        if p in self.tree:raise ValueError('prefix already recorded')
        if len(p)>0 and p[:-1] not in self.tree:raise ValueError('record prefixes in order')
        if not rs or len(rs)>READ_CAP:raise ValueError('bad readings')
        m=self._m();v,_,_=settle(rs,m,self.sb)
        if v is None or (len(rs)>1 and settle(rs[:-1],m,self.sb)[0] is not None):raise ValueError('readings must be exactly a stopping sequence')
        self.t+=1;self.reads.append(len(rs));code=0
        for b in v:code=2*code+b
        self.tree[p]=code
        if p==self.pending:self.pending=None

    # learner ------------------------------------------------------------------------------------------------------------
    def _need(self,w):
        if w not in self.tree:
            if self.queries>=self.cap:self.label='QCAP';yield None;return
            yield w
            if w not in self.tree:raise ValueError('host did not record the proposed word')

    def _row(self,s):return tuple(self.tree[s+e] for e in self.E)

    def _algo(self):
        k=self.k
        while True:
            self.rounds+=1
            while True:
                for s in self.S+[s+(a,) for s in self.S for a in range(k)]:
                    for e in self.E:
                        yield from self._need(s+e)
                        if self.label:return
                rows={self._row(s):i for i,s in enumerate(self.S)};new=None
                for s in self.S:
                    for a in range(k):
                        if self._row(s+(a,)) not in rows:new=s+(a,);break
                    if new:break
                if new is None:break
                self.S.append(new)
                if len(self.S)>self.N:self.label='EXCEEDS_N';self.H=None;yield None;return
            n=len(self.S);trans=[[rows[self._row(s+(a,))] for a in range(k)] for s in self.S];emis=[self.tree[s] for s in self.S]
            self.H=(trans,emis);L=self.N-n+1;cex=None
            def pred(w):
                q=0
                for a in w:q=trans[q][a]
                return emis[q]
            for d in range(L+1):
                perm=list(range(k));self.rng.shuffle(perm)
                for u in itertools.product(perm,repeat=d):
                    for s in self.S:
                        for e in self.E:
                            w=s+u+e;yield from self._need(w)
                            if self.label:return
                            self.suite_words+=1
                            if self.tree[w]!=pred(w):cex=w;break
                        if cex:break
                    if cex:break
                if cex:break
            if cex is None:self.label='ID';yield None;return
            self.cex.append(list(cex))
            for i in range(len(cex)):
                suf=cex[i:]
                if suf not in self.E:self.E.append(suf)

    # results ------------------------------------------------------------------------------------------------------------
    def result(self):
        if self.label is None:raise ValueError('not finished')
        d={'api':API,'label':self.label,'family_bound':self.N,'soundness':soundness()}
        if self.label=='ID':
            ct,ce=canonical(*self.H);d.update(n=len(self.S),transitions=ct,emissions=ce)
        return d

    def record(self):
        d=self.result();d.update(seed=self.seed,query_cap=self.cap,queries=self.queries,tree_nodes=len(self.tree),rounds=self.rounds,
            counterexamples=self.cex,S=[list(s) for s in self.S],E=[list(e) for e in self.E],suite_words_checked=self.suite_words,
            settled_observations=self.t,reads_total=sum(self.reads),eps_bar=self.eps_bar,delta=self.delta,
            tree=sorted([list(w),c] for w,c in self.tree.items()))
        return d
