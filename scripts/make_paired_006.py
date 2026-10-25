"""Paired, seed-clustered bootstraps for study-006 (BRUTE_PLAN_006 G6, G6b', G14'; R contrasts reported).

Written and committed (process step 5) before any study-006 run. Nothing here is tuned after results are seen.

G6 / G6b' (and the reported coverage contrasts): study-005 method -- 2000 resamples, numpy default_rng(20261025), seeds
resampled with replacement within each family; per-family statistic = sum over resampled seeds of (X - Y dual-certified
pairs over the seed's 3 mask cases) / sum of pairs; pooled = unweighted mean over the in_family_original families (5).
One fresh generator per contrast, families drawn in plan order (same resampled seeds for every contrast: paired design).
perm4 is reported separately with its own fresh generator.

G14' (not gated): R = S(E2)/S(A2) over the D78 block, S = stale false certificates (taken + counterfactual,
conditional or public; is_stale(step)) summed over the block. Bootstrap: 2000 resamples over the 384 seeds (each seed =
its 3 mask cases), python random.Random(20261025); each resample draws N seed indices with rng.randrange(N); R_b =
sum S(E2)/sum S(A2) (inf if the resampled S(A2) is 0). Percentile CI by nearest rank on the sorted 2000 values:
lower = sorted[50] (2.5%), upper = sorted[1949] (97.5%).
"""
from __future__ import annotations
import argparse,math,random,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_006 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha,is_stale

OUT=STUDY_DIR/'PAIRED_ANALYSIS.json'
B,SEED=2000,20261025
T=lambda c,a:c['arms'][a]['trace']
CT=lambda c:c['arms']['P4']['control_trace']
LL={'logloss_P4_minus_C':lambda c,i:T(c,'P4')[i]['logloss']-CT(c)[i]['logloss'],
    'logloss_A4_minus_C':lambda c,i:T(c,'A4')[i]['logloss']-CT(c)[i]['logloss'],
    'logloss_A4_minus_A3':lambda c,i:T(c,'A4')[i]['logloss']-T(c,'A3')[i]['logloss'],
    'logloss_A4_minus_A2':lambda c,i:T(c,'A4')[i]['logloss']-T(c,'A2')[i]['logloss'],
    'logloss_D2_minus_A4':lambda c,i:T(c,'D2')[i]['logloss']-T(c,'A4')[i]['logloss'],
    'logloss_F2_minus_A4':lambda c,i:T(c,'F2')[i]['logloss']-T(c,'A4')[i]['logloss']}


def _dual(r):return (r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None)


def _ci(boot):return [round(float(np.quantile(boot,.025)),6),round(float(np.quantile(boot,.975)),6)]


def coverage_contrast(by,fams,X,Y):
    rng=np.random.default_rng(SEED);fam_out={};boots=[];ests=[]
    for f in fams:
        cases=by[f];seeds=sorted({c['seed'] for c in cases});num=np.zeros(len(seeds));den=np.zeros(len(seeds))
        for c in cases:
            i=seeds.index(c['seed']);Bn=c['burn_in']
            for rx,ry in zip(T(c,X)[Bn:],T(c,Y)[Bn:]):num[i]+=_dual(rx)-_dual(ry);den[i]+=2
        idx=rng.integers(0,len(seeds),size=(B,len(seeds)))
        boot=num[idx].sum(1)/den[idx].sum(1);est=float(num.sum()/den.sum());boots.append(boot);ests.append(est)
        fam_out[f]={'gain':round(est,6),'pairs':int(den.sum()),'seeds':len(seeds),'ci95':_ci(boot)}
    return {'contrast':f'{X}-{Y}','families_pooled':list(fams),'pooled_gain':round(float(np.mean(ests)),6),
            'pooled_ci95':_ci(np.mean(boots,axis=0)),'families':fam_out}


def _stale(r):return r['wrong']+r['counterfactual']['wrong']   # as study-005 stale_false_certs (a public certificate is also conditional)


def stale_by_seed(cases,arm):
    seeds=sorted({c['seed'] for c in cases});s=[0]*len(seeds);pos={x:i for i,x in enumerate(seeds)}
    for c in cases:s[pos[c['seed']]]+=sum(_stale(r) for r in T(c,arm) if is_stale(r['step']))
    return seeds,s


def g14_ratio(cases,X='E2',Y='A2'):
    seeds,sy=stale_by_seed(cases,Y);_,sx=stale_by_seed(cases,X);N=len(seeds)
    rng=random.Random(SEED);boot=[]
    for _ in range(B):
        idx=[rng.randrange(N) for _ in range(N)];a=sum(sy[i] for i in idx);e=sum(sx[i] for i in idx)
        boot.append(e/a if a else math.inf)
    boot.sort();SX,SY=sum(sx),sum(sy)
    f=lambda v:None if v==math.inf else round(v,6)
    return {'statistic':f'R=S({X})/S({Y})','S_X':SX,'S_Y':SY,'R':round(SX/SY,6) if SY else None,'seeds':N,'cases':len(cases),
            'ci95':[f(boot[50]),f(boot[1949])],'resamples':B,'rng':'python random.Random(20261025)',
            'resamples_with_zero_denominator':sum(v==math.inf for v in boot),
            'seeds_with_stale_X':sum(v>0 for v in sx),'seeds_with_stale_Y':sum(v>0 for v in sy)}


def build():
    from scripts.study006_storage import ensure_raw;ensure_raw()
    d=load(STUDY_DIR/'SCIENTIFIC.json');plan=load(PLAN);C=plan['criteria']
    check('numpy default_rng 20261025' in C['G6b_prime_coverage_non_inferiority_vs_v020']['threshold'],'G6b bootstrap registration changed')
    check('random.Random(20261025)' in C['G14_prime_D7_D8_powered']['statistic'],'G14 bootstrap registration changed')
    by={f:[c for c in d['cases'] if c['family']==f] for f in plan['heldout_ranges']};IFO=plan['in_family_original']
    ll={}
    for f in plan['out_of_family']+IFO+['perm4']:
        cases=by[f];seeds=sorted({c['seed'] for c in cases});ll[f]={}
        for name,fn in LL.items():
            num=np.zeros(len(seeds));den=np.zeros(len(seeds))
            for c in cases:
                i=seeds.index(c['seed'])
                for k in range(c['burn_in'],c['steps']):num[i]+=fn(c,k);den[i]+=1
            r=np.random.default_rng(SEED);idx=r.integers(0,len(seeds),size=(B,len(seeds)))
            boot=num[idx].sum(1)/den[idx].sum(1)
            ll[f][name]={'estimate':round(float(num.sum()/den.sum()),6),'steps':int(den.sum()),'seeds':len(seeds),'ci95':_ci(boot)}
    return {'schema':'brute.paired-analysis.v4_0','resamples':B,'seed':SEED,'cluster':'seed within family',
            'scope':'coverage and log-loss: post-burn-in steps (9..44); stale certificates: all steps (plan metrics)',
            'scientific_sha256':sha(STUDY_DIR/'SCIENTIFIC.json'),
            'G6_dual_coverage_A4_minus_P4':coverage_contrast(by,IFO,'A4','P4'),
            'G6b_prime_dual_coverage_A4_minus_A2':coverage_contrast(by,IFO,'A4','A2'),
            'R_dual_coverage_P4_minus_P2_not_available':'P2 is not an arm in study-006',
            'R_dual_coverage_A3_minus_A2':coverage_contrast(by,IFO,'A3','A2'),
            'R_dual_coverage_A4_minus_A3':coverage_contrast(by,IFO,'A4','A3'),
            'G15_dual_coverage_D2_minus_A2':coverage_contrast(by,IFO,'D2','A2'),
            'G16_dual_coverage_F2_minus_A2':coverage_contrast(by,IFO,'F2','A2'),
            'R_dual_coverage_E2_minus_A2':coverage_contrast(by,IFO,'E2','A2'),
            'R6_perm4':{k:coverage_contrast(by,['perm4'],*k.split('-')) for k in ('A4-P4','A4-A2','A4-A3')},
            'G14_prime_R_D78':g14_ratio(d['d78_cases']),
            'G14_prime_R_main_drift4_reported':g14_ratio(by['drift4']),
            'logloss_contrasts':ll}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();obj=build()
    if a.check:check(OUT.read_bytes()==dumps(obj),'PAIRED_ANALYSIS.json does not reproduce');print('PAIRED_ANALYSIS reproduces')
    else:write_new(OUT,obj);print(dumps(obj).decode()[:3000])
