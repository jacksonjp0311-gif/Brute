"""G_recount for study-040 (deviation #152; new file built from the frozen scripts/recount_039.py, independent of the runner):
regenerates every world from its seed (experiments.worlds_040.world), rebuilds each arm's trace from the seeded passive
actions (worlds_026.actions) plus the stored extra actions by direct simulation of the true machine, checks the stored extra readings,
rechecks the final model's consistency and re-derives every label from the stop and the stored verdict lists with the
frozen 034 rule (scripts/recount_034.lab9 logic): 'ID' needs the final future and start searches UNSAT at every
n = n_min..N and the model behaviourally equal to the truth from the start (own product BFS); 'IDF' the future search UNSAT
at every n and the start search ending SAT; 'K_spent' (A15_cube, A15, A14) a future SAT and a word longer than the actions
left under K = 128; 'unknown' an UNKNOWN verdict or no M1.
For every arm every separating word is re-simulated on the stored M1 and M2, both machines rechecked on the round's
prefix and the truth on every prefix, and the actions used recounted. Writes <study>/RECOUNT_040.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_040.py results/study-040/main"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_040 import load,write_new,sha
from experiments import worlds_040 as W
from scripts.recount_033 import canon,consistent,truth_codes
from scripts.recount_034 import same,_all_unsat,_ends_sat,_words
ORDER=('A15_cube','A15','A14');ACTIVE=ORDER;KS={a:128 for a in ORDER}
LABELS=('ID','IDF','AMB','WRONG','IDU');N_DECLARED=dict(W.SIZES)


def lab14(a,w,N,arm):
    m=a['model'];st=a['stop'];F=a.get('future');S=a.get('start')
    if st=='unknown':
        ok=m is None or any(x[1]=='UNKNOWN' for y in (F,S) if y for x in y['verdicts'])
        return 'IDU' if ok else 'BAD_unknown'
    n=a['n_min']
    if st=='ID':
        if not (_all_unsat(F,n,N) and _all_unsat(S,n,N)):return 'BAD_ID_verdicts'
        return 'ID' if same(m[0],m[1],0,w.transitions,w.emissions,w.start) else 'WRONG'
    if st=='IDF':return 'IDF' if _all_unsat(F,n,N) and _ends_sat(S,n) else 'BAD_IDF_verdicts'
    if st=='K_spent' and arm in ACTIVE:
        r=a['rounds'][-1];return 'AMB' if _ends_sat(F,n) and r.get('word') and len(r['word'])>KS[arm]-a['used'] else 'BAD_K_spent'
    return 'BAD_stop'


def recount_case(c):
    w=W.world(c['seed'],c['family']);bad=[];out={};N=N_DECLARED[c['family']]
    if (w.n,w.k)!=(c['n'],c['k']) or c.get('N')!=N:bad.append('world_shape_or_N')
    pa=list(W.actions(c['seed'],0.0,w.k));tc=canon(w.transitions,w.emissions,w.start)
    for arm,a in c['arms'].items():
        if arm not in ORDER:bad.append(('unknown_arm',arm));continue
        ex=list(a.get('extra_acts') or [])
        acts=pa+ex;codes=truth_codes(w,acts)
        if arm in ACTIVE and [1<<x for x in codes[len(pa)+1:]]!=list(a.get('extra_masks') or []):bad.append((arm,'extra_readings'))
        m=a['model'];mc=m is not None and consistent(m[0],m[1],0,acts,codes);match=m is not None and canon(m[0],m[1],0)==tc
        rec={'label':lab14(a,w,N,arm),'canonical_match':match,'model_consistent':mc,'used':len(ex) if arm in ACTIVE else a['used'],'T_final':len(acts)}
        if rec['label'].startswith('BAD'):bad.append((arm,rec['label']))
        if arm in ACTIVE:
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
        k=f"{c['block']}/{c['key']}/{c['seed']}";per[k],b=recount_case(c)
        if b:bad[k]=b
    labels={arm:{L:sum(1 for v in per.values() if arm in v and v[arm]['label']==L) for L in LABELS} for arm in ORDER}
    act=lambda v:[a for a in ACTIVE if a in v]
    out={'schema':'brute.recount.v37_0','results_sha256':sha(d/'RESULTS.json'),'cases':len(per),'labels':labels,
         'words_unsound':sum(v[a]['words_unsound'] for v in per.values() for a in act(v)),
         'words_checked':sum(v[a]['words_checked'] for v in per.values() for a in act(v)),
         'words_checked_per_arm':{a:sum(v[a]['words_checked'] for v in per.values() if a in v) for a in ACTIVE},
         'truth_inconsistent':sum(sum(v[a]['truth_inconsistent_rounds'] for a in act(v))+sum(not x['truth_consistent_final'] for x in v.values()) for v in per.values()),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,'PASS':not bad and len(per)>0}
    write_new(d/'RECOUNT_040.json',out);print(json.dumps({k:v for k,v in out.items() if k!='per_case'},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
