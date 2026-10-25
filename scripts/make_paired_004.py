"""Paired, seed-clustered bootstrap for study-004 (plan G6(b), gated; G7 reported targets).

G6(b), as registered: 2000 resamples, numpy default_rng seed 20261025, seeds resampled with replacement within each
in_family family; per-family statistic = sum over resampled seeds of (A - P dual-certified pairs over the seed's 3 mask
cases) / sum of pairs; pooled = unweighted mean of the 5 per-family statistics. One generator draws the 5 families'
index matrices in plan in_family order.

Log-loss contrasts (reported): same resampling per family with a fresh generator (seed 20261025) per family and contrast;
per-seed statistic = sum of post-burn-in step differences over the seed's 3 mask cases; estimate = total / steps.
"""
from __future__ import annotations
import argparse,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_004 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha

OUT=STUDY_DIR/'PAIRED_ANALYSIS.json'
B,SEED=2000,20261025
LL={'logloss_P_minus_C':lambda c,i:c['arms']['P']['trace'][i]['logloss']-c['arms']['P']['control_trace'][i]['logloss'],
    'logloss_A_minus_C':lambda c,i:c['arms']['A']['trace'][i]['logloss']-c['arms']['P']['control_trace'][i]['logloss'],
    'logloss_A_minus_P':lambda c,i:c['arms']['A']['trace'][i]['logloss']-c['arms']['P']['trace'][i]['logloss'],
    'logloss_P_minus_suffix1':lambda c,i:c['arms']['P']['trace'][i]['logloss']-c['arms']['P']['trace'][i]['logloss_suffix']['1'],
    'logloss_A_minus_suffix1':lambda c,i:c['arms']['A']['trace'][i]['logloss']-c['arms']['A']['trace'][i]['logloss_suffix']['1']}


def _dual(r):return (r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None)


def _ci(boot):return [round(float(np.quantile(boot,.025)),6),round(float(np.quantile(boot,.975)),6)]


def build():
    d=load(STUDY_DIR/'SCIENTIFIC.json');plan=load(PLAN)
    reg=plan['criteria']['G6_active_coverage_gain']['threshold']
    check('2000 resamples, numpy default_rng seed 20261025' in reg,'bootstrap registration changed')
    by={f:[c for c in d['cases'] if c['family']==f] for f in plan['heldout_ranges']}
    rng=np.random.default_rng(SEED);fam_out={};boots=[];ests=[]
    for f in plan['in_family']:
        cases=by[f];seeds=sorted({c['seed'] for c in cases});num=np.zeros(len(seeds));den=np.zeros(len(seeds))
        for c in cases:
            i=seeds.index(c['seed']);Bn=c['burn_in']
            for ra,rp in zip(c['arms']['A']['trace'][Bn:],c['arms']['P']['trace'][Bn:]):
                num[i]+=_dual(ra)-_dual(rp);den[i]+=2
        idx=rng.integers(0,len(seeds),size=(B,len(seeds)))
        boot=num[idx].sum(1)/den[idx].sum(1);est=float(num.sum()/den.sum());boots.append(boot);ests.append(est)
        fam_out[f]={'gain':round(est,6),'pairs':int(den.sum()),'seeds':len(seeds),'ci95':_ci(boot)}
    pooled=np.mean(boots,axis=0)
    g6={'pooled_gain':round(float(np.mean(ests)),6),'pooled_ci95':_ci(pooled),'families':fam_out}
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
    return {'schema':'brute.paired-analysis.v2_0','resamples':B,'seed':SEED,'cluster':'seed within family',
            'scope':'post-burn-in steps (9..44)','scientific_sha256':sha(STUDY_DIR/'SCIENTIFIC.json'),
            'G6_dual_coverage_gain':g6,'logloss_contrasts':ll}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();obj=build()
    if a.check:check(OUT.read_bytes()==dumps(obj),'PAIRED_ANALYSIS.json does not reproduce');print('PAIRED_ANALYSIS reproduces')
    else:write_new(OUT,obj);print(dumps(obj).decode())
