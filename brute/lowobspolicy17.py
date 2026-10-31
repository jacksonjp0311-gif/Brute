"""A16_xf for Brute v0.41.0 (BRUTE_PLAN_044 design.arms.A16_xf; pre-run deviation #161 fixes the readings below). New file;
brute/scalesearch16.py (A16) and every earlier module are untouched and imported only.

A16_xf = an experiment-first schedule, then A16 exactly as frozen:
 (i) before the first least-model search it executes the first E actions of the fixed schedule xf_schedule(k, E): every
     action word of length 1, then 2, then 3, in lexicographic order over 0..k-1, concatenated and run in sequence from the
     state the passive trace ends in (the world has no reset, so "from the start" in the plan text is read as "from the
     current state"; #161 item 1). For k = 3 the length <= 3 words hold 3 + 18 + 81 = 102 actions > E = 32, so the plan's
     seeded random length-6 tail is never reached and no random number is drawn (Exact for k = 3; the tail is kept, seeded by
     tail_seed, for k <= 2 only, where the words hold fewer than E actions);
 (ii) then active16 on the extended trace with K - E experiments left, the same deadline, cap, solver and hook.
'used' counts every executed action (schedule + separating words) against the plan's K = 128 total; 'xf_used' is the
schedule part and 'words_used' the separating-word part.
Host-agnostic: no I/O, network, threads, child processes or global state; the world is reached only via observe."""
from __future__ import annotations
import random
from itertools import product
from time import perf_counter
from brute.scalesearch16 import QUERY_S14,K14,BUDGET14,active16,native
from brute.scalesearch4 import SOLVER4

__all__=['E17','TAIL_LEN','xf_schedule','active17xf']
E17=32;TAIL_LEN=6


def xf_schedule(k,E=E17,tail_seed=0):
    out=[]
    for L in (1,2,3):
        for w in product(range(k),repeat=L):out.extend(w)
    if len(out)<E:
        rng=random.Random(tail_seed)
        while len(out)<E:out.extend(rng.randrange(k) for _ in range(TAIL_LEN))
    return out[:E]


def active17xf(masks,acts,k,m,N,observe,deadline,K=K14,query_s=QUERY_S14,solver=SOLVER4,hook=None,factory=native,E=E17,tail_seed=0,clock=None):
    """Run the schedule (stopping early only if the deadline passes), then active16 with K - executed experiments."""
    clock=clock or perf_counter;masks=list(masks);acts=list(acts);sch=xf_schedule(k,min(E,K),tail_seed);done=[]
    for a in sch:
        if clock()>=deadline:break
        mk=observe(a);acts.append(a);masks.append(mk);done.append(a)
    r=active16(masks,acts,k,m,N,observe,deadline,K-len(done),query_s,solver,hook,factory)
    r['words_used']=r['used'];r['xf_used']=len(done);r['xf_actions']=done;r['used']=r['used']+len(done);r['K_total']=K
    return r
