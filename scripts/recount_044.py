"""G_recount for study-044 (BRUTE_PLAN_044; pre-run deviation #161; new file, the scripts/recount_043.py logic (frozen) unchanged
per arm, with the three 044 arms (A16_c9, A16_c30, A16_xf), independent of the runner and of brute/). Records:
  replay (smoke only): the frozen recount_043.recount_replay043 on the sealed 040 scale16 traces;
  fresh / probe: per arm: worlds_043 world, the seeded passive actions (eps 0) plus the case's extra actions, readings by simulating
          the true machine; label by the frozen 034 rule (recount_041.lab14) and the AMB-at-stop rule (recount_043.label043);
  A16_xf only (#161 item 1): the first xf_used extra actions equal an independently recomputed schedule (every action word of length
          1, 2, 3 in lex order over 0..k-1, concatenated, a random.Random(seed) length-6 tail only if those hold < 32 actions,
          truncated to 32), xf_used == 32 unless the stop is unknown, and words_executed_length + xf_used == used;
          A16_c9 / A16_c30: xf_used == 0 and words_executed_length == used.
Writes <study>/RECOUNT_044.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_044.py results/study-044/main"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_043 as W43
from scripts.recount_033 import canon,consistent,truth_codes
from scripts.recount_034 import _words,run
import random
from itertools import product
from scripts.recount_043 import label043,recount_replay043
ORDER=('A16_c9','A16_c30','A16_xf');XF_E=32;XF_TAIL=6;LABELS=('ID','IDF','AMB','WRONG','IDU');M=4


def schedule(k,seed,E=XF_E):
    out=[a for L in (1,2,3) for w in product(range(k),repeat=L) for a in w]
    if len(out)<E:
        rng=random.Random(seed)
        while len(out)<E:out+=[rng.randrange(k) for _ in range(XF_TAIL)]
    return out[:E]


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
        xu=a.get('xf_used',0)
        if arm=='A16_xf':
            if ex[:xu]!=schedule(w.k,c['seed'])[:xu]:bad.append((arm,'xf_schedule'))
            if xu!=XF_E and a['stop']!='unknown':bad.append((arm,'xf_short',xu))
        elif xu!=0:bad.append((arm,'xf_used_nonzero'))
        rec['xf_used']=xu
        if rec['words_executed_length']+xu!=a['used']:bad.append((arm,'used_vs_words'))
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
    out={'schema':'brute.recount.v41_0','results_sha256':sha(d/'RESULTS.json'),'replays':len(rp),'cases':len(per),'labels_main':labels,
         'labels_all':{arm:{L:sum(1 for v in per.values() if arm in v and v[arm]['label']==L) for L in LABELS} for arm in ORDER},
         'replay_labels':rl,'replay_wrong':sum(v['label']=='WRONG' for v in rp.values()),
         'amb_rule_applied':sum('amb_rule' in v for v in rp.values())+sum('amb_rule' in v[a] for v in per.values() for a in v),
         'words_unsound':sum(v[a]['words_unsound'] for v in per.values() for a in v),
         'words_checked':sum(v[a]['words_checked'] for v in per.values() for a in v),
         'words_checked_per_arm':{a:sum(v[a]['words_checked'] for v in per.values() if a in v) for a in ORDER},
         'truth_inconsistent':sum(sum(v[a]['truth_inconsistent_rounds'] for a in v)+sum(not x['truth_consistent_final'] for x in v.values()) for v in per.values()),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,'per_replay':rp,
         'PASS':not bad and len(per)>0}
    write_new(d/'RECOUNT_044.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','per_replay')},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
