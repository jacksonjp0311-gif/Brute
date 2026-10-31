"""G_recount for study-043 (BRUTE_PLAN_043; pre-run deviation #159; new file, the frozen scripts/recount_042.py logic unchanged
with the 043 world dispatch experiments.worlds_043 (lowobs12 from worlds_040, scale16 from worlds_039), independent of the runner
and of brute/). Records:
  replay (smoke only): the frozen recount_041.recount_replay on the sealed 040 scale16 final A14 trace, AMB-at-stop rule as 042;
  fresh / probe: per arm (A16, A14): worlds_043 world, the seeded passive actions (eps 0) plus the sealed extra actions, readings
          by simulating the true machine; label by the frozen 034 rule (recount_041.lab14); the AMB-at-stop rule of recount_042
          (plain-CNF reference experiments.v0310_reference.exists_different) for AMB and K_spent stops.
Writes <study>/RECOUNT_043.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_043.py results/study-043/main"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_043 as W43
from experiments.v0310_reference import exists_different
from scripts.recount_033 import canon,consistent,truth_codes
from scripts.recount_034 import _words,run
from scripts.recount_041 import lab14,recount_replay,sealed,WM
ORDER=('A16','A14');LABELS=('ID','IDF','AMB','WRONG','IDU');M=4


def cur(d,acts):
    q=0
    for a in acts:q=d[q][a]
    return q


def amb_ok(acts,codes,k,N,M1,s1,F,word=None,M2=None,s2=None):
    """The AMB-at-stop rule; returns (ok, detail)."""
    if M1 is None or not F or not F['verdicts'] or F['verdicts'][-1][1]!='SAT':return False,'future_not_ending_SAT'
    ns=F['verdicts'][-1][0];L=N+len(M1[0])-1
    if not consistent(M1[0],M1[1],0,acts,codes):return False,'M1_inconsistent'
    if s1!=cur(M1[0],acts):return False,'s1'
    if not exists_different(acts,codes,ns,k,M,M1,s1,'future',L):return False,'reference_finds_no_rival'
    if word is not None:
        if M2 is None or not consistent(M2[0],M2[1],0,acts,codes):return False,'M2_inconsistent'
        p1=run(M1[0],M1[1],s1,word);p2=run(M2[0],M2[1],s2,word)
        if not (p1[:-1]==p2[:-1] and p1[-1]!=p2[-1]):return False,'word_does_not_separate'
    return True,{'n_star':ns,'L':L}


def label043(a,w,N,acts,codes,k):
    st=a['stop']
    if st=='AMB':
        ok,det=amb_ok(acts,codes,k,N,a['model'],a.get('s1'),a.get('future'));return ('AMB' if ok else 'BAD_AMB'),det
    lab=lab14(a,w,N)
    if st=='K_spent' and lab=='AMB':
        r=a['rounds'][-1];T=r['T']
        ok,det=amb_ok(acts[:T],codes[:T+1],k,N,r['M1'],r['s1'],r.get('future'),r.get('word'),r.get('M2'),r.get('s2'))
        return ('AMB' if ok else 'BAD_AMB_K_spent'),det
    return lab,None


def recount_replay043(r):
    """Frozen recount_041 checks; an AMB stop is then judged by the AMB-at-stop rule instead of the frozen BAD_stop."""
    rec,bad=recount_replay(r)
    if r['stop']=='AMB':
        c=sealed(r['study'])[(r['key'],r['seed'])];Wm=WM[r['study']];w=Wm.world(c['seed'],c['family']);a=c['arms']['A14']
        acts=list(Wm.actions(c['seed'],0.0,w.k))+list(a['extra_acts']);codes=truth_codes(w,acts)
        ok,det=amb_ok(acts,codes,w.k,c['N'],r['model'],r['s1'],r['future']);bad=[b for b in bad if b!='BAD_stop']
        rec['label']='AMB' if ok else 'BAD_AMB';rec['amb_rule']=det
        if not ok:bad.append(('BAD_AMB',det))
    return rec,bad


def recount_case(c):
    w=W43.world(c['seed'],c['family']);bad=[];out={};N=W43.SIZES[c['family']]
    if (w.n,w.k)!=(c['n'],c['k']) or c.get('N')!=N:bad.append('world_shape_or_N')
    pa=list(W43.actions(c['seed'],0.0,w.k));tc=canon(w.transitions,w.emissions,w.start)
    for arm,a in c['arms'].items():
        if arm not in ORDER:bad.append(('unknown_arm',arm));continue
        ex=list(a.get('extra_acts') or []);acts=pa+ex;codes=truth_codes(w,acts)
        if [1<<x for x in codes[len(pa)+1:]]!=list(a.get('extra_masks') or []):bad.append((arm,'extra_readings'))
        m=a['model'];mc=m is not None and consistent(m[0],m[1],0,acts,codes);match=m is not None and canon(m[0],m[1],0)==tc
        L,det=label043(a,w,N,acts,codes,w.k)
        rec={'label':L,'canonical_match':match,'model_consistent':mc,'used':len(ex),'T_final':len(acts)}
        if det is not None:rec['amb_rule']=det
        if L.startswith('BAD'):bad.append((arm,L,det))
        rec.update(_words(a,acts,codes,w))
        if rec['words_executed_length']!=a['used']:bad.append((arm,'used_vs_words'))
        rec['truth_consistent_final']=consistent(w.transitions,w.emissions,w.start,acts,codes)
        for kk,v in rec.items():
            if kk in a and a[kk]!=v:bad.append((arm,kk,a[kk],v))
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
    out={'schema':'brute.recount.v40_0','results_sha256':sha(d/'RESULTS.json'),'replays':len(rp),'cases':len(per),'labels_main':labels,
         'labels_all':{arm:{L:sum(1 for v in per.values() if arm in v and v[arm]['label']==L) for L in LABELS} for arm in ORDER},
         'replay_labels':rl,'replay_wrong':sum(v['label']=='WRONG' for v in rp.values()),
         'amb_rule_applied':sum('amb_rule' in v for v in rp.values())+sum('amb_rule' in v[a] for v in per.values() for a in v),
         'words_unsound':sum(v[a]['words_unsound'] for v in per.values() for a in v),
         'words_checked':sum(v[a]['words_checked'] for v in per.values() for a in v),
         'words_checked_per_arm':{a:sum(v[a]['words_checked'] for v in per.values() if a in v) for a in ORDER},
         'truth_inconsistent':sum(sum(v[a]['truth_inconsistent_rounds'] for a in v)+sum(not x['truth_consistent_final'] for x in v.values()) for v in per.values()),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,'per_replay':rp,
         'PASS':not bad and len(per)>0}
    write_new(d/'RECOUNT_043.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','per_replay')},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
