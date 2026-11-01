"""GTABLE56 audit for study-056 (BRUTE_PLAN_056 criterion GTABLE56; pre-run deviation #185). New file. For every API20L / API20L_b
record of a block, from the trace alone (the world's passive actions plus the record's extra_acts, read noise-free from the world
through the frozen run_reference_047 trace), the observation table is replayed entry by entry:
  table:   at each logged step T the basis is extended in trace order from the previous basis (certify20l.table_of on the prefix
           0..T), the hypothesis and its missing / conflict cells are recomputed (certify20l.hypothesis) and must equal the entry's
           rows / missing / conflicts; a fill entry's word and kind must equal certify20l.fill_word, and the word must be what the
           walk then did (acts[T:T+len(word)]); a rows_exceed_N entry must have rows > N;
  checks:  each check entry is matched, in order, to the record's next round; that round's M1 must equal the recomputed H and its
           s1 H's state after the prefix; a counterexample word must be the next actions of the walk and must distinguish H from
           the SAT rival (scalesearch8.run_word from (H, s1) and (M2, s2) give different readings: checked here);
  basis:   the final basis rows are pairwise apart, recomputed here by explicit word search independent of scalesearch15 (some
           l >= 0 with equal actions for i < l and disjoint readings at t+l, u+l), so every consistent machine has >= rows states;
  summary: the record's table summary (basis, rows, columns, hypotheses, counterexamples, fill_steps, log) equals the replay.
Used by run_reference_056 (block main and smoke) and by the GTABLE56 gate. No wall time is used."""
from __future__ import annotations
import json
from experiments import worlds_050 as W50
from scripts import run_reference_047 as R47
from brute.api import certify20l as L
from brute.scalesearch8 import run_word
R47.ORDER=('API20L','API20L_b');R47.DELTA={a:None for a in R47.ORDER};R47.KEYS=('scale20t','compat20t');R47.W43=W50


def _j(x):return json.dumps(x,sort_keys=True)


def apart_word(masks,acts,t,u):
    T=len(acts);l=0
    while True:
        if not (masks[t+l]&masks[u+l]):return list(acts[t:t+l])
        if t+l>=T or u+l>=T or acts[t+l]!=acts[u+l]:return None
        l+=1


def audit_arm(c,arm):
    a=c['arms'][arm];v=R47.view(c,arm);w,acts,codes=R47.trace(v);masks=[1<<x for x in codes];bad=[];N=c['N']
    tb=a.get('table') or {};log=tb.get('log') or [];rounds=a.get('rounds') or [];B=[0];j=0;cols=[];hyps=0;cex=0;fill=0
    for i,ent in enumerate(log):
        T=ent['T']
        if T>len(acts):bad.append((i,'T_beyond_trace'));break
        m=masks[:T+1];ac=acts[:T];tab=L.table_of(m,ac,B);B=list(tab['basis'])
        if ent['rows']!=len(B):bad.append((i,'rows',ent['rows'],len(B)))
        if ent['kind']=='rows_exceed_N':
            if not len(B)>N:bad.append((i,'rows_not_above_N'))
            continue
        H,miss,conf=L.hypothesis(m,ac,w.k,tab)
        if ent['missing']!=len(miss) or ent['conflicts']!=len(conf):bad.append((i,'cells'))
        if ent['kind'] in ('home','cell','route'):
            wd,kind=L.fill_word(m,ac,w.k,tab,H,miss)
            if wd!=ent['word'] or kind!=ent['kind']:bad.append((i,'fill_word'))
            if list(acts[T:T+len(ent['word'])])!=ent['word']:bad.append((i,'fill_not_walked'))
            if kind=='home' and wd not in cols:cols.append(list(wd))
            fill+=len(ent['word']);continue
        if ent['kind']!='check':bad.append((i,'kind',ent['kind']));continue
        hyps+=1
        if j>=len(rounds):bad.append((i,'no_round'));continue
        r=rounds[j];j+=1;s1=0
        for x in ac:s1=H[0][s1][x]
        if _j(r.get('M1'))!=_j([list(map(list,H[0])),list(H[1])]) or r.get('s1')!=s1:bad.append((i,'H_differs'))
        if r.get('check')!=ent.get('check'):bad.append((i,'check_label'))
        if 'counterexample' in ent:
            cw=ent['counterexample'];cex+=1
            if r.get('word')!=cw:bad.append((i,'cex_not_round_word'))
            if list(acts[T:T+len(cw)])!=cw:bad.append((i,'cex_not_walked'))
            M2=r.get('M2');s2=r.get('s2')
            if M2 is None or run_word(H[0],H[1],s1,cw)==run_word(M2[0],M2[1],s2,cw):bad.append((i,'cex_does_not_distinguish'))
    if j!=len(rounds):bad.append(('rounds_unmatched',len(rounds)-j))
    pa=all(apart_word(masks,acts,B[x],B[y]) is not None for x in range(len(B)) for y in range(x+1,len(B)))
    if not pa:bad.append(('basis_not_pairwise_apart',))
    want={'basis':B,'rows':len(B),'columns':cols,'n_columns':len(cols),'hypotheses':hyps,'counterexamples':cex,'fill_steps':fill,'log':log}
    if _j({k:tb.get(k) for k in want})!=_j(want):bad.append(('summary_differs',))
    return {'id':v['id'],'entries':len(log),'rows':len(B),'columns':len(cols),'hypotheses':hyps,'counterexamples':cex,
            'counterexamples_checked':cex,'fill_steps':fill,'basis_pairwise_apart':pa,'mismatches':bad,'pass':not bad and bool(log)}


def audit(res,block,arms=('API20L','API20L_b'),keys=('scale20t','compat20t')):
    rows=[audit_arm(c,g) for c in res['cases'] if c['block']==block and c['key'] in keys for g in arms if g in c['arms']]
    return {'records':len(rows),'entries':sum(r['entries'] for r in rows),'counterexamples_checked':sum(r['counterexamples_checked'] for r in rows),
            'mismatch_records':[r['id'] for r in rows if not r['pass']],'per_record':rows,'PASS':bool(rows) and all(r['pass'] for r in rows)}
