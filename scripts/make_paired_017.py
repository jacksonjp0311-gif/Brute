"""Paired, seed-clustered bootstraps for study-017 (BRUTE_PLAN_017 metrics.bootstrap, transfer_definition.speedup and
.coverage). Committed and ledgered (scoring_freeze_017) before the held-out run_start; nothing is tuned after results are
seen. Adapted from make_paired_016 (frozen, not edited); the resampling routine is make_paired_015.contrast's with seed
20261028.

Per main target case the recorded summary is used (make_gates_017 recounts it from the traces; GS_ref5 audits it):
S[X] = T_cert(SP8) - T_cert(X) (censored at 45, own trajectory) and certificates[X] (own trajectory).
Contrasts d(case), main block (360 cases, families cycle3, switch3, unaliased2, ood4 in plan order):
  TV_RGLX4          = S[RGLX4] - S[RG4]                                (GRL headline)
  dC_RSXL4          = (certificates[RSXL4] - certificates[RG4]) / 88   (GDS2)
  dC_<X>            = (certificates[X] - certificates[RG4]) / 88       (dC_RGLX4 for R_coverage; the rest reported)
  C_<X>             = certificates[X] / 88
  S_<X>             = S[X]                (vs SP8)
  TV_<X>            = S[X] - S[RG4]       (GDS2 clause: TV_RSXL4 == 0 on every case is checked per case by make_gates_017)
  DLFn_minus_RG4    = S[DLFn] - S[RG4]    (reported, R_DLF)
ood5 block (72 cases, family ood5, reported only): S_RG4, S_RG5, S_RSXL5.
Bootstrap: 2000 resamples, numpy default_rng(20261028), one fresh generator per contrast; for each family in plan order
the family's target seeds are resampled with replacement (each seed = its 3 mask cases); resample statistic = pooled case
mean over all resampled cases; 95% CI = percentiles 2.5 / 97.5."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_017 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha
from scripts.make_paired_009 import B,_q

SEED=20261028;SLOTS=88
FAMILIES=('cycle3','switch3','unaliased2','ood4')
MAIN_ARMS=('RG4','RG5','RGLX4','RGL4','RSXL4','RSXLp','RSXLn','DLFp','DLFn','DLFa_p','DLFa_n','DLF2p','DLF2n','RSX4','EB')
TV_ARMS=tuple(a for a in MAIN_ARMS if a!='RG4')


def contrast(cases,fn,name,families=FAMILIES):
    rng=np.random.default_rng(SEED);fams=[f for f in families if any(c['family']==f for c in cases)]
    ts=[];ns=[];fam_out={};allD=[]
    for f in fams:
        cs=[c for c in cases if c['family']==f];seeds=sorted({c['seed'] for c in cs});n=len(seeds)
        tot=np.zeros(n);cnt=np.zeros(n);D=[]
        for c in cs:
            d=fn(c);i=seeds.index(c['seed']);tot[i]+=d;cnt[i]+=1;D.append(d)
        allD+=D;idx=rng.integers(0,n,size=(B,n));bt=tot[idx].sum(1);bn=cnt[idx].sum(1);ts.append(bt);ns.append(bn)
        fam_out[f]={'cases':len(cs),'seeds':n,'mean':round(float(np.mean(D)),6),'ci95':_q(bt/bn,.025,.975)}
    if not fams:return {'contrast':name,'mean':None,'ci95':None,'families':{}}
    boot=np.sum(ts,axis=0)/np.sum(ns,axis=0);hist={}
    for d in allD:k=str(round(d,6));hist[k]=hist.get(k,0)+1
    return {'contrast':name,'cases':len(allD),'mean':round(float(np.mean(allD)),6),'ci95':_q(boot,.025,.975),
            'families_in_order':fams,'families':fam_out,'histogram':dict(sorted(hist.items(),key=lambda x:float(x[0]))),
            'cases_positive':sum(d>0 for d in allD),'cases_negative':sum(d<0 for d in allD),'cases_zero':sum(d==0 for d in allD)}


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN)
    check('2000 resamples, seed 20261028' in plan['metrics']['bootstrap'],'bootstrap registration changed')
    s=load(study/'transfer'/'SEAL.json');check(s['scientific_sha256']==sha(study/'transfer'/'SCIENTIFIC.json'),'transfer SCIENTIFIC does not match its SEAL')
    allc=load(study/'transfer'/'SCIENTIFIC.json')['cases'];cs=[c for c in allc if c['family']!='ood5'];c5=[c for c in allc if c['family']=='ood5']
    out={'schema':'brute.paired-analysis.v15_0','study':plan['study'],'resamples':B,'seed':SEED,'cluster':'target seed within family (3 masks each)',
         'coverage_slots_per_case':SLOTS,'smoke_dry_run':smoke,'scientific_sha256':{'transfer':s['scientific_sha256']},'complete':{'transfer':s.get('complete')},
         'main_cases':len(cs),'ood5_cases':len(c5)}
    cert=lambda c,a:c['summary']['certificates'][a]
    for a in TV_ARMS:out['dC_'+a]=contrast(cs,lambda c,a=a:(cert(c,a)-cert(c,'RG4'))/SLOTS,f'dC({a}) = (certificates({a}) - certificates(RG4)) / 88')
    for a in MAIN_ARMS:out['C_'+a]=contrast(cs,lambda c,a=a:cert(c,a)/SLOTS,f'C({a}) = certificates({a}) / 88')
    for a in MAIN_ARMS:out['S_'+a]=contrast(cs,lambda c,a=a:c['summary']['S'][a],f'S({a}) = T_cert(SP8) - T_cert({a})')
    for a in TV_ARMS:out['TV_'+a]=contrast(cs,lambda c,a=a:c['summary']['S'][a]-c['summary']['S']['RG4'],f'TV({a}) = S({a}) - S(RG4)')
    out['DLFn_minus_RG4']=contrast(cs,lambda c:c['summary']['S']['DLFn']-c['summary']['S']['RG4'],'S(DLFn) - S(RG4)')
    for a in ('RG4','RG5','RSXL5'):out['ood5_S_'+a]=contrast(c5,lambda c,a=a:c['summary']['S'][a],f'ood5 S({a})',families=('ood5',))
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints, writes nothing')
    a=ap.parse_args()
    if a.smoke:obj=build(Path(a.study_dir),smoke=True);print({k:(v['mean'],v['ci95']) for k,v in obj.items() if isinstance(v,dict) and 'ci95' in v});raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'PAIRED_ANALYSIS_017.json'
    if a.check:check(out.read_bytes()==dumps(obj),'PAIRED_ANALYSIS_017.json does not reproduce');print('PAIRED_ANALYSIS_017 reproduces')
    else:write_new(out,obj);print({k:(v['mean'],v['ci95']) for k,v in obj.items() if isinstance(v,dict) and 'ci95' in v})
