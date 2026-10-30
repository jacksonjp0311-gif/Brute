"""G_recount for study-032 (deviation #136; built from scripts/recount_031.py, frozen): regenerates every world and
trajectory from its seed (experiments.worlds_026; family noisy_scaleN uses the scaleN world), recomputes the latent truth,
re-derives every certificate from the stored supports and unknown counts with the frozen rule (brute.noisyregion.rgn_decide
on exact answers), and recounts certificates, false certificates (F), F_truth (exact supports excluding the true next
code), U and U_inf per (case, arm), and the flip profile per case, independently of the runner's own counts. New file.
Writes <study>/RECOUNT_032.json (refuses overwrite); PASS iff every stored count and certificate reproduces.
  PYTHONPATH=. python scripts/recount_032.py results/study-032/main"""
import json,sys
from math import ceil,sqrt
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_032 import load,write_new,sha
from experiments import worlds_026 as W
from brute.noisyregion import rgn_decide
BURN_IN=8;EPS_ASSUMED=0.05;ARMS=('S7','S7_contra','S5','S1')


def _B(t):
    x=EPS_ASSUMED*t;return 0 if t<=0 else int(ceil(x+2.0*sqrt(x)-1e-12))


def _base(f):return f[len('noisy_'):] if f.startswith('noisy_') else f


def flip_profile(seed,eps,steps):
    fl=W.flips(seed,eps,steps);tot=sens=0;first=None
    for t,fr in enumerate(fl):
        tot+=sum(map(int,fr));sens+=len(fr)
        if first is None and tot>_B(sens):first=t
    return {'realised_flips':tot,'sensor_readings':sens,'B_end':_B(sens),'within_B':first is None,'first_exceed_reading':first}


def recount_case(c):
    w=W.world(c['seed'],_base(c['family']));tr=W.trajectory(w,c['seed'],c['eps']);steps=len(tr['actions'])
    T=[[w.emissions[w.transitions[q][b]] for b in range(w.k)] for q in tr['states'][:steps]]
    out={};bad=[]
    if (w.n,w.k)!=(c['n'],c['k']):bad.append('world_shape')
    nz=flip_profile(c['seed'],c['eps'],steps)
    if nz!=c['noise']:bad.append(('noise',c['noise'],nz))
    for arm,a in c['arms'].items():
        cert=[[rgn_decide(i+1,BURN_IN,None if a['sup'][i][b] is None else tuple(a['sup'][i][b])) if a['unk'][i][b]==0 else None
               for b in range(w.k)] for i in range(steps)]
        if cert!=a['cert']:bad.append((arm,'certificates_differ'))
        F=sum(1 for i in range(steps) for b in range(w.k) if cert[i][b] is not None and cert[i][b]!=T[i][b])
        U=sum(1 for i in range(steps) for b in range(w.k) if a['unk'][i][b]!=0)
        ex=[(i,b) for i in range(steps) for b in range(w.k) if a['unk'][i][b]==0 and a['sup'][i][b] is not None]
        Ft=sum(1 for i,b in ex if T[i][b] not in a['sup'][i][b])
        gc=int(a['status_end']=='grammar_contradicted')
        n=sum(1 for r in cert for x in r if x is not None)
        late=sum(1 for i in range(88,steps) for b in range(w.k) if cert[i][b] is not None)
        rec={'F':F,'U_count':U,'certificates':n,'planned':steps*w.k,'late_certificates':late,'F_truth':Ft,'F_truth_checked':len(ex),
             'grammar_contradicted':gc,'U_inf_count':steps*w.k if gc else U}
        for kk,v in rec.items():
            if a.get(kk)!=v:bad.append((arm,kk,a.get(kk),v))
        out[arm]=rec
    return out,bad


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;d=Path(argv[0]);res=load(d/'RESULTS.json');per={};bad={}
    for c in res['cases']:
        k=f"{c['block']}/{c['family']}/{c['seed']}/{c['eps']}";per[k],b=recount_case(c)
        if b:bad[k]=b
    F={arm:sum(v[arm]['F'] for v in per.values() if arm in v) for arm in ARMS}
    Ft={arm:sum(v[arm]['F_truth'] for v in per.values() if arm in v) for arm in ARMS}
    out={'schema':'brute.recount.v29_0','results_sha256':sha(d/'RESULTS.json'),'cases':len(per),'F_total':F,'F_truth_total':Ft,
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,'PASS':not bad and len(per)>0}
    write_new(d/'RECOUNT_032.json',out);print(json.dumps({k:v for k,v in out.items() if k!='per_case'},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
