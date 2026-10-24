"""Paired, seed-clustered bootstrap for study-003 (plan G6 reported target: 2000 resamples, seed 20261024).

Per family and contrast: the per-seed statistic sums post-burn-in step values over that seed's 3 mask
cases; estimate = total/steps; seeds are resampled with replacement. Reported, not gated.
"""
from __future__ import annotations
import argparse,math,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_003 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha

OUT=STUDY_DIR/'PAIRED_ANALYSIS.json'
LN4=math.log(4)
CONTRASTS={
 'logloss_v011_minus_v010':lambda r,k:r['logloss_brute']-k['logloss_brute'],
 'logloss_v011_minus_uniform':lambda r,k:r['logloss_brute']-LN4,
 'logloss_v011_minus_suffix1':lambda r,k:r['logloss_brute']-r['logloss_suffix']['1'],
 'logloss_v011_minus_v090':lambda r,k:r['logloss_brute']-r['logloss_v090'],
 'logloss_ablation_minus_v011':lambda r,k:r['logloss_ablation']-r['logloss_brute'],
}


def build():
    d=load(STUDY_DIR/'SCIENTIFIC.json');plan=load(PLAN)
    check('2000 resamples, seed 20261024' in plan['criteria']['G6_open_world_logloss']['reported_targets']['paired_bootstrap'],'bootstrap registration changed')
    B,seed=2000,20261024;out={}
    for fam in plan['heldout_ranges']:
        cases=[c for c in d['cases'] if c['family']==fam];seeds=sorted({c['seed'] for c in cases});out[fam]={}
        for name,fn in CONTRASTS.items():
            num=np.zeros(len(seeds));den=np.zeros(len(seeds))
            for c in cases:
                i=seeds.index(c['seed'])
                for r,k in zip(c['trace'],c['control_trace']):
                    if r['step']<=c['burn_in']:continue
                    num[i]+=fn(r,k);den[i]+=1
            rng=np.random.default_rng(seed);idx=rng.integers(0,len(seeds),size=(B,len(seeds)))
            boot=num[idx].sum(1)/den[idx].sum(1);est=float(num.sum()/den.sum())
            out[fam][name]={'estimate':round(est,6),'steps':int(den.sum()),'seeds':len(seeds),
                            'ci95':[round(float(np.quantile(boot,.025)),6),round(float(np.quantile(boot,.975)),6)]}
    return {'schema':'brute.paired-analysis.v1_1','resamples':B,'seed':seed,'cluster':'seed','scope':'post-burn-in steps (9..44)',
            'scientific_sha256':sha(STUDY_DIR/'SCIENTIFIC.json'),'families':out}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();obj=build()
    if a.check:check(OUT.read_bytes()==dumps(obj),'PAIRED_ANALYSIS.json does not reproduce');print('PAIRED_ANALYSIS reproduces')
    else:write_new(OUT,obj);print(dumps(obj).decode())
