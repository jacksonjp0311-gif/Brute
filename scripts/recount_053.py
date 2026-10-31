"""G_recount for study-053 (BRUTE_PLAN_053; pre-run deviation #179). New file; built from scripts/recount_052.py (frozen), whose compat
rule (the 052 IDF-equivalence rule, unchanged) and rooted / bfs_form are imported unchanged. The per-case logic is the frozen
scripts/recount_047.py recount_case, imported unchanged, with its module names ORDER / DELTA / W43 bound in this process to the 053
arms (part A at bound N = 16, part B at bound N = 20) and to experiments/worlds_050. The noise checks (k rule, majority votes against the clean reading,
declared eps / reads / eps_bar / delta) are the frozen scripts/recount_050.py noise_check with its module NOISE_OF bound to the 053
arms (eps_bar 0.10 and delta 0.001 equal 050's; asserted here).
Compat (GCOMPAT16N53 input, the plan 052 rule reused unchanged by plan 053 and fixed in #179): per compat seed, the recounted labels of
API16N16_c (eps 0) and API16E (bound 16) are equal, and
  ID: the final models are the same machine numbered by BFS from start state 0 with actions in order;
  IDF: both records have future_match true and the final models are the same machine numbered by BFS from each model's current
       state s1 (isomorphic with matching future from the current state);
  other labels: label equality only.
canon16e byte equality is reported too (H4, informational). Computed here, independent of brute/.
Writes <study>/RECOUNT_053.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_053.py results/study-053/main"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,check
from experiments import worlds_050 as W50
from experiments import brute_common_050 as C50
from experiments.brute_common_053 import ALL_ARMS,N_ARMS,NOISE_OF,EPS_BAR,DELTA
from scripts.recount_052 import rooted,bfs_form,compat_rule
from scripts import recount_050 as R50
from scripts import recount_047 as R47
check((C50.EPS_BAR,C50.DELTA)==(EPS_BAR,DELTA),'053 eps_bar / delta differ from 050')
R47.ORDER=ALL_ARMS;R47.DELTA={a:None for a in ALL_ARMS};R47.W43=W50;R50.NOISE_OF=dict(NOISE_OF)
recount_case=R47.recount_case;_counts=R47._counts;noise_check=R50.noise_check;KEYS=('noise16','noise16_bar','compat16','scale20c')



def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;d=Path(argv[0]);res=load(d/'RESULTS.json');per={};bad={};noise={};compat={}
    for c in res['cases']:
        k=f"{c['block']}/{c['key']}/{c['seed']}"
        if any(a.get('stop')=='majority_error' for a in c['arms'].values()):bad[k]=[('majority_error_prefix',)];continue
        per[k],b=recount_case(c)
        for arm,a in c['arms'].items():
            if arm in N_ARMS:
                noise[f'{k}/{arm}'],b2=noise_check(c,arm,a);b=b+b2
        if c['key']=='compat16':
            if 'API16N16_c' in c['arms'] and 'API16E' in c['arms']:
                compat[k]=compat_rule(c['arms']['API16N16_c'],c['arms']['API16E'],per[k]['API16N16_c']['label'],per[k]['API16E']['label'])
            else:compat[k]={'equal':False,'missing_arm':True}
        if b:bad[k]=b
    sub=lambda p:{arm:_counts([v for kk,v in per.items() if kk.startswith(p)],arm) for arm in ALL_ARMS if any(arm in v for kk,v in per.items() if kk.startswith(p))}
    allv=list(per.values());blk=res['block']
    out={'schema':'brute.recount.v50_0','results_sha256':sha(d/'RESULTS.json'),'cases':len(res['cases']),'recounted':len(per),
         'labels':{kk:sub(f'{blk}/{kk}/') for kk in KEYS},
         'compat':compat,'compat_equal':sum(x['equal'] for x in compat.values()),'noise':noise,
         'majority_errors':sum((x.get('majority_errors') or 0) for x in noise.values()),
         'misfires':{arm:sum(1 for v in allv if arm in v and v[arm]['misfire']) for arm in ALL_ARMS},
         'amb_rule_applied':sum('amb_rule' in v[a] for v in allv for a in v),
         'words_unsound':sum(v[a]['words_unsound'] for v in allv for a in v),
         'words_checked':sum(v[a]['words_checked'] for v in allv for a in v),
         'truth_inconsistent':sum(sum(v[a]['truth_inconsistent_rounds'] for a in v)+sum(not x['truth_consistent_final'] for x in v.values()) for v in allv),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,
         'PASS':not bad and len(per)==len(res['cases'])>0}
    write_new(d/'RECOUNT_053.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','noise')},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
