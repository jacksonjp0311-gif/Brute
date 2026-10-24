"""Reusable macro actions, exact primitive costs, verified in finite world."""
from __future__ import annotations
from collections import Counter
from heapq import heappush,heappop

def mine_macros(plans,min_support=2,max_len=3):
    counts=Counter()
    for p in plans:
        for k in range(2,min(max_len,len(p))+1):
            for i in range(len(p)-k+1):counts[tuple(p[i:i+k])]+=1
    return tuple(sorted((s for s,n in counts.items() if n>=min_support),key=lambda s:(-counts[s],len(s),s)))

def macro_plan(model,start,goal,macros=()):
    model.schema.validate(start);model.schema.validate(goal)
    queue=[(0,0,start)];best={start:0};previous={start:None};ticket=0;expansions=0
    primitives=tuple((i,) for i in range(len(model.actions)))
    for a in (*primitives,*macros):
        if not a or any(i<0 or i>=len(model.actions) for i in a):raise ValueError('invalid macro')
    while queue:
        dist,_,s=heappop(queue)
        if dist!=best[s]:continue
        expansions+=1
        if s==goal:
            seq=[];u=s
            while previous[u] is not None:
                prev,frag=previous[u];seq[:0]=list(frag);u=prev
            return {'status':'solved','actions':seq,'cost':dist,'expansions':expansions,
                    'shortest_certified':model.identified()}
        for frag in (*primitives,*macros):
            t=s
            for a in frag:
                t=model.certified(a,t)
                if t is None:break
            if t is None:continue
            newdist=dist+len(frag)
            if newdist<best.get(t,10**9):
                best[t]=newdist;previous[t]=(s,frag);ticket+=1
                heappush(queue,(newdist,ticket,t))
    return {'status':'abstain_unknown_or_unreachable','actions':None,'cost':None,
            'expansions':expansions,'shortest_certified':False}
