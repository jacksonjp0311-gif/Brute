"""GS_ref second implementation for study-032 (BRUTE_PLAN_032 GS_ref: exact flip-budget reference on S7). SAT-free,
imports no solver and no brute.* search code. New file; built from experiments/v0230_reference.py (frozen).

ref_code(codes, actions, b, c, n_max, bound, budget): depth-first search over trace positions 0..T that assigns states
with first-visit numbering (a new state gets the next number and any of the m codes), deterministic transitions, and
counts flipped sensor readings (popcount of state code XOR reading code); a branch is cut once the count exceeds bound.
Succeeds when the machine (at most n_max states, at most bound flips) can emit c after action b from the state at
position T (an unexercised transition may go to an existing state with code c or to a fresh state). Per (query, code)
the search stops after `budget` nodes. Answer per code: True (c possible), False (exhausted: c impossible), None.
bound(t) = ceil(0.05 t + 2 sqrt(0.05 t)) for t = 2 (T + 1) sensor readings (own implementation of the plan formula).
Audit (audit_case): every exact S7 answer is checked code by code: a code the reference proves possible that S7
excludes, or a code the reference proves impossible that S7 keeps, is a mismatch (so partially decided queries are
checked too); a query is decided iff every code is decided. mutate(): seeded mutation for the 20/20 test."""
from __future__ import annotations
import random,sys
from math import ceil,sqrt

__all__=['ref_code','ref_bound','audit_case','mutate','BUDGET','N_MAX']
BUDGET=20000;N_MAX=16;EPS=0.05


class _Out(Exception):pass


def ref_bound(T):
    x=EPS*2*(T+1);return int(ceil(x+2.0*sqrt(x)-1e-12))


def _pc(x):return bin(x).count('1')


def ref_code(codes,actions,b,c,n_max=N_MAX,bound=None,budget=BUDGET,m=4):
    T=len(actions);bound=ref_bound(T) if bound is None else bound;d={};e=[];nodes=[0]
    def tick():
        nodes[0]+=1
        if nodes[0]>budget:raise _Out
    def final(q):
        r=d.get((q,b))
        if r is not None:return e[r]==c
        return c in e or len(e)<n_max
    def go(t,q,f):
        tick()
        if t==T:return final(q)
        a=actions[t];o=codes[t+1];r=d.get((q,a))
        if r is not None:
            g=f+_pc(e[r]^o);return g<=bound and go(t+1,r,g)
        for r in sorted(range(len(e)),key=lambda r:_pc(e[r]^o)):
            g=f+_pc(e[r]^o)
            if g>bound:continue
            d[(q,a)]=r
            if go(t+1,r,g):return True
            del d[(q,a)]
        if len(e)<n_max:
            d[(q,a)]=len(e)
            for x in sorted(range(m),key=lambda x:_pc(x^o)):
                g=f+_pc(x^o)
                if g>bound:continue
                e.append(x)
                if go(t+1,len(e)-1,g):return True
                e.pop()
            del d[(q,a)]
        return False
    lim=sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(max(lim,4*T+100))
        for x in sorted(range(m),key=lambda x:_pc(x^codes[0])):
            g=_pc(x^codes[0])
            if g>bound:continue
            e.append(x)
            if go(0,0,g):return True
            e.pop()
        return False
    except _Out:return None
    finally:sys.setrecursionlimit(lim)


def _codes(readings):return [sum(bit<<(len(o)-1-j) for j,bit in enumerate(o)) for o in readings]


def audit_case(case,readings,actions,arm='S7',budget=BUDGET,deadline=None,order=None,m=4):
    """{'queries','exact','decided','partially_checked_codes','mismatches','undecided','not_reached','decided_keys'}."""
    from time import perf_counter
    A=case['arms'][arm];k=case['k'];codes=_codes(readings);steps=len(A['sup'])
    order=order or [(i,b) for i in range(steps) for b in range(k)]
    rep={'queries':steps*k,'exact':0,'decided':0,'decided_possible_codes':0,'decided_impossible_codes':0,'checked_codes':0,
         'mismatches':[],'undecided':0,'not_reached':0,'decided_keys':[]}
    for i,b in order:
        if A['unk'][i][b]!=0:continue
        rep['exact']+=1
        if deadline is not None and perf_counter()>=deadline:rep['not_reached']+=1;continue
        s=A['sup'][i][b];have=set(s) if s is not None else set();ans={}
        for c in range(m):
            r=ref_code(codes[:i+1],list(actions[:i]),b,c,N_MAX,ref_bound(i),budget,m);ans[c]=r
            if r is not None:
                rep['checked_codes']+=1
                if r!=(c in have):rep['mismatches'].append([i,b,s,c,r])
        if all(v is not None for v in ans.values()):
            sup=[c for c in range(m) if ans[c]] or None;rep['decided']+=1;rep['decided_keys'].append([i,b,sup])
            if sup is not None:rep['decided_possible_codes']+=len(sup);rep['decided_impossible_codes']+=m-len(sup)
        else:rep['undecided']+=1
    return rep


def mutate(decided,n,seed=290):
    rng=random.Random(seed);out=[];pool=[x for x in decided if x[2] is not None]
    for _ in range(n):
        i,b,sup=rng.choice(pool);s=set(sup);c=rng.randrange(4);s^={c};out.append((i,b,sorted(s),sup))
    return out
