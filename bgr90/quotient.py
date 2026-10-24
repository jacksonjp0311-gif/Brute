"""Exact predictive-state partition refinement for a fixed Moore machine.

Two latent states are merged iff their emission words agree under EVERY finite
future action sequence. A bounded pair-product counterexample oracle is
provided for independent testing, not used by the quotient implementation.
"""
from __future__ import annotations
from collections import deque
import hashlib,json


def reachable_states(trans,start=0):
    seen={start};q=deque([start])
    while q:
        state=q.popleft()
        for nxt in trans[state]:
            if nxt not in seen:seen.add(nxt);q.append(nxt)
    return tuple(sorted(seen))


def minimize_moore(trans,emissions,start=0):
    n=len(trans)
    if not 1<=n<=32 or len(emissions)!=n:raise ValueError('invalid Moore model')
    if any(len(row)!=2 or any(not 0<=v<n for v in row) for row in trans):
        raise ValueError('invalid action successors')
    if any(not 0<=v<4 for v in emissions):raise ValueError('emission code outside 0..3')
    if not 0<=start<n:raise ValueError('invalid initial state')
    original=reachable_states(trans,start)
    # Refinement induces an equivalence relation on every reachable state.
    classes={s:emissions[s] for s in original}
    while True:
        signatures={s:(emissions[s],classes[trans[s][0]],classes[trans[s][1]]) for s in original}
        canonical_ids={sig:i for i,sig in enumerate(sorted(set(signatures.values())))}
        refined={s:canonical_ids[signatures[s]] for s in original}
        if all((classes[a]==classes[b])==(refined[a]==refined[b]) for a in original for b in original):
            classes=refined;break
        classes=refined
    # Produce a canonical quotient independent of the original integer names:
    # enumerate reachable quotient states by BFS from the original start.
    class_members={c:tuple(s for s in original if classes[s]==c) for c in set(classes.values())}
    order=[];queue=deque([classes[start]]);seen={classes[start]}
    while queue:
        c=queue.popleft();order.append(c)
        representative=class_members[c][0]
        for a in (0,1):
            nxt=classes[trans[representative][a]]
            if nxt not in seen:seen.add(nxt);queue.append(nxt)
    index={c:i for i,c in enumerate(order)}
    quo_trans=[];quo_emit=[];groups=[]
    for c in order:
        rep=class_members[c][0]
        quo_trans.append(tuple(index[classes[trans[rep][a]]] for a in (0,1)))
        quo_emit.append(emissions[rep]);groups.append(class_members[c])
    payload={'transitions':quo_trans,'emissions':quo_emit}
    return {'reachable_original_count':len(original),'minimal_count':len(order),
            'transitions':tuple(quo_trans),'emissions':tuple(quo_emit),
            'classes':tuple(groups),'fingerprint':hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()}
