"""Brute v0.10.0 TRANSFER / ABSTRACTION track (BRUTE_PLAN_012 transfer_definition). New file.

learn_motifs: from ONE fully observed source world, the minimal-n consistent partial Moore machines (backtracking,
states numbered at first visit, start 0), abstracted to motifs (n, traversed transitions, emission CLASS pattern).
expand: every motif x action relabelling x injective class->code map x start x completion of open transitions,
deduplicated by canonical renumbering from the start state.
TransferTracker: filters the hypotheses by the target observations and turns them into extra certificates inside a
scratch (SP8) trajectory: SP8 certificate if any; else, after burn-in, a unanimous surviving prediction that lies in
the SP8 published support. Learner-visible data only.
"""
from __future__ import annotations
from itertools import permutations,product

LIBRARY_CAP=64;HYPOTHESIS_CAP=200000;MAX_N=4


def _compatible(code,obs):
    return all(o is None or o==((code>>(len(obs)-1-j))&1) for j,o in enumerate(obs))


def learn_motifs(codes,actions,max_n=MAX_N,cap=LIBRARY_CAP):
    """codes: fully observed emission codes (len(actions)+1). Returns the library dict."""
    if len(codes)!=len(actions)+1:raise ValueError('need one more code than actions')
    cls={};C=[cls.setdefault(c,len(cls)) for c in codes]
    for n in range(1,max_n+1):
        sols=set();T=[[None,None] for _ in range(n)];E=[None]*n;E[0]=C[0]
        def rec(t,s,used):
            if t==len(actions):
                if used==n:sols.add((n,tuple(map(tuple,T)),tuple(E)))
                return
            a=actions[t];c=C[t+1];q=T[s][a]
            if q is not None:
                if E[q]==c:rec(t+1,q,used)
                return
            for q in range(min(used+1,n)):
                fresh=q==used
                if not fresh and E[q]!=c:continue
                T[s][a]=q
                if fresh:E[q]=c
                rec(t+1,q,used+fresh)
                T[s][a]=None
                if fresh:E[q]=None
        rec(0,0,1)
        if sols:
            sols=sorted(sols)
            base={'min_n':n,'motif_count':len(sols)}
            if len(sols)>cap:return dict(base,status='over_cap',motifs=[])
            return dict(base,status='ok',motifs=[{'n':m[0],'trans':[list(r) for r in m[1]],'classes':list(m[2])} for m in sols])
    return {'min_n':None,'motif_count':0,'status':'none','motifs':[]}


def canonical(trans,emis,start):
    idx={start:0};order=[start];i=0
    while i<len(order):
        q=order[i];i+=1
        for a in (0,1):
            r=trans[q][a]
            if r not in idx:idx[r]=len(order);order.append(r)
    return tuple((idx[trans[q][0]],idx[trans[q][1]]) for q in order),tuple(emis[q] for q in order)


def expand(library,m=4,cap=HYPOTHESIS_CAP):
    """(sorted canonical (trans, emis) list, status)."""
    if library['status']!='ok':return [],library['status']
    out=set()
    for mo in library['motifs']:
        n=mo['n'];k=1+max(mo['classes']);holes=[(q,a) for q in range(n) for a in (0,1) if mo['trans'][q][a] is None]
        for fill in product(range(n),repeat=len(holes)):
            T=[list(r) for r in mo['trans']]
            for (q,a),v in zip(holes,fill):T[q][a]=v
            for TT in (T,[[r[1],r[0]] for r in T]):
                for code in permutations(range(m),k):
                    E=[code[x] for x in mo['classes']]
                    for st in range(n):
                        out.add(canonical(TT,E,st))
                        if len(out)>cap:return [],'over_cap'
    return sorted(out),'ok'


class TransferTracker:
    """Hypothesis filter over one target trajectory."""
    def __init__(self,hypotheses,initial_obs,burn_in):
        self.burn_in=burn_in;self.n0=len(hypotheses)
        self.alive=[(T,E,0) for T,E in hypotheses if _compatible(E[0],initial_obs)]
        self.disabled_step=None if self.alive else 0

    def predict(self,b):
        """The unanimous next code after action b over the survivors, else None."""
        if not self.alive:return None
        P={E[T[s][b]] for T,E,s in self.alive}
        return next(iter(P)) if len(P)==1 else None

    def decide(self,step,b,sp8_certificate,sp8_support):
        """(certificate, rule) for action b at this step."""
        if sp8_certificate is not None:return sp8_certificate,'sp8'
        if step<=self.burn_in or sp8_support is None:return None,None
        c=self.predict(b)
        if c is not None and c in sp8_support:return c,'transfer'
        return None,None

    def observe(self,step,action,obs):
        if not self.alive:return
        nxt=[]
        for T,E,s in self.alive:
            r=T[s][action]
            if _compatible(E[r],obs):nxt.append((T,E,r))
        self.alive=nxt
        if not nxt and self.disabled_step is None:self.disabled_step=step
