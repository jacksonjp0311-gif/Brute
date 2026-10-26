"""Paired, seed-clustered bootstraps for study-012 (BRUTE_PLAN_012 scoring.bootstrap). Committed and ledgered
(scoring_freeze_012) before the held-out run_start; nothing is tuned after results are seen.

Coverage contrasts (the frozen make_paired_009.contrast estimator, imported unchanged): 2000 resamples,
numpy default_rng(20261026), one fresh generator per contrast, seeds resampled with replacement WITHIN each family (each
seed = its 3 mask cases); per-family statistic = sum over resampled seeds of (X - Y certified forecasts, post-burn-in
steps, taken + counterfactual) / sum of forecasts; pooled = unweighted mean over the listed families (plan order);
95% CI = percentiles 2.5/97.5.
  Gated: G6b J10 - A2 and GJ10 J10 - J9 on in_family_original_2x2. Reported: J10 - SP8, J9 - SP8, SP8 - A2.

Transfer contrasts (GT_b, GT_c; metrics.steps_to_cert_transfer): per target case T_cert(SP8) = first step whose SP8
taken-action forecast carries a conditional certificate (45 if none), T_cert(TR) = the recorded TR first_cert_step
(first step whose TR taken-action certificate is non-null, 45 if none); S = T_cert(SP8) - T_cert(TRp) (positive pairs),
S_n = T_cert(SP8) - T_cert(TRn) (negative control). Bootstrap: 2000 resamples, numpy default_rng(20261026), one fresh
generator per contrast; for each transfer family in plan order (cycle3, switch3, unaliased2, ood4) the family's target
seeds are resampled with replacement (each seed = its 3 mask cases); the resample statistic is the mean S over ALL
resampled cases of all four families (pooled case mean; families have equal size). 95% CI = percentiles 2.5/97.5.
GT_b passes iff mean S >= 1.0 AND CI lower > 0; GT_c (ii) passes iff CI lower of mean S_n <= 0 (scored in make_gates_012).
Per-family means, CIs and S histograms are reported."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_012 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha
from scripts.make_paired_009 import contrast,coverage,B,SEED,tcert,_q

TRANSFER_FAMILIES=('cycle3','switch3','unaliased2','ood4')


def saving(c,tr):return tcert(c['arms']['SP8']['trace'])-c['transfer'][tr]['first_cert_step']


def transfer_contrast(cases,tr):
    rng=np.random.default_rng(SEED);fams=[f for f in TRANSFER_FAMILIES if any(c['family']==f for c in cases)]
    idx_sum=[];idx_n=[];fam_out={};allS=[]
    for f in fams:
        cs=[c for c in cases if c['family']==f];seeds=sorted({c['seed'] for c in cs});n=len(seeds)
        tot=np.zeros(n);cnt=np.zeros(n);S=[]
        for c in cs:
            s=saving(c,tr);i=seeds.index(c['seed']);tot[i]+=s;cnt[i]+=1;S.append(s)
        allS+=S;idx=rng.integers(0,n,size=(B,n));bt=tot[idx].sum(1);bn=cnt[idx].sum(1);idx_sum.append(bt);idx_n.append(bn)
        hist={}
        for s in S:hist[str(s)]=hist.get(str(s),0)+1
        fam_out[f]={'cases':len(cs),'seeds':n,'mean_S':round(float(np.mean(S)),6),'ci95':_q(bt/bn,.025,.975),
                    'histogram':dict(sorted(hist.items(),key=lambda x:int(x[0]))),
                    'mean_tcert_SP8':round(float(np.mean([tcert(c['arms']['SP8']['trace']) for c in cs])),6),
                    'mean_tcert_TR':round(float(np.mean([c['transfer'][tr]['first_cert_step'] for c in cs])),6),
                    'censored_SP8':sum(tcert(c['arms']['SP8']['trace'])==45 for c in cs),
                    'censored_TR':sum(c['transfer'][tr]['first_cert_step']==45 for c in cs)}
    if not fams:return {'arm':tr,'mean_S':None,'ci95':None,'families':{}}
    boot=np.sum(idx_sum,axis=0)/np.sum(idx_n,axis=0)
    hist={}
    for s in allS:hist[str(s)]=hist.get(str(s),0)+1
    return {'arm':tr,'statistic':'T_cert(SP8) - T_cert(%s), pooled case mean'%tr,'cases':len(allS),'mean_S':round(float(np.mean(allS)),6),
            'ci95':_q(boot,.025,.975),'families_in_order':fams,'families':fam_out,
            'histogram':dict(sorted(hist.items(),key=lambda x:int(x[0]))),
            'cases_helped':sum(s>0 for s in allS),'cases_hurt':sum(s<0 for s in allS),'cases_equal':sum(s==0 for s in allS)}


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN)
    check('2000 resamples, numpy default_rng(20261026)' in plan['scoring']['bootstrap'],'bootstrap registration changed')
    out={'schema':'brute.paired-analysis.v10_0','study':plan['study'],'resamples':B,'seed':SEED,'cluster':'seed within family',
         'smoke_dry_run':smoke,'scientific_sha256':{},'complete':{}}
    for b in ('2x2','transfer'):
        s=load(study/b/'SEAL.json');check(s['scientific_sha256']==sha(study/b/'SCIENTIFIC.json'),f'{b} SCIENTIFIC does not match its SEAL')
        out['scientific_sha256'][b]=s['scientific_sha256'];out['complete'][b]=s.get('complete')
    d2=load(study/'2x2'/'SCIENTIFIC.json')
    two={f:[c for c in d2['cases'] if c['family']==f] for f in plan['heldout_ranges_2x2']};two={f:v for f,v in two.items() if v}
    IF=[f for f in plan['in_family_2x2'] if f in two];IFO=[f for f in plan['in_family_original_2x2'] if f in two]
    out.update({'G6b_dual_coverage_J10_minus_A2':contrast(two,IFO,'J10','A2'),
                'GJ10_dual_coverage_J10_minus_J9':contrast(two,IFO,'J10','J9'),
                'R_J10_minus_SP8_in_family_original':contrast(two,IFO,'J10','SP8'),
                'R_J10_minus_SP8_in_family':contrast(two,IF,'J10','SP8'),
                'R_J9_minus_SP8_in_family_original':contrast(two,IFO,'J9','SP8'),
                'R_SP8_minus_A2_in_family_original':contrast(two,IFO,'SP8','A2'),
                'R_coverage_all_point':{'2x2':{a:coverage(two,list(two),a) for a in ('J10','J9','SP8','A4','A2')}}})
    tc=load(study/'transfer'/'SCIENTIFIC.json')['cases']
    out['GT_b_transfer_saving_TRp']=transfer_contrast(tc,'TRp')
    out['GT_c_negative_control_saving_TRn']=transfer_contrast(tc,'TRn')
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints, writes nothing')
    a=ap.parse_args()
    if a.smoke:obj=build(Path(a.study_dir),smoke=True);print(dumps(obj).decode()[:6000]);raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'PAIRED_ANALYSIS_012.json'
    if a.check:check(out.read_bytes()==dumps(obj),'PAIRED_ANALYSIS_012.json does not reproduce');print('PAIRED_ANALYSIS_012 reproduces')
    else:write_new(out,obj);print(dumps(obj).decode()[:3000])
