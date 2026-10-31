"""G_recount for study-050 (BRUTE_PLAN_050; pre-run deviation #173). New file. The per-case logic is the frozen
scripts/recount_047.py recount_case, imported unchanged, with its module names ORDER / DELTA / W43 bound in this process to the 050
arms (every arm at bound N = the family size) and to experiments/worlds_050 (scale12 added; every other family dispatches to
worlds_047 unchanged). The truth trace is the clean world: a certify/16n record whose majority reading differs from the truth is a
recount mismatch (and its label is recounted against the truth).
Added for the noise arms (independent of brute/): (i) k per observation equals the declared rule (reads fixed, else the smallest odd
k with 2 exp(-2k(1/2-eps_bar)^2) <= delta 6/(pi^2 t^2), recomputed here); (ii) every vote vector gives, by per-bit majority, the
clean reading of that observation (majority_errors recomputed and compared with the record); (iii) part c: canon16e(API16N_c) equals
canon16e of the part-k API16E record on the same control seed (GCOMPAT16N input).
Writes <study>/RECOUNT_050.json (refuses overwrite).
  PYTHONPATH=. python scripts/recount_050.py results/study-050/main"""
import json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from experiments import worlds_050 as W50
from experiments.worlds_026 import bits
from experiments.brute_common_050 import ALL_ARMS,N_ARMS,NOISE_OF,EPS_BAR,DELTA
from scripts import recount_047 as R47
from scripts.recount_033 import truth_codes
R47.ORDER=ALL_ARMS;R47.DELTA={a:None for a in ALL_ARMS};R47.W43=W50
recount_case=R47.recount_case;_counts=R47._counts;KEYS=('scale20','control','noise12')


def k_rule(t,reads):
    if reads is not None:return reads
    need=math.log(2*math.pi**2*t*t/(6.0*DELTA))/(2.0*(0.5-EPS_BAR)**2);k=max(1,math.ceil(need-1e-12));return k+1 if k%2==0 else k


def noise_check(c,arm,a):
    bad=[];w=W50.world(c['seed'],c['family']);acts=list(W50.actions(c['seed'],0.0,w.k))+list(a['extra_acts']);tc=truth_codes(w,acts)
    eps,reads=NOISE_OF[arm];ks=a.get('reads_per_obs') or [];V=a.get('votes') or []
    if len(ks)!=len(tc) or len(V)!=len(tc):bad.append((arm,'observation_count',len(ks),len(V),len(tc)));return {'majority_errors':None},bad
    if ks!=[k_rule(t+1,reads) for t in range(len(ks))]:bad.append((arm,'k_rule'))
    err=sum(1 for k,v,code in zip(ks,V,tc) if tuple(1 if 2*o>k else 0 for o in v)!=bits(code))
    if err!=a.get('majority_errors'):bad.append((arm,'majority_errors',a.get('majority_errors'),err))
    for f,v in (('eps',eps),('reads',reads),('eps_bar',EPS_BAR),('noise_delta',DELTA),('reads_total',sum(ks))):
        if a.get(f)!=v:bad.append((arm,f,a.get(f),v))
    return {'majority_errors':err,'reads_total':sum(ks),'reads_max':max(ks),'observations':len(ks)},bad


def main(argv=None):
    from experiments.brute_study_050 import canon16e
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
            s=K.get(c['seed']);eq=bool(s is not None and 'API16E' in s['arms'] and canon16e(c['arms']['API16N_c'])==canon16e(s['arms']['API16E']))
            compat[k]={'canon16e_equal':eq,'label':per[k]['API16N_c']['label'],'control_label':per.get(f"main/control/{c['seed']}",{}).get('API16E',{}).get('label')}
        if b:bad[k]=b
    sub=lambda p:{arm:_counts([v for kk,v in per.items() if kk.startswith(p)],arm) for arm in ALL_ARMS if any(arm in v for kk,v in per.items() if kk.startswith(p))}
    allv=list(per.values())
    out={'schema':'brute.recount.v47_0','results_sha256':sha(d/'RESULTS.json'),'cases':len(res['cases']),'recounted':len(per),
         'labels':{kk:sub(f'main/{kk}/') for kk in KEYS},'labels_c':sub('c/control/'),
         'compat':compat,'compat_equal':sum(x['canon16e_equal'] for x in compat.values()),'noise':noise,
         'majority_errors':sum((x.get('majority_errors') or 0) for x in noise.values()),
         'misfires':{arm:sum(1 for v in allv if arm in v and v[arm]['misfire']) for arm in ALL_ARMS},
         'amb_rule_applied':sum('amb_rule' in v[a] for v in allv for a in v),
         'words_unsound':sum(v[a]['words_unsound'] for v in allv for a in v),
         'words_checked':sum(v[a]['words_checked'] for v in allv for a in v),
         'truth_inconsistent':sum(sum(v[a]['truth_inconsistent_rounds'] for a in v)+sum(not x['truth_consistent_final'] for x in v.values()) for v in allv),
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,
         'PASS':not bad and len(per)==len(res['cases'])>0}
    write_new(d/'RECOUNT_050.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('per_case','noise')},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
