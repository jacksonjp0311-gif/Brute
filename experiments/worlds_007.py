"""World generators for study BRUTE-050-REGION-007 (experiments/BRUTE_PLAN_007.json breadth_worlds).

2x2 families: the frozen study-006 dispatcher (experiments/worlds_006.py). Breadth families big6, sens3, act3, ood6s3:
HiddenWorldK with k actions and s binary sensors, written from the plan text. Hidden truth never reaches a learner."""
from __future__ import annotations
import random
from dataclasses import dataclass
from experiments.worlds_006 import world as world_2x2,next_hidden as next_hidden_2x2,FAMILIES_006

FAMILIES_2X2=FAMILIES_006
FAMILIES_BREADTH=('big6','sens3','act3','ood6s3')
# family: (seed offset, n, k, s, number of distinct codes, emission pattern over code indices)
GENERATORS={'big6':(307,6,2,2,3,(0,0,1,1,2,2)),'sens3':(311,4,2,3,3,(0,0,1,2)),
            'act3':(313,4,3,2,3,(0,0,1,2)),'ood6s3':(317,6,2,3,4,(0,0,1,1,2,3))}


@dataclass(frozen=True)
class HiddenWorldK:
    n:int;k:int;s:int;transitions:tuple;emissions:tuple;start:int;seed:int;family:str

    @property
    def m(self):return 1<<self.s

    def emission(self,h):return self.emissions[h]

    def next(self,h,a):return self.transitions[h][a]

    def bits(self,code):return tuple((code>>(self.s-1-j))&1 for j in range(self.s))

    def observed(self,h,rate,step):
        rng=random.Random((self.seed*1299709+step*23011+701)%(2**64))
        return tuple(b if rng.random()>=rate else None for b in self.bits(self.emissions[h]))


def _reach(rng,n,k):
    for _ in range(10000):
        T=[[rng.randrange(n) for a in range(k)] for q in range(n)];start=rng.randrange(n)
        seen={start};todo=[start]
        while todo:
            q=todo.pop()
            for x in T[q]:
                if x not in seen:seen.add(x);todo.append(x)
        if len(seen)==n:return tuple(tuple(r) for r in T),start
    raise ValueError('no reachable machine in 10000 draws')


def breadth_world(seed,family):
    off,n,k,s,nc,pat=GENERATORS[family];rng=random.Random(seed*130363+off)
    T,start=_reach(rng,n,k);codes=rng.sample(range(1<<s),nc);em=[codes[j] for j in pat];rng.shuffle(em)
    return HiddenWorldK(n,k,s,T,tuple(em),start,seed,family)


def passive_actions(seed,steps,k):
    rng=random.Random(seed*72031+37);return tuple(rng.randrange(k) for _ in range(steps))


def minimal_states(w):
    """EVALUATOR ONLY: size of the minimal Moore machine of the (reachable) world, by partition refinement."""
    block={q:w.emissions[q] for q in range(w.n)}
    while True:
        sig={q:(block[q],)+tuple(block[w.transitions[q][a]] for a in range(w.k)) for q in range(w.n)}
        ids={};new={q:ids.setdefault(sig[q],len(ids)) for q in range(w.n)}
        if len(set(new.values()))==len(set(block.values())):return len(ids)
        block=new
