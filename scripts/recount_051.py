"""G_recount for study-051 (BRUTE_PLAN_051; pre-run deviation #175). New file. The per-case logic is the frozen
scripts/recount_047.py recount_case, imported unchanged, with its module names ORDER / DELTA / W43 bound in this process to the 051
arms (every arm at bound N = the family size; API16S_c at 12) and to experiments/worlds_050. The noise checks (k rule, majority
votes against the clean reading, declared eps / reads / eps_bar / delta) are the frozen scripts/recount_050.py noise_check (its
NOISE_OF / EPS_BAR / DELTA equal the 051 ones for API16N and API16N_b; asserted here).
Part c (GCOMPAT16S input): for each part c control seed, the recounted label of API16S_c equals the recounted label of the part-k
API16E record, and for ID / IDF the final models are the same machine in canonical form (numbered by BFS from start state 0 with
actions in order; computed here, independent of brute/).
Writes <study>/RECOUNT_051.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_051.py results/study-051/main"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,check
from experiments import worlds_050 as W50
from experiments import brute_common_050 as C50
from experiments.brute_common_051 import ALL_ARMS,N_ARMS,NOISE_OF,EPS_BAR,DELTA,C_ARM
from scripts import recount_050 as R50
from scripts import recount_047 as R47
check(all(C50.NOISE_OF[a]==NOISE_OF[a] for a in N_ARMS) and (C50.EPS_BAR,C50.DELTA)==(EPS_BAR,DELTA),'051 noise settings differ from 050')
R47.ORDER=ALL_ARMS;R47.DELTA={a:None for a in ALL_ARMS};R47.W43=W50
recount_case=R47.recount_case;_counts=R47._counts;noise_check=R50.noise_check;KEYS=('scale20','control','noise12')


def bfs_form(m):
    if m is None:return None
    d,e=m;idx={0:0};order=[0];i=0
    while i<len(order):
        q=order[i];i+=1
        for r in d[q]:
            if r not in idx:idx[r]=len(order);order.append(r)
    return [[[idx[r] for r in d[q]] for q in order],[e[q] for q in order]]


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;d=Path(argv[0]);res=load(d/'RESULTS.json');per={};bad={};noise={};compat={}
    K={c['seed']:c for c in res['cases'] if c['block']=='main' and c['key']=='control'}
    for c in res['cases']:
        k=f"{c['block']}/{c['key']}/{c['seed']}"
        if any(a.get('stop')=='majority_error' for a in c['arms'].values()):bad[k]=[('majority_error_prefix',)];continue
        per[k],b=recount_case(c)
        for arm,a in c['arms'].items():
            if arm in N_ARMS:
                noise[f'{k}/{arm}'],b2=noise_check(c,arm,a);b=b+b2
        if c['block']=='c':
            s=K.get(c['seed']);kl=per.get(f"main/control/{c['seed']}",{}).get('API16E',{}).get('label') if s is not None else None
            if s is not None and kl is None and 'API16E' in s['arms']:kl=recount_case(s)[0]['API16E']['label']
            cl=per[k][C_ARM]['label'];same_label=kl is not None and cl==kl
            m1=bfs_form(c['arms'][C_ARM].get('model'));m2=bfs_form(s['arms']['API16E'].get('model')) if s is not None else None
            same_m=(m1==m2 and m1 is not None) if cl in ('ID','IDF') else None
            compat[k]={'label':cl,'control_label':kl,'label_equal':same_label,'machine_equal':same_m,
                       'equal':bool(same_label and (same_m is not False))}
        if b:bad[k]=b
    sub=lambda p:{arm:_counts([v for kk,v in per.items() if kk.startswith(p)],arm) for arm in ALL_ARMS if any(arm in v for kk,v in per.items() if kk.startswith(p))}
    allv=list(per.values())
    out={'schema':'brute.recount.v48_0','results_sha256':sha(d/'RESULTS.json'),'cases':len(res['cases']),'recounted':len(per),
         'labels':{kk:sub(f'main/{kk}/') for kk in KEYS},'labels_c':sub('c/control/'),
         'compat':compat,'compat_equal':sum(x['equal'] for x in compat.values()),'noise':noise,
         'majority_errors':sum((x.get('majority_errors') or 0) for x in noise.values()),
         'misfires':{arm:sum(1 for v in allv if arm in v and v[arm]['misfire']) for arm in ALL_ARMS},
         'amb_rule_applied':sum('amb_rule' in v[a] for v in allv for a in v),
         'words_unsound':sum(v[a]['words_unsound'] for v in allv for a in v),
         'words_checked':sum(v[a]['words_checked'] for v in allv for a in v),
         'truth_inconsistent':sum(sum(v[a]['truth_inconsistent_rounds'] for a in v)+sum(not x['truth_consistent_final'] for x in v.values()) for v in allv),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,
         'PASS':not bad and len(per)==len(res['cases'])>0}
    write_new(d/'RECOUNT_051.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','noise')},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
