"""Brute v0.66.0 embeddable certify interface, version 32h (BRUTE_PLAN_070): RESET-FREE certification with Brute's SAT version
space, fed by homing-based tests. New file; certify32p.py and every earlier module are untouched and imported only.

certify/32h is the UNCHANGED certify/32p identifier (SAT version space of every Moore machine with <= N states consistent with the
ONE reset-free trajectory; clique-anchored symmetry breaking; rival search; separating words) with ONE change, the experiment
policy. After every AMB stop check the proposed word is the engine's separating word w (as certify/32p) FOLLOWED BY a homing-based
test batch computed from the least machine M1 (Brute's current hypothesis):
  h  = a shortest homing sequence of M1 (textbook: for any two M1 states with equal readings along h, h ends them in one state),
  then segments h . p . u . e, where p walks M1 (as predicted) to state t, u in Sigma^d, e in a characterizing set of M1,
  (t, u, e) enumerated depth by depth (d = 0, 1, ...; order shuffled by random.Random(seed)), batch_steps actions per round.
The homing sequence and the suite shape are textbook (Vasilevskii-Chow style tests re-synchronised by a homing sequence instead of
a reset). The certificate is Brute's: the label comes ONLY from the certify/32p SAT stop check on the whole trajectory, so the
guarantee does NOT assume h is homing for the target (it is only a test-design heuristic).
    c = Certifier32H(initial, num_actions=3, family_bound=9, read_bits=2, conflict_cap=C, budget_conflicts=B, K=40000, seed=s)
    w = c.propose(); for a in w: c.observe(a, reading); ...; c.result()          # as certify/32p
Guarantee (label 'ID' / 'IDF'): certify/32p's, exact, CONDITIONAL on noise-free readings and on the true machine having at most
family_bound states. 'IDF': every such machine consistent with the trajectory predicts the same future from now; 'ID' also the same
start. No reset is used or assumed.
Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations
import itertools,random
from brute.api import certify32p as P32
from brute.api.certify32p import Certifier32P,NODE_CAP,MAX_BOUND
from brute.api.certify8 import _int

API='brute.certify/32h'
BATCH_STEPS=400
__all__=['API','MAX_BOUND','NODE_CAP','BATCH_STEPS','Certifier32H','homing_sequence','char_set','soundness']


def soundness():
    s=P32.soundness();s.update(api=API,resets=False,policy='separating word + homing-based test batch from the least machine (heuristic only; not assumed by the label)');return s


def _norm(M):
    T,E=M
    return [list(r) for r in T],list(E)


def homing_sequence(T,E,cap=200000):
    """A shortest homing sequence of the Moore machine (T, E) (readings include the one before the first action): BFS over the
    current-uncertainty partition; None if none is found within cap nodes. Deterministic."""
    n=len(T);k=len(T[0]) if n else 0
    def key(blocks):return tuple(sorted(blocks))
    start={}
    for q in range(n):start.setdefault(E[q],set()).add(q)
    s0=key(tuple(sorted(b)) for b in start.values())
    done=lambda bl:all(len(b)==1 for b in bl)
    if done(s0):return []
    seen={s0:None};q=[s0];i=0
    while i<len(q) and len(seen)<cap:
        cur=q[i];i+=1
        for a in range(k):
            nb=[]
            for b in cur:
                g={}
                for x in b:y=T[x][a];g.setdefault(E[y],set()).add(y)
                nb.extend(tuple(sorted(v)) for v in g.values())
            nk=key(set(nb))
            if nk in seen:continue
            seen[nk]=(cur,a)
            if done(nk):
                w=[];c=nk
                while seen[c] is not None:p,aa=seen[c];w.append(aa);c=p
                return w[::-1]
            q.append(nk)
    return None


def _dist(T,E,p,q):
    """Shortest word separating states p and q (product BFS), or None."""
    seen={(p,q):()};Q=[(p,q)];i=0
    while i<len(Q):
        x=Q[i];i+=1
        if E[x[0]]!=E[x[1]]:return list(seen[x])
        for a in range(len(T[0])):
            y=(T[x[0]][a],T[x[1]][a])
            if y not in seen:seen[y]=seen[x]+(a,);Q.append(y)
    return None


def char_set(T,E):
    """Sorted distinct shortest separating words over all state pairs, the empty word first (a characterizing set)."""
    W={()}
    for p in range(len(T)):
        for q in range(p+1,len(T)):
            d=_dist(T,E,p,q)
            if d is not None:W.add(tuple(d))
    return sorted(W,key=lambda w:(len(w),w))


def _path(T,s,t):
    seen={s:()};Q=[s];i=0
    while i<len(Q):
        x=Q[i];i+=1
        if x==t:return list(seen[x])
        for a in range(len(T[0])):
            y=T[x][a]
            if y not in seen:seen[y]=seen[x]+(a,);Q.append(y)
    return None


class Certifier32H(Certifier32P):
    def __init__(self,initial=None,num_actions=None,family_bound=None,search='a16d',read_bits=2,seed=0,batch_steps=BATCH_STEPS,K=40000,**kw):
        _int(seed,'seed');_int(batch_steps,'batch_steps')
        if batch_steps<1:raise ValueError('batch_steps must be positive')
        super().__init__(initial,num_actions,family_bound,search,read_bits=read_bits,K=K,**kw)
        self.seed=seed;self.batch_steps=batch_steps;self.rng=random.Random(seed);self.cursor=None;self.batches=[]

    def _suite(self,T,E):
        """Generator of (t, u, e) for M1, depth by depth up to N - n + 1, then repeats from depth 0 with a fresh shuffle."""
        n=len(T);k=len(T[0]);C=char_set(T,E)
        while True:
            for d in range(self.N-n+2):
                items=[(t,u,e) for t in range(n) for u in itertools.product(range(k),repeat=d) for e in C];self.rng.shuffle(items)
                for x in items:yield d,x

    def propose(self):
        w=super().propose()
        if w is None:return None
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

    def record(self):
        d=dict(super().record());d['batches']=list(self.batches);d['seed']=self.seed;d['batch_steps']=self.batch_steps;return d

    def current(self):
        d=super().current();d['api']=API;return d

    def result(self):
        d=super().result();d['api']=API;d['soundness']=soundness();d['batches']=len(self.batches);return d
