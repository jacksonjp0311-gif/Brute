"""Case-level paired bootstraps for study-025 (lean, BRUTE_PLAN_025_A2: transfer = the 90-case lean block; arms RG4, RGB6, RGL4, RGL5, RGNB4, RGN4_or; pairs RGB6-RGL4 (GBC c), RGB6-RGNB4 (GBC d), RGB6-RGL5, RGB6-RGN4_or, RGL5-RGL4, RGL4-RGNB4). Original note (BRUTE_PLAN_025; adapted from scripts/make_paired_023.py, frozen).
BRUTE_PLAN_025 names the contrasts but not the resampling, and GLS (c) says "paired-bootstrap CI95". The study-023
registration is used unchanged: "paired bootstrap (10000 resamples, seed 23) over cases", numpy default_rng(23),
percentile 2.5 / 97.5 (deviation #117 item 1; the string is checked in BRUTE_PLAN_023.json). Committed with the source freeze
before the held-out run_start (A2: no separate scoring-freeze wait); nothing is tuned after results are seen.

Resampling: the n cases of a subset (at a fixed eps a case is a seed) are resampled with replacement, statistic = case
mean; every contrast restarts the generator, so both arms of a difference see the same resampled cases. Per case the
recorded summary is used (make_gates_025 recounts it from the traces; GS_ref10 audits it).
Subsets of the transfer block: eps0 / eps1 / eps2 (120 main cases each), noisy (eps1 + eps2, 240), stress (eps 0.05, 30).
For every subset and every arm X in RG4, RGL4, RGL5, RGNA4, RGNB4, RGN4_or that ALL cases of the subset carry (RGNB4
only at eps 0.02):
  C_late_<X>_<sub>     = certificates in steps 45..88 / 88
  C_early28_<X>_<sub>  = certificates in steps 1..28 / 56
  C_full_<X>_<sub>     = certificates / 176
  casefalse_<X>_<sub>  = 1 if the case has >= 1 false certificate for X
  dC_late_RGL5_RGL4_<sub>   (GLS c on eps2)      dC_late_RGL5_RGNB4_<sub>  (GLS d on eps2)
  dC_late_RGL5_RGNA4_<sub>, dC_late_RGL5_RGN4_or_<sub>, dC_early28_RGL5_RGL4_<sub>, dC_early28_RGL5_RGNB4_<sub> (reported)
  ratio_late_RGL5_RGNB4_<sub>, ratio_late_RGL5_RGN4_or_<sub> (point values, reported)
and C_curve_<sub>[X] = per step t = 1..88 the mean over cases of certificates at t / 2 (no CI; reported)."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_025 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha

SEED=23;B=10000;STEPS=88
REG='paired bootstrap (10000 resamples, seed 23)'
ARMS=('RG4','RGB6','RGL4','RGL5','RGNB4','RGN4_or')
PAIRS=(('RGB6','RGL4'),('RGB6','RGNB4'),('RGB6','RGL5'),('RGB6','RGN4_or'),('RGL5','RGL4'),('RGL4','RGNB4'))
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
    check(REG in load(ROOT/'experiments/BRUTE_PLAN_023.json')['metrics'],'study-023 bootstrap registration not found')
    check('paired-bootstrap CI95' in plan['criteria']['GBC_headline']['c'],'GBC c registration changed')
    s=load(study/'transfer'/'SEAL.json');check(s['scientific_sha256']==sha(study/'transfer'/'SCIENTIFIC.json'),'transfer SCIENTIFIC does not match its SEAL')
    allc=load(study/'transfer'/'SCIENTIFIC.json')['cases']
    out={'schema':'brute.paired-analysis.v22_0','study':plan['study'],'resamples':B,'seed':SEED,'registration':REG+' (as study-023, deviation #117)',
         'cluster':'case (= seed at a fixed eps)','windows':{'late':[45,88],'early28':[1,28],'slots':{'late':88,'early28':56,'full':176}},
         'smoke_dry_run':smoke,'scientific_sha256':{'transfer':s['scientific_sha256']},'complete':{'transfer':s.get('complete')},'cases':len(allc)}
    S=lambda c,k,a:c['summary'][k][a]
    for sub,sel in SUBSETS.items():
        cs=[c for c in allc if sel(c)];out['n_'+sub]=len(cs)
        has=lambda x:bool(cs) and all(x in c['summary']['certificates'] for c in cs)
        for a in [x for x in ARMS if has(x)]:
            out[f'C_late_{a}_{sub}']=contrast(cs,lambda c,a=a:S(c,'certificates_late',a)/88,f'C_late({a}) = certificates in steps 45-88 / 88 on {sub}')
            out[f'C_early28_{a}_{sub}']=contrast(cs,lambda c,a=a:S(c,'certificates_early28',a)/56,f'C_early28({a}) = certificates in steps 1-28 / 56 on {sub}')
            out[f'C_full_{a}_{sub}']=contrast(cs,lambda c,a=a:S(c,'certificates',a)/176,f'C_full({a}) = certificates / 176 on {sub}')
            out[f'casefalse_{a}_{sub}']=contrast(cs,lambda c,a=a:float(S(c,'case_false',a)),f'case-false({a}) on {sub}')
        for x,y in PAIRS:
            if not(has(x) and has(y)):continue
            out[f'dC_late_{x}_{y}_{sub}']=contrast(cs,lambda c,x=x,y=y:(S(c,'certificates_late',x)-S(c,'certificates_late',y))/88,f'C_late({x}) - C_late({y}) on {sub}')
            out[f'dC_early28_{x}_{y}_{sub}']=contrast(cs,lambda c,x=x,y=y:(S(c,'certificates_early28',x)-S(c,'certificates_early28',y))/56,f'C_early28({x}) - C_early28({y}) on {sub}')
            den=sum(S(c,'certificates_late',y) for c in cs)
            out[f'ratio_late_{x}_{y}_{sub}']=round(sum(S(c,'certificates_late',x) for c in cs)/den,6) if den else None
        out[f'C_curve_{sub}']={a:[round(sum(c['summary']['per_step'][a][t] for c in cs)/(2*len(cs)),6) for t in range(STEPS)] for a in ARMS if cs and all(a in c['summary']['per_step'] for c in cs)}
    return out


def _brief(obj):return {k:(v['mean'],v['ci95']) for k,v in obj.items() if isinstance(v,dict) and 'ci95' in v and 'RGB6' in k and ('eps2' in k or 'noisy' in k)}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints, writes nothing')
    a=ap.parse_args()
    if a.smoke:obj=build(Path(a.study_dir),smoke=True);print(_brief(obj));raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'PAIRED_ANALYSIS_025.json'
    if a.check:check(out.read_bytes()==dumps(obj),'PAIRED_ANALYSIS_025.json does not reproduce');print('PAIRED_ANALYSIS_025 reproduces')
    else:write_new(out,obj);print(_brief(obj))
