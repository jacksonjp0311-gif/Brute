"""G_recount63 for study-063 (BRUTE_PLAN_063 G_recount63; new file, built from scripts/recount_062.py (frozen); uses no brute/ search
code). Per record: rebuild the trace from experiments/worlds_058 'scale20' (prefix = worlds_026 actions, eps 0, plus the recorded extra actions),
recompute the true codes, check the recorded prefix and extra masks (1 << code), K accounting (used = number of extra actions,
<= 400), the final model's consistency with the whole trace (if any), the read width (2) and the truth label (ID from the start
state, IDF from s1 against the true current state; AMB / K_spent -> AMB; unknown -> IDU). certify/20p changes only the pool (the
clique anchor), not which actions are taken, so there is no window-policy check. Then recount ID+IDF per arm.
The trace / model helpers are the frozen scripts/recount_058.py ones (imported; nothing rebound).
PASS iff every record matches and the recounted per-arm counts equal the study's. Writes <study>/RECOUNT_063.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_063.py results/study-063/main"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_058 as W58
from scripts.recount_058 import _eq,_consistent
ARMS=('B2','P2','P2b');FAM={'B2':'scale20','P2':'scale20','P2b':'scale20'};K=400;N=20


def recount_case(c):
    out={};bad=[]
    for arm,a in c['arms'].items():
        w=W58.world(c['seed'],FAM[arm]);pa=list(W58.actions(c['seed'],0.0,w.k));acts=pa+list(a['extra_acts'])
        q=w.start;codes=[w.emissions[q]]
        for x in acts:q=w.transitions[q][x];codes.append(w.emissions[q])
        if a['family']!=FAM[arm] or a['read_bits']!=W58.BITS[FAM[arm]] or a['read_bits']!=2:bad.append((arm,'family/bits'))
        if [1<<x for x in codes[:len(pa)+1]]!=list(a['prefix_masks']):bad.append((arm,'prefix_readings'))
        if [1<<x for x in codes[len(pa)+1:]]!=list(a['extra_masks']):bad.append((arm,'extra_readings'))
        if a['used']!=len(a['extra_acts']) or a['used']>K:bad.append((arm,'K_accounting'))
        m=a['model'];stop=a['stop']
        if m is not None and not _consistent(m[0],m[1],acts,codes):bad.append((arm,'model_inconsistent'))
        if m is not None and (len(m[0])!=a['n_min'] or a['n_min']>N):bad.append((arm,'n_min'))
        if stop=='unknown':lab='IDU'
        elif stop in ('AMB','K_spent'):lab='AMB'
        elif m is None:lab='WRONG'
        elif stop=='ID':lab='ID' if _eq(m[0],m[1],0,w.transitions,w.emissions,w.start) else 'WRONG'
        elif stop=='IDF':lab='IDF' if _eq(m[0],m[1],a['s1'],w.transitions,w.emissions,q) else 'WRONG'
        else:lab='WRONG'
        if lab!=a['label']:bad.append((arm,'label',a['label'],lab))
        out[arm]={'label':lab,'stop':stop,'steps':len(acts)}
    return out,bad


def main(argv):
    study=Path(argv[0]);R=load(study/'RESULTS.json');recs={};bad=[];cnt={g:0 for g in ARMS};study_cnt={g:0 for g in ARMS}
    for c in R['cases']:
        o,b=recount_case(c);recs[str(c['seed'])]=o;bad+=[[c['seed']]+list(x) for x in b]
        for g,v in o.items():cnt[g]+=v['label'] in ('ID','IDF')
        for g,v in c['arms'].items():study_cnt[g]+=v['label'] in ('ID','IDF')
    wrong=sum(1 for o in recs.values() for v in o.values() if v['label']=='WRONG')
    rep={'schema':'brute.recount.v60','results_sha256':sha(study/'RESULTS.json'),'cases':len(R['cases']),'records':sum(len(o) for o in recs.values()),
         'mismatches':bad,'decided_by_arm':cnt,'study_decided_by_arm':study_cnt,'wrong':wrong,'per_case':recs,
         'PASS':not bad and cnt==study_cnt}
    write_new(study/'RECOUNT_063.json',rep);print(json.dumps({k:rep[k] for k in ('records','mismatches','decided_by_arm','wrong','PASS')}))
    return 0 if rep['PASS'] else 1


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
