"""G_recount for study-052 (BRUTE_PLAN_052; pre-run deviation #177). New file. The per-case logic is the frozen
scripts/recount_047.py recount_case, imported unchanged, with its module names ORDER / DELTA / W43 bound in this process to the 052
arms (every arm at bound N = 12) and to experiments/worlds_050. The noise checks (k rule, majority votes against the clean reading,
declared eps / reads / eps_bar / delta) are the frozen scripts/recount_050.py noise_check with its module NOISE_OF bound to the 052
arms (eps_bar 0.10 and delta 0.001 equal 050's; asserted here).
Compat (GCOMPAT16N52 input, rule declared in plan 052 before data and fixed in #177): per compat seed, the recounted labels of
API16N_c (eps 0) and API16E are equal, and
  ID: the final models are the same machine numbered by BFS from start state 0 with actions in order;
  IDF: both records have future_match true and the final models are the same machine numbered by BFS from each model's current
       state s1 (isomorphic with matching future from the current state);
  other labels: label equality only.
canon16e byte equality is reported too (H4, informational). Computed here, independent of brute/.
Writes <study>/RECOUNT_052.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_052.py results/study-052/main"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,check
from experiments import worlds_050 as W50
from experiments import brute_common_050 as C50
from experiments.brute_common_052 import ALL_ARMS,N_ARMS,NOISE_OF,EPS_BAR,DELTA
from scripts import recount_050 as R50
from scripts import recount_047 as R47
check((C50.EPS_BAR,C50.DELTA)==(EPS_BAR,DELTA),'052 eps_bar / delta differ from 050')
R47.ORDER=ALL_ARMS;R47.DELTA={a:None for a in ALL_ARMS};R47.W43=W50;R50.NOISE_OF=dict(NOISE_OF)
recount_case=R47.recount_case;_counts=R47._counts;noise_check=R50.noise_check;KEYS=('noise12','noise12_bar','compat')


def rooted(m,s):
    """Reachable part of model m = (d, e) from state s, numbered by BFS with actions in order; None if m or s is None."""
    if m is None or s is None:return None
    d,e=m;idx={s:0};o=[s];i=0
    while i<len(o):
        q=o[i];i+=1
        for t in d[q]:
            if t not in idx:idx[t]=len(o);o.append(t)
    return [[[idx[t] for t in d[q]] for q in o],[e[q] for q in o]]


def bfs_form(m):return rooted(m,0)


def compat_rule(n,e,ln,le):
    """GCOMPAT16N52 per-case rule on the API16N_c record n and the API16E record e with recounted labels ln, le."""
    from experiments.brute_study_051 import canon16e
    out={'label':ln,'control_label':le,'label_equal':ln==le,'canon16e_equal':canon16e(n)==canon16e(e)}
    if ln==le=='ID':out['rule']='same machine from start state 0';out['machine_equal']=bfs_form(n.get('model'))==bfs_form(e.get('model'))!=None
    elif ln==le=='IDF':
        out['rule']='future_match on both and same machine from the current state s1'
        out['future_match']=[n.get('future_match'),e.get('future_match')]
        out['machine_equal']=bool(n.get('future_match') is True and e.get('future_match') is True
                                  and rooted(n.get('model'),n.get('s1'))==rooted(e.get('model'),e.get('s1'))!=None)
    else:out['rule']='label equality only';out['machine_equal']=None
    out['equal']=bool(out['label_equal'] and out['machine_equal'] is not False);return out


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;d=Path(argv[0]);res=load(d/'RESULTS.json');per={};bad={};noise={};compat={}
    for c in res['cases']:
        k=f"{c['block']}/{c['key']}/{c['seed']}"
        if any(a.get('stop')=='majority_error' for a in c['arms'].values()):bad[k]=[('majority_error_prefix',)];continue
        per[k],b=recount_case(c)
        for arm,a in c['arms'].items():
            if arm in N_ARMS:
                noise[f'{k}/{arm}'],b2=noise_check(c,arm,a);b=b+b2
        if c['key']=='compat':
            if 'API16N_c' in c['arms'] and 'API16E' in c['arms']:
                compat[k]=compat_rule(c['arms']['API16N_c'],c['arms']['API16E'],per[k]['API16N_c']['label'],per[k]['API16E']['label'])
            else:compat[k]={'equal':False,'missing_arm':True}
        if b:bad[k]=b
    sub=lambda p:{arm:_counts([v for kk,v in per.items() if kk.startswith(p)],arm) for arm in ALL_ARMS if any(arm in v for kk,v in per.items() if kk.startswith(p))}
    allv=list(per.values());blk=res['block']
    out={'schema':'brute.recount.v49_0','results_sha256':sha(d/'RESULTS.json'),'cases':len(res['cases']),'recounted':len(per),
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
    write_new(d/'RECOUNT_052.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','noise')},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
