"""GCUBE55 audit for study-055 (BRUTE_PLAN_055 criterion GCUBE55; pre-run deviation #183). New file, independent of brute/: it does
not import certify20c, scalesearch15 or any solver. For every API20C / API20C_b record of a block, from the trace alone (the world's
passive actions plus the record's extra_acts, read noise-free from the world through the frozen run_reference_047 trace):
  plan:    for each capped query in the record's cube log (n, T): positions 0..min(5, T+1)-1; every colouring of those positions in
           range(n) by brute force (itertools.product, lexicographic), kept iff it is a restricted-growth string (first-visit
           symmetry: c[0] = 0 and c[i] <= max(c[:i]) + 1); pairs = position pairs (t < u) with intersecting readings that are apart on
           the trace prefix 0..T, apartness recomputed here by explicit word search (some l >= 0 with u + l <= T, equal actions at
           t+i and u+i for i < l, and disjoint readings at t+l and u+l); a colouring is pruned iff it gives t and u one colour for some
           such pair (the first pair in sorted order is the one named). The recomputed live list, its order and the pruned list
           (cube and pair) must equal the record's;
  pruned:  every pruned cube is checked UNSAT independently: the named pair's distinguishing word is exhibited (start t, u, word,
           the two disjoint readings); a deterministic machine that puts t and u in one state reads the same after the same word,
           so no machine satisfies the cube (Exact);
  conflicts: the record's per-call chunk conflicts (rounds' chunk_conflicts) sum to its conflicts_spent; each cube query is
           matched, in log order, to a distinct later-or-equal logged call whose chunk count is 1 + sum(cube_chunks) and whose
           conflict sum is first + sum(cube_conflicts), with first = its first chunk.
Used by run_reference_055 (block main and smoke) and by the GCUBE55 gate. No wall time is used."""
from __future__ import annotations
import itertools
from experiments import worlds_050 as W50
from scripts import run_reference_047 as R47
DEPTH=5
# same bindings as run_reference_055 (study-055 arms and worlds), so the audit also works when imported alone
R47.ORDER=('API20C','API20C_b');R47.DELTA={a:None for a in R47.ORDER};R47.KEYS=('scale20t','compat20t');R47.W43=W50


def apart_word(masks,acts,T,t,u):
    """(l, word) for the shortest l with u+l <= T, acts[t+i] == acts[u+i] (i < l) and masks[t+l] & masks[u+l] == 0, else None."""
    l=0
    while u+l<=T:
        if not (masks[t+l]&masks[u+l]):return l,list(acts[t:t+l])
        if u+l>=T or acts[t+l]!=acts[u+l]:return None
        l+=1
    return None


def plan(n,T,masks,acts,depth=DEPTH):
    d=min(depth,T+1);pos=list(range(d))
    pairs=sorted((t,u) for t in pos for u in pos if t<u and masks[t]&masks[u] and apart_word(masks,acts,T,t,u) is not None)
    live=[];pruned=[]
    for c in itertools.product(range(n),repeat=d):
        if not c or c[0]!=0 or any(c[i]>max(c[:i])+1 for i in range(1,d)):continue
        hit=next(((t,u) for (t,u) in pairs if c[t]==c[u]),None)
        if hit is None:live.append(list(c))
        else:pruned.append([list(c),list(hit)])
    return pos,live,pruned,pairs


def audit_arm(c,arm):
    a=c['arms'][arm];v=R47.view(c,arm);w,acts,codes=R47.trace(v);masks=[1<<x for x in codes];bad=[];qs=((a.get('cube') or {}).get('queries')) or []
    calls=[ch for r in a['rounds'] for ch in r.get('chunk_conflicts',[])]
    tot=sum(sum(ch) for ch in calls);sum_ok=tot==a.get('conflicts_spent')
    if not sum_ok:bad.append(('conflicts_spent',tot,a.get('conflicts_spent')))
    j=0;pruned_checked=0;cubes=0;npr=0;closed=0;sat=0;opn=0
    for i,q in enumerate(qs):
        T=q['T']
        if T>len(acts):bad.append((i,'T_beyond_trace'));continue
        pos,live,pruned,_=plan(q['n'],T,masks,acts)
        if pos!=q['positions']:bad.append((i,'positions'))
        if live!=q['cubes']:bad.append((i,'cubes_or_order'))
        if pruned!=q['pruned']:bad.append((i,'pruned'))
        for cb,(t,u) in q['pruned']:
            wd=apart_word(masks,acts,T,t,u)
            if wd is None or cb[t]!=cb[u]:bad.append((i,'pruned_not_unsat',cb,[t,u]))
            else:pruned_checked+=1
        want=(1+sum(q['cube_chunks']),q['first']+sum(q['cube_conflicts']))
        while j<len(calls) and not (len(calls[j])==want[0] and sum(calls[j])==want[1] and calls[j][0]==q['first']):j+=1
        if j>=len(calls):bad.append((i,'no_matching_call',want))
        else:j+=1
        cubes+=len(q['cubes']);npr+=len(q['pruned']);closed+=len(q['closed']);sat+=q['sat'] is not None;opn+=len(q['open'] or [])
    return {'id':v['id'],'queries':len(qs),'cubes':cubes,'pruned':npr,'pruned_checked_unsat':pruned_checked,'closed_unsat':closed,
            'sat_cubes':sat,'open_at_stop':opn,'conflict_sum_ok':sum_ok,'per_query':[{'n':q['n'],'phase':q['phase'],'T':q['T'],'cubes':len(q['cubes']),
            'pruned':len(q['pruned']),'closed':len(q['closed']),'sat':q['sat'],'open':len(q['open'] or []),'why':q['why']} for q in qs],
            'mismatches':bad,'pass':not bad}


def audit(res,block,arms=('API20C','API20C_b'),keys=('scale20t','compat20t')):
    rows=[audit_arm(c,g) for c in res['cases'] if c['block']==block and c['key'] in keys for g in arms if g in c['arms']]
    return {'records':len(rows),'queries':sum(r['queries'] for r in rows),'cubes':sum(r['cubes'] for r in rows),
            'pruned':sum(r['pruned'] for r in rows),'pruned_checked_unsat':sum(r['pruned_checked_unsat'] for r in rows),
            'mismatch_records':[r['id'] for r in rows if not r['pass']],'per_record':rows,'PASS':bool(rows) and all(r['pass'] for r in rows)}
