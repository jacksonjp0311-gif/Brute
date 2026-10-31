"""G_recount for study-045 (BRUTE_PLAN_045; pre-run deviation #163; new file, the frozen scripts/recount_043.py logic unchanged
per arm, with the three 045 arms (A16_N, A16_nf1, A16_nf2), independent of the runner and of brute/). Records:
  replay (smoke only): the frozen recount_043.recount_replay043 on the sealed 040 scale16 traces (A16_N);
  fresh / probe: per arm: worlds_043 world, the seeded passive actions (eps 0) plus the case's extra actions, readings by simulating
          the true machine; label by the frozen 034 rule (recount_041.lab14) and the AMB-at-stop rule (recount_043.label043), with
          the arm's bound N_eff: A16_N N_eff = the family size; A16_nf1 / A16_nf2 N_eff = n_min + delta (#163 item 2), and the
          recorded bound (case and every round with an n_min) must equal n_min + delta;
  future_match (#163 item 3): recomputed independently (the model from s1 versus the true machine from the true final state,
          by product-automaton reachability: equal iff no reachable state pair differs in emission) and must equal the recorded
          field; a misfire is a WRONG label or an IDF label with future_match false.
Writes <study>/RECOUNT_045.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_045.py results/study-045/main"""
import json,sys
from itertools import product
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_043 as W43
from scripts.recount_033 import canon,consistent,truth_codes
from scripts.recount_034 import _words
from scripts.recount_043 import label043,recount_replay043
ORDER=('A16_N','A16_nf1','A16_nf2');DELTA={'A16_N':None,'A16_nf1':1,'A16_nf2':2};LABELS=('ID','IDF','AMB','WRONG','IDU')


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


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;d=Path(argv[0]);res=load(d/'RESULTS.json');per={};bad={};rp={}
    for r in res['replays']:
        k=f"replay/{r['part']}/{r['study']}/{r['key']}/{r['seed']}/{r['variant']}/{r['repeat']}";rp[k],b=recount_replay043(r)
        if b:bad[k]=b
    for c in res['cases']:
        k=f"{c['block']}/{c['key']}/{c['seed']}";per[k],b=recount_case(c)
        if b:bad[k]=b
    main_=[v for k,v in per.items() if k.startswith('main/')]
    labels={arm:{L:sum(1 for v in main_ if arm in v and v[arm]['label']==L) for L in LABELS} for arm in ORDER}
    rl={}
    for k,v in rp.items():
        x=rl.setdefault(k.split('/')[5],{});x[v['label']]=x.get(v['label'],0)+1
    out={'schema':'brute.recount.v42_0','results_sha256':sha(d/'RESULTS.json'),'replays':len(rp),'cases':len(per),'labels_main':labels,
         'labels_all':{arm:{L:sum(1 for v in per.values() if arm in v and v[arm]['label']==L) for L in LABELS} for arm in ORDER},
         'misfires_main':{arm:sum(1 for v in main_ if arm in v and v[arm]['misfire']) for arm in ORDER},
         'replay_labels':rl,'replay_wrong':sum(v['label']=='WRONG' for v in rp.values()),
         'amb_rule_applied':sum('amb_rule' in v for v in rp.values())+sum('amb_rule' in v[a] for v in per.values() for a in v),
         'words_unsound':sum(v[a]['words_unsound'] for v in per.values() for a in v),
         'words_checked':sum(v[a]['words_checked'] for v in per.values() for a in v),
         'words_checked_per_arm':{a:sum(v[a]['words_checked'] for v in per.values() if a in v) for a in ORDER},
         'truth_inconsistent':sum(sum(v[a]['truth_inconsistent_rounds'] for a in v)+sum(not x['truth_consistent_final'] for x in v.values()) for v in per.values()),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,'per_replay':rp,
         'PASS':not bad and len(per)>0}
    write_new(d/'RECOUNT_045.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','per_replay')},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
