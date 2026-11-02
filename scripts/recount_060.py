"""G_recount for study-060 (BRUTE_PLAN_060 G_recount; pre-run deviation #194; new file; uses no brute/ code and not worlds_060).
Per record: rebuild the world DIRECTLY from experiments/worlds_026.scale_world(seed, n) (transitions, start) and
experiments/worlds_058.emissions(seed, 4, n) (n 24 for S24 / S24b, 32 for S32), the trace from worlds_026.actions(seed, 0, 3) plus the
recorded extra actions, and recompute the true codes; the recorded prefix and extra masks must equal 1 << true code. Then the final
model's consistency with the trace, n_min <= the declared bound, the bound itself (24 / 32), the true minimal size under the 4-bit
emissions (own Moore refinement) and the truth label (ID from the start state, IDF from s1 against the true current state; AMB /
K_spent -> AMB; unknown -> IDU; none -> NOFIT). Then recount ID+IDF and WRONG per arm. PASS iff every record matches and the
recounted counts equal the study's.
Writes <study>/RECOUNT_060.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_060.py results/study-060/main"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_026 as W26
from experiments import worlds_058 as W58
from scripts.recount_058 import _eq,_consistent
ARMS=('S24','S24b','S32');SIZE={'S24':24,'S24b':24,'S32':32};FAM={'S24':'scale24r4','S24b':'scale24r4','S32':'scale32r4'};SB=4


def minimal(T,E,s0):
    reach={s0};st=[s0]
    while st:
        q=st.pop()
        for x in T[q]:
            if x not in reach:reach.add(x);st.append(x)
    cls={q:E[q] for q in reach};k=len(T[s0])
    while True:
        sig={q:(cls[q],)+tuple(cls[T[q][a]] for a in range(k)) for q in reach};ids={}
        new={q:ids.setdefault(sig[q],len(ids)) for q in sorted(reach)}
        if len(ids)==len(set(cls.values())):return len(ids)
        cls=new


def recount_case(c):
    out={};bad=[]
    for arm,a in c['arms'].items():
        n=SIZE[arm];b=W26.scale_world(c['seed'],n);T=[list(r) for r in b.transitions];E=W58.emissions(c['seed'],SB,n);s0=b.start
        pa=list(W26.actions(c['seed'],0.0,3));acts=pa+list(a['extra_acts'])
        q=s0;codes=[E[q]]
        for x in acts:q=T[q][x];codes.append(E[q])
        if a['family']!=FAM[arm] or a['read_bits']!=SB or a['bound']!=n or c['N']!=n:bad.append((arm,'family/bits/bound'))
        ts=minimal(T,E,s0)
        if a['true_size']!=ts:bad.append((arm,'true_size',a['true_size'],ts))
        if [1<<x for x in codes[:len(pa)+1]]!=list(a['prefix_masks']):bad.append((arm,'prefix_readings'))
        if [1<<x for x in codes[len(pa)+1:]]!=list(a['extra_masks']):bad.append((arm,'extra_readings'))
        m=a['model'];stop=a['stop']
        if m is not None and not _consistent(m[0],m[1],acts,codes):bad.append((arm,'model_inconsistent'))
        if m is not None and (len(m[0])!=a['n_min'] or a['n_min']>n):bad.append((arm,'n_min'))
        if stop=='unknown':lab='IDU'
        elif stop in ('AMB','K_spent'):lab='AMB'
        elif stop=='none':lab='NOFIT'
        elif m is None:lab='WRONG'
        elif stop=='ID':lab='ID' if _eq(m[0],m[1],0,T,E,s0) else 'WRONG'
        elif stop=='IDF':lab='IDF' if _eq(m[0],m[1],a['s1'],T,E,q) else 'WRONG'
        else:lab='WRONG'
        if lab!=a['label']:bad.append((arm,'label',a['label'],lab))
        out[arm]={'label':lab,'stop':stop,'steps':len(acts),'true_size':ts}
    return out,bad


def main(argv):
    study=Path(argv[0]);R=load(study/'RESULTS.json');recs={};bad=[];cnt={g:0 for g in ARMS};study_cnt={g:0 for g in ARMS}
    for c in R['cases']:
        o,b=recount_case(c);recs[f"{c['key']}/{c['seed']}"]=o;bad+=[[c['key'],c['seed']]+list(x) for x in b]
        for g,v in o.items():cnt[g]+=v['label'] in ('ID','IDF')
        for g,v in c['arms'].items():study_cnt[g]+=v['label'] in ('ID','IDF')
    wrong={g:sum(1 for o in recs.values() for h,v in o.items() if h==g and v['label']=='WRONG') for g in ARMS}
    rep={'schema':'brute.recount.v60','results_sha256':sha(study/'RESULTS.json'),'cases':len(R['cases']),'records':sum(len(o) for o in recs.values()),
         'mismatches':bad,'decided_by_arm':cnt,'study_decided_by_arm':study_cnt,'wrong_by_arm':wrong,'per_case':recs,
         'PASS':not bad and cnt==study_cnt}
    write_new(study/'RECOUNT_060.json',rep);print(json.dumps({k:rep[k] for k in ('records','mismatches','decided_by_arm','wrong_by_arm','PASS')}))
    return 0 if rep['PASS'] else 1


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
