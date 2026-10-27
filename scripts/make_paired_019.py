"""Paired, seed-clustered bootstraps for study-019 (BRUTE_PLAN_019 metrics.bootstrap: 2000 resamples, seed 20261030, 95%
percentile CI). Committed and ledgered (scoring_freeze_019) before the held-out run_start; nothing is tuned after
results are seen. Resampling routine = make_paired_018.contrast's (frozen) with seed 20261030: for each family in plan
order the family's target seeds are resampled with replacement (each seed = its cases in the subset); statistic =
pooled case mean; CI = percentiles 2.5 / 97.5. Every contrast restarts the generator (np.random.default_rng(20261030)),
so the two arms of a paired difference always see the same resampled seeds.

Per case the recorded summary is used (make_gates_019 recounts it from the traces; GS_ref7 audits it).
Main subsets of the transfer block (schema brute.case.v17_0): eps0 / eps1 / eps2 (120 cases each), noisy (eps1 + eps2, 240),
stress (eps 0.05, 120). For every main subset and every arm X in SP8, RG4, RGN4, RGNB4, RGNB4_0, RGN4_or:
  C_<X>_<subset>          = certificates[X] / 88
  dC_<X>_<subset>         = (certificates[X] - certificates[RG4]) / 88   (X != RG4)
  casefalse_<X>_<subset>  = 1 if the case has >= 1 false certificate for X
  dC_RGNB4_RGN4_<subset>  = (certificates[RGNB4] - certificates[RGN4]) / 88   (GNB clause (c) on eps2)
  (C_RGNB4_eps2: GNB clause (d).)
alphabet3 subsets (schema brute.case3.v17_0, family rand4a3): a3_eps0, a3_eps2 (48 cases each); arms RG4_3, RGN4_3,
RGNB4_3: C_<X>_<subset> = certificates[X] / 132, casefalse_<X>_<subset>, dC_RGNB4_3_RGN4_3_<subset> (R_alphabet3_coverage)."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_019 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha
from scripts.make_paired_009 import B,_q

SEED=20261030;SLOTS=88;SLOTS3=132
FAMILIES=('cycle3','switch3','unaliased2','ood4');A3_FAMILIES=('rand4a3',)
ARMS=('SP8','RG4','RGN4','RGNB4','RGNB4_0','RGN4_or');A3_ARMS=('RG4_3','RGN4_3','RGNB4_3')
def _main(c):return c.get('schema')=='brute.case.v17_0'
def _a3(c):return c.get('schema')=='brute.case3.v17_0'
def _stress(c):return c['block']=='stress' or (c['block'].startswith('smoke') and c['eps']==0.05)
SUBSETS={'eps0':lambda c:_main(c) and not _stress(c) and c['eps']==0.0,'eps1':lambda c:_main(c) and not _stress(c) and c['eps']==0.01,
         'eps2':lambda c:_main(c) and not _stress(c) and c['eps']==0.02,'noisy':lambda c:_main(c) and not _stress(c) and c['eps'] in (0.01,0.02),
         'stress':lambda c:_main(c) and _stress(c)}
A3_SUBSETS={'a3_eps0':lambda c:_a3(c) and c['eps']==0.0,'a3_eps2':lambda c:_a3(c) and c['eps']==0.02}


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
    if not fams:return {'contrast':name,'cases':0,'mean':None,'ci95':None,'families':{}}
    boot=np.sum(ts,axis=0)/np.sum(ns,axis=0)
    return {'contrast':name,'cases':len(allD),'mean':round(float(np.mean(allD)),6),'ci95':_q(boot,.025,.975),
            'families_in_order':fams,'families':fam_out,
            'cases_positive':sum(d>0 for d in allD),'cases_negative':sum(d<0 for d in allD),'cases_zero':sum(d==0 for d in allD)}


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN)
    check('2000 resamples, seed 20261030' in plan['metrics']['bootstrap'],'bootstrap registration changed')
    s=load(study/'transfer'/'SEAL.json');check(s['scientific_sha256']==sha(study/'transfer'/'SCIENTIFIC.json'),'transfer SCIENTIFIC does not match its SEAL')
    allc=load(study/'transfer'/'SCIENTIFIC.json')['cases']
    out={'schema':'brute.paired-analysis.v17_0','study':plan['study'],'resamples':B,'seed':SEED,'cluster':'target seed within family',
         'coverage_slots_per_case':{'main':SLOTS,'alphabet3':SLOTS3},'smoke_dry_run':smoke,'scientific_sha256':{'transfer':s['scientific_sha256']},
         'complete':{'transfer':s.get('complete')},'cases':len(allc)}
    cert=lambda c,a:c['summary']['certificates'][a]
    for sub,sel in SUBSETS.items():
        cs=[c for c in allc if sel(c)];out['n_'+sub]=len(cs)
        for a in ARMS:
            out[f'C_{a}_{sub}']=contrast(cs,lambda c,a=a:cert(c,a)/SLOTS,f'C({a}) = certificates({a}) / 88 on {sub}')
            out[f'casefalse_{a}_{sub}']=contrast(cs,lambda c,a=a:float(c['summary']['case_false'][a]),f'case-false({a}) on {sub}')
            if a!='RG4':out[f'dC_{a}_{sub}']=contrast(cs,lambda c,a=a:(cert(c,a)-cert(c,'RG4'))/SLOTS,f'dC({a}) = (certificates({a}) - certificates(RG4)) / 88 on {sub}')
        out[f'dC_RGNB4_RGN4_{sub}']=contrast(cs,lambda c:(cert(c,'RGNB4')-cert(c,'RGN4'))/SLOTS,f'dC = (certificates(RGNB4) - certificates(RGN4)) / 88 on {sub}')
    for sub,sel in A3_SUBSETS.items():
        cs=[c for c in allc if sel(c)];out['n_'+sub]=len(cs)
        for a in A3_ARMS:
            out[f'C_{a}_{sub}']=contrast(cs,lambda c,a=a:cert(c,a)/SLOTS3,f'C({a}) = certificates({a}) / 132 on {sub}',A3_FAMILIES)
            out[f'casefalse_{a}_{sub}']=contrast(cs,lambda c,a=a:float(c['summary']['case_false'][a]),f'case-false({a}) on {sub}',A3_FAMILIES)
        out[f'dC_RGNB4_3_RGN4_3_{sub}']=contrast(cs,lambda c:(cert(c,'RGNB4_3')-cert(c,'RGN4_3'))/SLOTS3,f'dC = (certificates(RGNB4_3) - certificates(RGN4_3)) / 132 on {sub}',A3_FAMILIES)
    return out


def _brief(obj):return {k:(v['mean'],v['ci95']) for k,v in obj.items() if isinstance(v,dict) and 'ci95' in v and (k.startswith('C_RGNB4') or k.startswith('dC_RGNB4_RGN4'))}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints, writes nothing')
    a=ap.parse_args()
    if a.smoke:obj=build(Path(a.study_dir),smoke=True);print(_brief(obj));raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'PAIRED_ANALYSIS_019.json'
    if a.check:check(out.read_bytes()==dumps(obj),'PAIRED_ANALYSIS_019.json does not reproduce');print('PAIRED_ANALYSIS_019 reproduces')
    else:write_new(out,obj);print(_brief(obj))
