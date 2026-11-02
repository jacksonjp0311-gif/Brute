"""G_recount for study-061 (BRUTE_PLAN_061 G_recount; pre-run deviation #196; new file; uses no brute/ code and not worlds_060).
The per-record recount is the frozen scripts/recount_060.recount_case (rebuild the world DIRECTLY from worlds_026.scale_world and
worlds_058.emissions, recompute true codes, masks, model consistency, n_min, bound, true minimal size and the truth label),
imported unchanged; the 061 arms and families are the same as 060 (S24 / S24b scale24r4 bound 24, S32 scale32r4 bound 32).
Then recount ID+IDF and WRONG per arm. PASS iff every record matches and the recounted counts equal the study's.
Writes <study>/RECOUNT_061.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_061.py results/study-061/main"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from scripts.recount_060 import recount_case,ARMS


def main(argv):
    study=Path(argv[0]);R=load(study/'RESULTS.json');recs={};bad=[];cnt={g:0 for g in ARMS};study_cnt={g:0 for g in ARMS}
    for c in R['cases']:
        o,b=recount_case(c);recs[f"{c['key']}/{c['seed']}"]=o;bad+=[[c['key'],c['seed']]+list(x) for x in b]
        for g,v in o.items():cnt[g]+=v['label'] in ('ID','IDF')
        for g,v in c['arms'].items():study_cnt[g]+=v['label'] in ('ID','IDF')
    wrong={g:sum(1 for o in recs.values() for h,v in o.items() if h==g and v['label']=='WRONG') for g in ARMS}
    rep={'schema':'brute.recount.v61','results_sha256':sha(study/'RESULTS.json'),'cases':len(R['cases']),'records':sum(len(o) for o in recs.values()),
         'mismatches':bad,'decided_by_arm':cnt,'study_decided_by_arm':study_cnt,'wrong_by_arm':wrong,'per_case':recs,
         'PASS':not bad and cnt==study_cnt}
    write_new(study/'RECOUNT_061.json',rep);print(json.dumps({k:rep[k] for k in ('records','mismatches','decided_by_arm','wrong_by_arm','PASS')}))
    return 0 if rep['PASS'] else 1


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
