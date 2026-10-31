"""G_recount for study-041 (BRUTE_PLAN_041; deviation #154; new file built from the frozen scripts/recount_040.py, independent of the
runner and of brute/encaudit16). Two record kinds:
  replay  rebuilds the sealed final A14 trace from the seed (experiments.worlds_039 / worlds_040 .actions, eps 0) plus the sealed
          extra actions, readings by direct simulation of the true machine; checks the replay's T and the sealed [check, n_min]
          against the sealed study file; rechecks the returned model on the trace and re-derives the stop label from the stored
          verdict lists with the frozen 034 rule ('ID' needs the future and start searches UNSAT at every n = n_min..N and the
          model behaviourally equal to the truth; 'IDF' future UNSAT at every n and start ending SAT; 'unknown' an UNKNOWN
          verdict or no model; anything else WRONG / BAD); recounts queries and per-phase call totals from the call log.
  fresh   per-arm recount exactly as recount_040 (worlds_039 worlds, K = 128 for A14 / A15 / A15_cube).
Writes <study>/RECOUNT_041.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_041.py results/study-041/main"""
import gzip,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_039 as W39,worlds_040 as W40
from scripts.recount_033 import canon,consistent,truth_codes
from scripts.recount_034 import same,_all_unsat,_ends_sat,_words
ORDER=('A15_cube','A15','A14');LABELS=('ID','IDF','AMB','WRONG','IDU');WM={'039':W39,'040':W40}
SEALED={'039':ROOT/'results/study-039/main/RESULTS.json.gz','040':ROOT/'results/study-040/main/RESULTS.json.gz'}
_S={}


def sealed(st):
    if st not in _S:_S[st]={(c['key'],c['seed']):c for c in json.load(gzip.open(SEALED[st]))['cases']}
    return _S[st]


def lab14(a,w,N):
    m=a['model'];st=a['stop'];F=a.get('future');S=a.get('start')
    if st=='unknown':
        ok=m is None or any(x[1]=='UNKNOWN' for y in (F,S) if y for x in y['verdicts'])
        return 'IDU' if ok else 'BAD_unknown'
    n=a['n_min']
    if st=='ID':
        if not (_all_unsat(F,n,N) and _all_unsat(S,n,N)):return 'BAD_ID_verdicts'
        return 'ID' if same(m[0],m[1],0,w.transitions,w.emissions,w.start) else 'WRONG'
    if st=='IDF':return 'IDF' if _all_unsat(F,n,N) and _ends_sat(S,n) else 'BAD_IDF_verdicts'
    if st=='K_spent':
        r=a['rounds'][-1];return 'AMB' if _ends_sat(F,n) and r.get('word') and len(r['word'])>a['K']-a['used'] else 'BAD_K_spent'
    return 'BAD_stop'


def recount_replay(r):
    bad=[];c=sealed(r['study'])[(r['key'],r['seed'])];Wm=WM[r['study']];w=Wm.world(c['seed'],c['family']);a=c['arms']['A14']
    acts=list(Wm.actions(c['seed'],0.0,w.k))+list(a['extra_acts']);codes=truth_codes(w,acts)
    if [1<<x for x in codes[len(acts)-len(a['extra_acts'])+1:]]!=list(a['extra_masks']):bad.append('sealed_extra_readings')
    if r['T']!=len(acts):bad.append(('T',r['T'],len(acts)))
    if (r['k'],r['N'])!=(w.k,c['N']) or c['N']!=Wm.SIZES[c['family']]:bad.append('k_or_N')
    sr=a['rounds'][-1]
    if r['sealed']!=[sr['check'],sr['n_min']]:bad.append(('sealed',r['sealed'],[sr['check'],sr['n_min']]))
    m=r['model'];mc=None if m is None else consistent(m[0],m[1],0,acts,codes)
    if mc is False:bad.append('model_inconsistent')
    if r['model_consistent']!=mc:bad.append(('model_consistent',r['model_consistent'],mc))
    lab=lab14(r,w,c['N'])
    if lab.startswith('BAD'):bad.append(lab)
    if r['queries']!=len(r['query_walls']):bad.append('queries')
    by={}
    for x in r['calls']:
        b=by.setdefault(x['phase'],[0,0]);b[0]+=1;b[1]+=bool(x['capped'])
    if {p:[v['calls'],v['capped']] for p,v in r['by_phase'].items()}!=by:bad.append('by_phase')
    if not consistent(w.transitions,w.emissions,w.start,acts,codes):bad.append('truth_inconsistent')
    return {'label':lab,'stop':r['stop'],'n_min':r['n_min'],'model_consistent':mc,'canonical_match':m is not None and canon(m[0],m[1],0)==canon(w.transitions,w.emissions,w.start)},bad


def recount_case(c):
    w=W39.world(c['seed'],c['family']);bad=[];out={};N=W39.SIZES[c['family']]
    if (w.n,w.k)!=(c['n'],c['k']) or c.get('N')!=N:bad.append('world_shape_or_N')
    pa=list(W39.actions(c['seed'],0.0,w.k));tc=canon(w.transitions,w.emissions,w.start)
    for arm,a in c['arms'].items():
        if arm not in ORDER:bad.append(('unknown_arm',arm));continue
        ex=list(a.get('extra_acts') or []);acts=pa+ex;codes=truth_codes(w,acts)
        if [1<<x for x in codes[len(pa)+1:]]!=list(a.get('extra_masks') or []):bad.append((arm,'extra_readings'))
        m=a['model'];mc=m is not None and consistent(m[0],m[1],0,acts,codes);match=m is not None and canon(m[0],m[1],0)==tc
        rec={'label':lab14(a,w,N),'canonical_match':match,'model_consistent':mc,'used':len(ex),'T_final':len(acts)}
        if rec['label'].startswith('BAD'):bad.append((arm,rec['label']))
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
        k=f"replay/{r['part']}/{r['study']}/{r['key']}/{r['seed']}/{r['variant']}/{r['repeat']}";rp[k],b=recount_replay(r)
        if b:bad[k]=b
    for c in res['cases']:
        k=f"{c['block']}/{c['key']}/{c['seed']}";per[k],b=recount_case(c)
        if b:bad[k]=b
    labels={arm:{L:sum(1 for v in per.values() if arm in v and v[arm]['label']==L) for L in LABELS} for arm in ORDER}
    rl={}
    for k,v in rp.items():
        x=rl.setdefault(k.split('/')[5],{});x[v['label']]=x.get(v['label'],0)+1
    out={'schema':'brute.recount.v38_0','results_sha256':sha(d/'RESULTS.json'),'replays':len(rp),'cases':len(per),'labels':labels,
         'replay_labels':rl,'replay_wrong':sum(v['label']=='WRONG' for v in rp.values()),
         'words_unsound':sum(v[a]['words_unsound'] for v in per.values() for a in v),
         'words_checked':sum(v[a]['words_checked'] for v in per.values() for a in v),
         'words_checked_per_arm':{a:sum(v[a]['words_checked'] for v in per.values() if a in v) for a in ORDER},
         'truth_inconsistent':sum(sum(v[a]['truth_inconsistent_rounds'] for a in v)+sum(not x['truth_consistent_final'] for x in v.values()) for v in per.values()),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,'per_replay':rp,
         'PASS':not bad and len(per)>0 and len(rp)>0}
    write_new(d/'RECOUNT_041.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','per_replay')},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
