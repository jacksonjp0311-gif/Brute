"""G_recount for study-034 (deviation #140; new file, independent of the runner): regenerates every world from its seed
(experiments.worlds_026), rebuilds each arm's trace from the seeded passive actions plus the stored extra actions by direct
simulation of the true machine (A9_random's extra actions are regenerated from random.Random(seed*91034+34)), checks the
stored extra readings, rechecks the final model's consistency, and re-derives every label:
  A8, S5, S1: the 033 rule from (unknown, second_found, unique, canonical match) (A8 'none' -> WRONG);
  A9, A9_random: from the stop and the stored verdict lists: 'ID' needs the final future and start searches UNSAT at every
  n = n_min..N and the model behaviourally equal to the truth from the start (own product BFS); 'IDF' needs the future
  search UNSAT at every n and the start search ending SAT; A9 'K_spent' needs a future SAT and a word longer than the
  actions left; A9_random 'AMB' a future SAT; 'unknown' an UNKNOWN verdict or no M1.
For A8 and A9 every separating word is re-simulated on the stored M1 and M2 (equal codes before the last action, different
after), both machines rechecked on the round's prefix and the truth on every prefix, and the actions used recounted.
Writes <study>/RECOUNT_034.json (refuses overwrite); PASS iff every label, count and soundness field reproduces.
  PYTHONPATH=. python scripts/recount_034.py results/study-034/main"""
import json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_034 import load,write_new,sha
from experiments import worlds_026 as W
from scripts.recount_033 import canon,consistent,run,truth_codes,lab
ARMS=('A9','A9_random','A8','S5','S1');K=64;LABELS=('ID','IDF','AMB','WRONG','IDU')
N_DECLARED={'scale8':8,'scale12':12,'scale16':16,'control_cycle3':3}


def same(d1,e1,s1,d2,e2,s2):
    k=len(d1[0]);seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return False
        for a in range(k):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return True


def _all_unsat(S,n_min,N):
    return S is not None and not S['found'] and not S['unknown'] and S['verdicts']==[[n,'UNSAT'] for n in range(n_min,N+1)]


def _ends_sat(S,n_min):
    v=S and S['verdicts'];return bool(v) and S['found'] and v[-1][1]=='SAT' and all(x[1]=='UNSAT' for x in v[:-1]) and v[0][0]==n_min


def lab9(a,w,N,arm):
    m=a['model'];st=a['stop'];F=a.get('future');S=a.get('start')
    if st=='unknown':
        ok=m is None or any(x[1]=='UNKNOWN' for y in (F,S) if y for x in y['verdicts'])
        return 'IDU' if ok else 'BAD_unknown'
    if st=='none':return 'WRONG'
    n=a['n_min']
    if st=='ID':
        if not (_all_unsat(F,n,N) and _all_unsat(S,n,N)):return 'BAD_ID_verdicts'
        return 'ID' if same(m[0],m[1],0,w.transitions,w.emissions,w.start) else 'WRONG'
    if st=='IDF':return 'IDF' if _all_unsat(F,n,N) and _ends_sat(S,n) else 'BAD_IDF_verdicts'
    if st=='K_spent' and arm=='A9':
        r=a['rounds'][-1];return 'AMB' if _ends_sat(F,n) and r.get('word') and len(r['word'])>K-a['used'] else 'BAD_K_spent'
    if st=='AMB' and arm=='A9_random':return 'AMB' if _ends_sat(F,n) else 'BAD_AMB'
    return 'BAD_stop'


def _words(a,acts,codes,w):
    ws=wu=ti=0
    for r in a['rounds']:
        T=r['T']
        if not consistent(w.transitions,w.emissions,w.start,acts[:T],codes[:T+1]):ti+=1
        if r.get('word'):
            (d1,e1),(d2,e2)=r['M1'],r['M2'];p1=run(d1,e1,r['s1'],r['word']);p2=run(d2,e2,r['s2'],r['word']);ws+=1
            ok=(p1[:-1]==p2[:-1] and p1[-1]!=p2[-1] and consistent(d1,e1,0,acts[:T],codes[:T+1]) and consistent(d2,e2,0,acts[:T],codes[:T+1]))
            wu+=not ok
    return dict(words_checked=ws,words_unsound=wu,truth_inconsistent_rounds=ti,
                words_executed_length=sum(len(r['word']) for r in a['rounds'] if r.get('executed')))


def recount_case(c):
    w=W.world(c['seed'],c['family']);bad=[];out={};N=N_DECLARED[c['family']]
    if (w.n,w.k)!=(c['n'],c['k']) or c.get('N')!=N:bad.append('world_shape_or_N')
    pa=list(W.actions(c['seed'],0.0,w.k));tc=canon(w.transitions,w.emissions,w.start)
    for arm in ARMS:
        a=c['arms'][arm];ex=list(a.get('extra_acts') or [])
        if arm=='A9_random':
            rng=random.Random(c['seed']*91034+34);exp=[rng.randrange(w.k) for _ in range(min(c['arms']['A9']['used'],K))]
            if ex!=exp:bad.append((arm,'random_actions'))
        acts=pa+ex;codes=truth_codes(w,acts)
        if arm in ('A8','A9') and [1<<x for x in codes[len(pa)+1:]]!=list(a.get('extra_masks') or []):bad.append((arm,'extra_readings'))
        m=a['model'];mc=m is not None and consistent(m[0],m[1],0,acts,codes);match=m is not None and canon(m[0],m[1],0)==tc
        if arm in ('A9','A9_random'):
            rec={'label':lab9(a,w,N,arm),'canonical_match':match,'model_consistent':mc,'used':len(ex) if arm=='A9' else a['used'],'T_final':len(acts)}
            if rec['label'].startswith('BAD'):bad.append((arm,rec['label']))
        else:
            rec={'label':lab(a,match),'match':match,'model_consistent':mc,'used':len(ex) if arm=='A8' else a['used'],'T_final':len(acts)}
            if arm=='A8' and a['stop']=='none':rec['label']='WRONG'
        if arm in ('A8','A9'):
            rec.update(_words(a,acts,codes,w))
            if rec['words_executed_length']!=a['used']:bad.append((arm,'used_vs_words'))
        rec['truth_consistent_final']=consistent(w.transitions,w.emissions,w.start,acts,codes)
        for kk,v in rec.items():
            if kk in a and a[kk]!=v:bad.append((arm,kk,a[kk],v))
        if a['model_consistent'] is not True and a['model'] is not None:bad.append((arm,'model_inconsistent'))
        out[arm]=rec
    return out,bad


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;d=Path(argv[0]);res=load(d/'RESULTS.json');per={};bad={}
    for c in res['cases']:
        k=f"{c['block']}/{c['family']}/{c['seed']}";per[k],b=recount_case(c)
        if b:bad[k]=b
    labels={arm:{L:sum(1 for v in per.values() if v[arm]['label']==L) for L in LABELS} for arm in ARMS}
    out={'schema':'brute.recount.v31_0','results_sha256':sha(d/'RESULTS.json'),'cases':len(per),'labels':labels,
         'words_unsound':sum(v[a]['words_unsound'] for v in per.values() for a in ('A8','A9')),
         'words_checked':sum(v[a]['words_checked'] for v in per.values() for a in ('A8','A9')),
         'words_checked_A9':sum(v['A9']['words_checked'] for v in per.values()),
         'truth_inconsistent':sum(v['A8']['truth_inconsistent_rounds']+v['A9']['truth_inconsistent_rounds']+sum(not v[a]['truth_consistent_final'] for a in ARMS) for v in per.values()),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,'PASS':not bad and len(per)>0}
    write_new(d/'RECOUNT_034.json',out);print(json.dumps({k:v for k,v in out.items() if k!='per_case'},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
