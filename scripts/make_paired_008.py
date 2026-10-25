"""Paired, seed-clustered bootstraps for study-008 (BRUTE_PLAN_008 G6b for R6 and C6; R_coverage_all reported).
Committed before the held-out run_start; nothing is tuned after results are seen.

Method (plan scoring.bootstrap): 2000 resamples, numpy default_rng(20261026), seeds resampled with replacement within
each family; per-family statistic = sum over resampled seeds of (X - Y certified forecasts over the seed's 3 mask cases,
post-burn-in, every action) / sum of forecasts; pooled = unweighted mean over the listed families. One fresh generator
per contrast, families in plan order. Same estimator as the frozen make_paired_006/007 (copied here because those
hard-code default_rng(20261025)); 2x2 = dual coverage (taken + counterfactual), breadth = all k actions per step.
Per-mask values and per-arm absolute coverage are point estimates (no CI)."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_008 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha

B,SEED=2000,20261026
T=lambda c,a:c['arms'][a]['trace']
def _dual(r):return (r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None)
def _certs(r):return sum(f['certificate'] is not None for f in r['forecasts'])
def _ci(boot):return [round(float(np.quantile(boot,.025)),6),round(float(np.quantile(boot,.975)),6)]


def contrast(by,fams,X,Y,breadth=False):
    rng=np.random.default_rng(SEED);fam_out={};boots=[];ests=[]
    for f in fams:
        cases=by[f];seeds=sorted({c['seed'] for c in cases});num=np.zeros(len(seeds));den=np.zeros(len(seeds))
        for c in cases:
            i=seeds.index(c['seed']);Bn=c['burn_in']
            for rx,ry in zip(T(c,X)[Bn:],T(c,Y)[Bn:]):
                if breadth:num[i]+=_certs(rx)-_certs(ry);den[i]+=len(rx['forecasts'])
                else:num[i]+=_dual(rx)-_dual(ry);den[i]+=2
        idx=rng.integers(0,len(seeds),size=(B,len(seeds)))
        boot=num[idx].sum(1)/den[idx].sum(1);est=float(num.sum()/den.sum());boots.append(boot);ests.append(est)
        fam_out[f]={'gain':round(est,6),'forecasts':int(den.sum()),'seeds':len(seeds),'ci95':_ci(boot)}
    return {'contrast':f'{X}-{Y}','families_pooled':list(fams),'pooled_gain':round(float(np.mean(ests)),6),
            'pooled_ci95':_ci(np.mean(boots,axis=0)),'families':fam_out}


def coverage(by,fams,X,breadth=False):
    out={}
    for f in fams:
        n=d=0
        for c in by[f]:
            for r in T(c,X)[c['burn_in']:]:
                if breadth:n+=_certs(r);d+=len(r['forecasts'])
                else:n+=_dual(r);d+=2
        out[f]=round(n/d,6) if d else None
    return out


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


def build(study=STUDY_DIR,block2='2x2',blockb='breadth'):
    study=Path(study)
    if study==STUDY_DIR:
        from scripts.study008_storage import ensure_raw;ensure_raw()
    d=load(study/'SCIENTIFIC.json');plan=load(PLAN)
    check('2000 resamples, numpy default_rng(20261026)' in plan['scoring']['bootstrap'],'bootstrap registration changed')
    two={f:[c for c in d['cases'] if c['block']==block2 and c['family']==f] for f in plan['heldout_ranges_2x2']}
    br={f:[c for c in d['cases'] if c['block']==blockb and c['family']==f] for f in plan['heldout_ranges_breadth']}
    two={f:v for f,v in two.items() if v};br={f:v for f,v in br.items() if v}
    IF=[f for f in plan['in_family_2x2'] if f in two];IFO=[f for f in plan['in_family_original_2x2'] if f in two]
    IB=[f for f in plan['in_family_breadth'] if f in br];ALL2=list(two);ALLB=list(br)
    out={'schema':'brute.paired-analysis.v6_0','resamples':B,'seed':SEED,'cluster':'seed within family',
         'scope':'post-burn-in steps; 2x2 dual coverage (taken + counterfactual); breadth all-action coverage',
         'scientific_sha256':sha(study/'SCIENTIFIC.json'),
         'G6b_dual_coverage_R6_minus_A2':contrast(two,IFO,'R6','A2'),
         'G6b_dual_coverage_C6_minus_A2':contrast(two,IFO,'C6','A2'),
         'R_dual_coverage_A5_minus_A2':contrast(two,IFO,'A5','A2'),
         'R_dual_coverage_A4_minus_A2':contrast(two,IFO,'A4','A2'),
         'R_dual_coverage_R6_minus_A5':contrast(two,IF,'R6','A5'),
         'R_dual_coverage_C6_minus_A5':contrast(two,IF,'C6','A5'),
         'R_dual_coverage_C6_minus_R6':contrast(two,IF,'C6','R6'),
         'R_dual_coverage_R6_minus_A5_per_mask':per_mask(two,IF,'R6','A5'),
         'R_dual_coverage_C6_minus_A5_per_mask':per_mask(two,IF,'C6','A5'),
         'R_breadth_coverage_BR6_minus_B5':contrast(br,IB,'BR6','B5',True),
         'R_breadth_coverage_BC6_minus_B5':contrast(br,IB,'BC6','B5',True),
         'R_coverage_all_point':{'2x2':{a:coverage(two,ALL2,a) for a in ('R6','C6','A5','A4','A2')},
                                 'breadth':{a:coverage(br,ALLB,a,True) for a in ('B5','BR6','BC6')}}}
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory (blocks smoke-2x2 / smoke-breadth); prints, writes nothing')
    a=ap.parse_args()
    if a.smoke:obj=build(Path(a.study_dir),'smoke-2x2','smoke-breadth');print(dumps(obj).decode()[:3000]);raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'PAIRED_ANALYSIS.json'
    if a.check:check(out.read_bytes()==dumps(obj),'PAIRED_ANALYSIS.json does not reproduce');print('PAIRED_ANALYSIS reproduces')
    else:write_new(out,obj);print(dumps(obj).decode()[:2500])
