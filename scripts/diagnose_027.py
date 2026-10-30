"""Post-hoc, informational bottleneck diagnosis for study-027 (deviation #127 item 3). New file, written AFTER the
results were seen; it gates nothing and changes no gate. It reads the sealed RESULTS.json (which keeps the
*_informational wall fields that SCIENTIFIC.json drops) and writes results/study-027/DIAGNOSIS_027.json.
Per arm (S1, S2, S2_tight) and family, eps-0 main cases: mean arm wall, mean and max of the per-case max query time,
steps per second, solver calls per second (S2 arms), the UNKNOWN split, and the final proven lower bound n_lo vs n.
  PYTHONPATH=. python scripts/diagnose_027.py"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_027 import load,write_new,sha
D=ROOT/'results/study-027/main'


def m(v):return None if not v else round(sum(v)/len(v),3)


def main():
    R=load(D/'RESULTS.json');out={}
    for f in ('scale8','scale12','scale16','control_cycle3'):
        cs=[c for c in R['cases'] if c['block']=='main' and c['family']==f and c['eps']==0]
        for a in ('S1','S2','S2_tight'):
            A=[c['arms'][a] for c in cs if a in c['arms']];w=[x['arm_wall_informational'] for x in A];q=[x['query_max_informational'] for x in A]
            nr=sum(u==-1 for x in A for r in x['unk'] for u in r);su=sum(u>=1 for x in A for r in x['unk'] for u in r);pl=sum(x['planned'] for x in A)
            rec={'cases':len(A),'arm_wall_mean':m(w),'query_max_mean':m(q),'query_max_max':round(max(q),3) if q else None,
                 'steps_per_s':m([x['steps_done']/x['arm_wall_informational'] for x in A if x['arm_wall_informational']>0]),
                 'full_176':sum(x['steps_done']==176 for x in A),'not_run_frac':round(nr/pl,4) if pl else None,'solver_unknown_frac':round(su/pl,4) if pl else None,
                 'cases_with_query_ge_5s':sum(v>=5 for v in q)}
            if a!='S1':
                rec.update(solves_per_s=m([x['solves']/x['arm_wall_informational'] for x in A if x['arm_wall_informational']>0]),
                           n_lo_mean=m([x['n_lo'] for x in A]),n_lo_eq_n=sum(x['n_lo']==c['n'] for x,c in zip(A,cs)),n_max=A[0]['n_max'] if A else None)
            out[f'{a}/{f}']=rec
    rep={'schema':'brute.diagnosis-027.v1','informational':True,'post_hoc':True,'results_sha256':sha(D/'RESULTS.json'),'eps0':out}
    write_new(ROOT/'results/study-027/DIAGNOSIS_027.json',rep);print(json.dumps(out,indent=0))


if __name__=='__main__':main()
