"""Paired, seed-clustered bootstrap for study-005 (plan G6(b), G6b, G14-P2; log-loss contrasts reported).

Registered method (BRUTE_PLAN_005 G6/G6b/G14): 2000 resamples, numpy default_rng seed 20261025, seeds resampled with
replacement within each in_family family; per-family statistic = sum over resampled seeds of (X - Y dual-certified
pairs over the seed's 3 mask cases) / sum of pairs; pooled = unweighted mean of the 5 per-family statistics. As in
study-004, one generator (seed 20261025) draws the 5 families' index matrices in plan in_family order; G6 (A3-P3) and
G6b (A3-A2) each start a fresh generator with that seed, so both contrasts use the same resampled seeds (paired design).

G14-P2 (reported): stale false certificates on drift4, main (24 seeds) + extended (72 seeds) blocks, E2 - A2; per-seed
statistic = stale count difference summed over the seed's mask cases; bootstrap statistic = resampled total; fresh
generator seed 20261025. Log-loss contrasts: as study-004 (fresh generator per family and contrast).
"""
from __future__ import annotations
import argparse,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_005 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha,is_stale

OUT=STUDY_DIR/'PAIRED_ANALYSIS.json'
B,SEED=2000,20261025
T=lambda c,a:c['arms'][a]['trace']
CT=lambda c:c['arms']['P3']['control_trace']
LL={'logloss_P3_minus_C':lambda c,i:T(c,'P3')[i]['logloss']-CT(c)[i]['logloss'],
    'logloss_A3_minus_C':lambda c,i:T(c,'A3')[i]['logloss']-CT(c)[i]['logloss'],
    'logloss_A3_minus_A2':lambda c,i:T(c,'A3')[i]['logloss']-T(c,'A2')[i]['logloss'],
    'logloss_A3_minus_P3':lambda c,i:T(c,'A3')[i]['logloss']-T(c,'P3')[i]['logloss'],
    'logloss_E2_minus_A2':lambda c,i:T(c,'E2')[i]['logloss']-T(c,'A2')[i]['logloss'],
    'logloss_P3_minus_suffix1':lambda c,i:T(c,'P3')[i]['logloss']-T(c,'P3')[i]['logloss_suffix']['1'],
    'logloss_A3_minus_suffix1':lambda c,i:T(c,'A3')[i]['logloss']-T(c,'A3')[i]['logloss_suffix']['1']}


def _dual(r):return (r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None)


def _ci(boot):return [round(float(np.quantile(boot,.025)),6),round(float(np.quantile(boot,.975)),6)]


def coverage_contrast(by,plan,X,Y):
    rng=np.random.default_rng(SEED);fam_out={};boots=[];ests=[]
    for f in plan['in_family']:
        cases=by[f];seeds=sorted({c['seed'] for c in cases});num=np.zeros(len(seeds));den=np.zeros(len(seeds))
        for c in cases:
            i=seeds.index(c['seed']);Bn=c['burn_in']
            for rx,ry in zip(T(c,X)[Bn:],T(c,Y)[Bn:]):num[i]+=_dual(rx)-_dual(ry);den[i]+=2
        idx=rng.integers(0,len(seeds),size=(B,len(seeds)))
        boot=num[idx].sum(1)/den[idx].sum(1);est=float(num.sum()/den.sum());boots.append(boot);ests.append(est)
        fam_out[f]={'gain':round(est,6),'pairs':int(den.sum()),'seeds':len(seeds),'ci95':_ci(boot)}
    return {'contrast':f'{X}-{Y}','pooled_gain':round(float(np.mean(ests)),6),'pooled_ci95':_ci(np.mean(boots,axis=0)),'families':fam_out}


def stale_contrast(cases,X='E2',Y='A2'):
    seeds=sorted({c['seed'] for c in cases});num=np.zeros(len(seeds));sx=np.zeros(len(seeds));sy=np.zeros(len(seeds))
    st=lambda r:r['wrong']+r['counterfactual']['wrong']
    for c in cases:
        i=seeds.index(c['seed'])
        sx[i]+=sum(st(r) for r in T(c,X) if is_stale(r['step']));sy[i]+=sum(st(r) for r in T(c,Y) if is_stale(r['step']))
    num=sx-sy;idx=np.random.default_rng(SEED).integers(0,len(seeds),size=(B,len(seeds)))
    boot=num[idx].sum(1)
    return {'contrast':f'S({X})-S({Y})','S_X':int(sx.sum()),'S_Y':int(sy.sum()),'estimate':int(num.sum()),'seeds':len(seeds),
            'cases':len(cases),'ci95':_ci(boot),'seeds_with_stale_X':int((sx>0).sum()),'seeds_with_stale_Y':int((sy>0).sum())}


def build():
    from scripts.study005_storage import ensure_raw;ensure_raw()
    d=load(STUDY_DIR/'SCIENTIFIC.json');plan=load(PLAN)
    for k in ('G6_active_coverage_gain','G6b_coverage_non_inferiority_vs_v020'):
        check('2000 resamples, numpy default_rng seed 20261025' in plan['criteria'][k]['threshold'] or 'same method and rng seed as G6' in plan['criteria'][k]['threshold'],'bootstrap registration changed')
    by={f:[c for c in d['cases'] if c['family']==f] for f in plan['heldout_ranges']}
    ll={}
    for f,cases in by.items():
        seeds=sorted({c['seed'] for c in cases});ll[f]={}
        for name,fn in LL.items():
            num=np.zeros(len(seeds));den=np.zeros(len(seeds))
            for c in cases:
                i=seeds.index(c['seed'])
                for k in range(c['burn_in'],c['steps']):num[i]+=fn(c,k);den[i]+=1
            r=np.random.default_rng(SEED);idx=r.integers(0,len(seeds),size=(B,len(seeds)))
            boot=num[idx].sum(1)/den[idx].sum(1)
            ll[f][name]={'estimate':round(float(num.sum()/den.sum()),6),'steps':int(den.sum()),'seeds':len(seeds),'ci95':_ci(boot)}
    drift=by['drift4']+d['extended_cases']
    return {'schema':'brute.paired-analysis.v3_0','resamples':B,'seed':SEED,'cluster':'seed within family',
            'scope':'coverage and log-loss: post-burn-in steps (9..44); stale certificates: all steps (definition in plan metrics)',
            'scientific_sha256':sha(STUDY_DIR/'SCIENTIFIC.json'),
            'G6_dual_coverage_gain':coverage_contrast(by,plan,'A3','P3'),
            'G6b_dual_coverage_A3_minus_A2':coverage_contrast(by,plan,'A3','A2'),
            'R1_dual_coverage_P3_minus_P2':coverage_contrast(by,plan,'P3','P2'),
            'R_dual_coverage_E2_minus_A2':coverage_contrast(by,plan,'E2','A2'),
            'G14_stale_E2_minus_A2':{'main_plus_extended':stale_contrast(drift),'main_only':stale_contrast(by['drift4']),
                                     'A3_minus_A2_main_plus_extended':stale_contrast(drift,'A3','A2')},
            'logloss_contrasts':ll}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();obj=build()
    if a.check:check(OUT.read_bytes()==dumps(obj),'PAIRED_ANALYSIS.json does not reproduce');print('PAIRED_ANALYSIS reproduces')
    else:write_new(OUT,obj);print(dumps(obj).decode()[:3000])
