"""G_recount for study-054 (BRUTE_PLAN_054 as amended by 054a; pre-run deviation #181). New file; built from scripts/recount_053.py
(frozen). The per-case logic is the frozen scripts/recount_047.py recount_case, imported unchanged, with its module names ORDER /
DELTA / W43 bound in this process to the 054 arms (every arm at its record's bound N: 20 in scale20t, 16 in compat20t) and to
experiments/worlds_050. Compat (GCOMPAT20T54 input, the 052 IDF-equivalence rule reused unchanged): per compat20t seed the
recounted labels of API20T (bound 16) and API16E (bound 16) are equal, and for ID the final models are the same machine numbered by
BFS from start state 0; for IDF both records have future_match true and the final models are the same machine numbered by BFS from
each model's current state; other labels: label equality only (scripts/recount_052.compat_rule, frozen). Computed here,
independent of brute/. Writes <study>/RECOUNT_054.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_054.py results/study-054/main"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_050 as W50
from experiments.brute_common_054 import ALL_ARMS
from scripts.recount_052 import compat_rule
from scripts import recount_047 as R47
R47.ORDER=ALL_ARMS;R47.DELTA={a:None for a in ALL_ARMS};R47.W43=W50
recount_case=R47.recount_case;_counts=R47._counts;KEYS=('scale20t','compat20t')


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;d=Path(argv[0]);res=load(d/'RESULTS.json');per={};bad={};compat={}
    for c in res['cases']:
        k=f"{c['block']}/{c['key']}/{c['seed']}";per[k],b=recount_case(c)
        if c['key']=='compat20t':
            if 'API20T' in c['arms'] and 'API16E' in c['arms']:
                compat[k]=compat_rule(c['arms']['API20T'],c['arms']['API16E'],per[k]['API20T']['label'],per[k]['API16E']['label'])
            else:compat[k]={'equal':False,'missing_arm':True}
        if b:bad[k]=b
    sub=lambda p:{arm:_counts([v for kk,v in per.items() if kk.startswith(p)],arm) for arm in ALL_ARMS if any(arm in v for kk,v in per.items() if kk.startswith(p))}
    allv=list(per.values());blk=res['block']
    out={'schema':'brute.recount.v51_0','results_sha256':sha(d/'RESULTS.json'),'cases':len(res['cases']),'recounted':len(per),
         'labels':{kk:sub(f'{blk}/{kk}/') for kk in KEYS},
         'compat':compat,'compat_equal':sum(x['equal'] for x in compat.values()),
         'misfires':{arm:sum(1 for v in allv if arm in v and v[arm]['misfire']) for arm in ALL_ARMS},
         'amb_rule_applied':sum('amb_rule' in v[a] for v in allv for a in v),
         'words_unsound':sum(v[a]['words_unsound'] for v in allv for a in v),
         'words_checked':sum(v[a]['words_checked'] for v in allv for a in v),
         'truth_inconsistent':sum(sum(v[a]['truth_inconsistent_rounds'] for a in v)+sum(not x['truth_consistent_final'] for x in v.values()) for v in allv),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,
         'PASS':not bad and len(per)==len(res['cases'])>0}
    write_new(d/'RECOUNT_054.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('per_case',)},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
