"""Brute v0.69.0 (BRUTE_PLAN_073): bitset apartness, greedy clique, exact maximum clique and apart pairs. New file; nothing earlier is touched.

These functions return EXACTLY what brute.scalesearch15.apart_matrix / greedy_clique, brute.api.certify20p.max_clique0 and the pair set of
Pool15._update return, but they hold each trace position's apart neighbours as one Python int (a bitset) instead of a set of ints and a
T x T bytearray matrix, and they build the relation by the same recurrence on whole rows. The old max_clique0 built one Python set of
about T/1.4 integers per position (about 1.4 GB of Python objects at T = 5700, the memory kill of study 072's true+3 arm); this holds
T bitsets of T bits (4 MB at T = 5700, 200 MB at T = 40000).
Apartness (as scalesearch15): positions t < u are apart iff masks[t] & masks[u] == 0, or (u < T, acts[t] == acts[u] and positions t+1
and u+1 are apart). Host-agnostic: no I/O, network, threads, child processes or global state.
"""
from __future__ import annotations

__all__=['apart_bitsets','greedy_clique33','max_clique33','apart_pairs33']


def apart_bitsets(masks,acts):
    """adj[t] = bitset (int) of the positions apart from t (symmetric, bit t clear), t = 0..T."""
    T=len(acts);T1=T+1;full=(1<<T1)-1
    by_mask={};by_act=[0]*(max(acts)+1 if acts else 1)
    for u,mk in enumerate(masks):by_mask[mk]=by_mask.get(mk,0)|(1<<u)
    for u,a in enumerate(acts):by_act[a]|=1<<u               # positions u < T with acts[u] == a
    base={mk:0 for mk in by_mask}
    for mk in by_mask:
        for m2,b in by_mask.items():
            if not (mk&m2):base[mk]|=b                       # positions whose own mask is disjoint from mk
    row=[0]*(T1+1)                                            # row[t]: apart partners u > t
    for t in range(T,-1,-1):
        above=full&~((1<<(t+1))-1);r=base[masks[t]]&above
        if t<T:r|=(by_act[acts[t]]&(row[t+1]>>1))&above      # u < T is implied by by_act (only u < T carry an action)
        row[t]=r
    col=[0]*(T1+1)                                            # col[u]: apart partners t < u
    for u in range(T,-1,-1):
        below=(1<<u)-1;c=base[masks[u]]&below
        if u<T:c|=(by_act[acts[u]]&(col[u+1]>>1))&below
        col[u]=c
    return [row[t]|col[t] for t in range(T1)]


def _bits(x):
    out=[]
    while x:
        low=x&-x;out.append(low.bit_length()-1);x^=low
    return out


def greedy_clique33(adj):
    """scalesearch15.greedy_clique: position 0, then the others by decreasing degree (ties by position), added when apart from every member."""
    T1=len(adj);deg=[a.bit_count() for a in adj];C=[0];cand=adj[0]
    for t in sorted(range(1,T1),key=lambda t:(-deg[t],t)):
        if (cand>>t)&1 and all((adj[t]>>c)&1 for c in C):C.append(t)
    return C


def max_clique33(adj,floor,cap=200000):
    """(clique, exact): certify20p.max_clique0 on bitsets: the largest clique containing position 0, never smaller than floor; exact unless
    the node cap is hit. Same branching order and tie-breaks as max_clique0, so the same answer."""
    n=len(adj);deg=[a.bit_count() for a in adj];best=sorted(floor);nodes=[0]
    def colour_sort(P):
        P=sorted(P,key=lambda v:(-deg[v],v));cls=[]
        for v in P:
            av=adj[v]
            for i,c in enumerate(cls):
                if not (av&c):cls[i]=c|(1<<v);break
            else:cls.append(1<<v)
        order=[];bounds=[]
        for i,c in enumerate(cls):
            for v in _bits(c):order.append(v);bounds.append(i+1)
        return order,bounds
    def expand(R,P):
        nonlocal best
        nodes[0]+=1
        if nodes[0]>cap:return
        order,bounds=colour_sort(P)
        for i in range(len(order)-1,-1,-1):
            if len(R)+bounds[i]<=len(best):return
            v=order[i];R2=R+[v];av=adj[v];P2=[u for u in order[:i] if (av>>u)&1]
            if not P2:
                if len(R2)>len(best):best=sorted(R2)
            else:expand(R2,P2)
    expand([0],_bits(adj[0]))
    return best,nodes[0]<=cap


def apart_pairs33(adj,masks):
    """{(t,u): t < u, apart on the trace, own masks intersect}: Pool15._update's pair set."""
    T1=len(adj);out=set();by_mask={}
    for u,mk in enumerate(masks):by_mask[mk]=by_mask.get(mk,0)|(1<<u)
    inter={mk:0 for mk in by_mask}
    for mk in by_mask:
        for m2,b in by_mask.items():
            if mk&m2:inter[mk]|=b
    for t in range(T1):
        x=adj[t]&inter[masks[t]]&~((1<<(t+1))-1)
        for u in _bits(x):out.add((t,u))
    return out
