"""Paired, seed-clustered bootstraps for study-014 (BRUTE_PLAN_014 metrics.bootstrap, transfer_definition.speedup).
Committed and ledgered (scoring_freeze_014) before the held-out run_start; nothing is tuned after results are seen.

Per target case the recorded summary S[X] = T_cert(SP8) - T_cert(X) (taken action, censored at 45; for DX on the DX
trajectory) is used; make_gates_014 checks it against the traces (GS_b) and GS_ref audits it.
Contrasts d(case):
  S_<X>            = S[X]                      (vs SP8; GS_rg uses S_RG4)
  TV_<X>           = S[X] - S[RG4]             (transfer value; GS_d TV_DLFp, GS_c TV_DLFn)
  DX_minus_DLF_p/n = S[DXp] - S[DLFp], S[DXn] - S[DLFn]   (GS_x uses _p)
Bootstrap (as make_paired_013.transfer_contrast): 2000 resamples, numpy default_rng(20261026), one fresh generator per
contrast; for each transfer family in plan order (cycle3, switch3, unaliased2, ood4) the family's target seeds are
resampled with replacement (each seed = its 3 mask cases); resample statistic = mean d over all resampled cases of all
families (pooled case mean); 95% CI = percentiles 2.5 / 97.5. Per-family means and CIs and d histograms are reported."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_014 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha
from experiments.brute_study_014 import ARMS
from scripts.make_paired_009 import B,SEED,_q

FAMILIES=('cycle3','switch3','unaliased2','ood4')
TV_ARMS=('RG2','RG3','RG5','DLFp','DLFn','DLF0p','DLF0n','ATp','ATn','LXp','LXn','DXp','DXn')


def contrast(cases,fn,name):
    rng=np.random.default_rng(SEED);fams=[f for f in FAMILIES if any(c['family']==f for c in cases)]
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
    check('2000 resamples, random seed 20261026' in plan['metrics']['bootstrap'],'bootstrap registration changed')
    s=load(study/'transfer'/'SEAL.json');check(s['scientific_sha256']==sha(study/'transfer'/'SCIENTIFIC.json'),'transfer SCIENTIFIC does not match its SEAL')
    cs=load(study/'transfer'/'SCIENTIFIC.json')['cases']
    out={'schema':'brute.paired-analysis.v12_0','study':plan['study'],'resamples':B,'seed':SEED,'cluster':'target seed within family (3 masks each)',
         'smoke_dry_run':smoke,'scientific_sha256':{'transfer':s['scientific_sha256']},'complete':{'transfer':s.get('complete')}}
    for a in ARMS:out['S_'+a]=contrast(cs,lambda c,a=a:c['summary']['S'][a],f'S({a}) = T_cert(SP8) - T_cert({a})')
    for a in TV_ARMS:out['TV_'+a]=contrast(cs,lambda c,a=a:c['summary']['S'][a]-c['summary']['S']['RG4'],f'TV({a}) = S({a}) - S(RG4)')
    for p in ('p','n'):out['DX_minus_DLF_'+p]=contrast(cs,lambda c,p=p:c['summary']['S']['DX'+p]-c['summary']['S']['DLF'+p],f'S(DX{p}) - S(DLF{p})')
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints, writes nothing')
    a=ap.parse_args()
    if a.smoke:obj=build(Path(a.study_dir),smoke=True);print({k:(v['mean'],v['ci95']) for k,v in obj.items() if isinstance(v,dict) and 'ci95' in v});raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'PAIRED_ANALYSIS_014.json'
    if a.check:check(out.read_bytes()==dumps(obj),'PAIRED_ANALYSIS_014.json does not reproduce');print('PAIRED_ANALYSIS_014 reproduces')
    else:write_new(out,obj);print({k:(v['mean'],v['ci95']) for k,v in obj.items() if isinstance(v,dict) and 'ci95' in v})
