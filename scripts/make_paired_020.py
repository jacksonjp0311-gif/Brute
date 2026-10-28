"""Case-level bootstraps for study-020 (BRUTE_PLAN_020 metrics.CI: "case-level bootstrap 95%, 10000 resamples, seed fixed
in the scoring freeze"; #103 item 4: numpy default_rng(20261028), percentile 2.5 / 97.5). Committed and ledgered
(scoring_freeze_020) before the held-out run_start; nothing is tuned after results are seen.

Resampling: the n cases of a subset (at a fixed eps a case is a seed) are resampled with replacement, statistic = case
mean; every contrast restarts the generator (np.random.default_rng(20261028)), so the two arms of a difference see the
same resampled cases. Per case the recorded summary is used (make_gates_020 recounts it from the traces; GS_ref8 audits it).
Subsets of the transfer block: eps0 / eps1 / eps2 (120 main cases each), noisy (eps1 + eps2, 240), stress (eps 0.05, 120).
For every subset and arm X in SP8, RG4, RGN4, RGNB4, RGN4_or:
  C_late_<X>_<sub>     = certificates in steps 45..88 / 88        (GLH (c), (d) on RGNB4 / eps2)
  C_early28_<X>_<sub>  = certificates in steps 1..28 / 56         (GLH_early_control on RGNB4 / eps2)
  C_full_<X>_<sub>     = certificates / 176
  casefalse_<X>_<sub>  = 1 if the case has >= 1 false certificate for X
  dC_late_RGNB4_RGN4_<sub> = C_late(RGNB4) - C_late(RGN4)
  bit_late_RGNB4_<sub> / bit_full_RGNB4_<sub> = per-bit coverage (late / 176, full / 352), bitfalse_RGNB4_<sub> = case has a false bit
and C_curve_<sub>[X] = per step t = 1..88 the mean over cases of certificates at t / 2 (no CI; reported)."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_020 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha

SEED=20261028;B=10000;STEPS=88
ARMS=('SP8','RG4','RGN4','RGNB4','RGN4_or')
def _stress(c):return c['block']=='stress' or (c['block'].startswith('smoke') and c['eps']==0.05)
SUBSETS={'eps0':lambda c:not _stress(c) and c['eps']==0.0,'eps1':lambda c:not _stress(c) and c['eps']==0.01,
         'eps2':lambda c:not _stress(c) and c['eps']==0.02,'noisy':lambda c:not _stress(c) and c['eps'] in (0.01,0.02),
         'stress':lambda c:_stress(c)}


def _q(x):return [round(float(np.percentile(x,2.5)),6),round(float(np.percentile(x,97.5)),6)]


def contrast(cases,fn,name):
    if not cases:return {'contrast':name,'cases':0,'mean':None,'ci95':None}
    D=np.array([fn(c) for c in cases],dtype=float);n=len(D);rng=np.random.default_rng(SEED)
    boot=D[rng.integers(0,n,size=(B,n))].mean(1)
    return {'contrast':name,'cases':n,'mean':round(float(D.mean()),6),'ci95':_q(boot),
            'cases_positive':int((D>0).sum()),'cases_negative':int((D<0).sum()),'cases_zero':int((D==0).sum())}


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN)
    check('case-level bootstrap 95%, 10000 resamples' in plan['metrics']['CI'],'bootstrap registration changed')
    s=load(study/'transfer'/'SEAL.json');check(s['scientific_sha256']==sha(study/'transfer'/'SCIENTIFIC.json'),'transfer SCIENTIFIC does not match its SEAL')
    allc=load(study/'transfer'/'SCIENTIFIC.json')['cases']
    out={'schema':'brute.paired-analysis.v18_0','study':plan['study'],'resamples':B,'seed':SEED,'cluster':'case (= seed at a fixed eps)',
         'windows':{'late':[45,88],'early28':[1,28],'slots':{'late':88,'early28':56,'full':176,'bit_late':176,'bit_full':352}},
         'smoke_dry_run':smoke,'scientific_sha256':{'transfer':s['scientific_sha256']},'complete':{'transfer':s.get('complete')},'cases':len(allc)}
    S=lambda c,k,a:c['summary'][k][a]
    for sub,sel in SUBSETS.items():
        cs=[c for c in allc if sel(c)];out['n_'+sub]=len(cs)
        for a in ARMS:
            out[f'C_late_{a}_{sub}']=contrast(cs,lambda c,a=a:S(c,'certificates_late',a)/88,f'C_late({a}) = certificates in steps 45-88 / 88 on {sub}')
            out[f'C_early28_{a}_{sub}']=contrast(cs,lambda c,a=a:S(c,'certificates_early28',a)/56,f'C_early28({a}) = certificates in steps 1-28 / 56 on {sub}')
            out[f'C_full_{a}_{sub}']=contrast(cs,lambda c,a=a:S(c,'certificates',a)/176,f'C_full({a}) = certificates / 176 on {sub}')
            out[f'casefalse_{a}_{sub}']=contrast(cs,lambda c,a=a:float(S(c,'case_false',a)),f'case-false({a}) on {sub}')
        out[f'dC_late_RGNB4_RGN4_{sub}']=contrast(cs,lambda c:(S(c,'certificates_late','RGNB4')-S(c,'certificates_late','RGN4'))/88,f'C_late(RGNB4) - C_late(RGN4) on {sub}')
        out[f'bit_late_RGNB4_{sub}']=contrast(cs,lambda c:c['summary']['perbit']['late_certified_bits']/176,f'per-bit coverage steps 45-88 / 176 on {sub}')
        out[f'bit_full_RGNB4_{sub}']=contrast(cs,lambda c:c['summary']['perbit']['certified_bits']/352,f'per-bit coverage / 352 on {sub}')
        out[f'bitfalse_RGNB4_{sub}']=contrast(cs,lambda c:float(c['summary']['perbit']['case_false']),f'case has a false bit on {sub}')
        out[f'C_curve_{sub}']={a:[round(sum(c['summary']['per_step'][a][t] for c in cs)/(2*len(cs)),6) if cs else None for t in range(STEPS)] for a in ARMS}
    return out


def _brief(obj):return {k:(v['mean'],v['ci95']) for k,v in obj.items() if isinstance(v,dict) and 'ci95' in v and 'RGNB4' in k and ('eps2' in k or 'noisy' in k)}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints, writes nothing')
    a=ap.parse_args()
    if a.smoke:obj=build(Path(a.study_dir),smoke=True);print(_brief(obj));raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'PAIRED_ANALYSIS_020.json'
    if a.check:check(out.read_bytes()==dumps(obj),'PAIRED_ANALYSIS_020.json does not reproduce');print('PAIRED_ANALYSIS_020 reproduces')
    else:write_new(out,obj);print(_brief(obj))
