"""Paired, seed-clustered bootstraps for study-007 (BRUTE_PLAN_007 G6b (M5), GM, R_breadth). Committed before any
study-007 run; nothing is tuned after results are seen.

Method (plan scoring.bootstrap, = study-005/006): 2000 resamples, numpy default_rng(20261025), seeds resampled with
replacement within each family; per-family statistic = sum over resampled seeds of (X - Y certified forecasts over the
seed's 3 mask cases, post-burn-in, every action) / sum of forecasts; pooled = unweighted mean over the listed families.
One fresh generator per contrast, families in plan order. 2x2 uses the frozen make_paired_006.coverage_contrast
(dual coverage: taken + counterfactual). Breadth uses the same estimator over all k actions per step.
Per-mask values are point estimates (no CI)."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_007 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha
from scripts.make_paired_006 import coverage_contrast,_ci,_dual,B,SEED

T=lambda c,a:c['arms'][a]['trace']


def _certs(r):return sum(f['certificate'] is not None for f in r['forecasts'])


def breadth_contrast(by,fams,X,Y):
    rng=np.random.default_rng(SEED);fam_out={};boots=[];ests=[]
    for f in fams:
        cases=by[f];seeds=sorted({c['seed'] for c in cases});num=np.zeros(len(seeds));den=np.zeros(len(seeds))
        for c in cases:
            i=seeds.index(c['seed']);Bn=c['burn_in']
            for rx,ry in zip(T(c,X)[Bn:],T(c,Y)[Bn:]):num[i]+=_certs(rx)-_certs(ry);den[i]+=len(rx['forecasts'])
        idx=rng.integers(0,len(seeds),size=(B,len(seeds)))
        boot=num[idx].sum(1)/den[idx].sum(1);est=float(num.sum()/den.sum());boots.append(boot);ests.append(est)
        fam_out[f]={'gain':round(est,6),'forecasts':int(den.sum()),'seeds':len(seeds),'ci95':_ci(boot)}
    return {'contrast':f'{X}-{Y}','families_pooled':list(fams),'pooled_gain':round(float(np.mean(ests)),6),
            'pooled_ci95':_ci(np.mean(boots,axis=0)),'families':fam_out}


def per_mask(by,fams,X,Y,breadth=False):
    out={}
    for f in fams:
        out[f]={}
        for m in sorted({c['mask_rate'] for c in by[f]}):
            n=d=0
            for c in by[f]:
                if c['mask_rate']!=m:continue
                for rx,ry in zip(T(c,X)[c['burn_in']:],T(c,Y)[c['burn_in']:]):
                    if breadth:n+=_certs(rx)-_certs(ry);d+=len(rx['forecasts'])
                    else:n+=_dual(rx)-_dual(ry);d+=2
            out[f][str(m)]=round(n/d,6) if d else None
    return out


def build(study=STUDY_DIR):
    study=Path(study)
    if study==STUDY_DIR:
        from scripts.study007_storage import ensure_raw;ensure_raw()
    d=load(study/'SCIENTIFIC.json');plan=load(PLAN)
    check('2000 resamples, numpy default_rng(20261025)' in plan['scoring']['bootstrap'],'bootstrap registration changed')
    two={f:[c for c in d['cases'] if c['block']=='2x2' and c['family']==f] for f in plan['heldout_ranges_2x2']}
    br={f:[c for c in d['cases'] if c['block']=='breadth' and c['family']==f] for f in plan['heldout_ranges_breadth']}
    IF,IFO,IB=plan['in_family_2x2'],plan['in_family_original_2x2'],plan['in_family_breadth']
    out={'schema':'brute.paired-analysis.v5_0','resamples':B,'seed':SEED,'cluster':'seed within family',
         'scope':'post-burn-in steps; 2x2 dual coverage (taken + counterfactual); breadth all-action coverage',
         'scientific_sha256':sha(study/'SCIENTIFIC.json'),
         'G6b_dual_coverage_M5_minus_A2':coverage_contrast(two,IFO,'M5','A2'),
         'R_dual_coverage_A5_minus_A2':coverage_contrast(two,IFO,'A5','A2'),
         'R_dual_coverage_A4_minus_A2':coverage_contrast(two,IFO,'A4','A2'),
         'R_dual_coverage_A5_minus_A4':coverage_contrast(two,IFO,'A5','A4'),
         'GM_dual_coverage_M5_minus_A5':coverage_contrast(two,IF,'M5','A5'),
         'GM_dual_coverage_M5_minus_A5_per_mask':per_mask(two,IF,'M5','A5'),
         'GM_breadth_coverage_BM5_minus_B5':breadth_contrast(br,IB,'BM5','B5'),
         'R_breadth_coverage_BP5_minus_B5':breadth_contrast(br,IB,'BP5','B5'),
         'R_breadth_coverage_BM5_minus_B5_per_mask':per_mask(br,IB,'BM5','B5',True),
         'R_breadth_coverage_BP5_minus_B5_per_mask':per_mask(br,IB,'BP5','B5',True)}
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    a=ap.parse_args();obj=build(Path(a.study_dir));out=Path(a.study_dir)/'PAIRED_ANALYSIS.json'
    if a.check:check(out.read_bytes()==dumps(obj),'PAIRED_ANALYSIS.json does not reproduce');print('PAIRED_ANALYSIS reproduces')
    else:write_new(out,obj);print(dumps(obj).decode()[:2500])
