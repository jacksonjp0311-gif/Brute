"""G_recount for study-031 (deviation #123 item 12; #128; #130; #132; #134; built from scripts/recount_030.py, frozen): regenerates every world and trajectory from its seed (experiments.
worlds_026), recomputes the latent truth, re-derives every certificate from the stored supports and unknown counts with
the frozen rule (brute.noisyregion.rgn_decide on exact answers), and recounts certificates, false certificates and
UNKNOWN queries per (case, arm), independently of the runner's own counts. New file.
Writes <study>/RECOUNT_031.json (refuses overwrite); PASS iff every stored count and certificate reproduces.
  PYTHONPATH=. python scripts/recount_031.py results/study-031/main"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_031 import load,write_new,sha
from experiments import worlds_026 as W
from brute.noisyregion import rgn_decide
BURN_IN=8


def recount_case(c):
    w=W.world(c['seed'],c['family']);tr=W.trajectory(w,c['seed'],c['eps']);steps=len(tr['actions'])
    T=[[w.emissions[w.transitions[q][b]] for b in range(w.k)] for q in tr['states'][:steps]]
    out={};bad=[]
    if (w.n,w.k)!=(c['n'],c['k']):bad.append('world_shape')
    for arm,a in c['arms'].items():
        cert=[[rgn_decide(i+1,BURN_IN,None if a['sup'][i][b] is None else tuple(a['sup'][i][b])) if a['unk'][i][b]==0 else None
               for b in range(w.k)] for i in range(steps)]
        if cert!=a['cert']:bad.append((arm,'certificates_differ'))
        F=sum(1 for i in range(steps) for b in range(w.k) if cert[i][b] is not None and cert[i][b]!=T[i][b])
        U=sum(1 for i in range(steps) for b in range(w.k) if a['unk'][i][b]!=0)
        n=sum(1 for r in cert for x in r if x is not None)
        late=sum(1 for i in range(88,steps) for b in range(w.k) if cert[i][b] is not None)
        rec={'F':F,'U_count':U,'certificates':n,'planned':steps*w.k,'late_certificates':late}
        for kk,v in rec.items():
            if a.get(kk)!=v:bad.append((arm,kk,a.get(kk),v))
        out[arm]=rec
    return out,bad


def main(argv=None):
    argv=sys.argv[1:] if argv is None else argv;d=Path(argv[0]);res=load(d/'RESULTS.json');per={};bad={}
    for c in res['cases']:
        k=f"{c['block']}/{c['family']}/{c['seed']}/{c['eps']}";per[k],b=recount_case(c)
        if b:bad[k]=b
    F={arm:sum(v[arm]['F'] for v in per.values() if arm in v) for arm in ('S6','S6_noorder','S5','S1')}
    out={'schema':'brute.recount.v28_0','results_sha256':sha(d/'RESULTS.json'),'cases':len(per),'F_total':F,
         'mismatching_cases':len(bad),'mismatches':{k:v for k,v in list(bad.items())[:50]},'per_case':per,'PASS':not bad and len(per)>0}
    write_new(d/'RECOUNT_031.json',out);print(json.dumps({k:v for k,v in out.items() if k!='per_case'},default=str));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
