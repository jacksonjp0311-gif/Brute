"""Paired, seed-clustered bootstrap for study-002 (plan: 2000 resamples, seed 20261024).

For each family and each contrast, the per-seed statistic is the sum over that seed's
cases (3 mask rates) of post-burn-in step values; the estimate is total/steps, and the
bootstrap resamples seeds with replacement.
"""
from __future__ import annotations
import argparse,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import STUDY_DIR,PLAN,load,dumps,write_new,check,sha

OUT=STUDY_DIR/'PAIRED_ANALYSIS.json'
CONTRASTS={
 'logloss_brute_minus_v090':lambda r:(r['logloss_brute']-r['logloss_v090'],1),
 'logloss_brute_minus_uniform':lambda r:(r['logloss_brute']-float(np.log(4)),1),
 'logloss_brute_minus_suffix1':lambda r:(r['logloss_brute']-r['logloss_suffix']['1'],1),
 'logloss_brute_minus_v089_on_v089_valid_steps':lambda r:(None,0) if r['logloss_v089'] is None else (r['logloss_brute']-r['logloss_v089'],1),
 'coverage_brute_minus_v090':lambda r:((r['certificate'] is not None)-(r['v090_certificate'] is not None),1),
 'false_certs_v090_minus_brute_per_step':lambda r:(r['v090_wrong']-r['brute_wrong'],1),
}


def build():
    d=load(STUDY_DIR/'SCIENTIFIC.json');plan=load(PLAN)
    check(plan['scoring']['bootstrap']=='paired, clustered by world seed, 2000 resamples, seed 20261024','bootstrap registration changed')
    B,seed=2000,20261024
    out={}
    for fam in plan['heldout_ranges']:
        cases=[c for c in d['cases'] if c['family']==fam];seeds=sorted({c['seed'] for c in cases})
        out[fam]={}
        for name,fn in CONTRASTS.items():
            num=np.zeros(len(seeds));den=np.zeros(len(seeds))
            for c in cases:
                i=seeds.index(c['seed'])
                for r in c['trace']:
                    if r['step']<=c['burn_in']:continue
                    v,w=fn(r)
                    if w:num[i]+=v;den[i]+=w
            rng=np.random.default_rng(seed)
            idx=rng.integers(0,len(seeds),size=(B,len(seeds)))
            with np.errstate(invalid='ignore',divide='ignore'):boot=num[idx].sum(1)/den[idx].sum(1)
            boot=boot[np.isfinite(boot)]
            est=float(num.sum()/den.sum()) if den.sum() else None
            out[fam][name]={'estimate':None if est is None else round(est,6),'steps':int(den.sum()),'seeds':len(seeds),
                            'ci95':None if est is None else [round(float(np.quantile(boot,.025)),6),round(float(np.quantile(boot,.975)),6)]}
    return {'schema':'brute.paired-analysis.v1','resamples':B,'seed':seed,'cluster':'seed','scope':'post-burn-in steps',
            'scientific_sha256':sha(STUDY_DIR/'SCIENTIFIC.json'),'families':out}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build()
    if a.check:check(OUT.read_bytes()==dumps(obj),'PAIRED_ANALYSIS.json does not reproduce');print('PAIRED_ANALYSIS reproduces')
    else:write_new(OUT,obj);print(dumps(obj).decode())
