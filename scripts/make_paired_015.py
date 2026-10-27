"""Paired, seed-clustered bootstraps for study-015 (BRUTE_PLAN_015 metrics.bootstrap, transfer_definition.speedup).
Committed and ledgered (scoring_freeze_015) before the held-out run_start; nothing is tuned after results are seen.
Adapted from make_paired_014 (frozen, not edited).

Per main target case the recorded summary S[X] = T_cert(SP8) - T_cert(X) (censored at 45; RSX4 / RSXp / RSXn on the RSX
trajectory) is used; make_gates_015 recounts it from the traces and GS_ref3 audits it.
Contrasts d(case), main block (288 cases, families cycle3, switch3, unaliased2, ood4 in plan order):
  S_<X>             = S[X]                (vs SP8)
  TV_<X>            = S[X] - S[RG4]       (GRS headline TV_RSX4; GEB value TV_EB)
  RSXn_minus_RSX4   = S[RSXn] - S[RSX4]   (GS_c3)
  RSXp_minus_RSX4   = S[RSXp] - S[RSX4]   (reported)
ood5 block (72 cases, family ood5, reported only): S_RG4, S_RG5.
Bootstrap: 2000 resamples, numpy default_rng(20261027), one fresh generator per contrast; for each family in plan order
the family's target seeds are resampled with replacement (each seed = its 3 mask cases); resample statistic = pooled case
mean over all resampled cases; 95% CI = percentiles 2.5 / 97.5."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_015 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha
from scripts.make_paired_009 import B,_q

SEED=20261027
FAMILIES=('cycle3','switch3','unaliased2','ood4')
MAIN_ARMS=('RG2','RG3','RG4','RG5','RSX4','RSXp','RSXn','DLFp','DLFn','EB','EB2')
TV_ARMS=('RG2','RG3','RG5','RSX4','RSXp','RSXn','DLFp','DLFn','EB','EB2')


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
    for d in allD:hist[str(d)]=hist.get(str(d),0)+1
    return {'contrast':name,'cases':len(allD),'mean':round(float(np.mean(allD)),6),'ci95':_q(boot,.025,.975),
            'families_in_order':fams,'families':fam_out,'histogram':dict(sorted(hist.items(),key=lambda x:int(x[0]))),
            'cases_positive':sum(d>0 for d in allD),'cases_negative':sum(d<0 for d in allD),'cases_zero':sum(d==0 for d in allD)}


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN)
    check('2000 resamples, seed 20261027' in plan['metrics']['bootstrap'],'bootstrap registration changed')
    s=load(study/'transfer'/'SEAL.json');check(s['scientific_sha256']==sha(study/'transfer'/'SCIENTIFIC.json'),'transfer SCIENTIFIC does not match its SEAL')
    allc=load(study/'transfer'/'SCIENTIFIC.json')['cases'];cs=[c for c in allc if c['family']!='ood5'];c5=[c for c in allc if c['family']=='ood5']
    out={'schema':'brute.paired-analysis.v13_0','study':plan['study'],'resamples':B,'seed':SEED,'cluster':'target seed within family (3 masks each)',
         'smoke_dry_run':smoke,'scientific_sha256':{'transfer':s['scientific_sha256']},'complete':{'transfer':s.get('complete')},
         'main_cases':len(cs),'ood5_cases':len(c5)}
    for a in MAIN_ARMS:out['S_'+a]=contrast(cs,lambda c,a=a:c['summary']['S'][a],f'S({a}) = T_cert(SP8) - T_cert({a})')
    for a in TV_ARMS:out['TV_'+a]=contrast(cs,lambda c,a=a:c['summary']['S'][a]-c['summary']['S']['RG4'],f'TV({a}) = S({a}) - S(RG4)')
    for x in ('RSXn','RSXp'):out[x+'_minus_RSX4']=contrast(cs,lambda c,x=x:c['summary']['S'][x]-c['summary']['S']['RSX4'],f'S({x}) - S(RSX4)')
    for a in ('RG4','RG5'):out['ood5_S_'+a]=contrast(c5,lambda c,a=a:c['summary']['S'][a],f'ood5 S({a})',families=('ood5',))
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints, writes nothing')
    a=ap.parse_args()
    if a.smoke:obj=build(Path(a.study_dir),smoke=True);print({k:(v['mean'],v['ci95']) for k,v in obj.items() if isinstance(v,dict) and 'ci95' in v});raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'PAIRED_ANALYSIS_015.json'
    if a.check:check(out.read_bytes()==dumps(obj),'PAIRED_ANALYSIS_015.json does not reproduce');print('PAIRED_ANALYSIS_015 reproduces')
    else:write_new(out,obj);print({k:(v['mean'],v['ci95']) for k,v in obj.items() if isinstance(v,dict) and 'ci95' in v})
