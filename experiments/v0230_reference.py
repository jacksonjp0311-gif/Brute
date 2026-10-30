"""GS_ref12 second implementation for study-026 (BRUTE_PLAN_026 GS_ref12; deviation #123 item 11). SAT-free, imports no
solver and no brute.* search code. New file.

ref_support(codes, actions, b, n_max, budget): for each code c, a depth-first search over trace positions 0..T assigns
states with first-visit numbering (a new state gets the next number), deterministic transitions and one code per state,
and succeeds when the machine (at most n_max states) can emit c after action b from the state at position T (an
unexercised transition may go to an existing state with code c or to a fresh state). Per (query, code) the search stops
after `budget` nodes. Answer per code: True (a machine was found: c possible), False (search exhausted: c impossible),
None (undecided). A query is decided iff every code is decided; its support is then the sorted list of possible codes
(None if no machine at all is consistent with the trace).
Audit (audit_case): compares every decided query with the stored S2 answer of a sealed case record (S2 exact answers
only); undecided queries are counted. mutate(): seeded mutation of decided S2 answers, for the 20/20 mutation test."""
from __future__ import annotations
import random

__all__=['ref_code','ref_support','audit_case','mutate','BUDGET','N_MAX']
BUDGET=20000;N_MAX=16


class _Out(Exception):pass


def ref_code(codes,actions,b,c,n_max=N_MAX,budget=BUDGET):
    """True / False / None for 'code c is possible after action b at the end of the trace'. c=None asks feasibility."""
    T=len(actions);d={};e=[codes[0]];nodes=[0]
    def tick():
        nodes[0]+=1
        if nodes[0]>budget:raise _Out
    def final(q):
        if c is None:return True
        r=d.get((q,b))
        if r is not None:return e[r]==c
        return c in e or len(e)<n_max
    def go(t,q):
        tick()
        if t==T:return final(q)
        a=actions[t];o=codes[t+1];r=d.get((q,a))
        if r is not None:return e[r]==o and go(t+1,r)
        for r in range(len(e)):
            if e[r]==o:
                d[(q,a)]=r
                if go(t+1,r):return True
                del d[(q,a)]
        if len(e)<n_max:
            e.append(o);d[(q,a)]=len(e)-1
            if go(t+1,len(e)-1):return True
            del d[(q,a)];e.pop()
        return False
    import sys
    lim=sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(max(lim,4*T+100));return go(0,0)
    except _Out:return None
    finally:sys.setrecursionlimit(lim)


def ref_support(codes,actions,b,m=4,n_max=N_MAX,budget=BUDGET):
    """(decided, support): support is the sorted possible-code list, or None if the trace has no consistent machine."""
    f=ref_code(codes,actions,b,None,n_max,budget)
    if f is None:return False,None
    if f is False:return True,None
    out=[];dec=True
    for c in range(m):
        r=ref_code(codes,actions,b,c,n_max,budget)
        if r is None:dec=False
        elif r:out.append(c)
    return dec,(out if dec else None)


def _codes(readings):return [sum(bit<<(len(o)-1-j) for j,bit in enumerate(o)) for o in readings]


def audit_case(case,readings,actions,budget=BUDGET,deadline=None,order=None):
    """{'queries', 'exact_s2', 'decided', 'mismatches': [...], 'undecided', 'not_reached'} for one case record.
    `order` is a list of (i, b) to visit (default: all, step-major); stops at `deadline` (perf_counter) if given."""
    from time import perf_counter
    s2=case['arms']['S2'];k=case['k'];codes=_codes(readings);steps=len(s2['sup'])
    order=order or [(i,b) for i in range(steps) for b in range(k)]
    rep={'queries':steps*k,'exact_s2':0,'decided':0,'decided_possible_codes':0,'decided_impossible_codes':0,'mismatches':[],
         'undecided':0,'not_reached':0,'decided_keys':[]}
    for n,(i,b) in enumerate(order):
        if s2['unk'][i][b]!=0:continue
        rep['exact_s2']+=1
        if deadline is not None and perf_counter()>=deadline:rep['not_reached']+=1;continue
        dec,sup=ref_support(codes[:i+1],list(actions[:i]),b,4,N_MAX,budget)
        if not dec:rep['undecided']+=1;continue
        rep['decided']+=1;rep['decided_keys'].append([i,b,sup])
        if sup is not None:rep['decided_possible_codes']+=len(sup);rep['decided_impossible_codes']+=4-len(sup)
        if sup!=s2['sup'][i][b]:rep['mismatches'].append([i,b,s2['sup'][i][b],sup])
    return rep


def mutate(decided,n,seed=230):
    """n seeded mutations of decided queries: (i, b, mutated support, reference support). Each mutation drops one possible
    code or adds one impossible code, so a correct audit must flag every one."""
    rng=random.Random(seed);out=[]
    pool=[x for x in decided if x[2] is not None]
    for _ in range(n):
        i,b,sup=rng.choice(pool);s=set(sup)
        c=rng.randrange(4);s^={c}
        out.append((i,b,sorted(s),sup))
    return out
