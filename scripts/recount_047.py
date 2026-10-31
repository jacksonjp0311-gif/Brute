"""G_recount for study-047 (BRUTE_PLAN_047; pre-run deviation #167; new file; the frozen scripts/recount_046.py per-case logic
copied unchanged apart from the world dispatch (experiments/worlds_047: scale16, control_cycle3, scale20) and the arm set
(API16D, API16D_b, A16_N, API16; every arm at bound N = the family size: 16 / 3 / 20), independent of the runner and of brute/).
Records:
  fresh (main, smoke, probe) and replay (a1, a2, a3_045, a3_046) records alike: world, the seeded passive actions (eps 0) plus the
          case's extra actions, readings by simulating the true machine; label by the frozen 034 rule and the AMB-at-stop rule
          (recount_043.label043) at bound N; future_match recomputed by product-automaton reachability; every recomputed field must
          equal the stored one;
  replay comparison and class (#167): recomputed from the sealed 045 / 046 A16_N record (sha-checked against its SEAL) with
          recount_033.canon: same label (the recounted replay label against the sealed label), same n_min, equal canonical model,
          T_final, executed words, and the difference class (none / infidelity / cap-timing / word-divergence); must equal the
          stored 'replay' fields.
Writes <study>/RECOUNT_047.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_047.py results/study-047/main"""
import json,sys
from itertools import product
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_047 as W43
from scripts.recount_033 import canon,consistent,truth_codes
from scripts.recount_034 import _words
from scripts.recount_043 import label043
ORDER=('API16D','API16D_b','A16_N','API16');DELTA={a:None for a in ORDER};LABELS=('ID','IDF','AMB','WRONG','IDU')
SEALED={'045':ROOT/'results/study-045/main','046':ROOT/'results/study-046/main'}
REPLAY_ARM={'a1':'A16_N','a2':'API16','a3_045':'API16D','a3_046':'API16D'}


def sealed(src):
    d=SEALED[src];seal=load(d/'SEAL.json')
    if sha(d/'RESULTS.json')!=seal['results_sha256']:raise SystemExit('sealed '+src+' RESULTS changed')
    return {(c['key'],c['seed']):c for c in load(d/'RESULTS.json')['cases'] if c.get('block','main')=='main'}


def fut_equal(d1,e1,s1,d2,e2,s2,k):
    """Product-automaton reachability: equal iff no reachable state pair differs in emission (independent of brute/ and 034)."""
    seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return False
        for a in range(k):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return True


def n_eff(arm,a,N):return N if DELTA[arm] is None else (None if a['n_min'] is None else a['n_min']+DELTA[arm])


def recount_case(c):
    """recount_046.recount_case with the 047 arms (all at bound N) and worlds_047."""
    w=W43.world(c['seed'],c['family']);bad=[];out={};N=W43.SIZES[c['family']]
    if (w.n,w.k)!=(c['n'],c['k']) or c.get('N')!=N:bad.append('world_shape_or_N')
    pa=list(W43.actions(c['seed'],0.0,w.k));tc=canon(w.transitions,w.emissions,w.start)
    for arm,a in c['arms'].items():
        if arm not in ORDER:bad.append(('unknown_arm',arm));continue
        ex=list(a.get('extra_acts') or []);acts=pa+ex;codes=truth_codes(w,acts)
        if [1<<x for x in codes[len(pa)+1:]]!=list(a.get('extra_masks') or []):bad.append((arm,'extra_readings'))
        m=a['model'];mc=m is not None and consistent(m[0],m[1],0,acts,codes);match=m is not None and canon(m[0],m[1],0)==tc
        if a.get('delta')!=DELTA[arm]:bad.append((arm,'delta',a.get('delta')))
        Ne=n_eff(arm,a,N)
        if DELTA[arm] is not None:
            for r in a['rounds']:
                if r.get('n_min') is not None and r.get('bound')!=r['n_min']+DELTA[arm]:bad.append((arm,'round_bound',r['T']))
            if a['stop']!='unknown' and a.get('bound')!=Ne:bad.append((arm,'bound',a.get('bound'),Ne))
        elif a.get('bound')!=N:bad.append((arm,'bound_N'))
        if Ne is None:
            if a['stop']!='unknown':bad.append((arm,'no_n_min_but_decided'))
            L,det=('IDU' if a['stop']=='unknown' else 'BAD_no_n_min'),None
        else:L,det=label043(a,w,Ne,acts,codes,w.k)
        q=w.start
        for x in acts:q=w.transitions[q][x]
        fm=bool(m is not None and a.get('s1') is not None and fut_equal(m[0],m[1],a['s1'],w.transitions,w.emissions,q,w.k))
        rec={'label':L,'canonical_match':match,'model_consistent':mc,'used':len(ex),'T_final':len(acts),'future_match':fm,'N_eff':Ne}
        if det is not None:rec['amb_rule']=det
        if L.startswith('BAD'):bad.append((arm,L,det))
        rec.update(_words(a,acts,codes,w))
        if rec['words_executed_length']!=a['used']:bad.append((arm,'used_vs_words'))
        rec['truth_consistent_final']=consistent(w.transitions,w.emissions,w.start,acts,codes)
        rec['misfire']=bool(L=='WRONG' or (L=='IDF' and not fm))
        for kk,v in rec.items():
            if kk in a and kk!='N_eff' and a[kk]!=v:bad.append((arm,kk,a[kk],v))
        if a['model_consistent'] is not True and a['model'] is not None:bad.append((arm,'model_inconsistent'))
        out[arm]=rec
    return out,bad


def replay_check(c,rec,S,arm):
    """Independent replay comparison: recounted replay label vs the sealed A16_N label, n_min, canonical model, T_final, words, class."""
    s=S[(c['key'],c['seed'])]['arms']['A16_N'];a=c['arms'][arm];bad=[]
    cm=lambda m:None if m is None else canon(m[0],m[1],0)
    x={'label':[rec['label'],s['label']],'n_min':[a['n_min'],s['n_min']],'canonical_model_equal':cm(a['model'])==cm(s['model']),
       'T_final':[rec['T_final'],s['T_final']]}
    x['same']=bool(x['label'][0]==x['label'][1] and x['n_min'][0]==x['n_min'][1] and x['canonical_model_equal'])
    x['same_step']=bool(x['same'] and x['T_final'][0]==x['T_final'][1])
    wa=[r['word'] for r in a['rounds'] if r.get('word')];ws=[r['word'] for r in s['rounds'] if r.get('word')];x['words_equal']=wa==ws
    ca=sum(r['capped'] for r in a['rounds'])>0;cs=sum(r['capped'] for r in s['rounds'])>0
    x['class']='none' if (x['same'] and x['words_equal']) else ('infidelity' if not ca and not cs else ('cap-timing' if x['words_equal'] else 'word-divergence'))
    x['sealed_capped_any']=cs;x['replay_capped_any']=ca
    st=c.get('replay') or {}
    for k in ('label','n_min','canonical_model_equal','T_final','same','same_step','words_equal','class','sealed_capped_any','replay_capped_any'):
        if st.get(k)!=x[k]:bad.append(('replay',k,st.get(k),x[k]))
    return x,bad


def _counts(vals,arm):return {L:sum(1 for v in vals if arm in v and v[arm]['label']==L) for L in LABELS}


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;d=Path(argv[0]);res=load(d/'RESULTS.json');per={};bad={};rp={};rpc={}
    S={src:sealed(src) for src in ('045','046')} if res['replays'] else {}
    for c in res['replays']:
        k=f"{c['block']}/{c['key']}/{c['seed']}";rp[k],b=recount_case(c);arm=REPLAY_ARM[c['block']]
        x,b2=replay_check(c,rp[k][arm],S[c['source']],arm);x['part']=c['block'];rpc[k]=x;b=b+b2
        if b:bad[k]=b
    for c in res['cases']:
        k=f"{c['block']}/{c['key']}/{c['seed']}"+(f"/{c['probe']}" if c.get('probe') else '');per[k],b=recount_case(c)
        if b:bad[k]=b
    main_=[v for k,v in per.items() if k.startswith('main/')];allv=list(per.values())+list(rp.values())
    out={'schema':'brute.recount.v44_0','results_sha256':sha(d/'RESULTS.json'),'replays':len(rp),'cases':len(per),
         'labels_main':{arm:_counts(main_,arm) for arm in ORDER},'labels_all':{arm:_counts(per.values(),arm) for arm in ORDER},
         'labels_scale16_main':{arm:_counts([v for k,v in per.items() if k.startswith('main/scale16/')],arm) for arm in ORDER},
         'labels_scale20_main':{arm:_counts([v for k,v in per.items() if k.startswith('main/scale20/')],arm) for arm in ORDER},
         'replay_by_part':{p:{'n':sum(1 for x in rpc.values() if x['part']==p),'same':sum(x['same'] for x in rpc.values() if x['part']==p),
                              'classes':{q:sum(1 for x in rpc.values() if x['part']==p and x['class']==q) for q in ('none','cap-timing','word-divergence','infidelity')}}
                           for p in REPLAY_ARM},'replay_compare':rpc,
         'misfires_main':{arm:sum(1 for v in main_ if arm in v and v[arm]['misfire']) for arm in ORDER},
         'replay_wrong':sum(v[a]['label']=='WRONG' for v in rp.values() for a in v),
         'amb_rule_applied':sum('amb_rule' in v[a] for v in allv for a in v),
         'words_unsound':sum(v[a]['words_unsound'] for v in allv for a in v),
         'words_checked':sum(v[a]['words_checked'] for v in allv for a in v),
         'words_checked_per_arm':{a:sum(v[a]['words_checked'] for v in allv if a in v) for a in ORDER},
         'truth_inconsistent':sum(sum(v[a]['truth_inconsistent_rounds'] for a in v)+sum(not x['truth_consistent_final'] for x in v.values()) for v in allv),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,'per_replay':rp,
         'PASS':not bad and len(per)>0}
    write_new(d/'RECOUNT_047.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','per_replay','replay_compare')},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
