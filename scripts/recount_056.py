"""G_recount for study-056 (BRUTE_PLAN_056; pre-run deviation #185). New file; built from scripts/recount_055.py
(frozen). The per-case logic is the frozen scripts/recount_047.py recount_case, imported unchanged (one #185 reading for the 20l arms: used = round words + table fill_steps, see recount_case), with its module names ORDER /
DELTA / W43 bound in this process to the 056 arms (every arm at its record's bound N: 20 in scale20t, 16 in compat20t) and to
experiments/worlds_050. Compat (GCOMPAT20L56 input): compat_rule_056, pre-registered in plan 056 and applied only here (never to study
055 except the read-only recheck_12270005 in make_gates_056): per compat20t seed the recounted labels of API20L and API16E are equal and
  ID: the final models are the same machine numbered by BFS from start state 0;
  IDF: each arm's recounted future_match is true (its machine matches the clean truth from the true state at that arm's OWN stop step)
       and the minimised parts reachable from each arm's current state s1 are isomorphic as unpointed machines;
  other labels: label equality only.
compat_rule_056 was introduced after the 055 compat failure (#184 item 5) and is not retroactive. Computed here,
independent of brute/. Writes <study>/RECOUNT_056.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_056.py results/study-056/main"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_050 as W50
from experiments.brute_common_056 import ALL_ARMS
from scripts.recount_052 import rooted
from scripts import recount_047 as R47
R47.ORDER=ALL_ARMS;R47.DELTA={a:None for a in ALL_ARMS};R47.W43=W50
_counts=R47._counts;KEYS=('scale20t','compat20t');T_ARMS=('API20L','API20L_b')


def recount_case(c):
    """recount_047.recount_case (frozen) with one #185 reading for the certify/20l arms: their walk also executes table-filling
    words (logged in the table, replayed and checked walked by GTABLE56), so used = executed round words + table fill_steps.
    The 047 'used_vs_words' item is dropped for an API20L / API20L_b arm exactly when that sum holds, and kept otherwise."""
    out,bad=R47.recount_case(c)
    for arm in T_ARMS:
        if arm not in out:continue
        a=c['arms'][arm];fs=(a.get('table') or {}).get('fill_steps') or 0;rec=out[arm];rec['fill_steps']=fs
        rec['used_ok_056']=rec['words_executed_length']+fs==a['used']
        if rec['used_ok_056']:bad=[b for b in bad if b!=(arm,'used_vs_words')]
    return out,bad


def minimise(m,s):
    """Reachable part of Moore model m = (d, e) from s, minimised by partition refinement, numbered by BFS from the class of s."""
    r=rooted(m,s)
    if r is None:return None
    d,e=r;n=len(d);cls=[e[q] for q in range(n)]
    while True:
        sig=[(cls[q],tuple(cls[t] for t in d[q])) for q in range(n)];ids={}
        new=[ids.setdefault(x,len(ids)) for x in sig]
        if len(ids)==len(set(cls)):break
        cls=new
    cls=[ids[x] for x in sig];k=len(ids);dd=[None]*k;ee=[None]*k
    for q in range(n):dd[cls[q]]=[cls[t] for t in d[q]];ee[cls[q]]=e[q]
    return rooted((dd,ee),cls[0])


def unpointed_iso(ma,sa,mb,sb):
    """compat_rule_056 IDF part: the minimised parts reachable from sa in ma and from sb in mb are isomorphic as unpointed machines.
    B's part is reachable from its root, so an isomorphism maps that root to some state r of A's part whose BFS form equals B's."""
    A=minimise(ma,sa);B=minimise(mb,sb)
    if A is None or B is None or len(A[0])!=len(B[0]):return False
    return any(rooted(A,r)==B for r in range(len(A[0])))


def compat_rule_056(x,y,lx,ly,fx,fy):
    """GCOMPAT20L56 per-case rule on the API20L record x and the API16E record y, recounted labels lx, ly and recounted
    future_match fx, fy (each at the arm's own stop step)."""
    out={'label':lx,'control_label':ly,'label_equal':lx==ly,'rule_name':'compat_rule_056'}
    if lx==ly=='ID':
        out['rule']='same machine from start state 0';out['machine_equal']=rooted(x.get('model'),0)==rooted(y.get('model'),0)!=None
    elif lx==ly=='IDF':
        out['rule']='future_match at each own stop step and unpointed-isomorphic minimised parts from each current state'
        out['future_match']=[fx,fy];out['unpointed_iso']=unpointed_iso(x.get('model'),x.get('s1'),y.get('model'),y.get('s1'))
        out['machine_equal']=bool(fx is True and fy is True and out['unpointed_iso'])
    else:out['rule']='label equality only';out['machine_equal']=None
    out['equal']=bool(out['label_equal'] and out['machine_equal'] is not False);return out


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;d=Path(argv[0]);res=load(d/'RESULTS.json');per={};bad={};compat={}
    for c in res['cases']:
        k=f"{c['block']}/{c['key']}/{c['seed']}";per[k],b=recount_case(c)
        if c['key']=='compat20t':
            if 'API20L' in c['arms'] and 'API16E' in c['arms']:
                px,py=per[k]['API20L'],per[k]['API16E']
                compat[k]=compat_rule_056(c['arms']['API20L'],c['arms']['API16E'],px['label'],py['label'],px.get('future_match'),py.get('future_match'))
            else:compat[k]={'equal':False,'missing_arm':True}
        if b:bad[k]=b
    sub=lambda p:{arm:_counts([v for kk,v in per.items() if kk.startswith(p)],arm) for arm in ALL_ARMS if any(arm in v for kk,v in per.items() if kk.startswith(p))}
    allv=list(per.values());blk=res['block']
    out={'schema':'brute.recount.v53_0','results_sha256':sha(d/'RESULTS.json'),'cases':len(res['cases']),'recounted':len(per),
         'labels':{kk:sub(f'{blk}/{kk}/') for kk in KEYS},
         'compat':compat,'compat_equal':sum(x['equal'] for x in compat.values()),
         'misfires':{arm:sum(1 for v in allv if arm in v and v[arm]['misfire']) for arm in ALL_ARMS},
         'amb_rule_applied':sum('amb_rule' in v[a] for v in allv for a in v),
         'words_unsound':sum(v[a]['words_unsound'] for v in allv for a in v),
         'words_checked':sum(v[a]['words_checked'] for v in allv for a in v),
         'truth_inconsistent':sum(sum(v[a]['truth_inconsistent_rounds'] for a in v)+sum(not x['truth_consistent_final'] for x in v.values()) for v in allv),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,
         'PASS':not bad and len(per)==len(res['cases'])>0}
    write_new(d/'RECOUNT_056.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('per_case',)},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
