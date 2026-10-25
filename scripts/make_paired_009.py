"""Paired, seed-clustered bootstraps for study-009 (BRUTE_PLAN_009 scoring.bootstrap). Committed and ledgered
(scoring_freeze_009) before the held-out run_start; nothing is tuned after results are seen.

Method: 2000 resamples, numpy default_rng(20261026), seeds resampled with replacement WITHIN each family (each seed = its
3 mask cases); per-family statistic = sum over resampled seeds of (X - Y certified forecasts over the seed's mask cases,
post-burn-in steps, taken + counterfactual) / sum of forecasts; pooled = unweighted mean over the listed families; 95% CI =
percentiles 2.5/97.5. Same estimator as the frozen make_paired_008 (one fresh generator per contrast, families in plan order).

GP1 (i), planning block, in_family_original families (40 seeds, 120 cases): P7 (planning block) vs A5 (the frozen A5 trace of
the same case from the main 2x2 block). ONE resample set (one generator, one index matrix per family) is used for both routes:
  route_coverage: dual coverage P7 - A5 as above; 97.5% CI = percentiles 1.25/98.75;
  route_tcert: T_cert(case) = first step t (1..44) whose taken-action forecast carries a conditional certificate, 45 if none;
    per-family statistic = sum over resampled seeds of (T_P7 - T_A5) / number of resampled cases; pooled = unweighted mean
    over families; 97.5% CI = percentiles 1.25/98.75.
Only cases present in BOTH blocks enter (a missing case is reported; GP1 (vi)/(G10) fail on incompleteness separately).
Breadth contrasts use all k forecasts of each step."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_009 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha

B,SEED=2000,20261026
STEPS=44
T=lambda c,a:c['arms'][a]['trace']
def _dual(r):return (r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None)
def _certs(r):return sum(f['certificate'] is not None for f in r['forecasts'])
def _q(boot,lo,hi):return [round(float(np.quantile(boot,lo)),6),round(float(np.quantile(boot,hi)),6)]


def tcert(trace):
    for r in trace:
        if r['certificate'] is not None:return r['step']
    return STEPS+1


def contrast(by,fams,X,Y,breadth=False,byY=None):
    rng=np.random.default_rng(SEED);fam_out={};boots=[];ests=[]
    for f in fams:
        cases=by[f];seeds=sorted({c['seed'] for c in cases});num=np.zeros(len(seeds));den=np.zeros(len(seeds))
        for c in cases:
            i=seeds.index(c['seed']);Bn=c['burn_in'];cy=c if byY is None else byY[(c['family'],c['seed'],c['mask_rate'])]
            for rx,ry in zip(T(c,X)[Bn:],T(cy,Y)[Bn:]):
                if breadth:num[i]+=_certs(rx)-_certs(ry);den[i]+=len(rx['forecasts'])
                else:num[i]+=_dual(rx)-_dual(ry);den[i]+=2
        idx=rng.integers(0,len(seeds),size=(B,len(seeds)))
        boot=num[idx].sum(1)/den[idx].sum(1);est=float(num.sum()/den.sum());boots.append(boot);ests.append(est)
        fam_out[f]={'gain':round(est,6),'forecasts':int(den.sum()),'seeds':len(seeds),'ci95':_q(boot,.025,.975)}
    return {'contrast':f'{X}-{Y}','families_pooled':list(fams),'pooled_gain':round(float(np.mean(ests)),6) if ests else None,
            'pooled_ci95':_q(np.mean(boots,axis=0),.025,.975) if boots else None,'families':fam_out}


def gp1(plan_by,a5,fams):
    """Both GP1 (i) routes from one resample set."""
    rng=np.random.default_rng(SEED);cov_b=[];cov_e=[];tc_b=[];tc_e=[];fam_out={};missing=[]
    for f in fams:
        cases=[c for c in plan_by.get(f,[]) if (c['family'],c['seed'],c['mask_rate']) in a5]
        missing+=[f"{c['family']}/{c['seed']}/{c['mask_rate']}" for c in plan_by.get(f,[]) if (c['family'],c['seed'],c['mask_rate']) not in a5]
        if not cases:continue
        seeds=sorted({c['seed'] for c in cases});n=len(seeds)
        num=np.zeros(n);den=np.zeros(n);dt=np.zeros(n);nc=np.zeros(n)
        tcp=[];tca=[]
        for c in cases:
            i=seeds.index(c['seed']);Bn=c['burn_in'];y=a5[(c['family'],c['seed'],c['mask_rate'])]
            for rx,ry in zip(T(c,'P7')[Bn:],T(y,'A5')[Bn:]):num[i]+=_dual(rx)-_dual(ry);den[i]+=2
            tp,ta=tcert(T(c,'P7')),tcert(T(y,'A5'));dt[i]+=tp-ta;nc[i]+=1;tcp.append(tp);tca.append(ta)
        idx=rng.integers(0,n,size=(B,n))
        cb=num[idx].sum(1)/den[idx].sum(1);tb=dt[idx].sum(1)/nc[idx].sum(1)
        ce=float(num.sum()/den.sum());te=float(dt.sum()/nc.sum())
        cov_b.append(cb);cov_e.append(ce);tc_b.append(tb);tc_e.append(te)
        fam_out[f]={'cases':len(cases),'seeds':n,'coverage_gain':round(ce,6),'coverage_ci95':_q(cb,.025,.975),
                    'tcert_diff':round(te,6),'tcert_ci95':_q(tb,.025,.975),
                    'mean_tcert_P7':round(sum(tcp)/len(tcp),6),'mean_tcert_A5':round(sum(tca)/len(tca),6),
                    'censored_P7':sum(t==STEPS+1 for t in tcp),'censored_A5':sum(t==STEPS+1 for t in tca)}
    if not fam_out:return {'families':{},'missing_comparator':missing,'route_coverage':None,'route_tcert':None}
    C=np.mean(cov_b,axis=0);Tt=np.mean(tc_b,axis=0)
    rc={'pooled_gain':round(float(np.mean(cov_e)),6),'ci97_5':_q(C,.0125,.9875),'ci95_reported':_q(C,.025,.975)}
    rt={'pooled_diff':round(float(np.mean(tc_e)),6),'ci97_5':_q(Tt,.0125,.9875),'ci95_reported':_q(Tt,.025,.975)}
    rc['pass']=rc['ci97_5'][0]>0;rt['pass']=rt['ci97_5'][1]<0
    return {'families':fam_out,'families_pooled':[f for f in fams if f in fam_out],'missing_comparator':missing,
            'route_coverage':rc,'route_tcert':rt,'one_resample_set':True,'resamples':B,'seed':SEED}


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


def block(study,name):
    d=load(study/name/'SCIENTIFIC.json');s=load(study/name/'SEAL.json')
    check(s['scientific_sha256']==sha(study/name/'SCIENTIFIC.json'),f'{name} SCIENTIFIC does not match its SEAL')
    return d,s


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN)
    check('2000 resamples, numpy default_rng(20261026)' in plan['scoring']['bootstrap'],'bootstrap registration changed')
    d2,s2=block(study,'2x2');db,sb=block(study,'breadth');dp,sp=block(study,'planning')
    two={f:[c for c in d2['cases'] if c['family']==f] for f in plan['heldout_ranges_2x2']};two={f:v for f,v in two.items() if v}
    br={f:[c for c in db['cases'] if c['family']==f] for f in plan['heldout_ranges_breadth']};br={f:v for f,v in br.items() if v}
    pl={f:[c for c in dp['cases'] if c['family']==f] for f in plan['heldout_ranges_2x2']};pl={f:v for f,v in pl.items() if v}
    IF=[f for f in plan['in_family_2x2'] if f in two];IFO=[f for f in plan['in_family_original_2x2'] if f in two]
    IB=[f for f in plan['in_family_breadth'] if f in br];PIFO=[f for f in plan['in_family_original_2x2'] if f in pl]
    a5={(c['family'],c['seed'],c['mask_rate']):c for c in d2['cases']}
    if smoke:   # dry run only: smoke planning seeds are not in the smoke 2x2 block; P7's own trace stands in for A5
        a5={(c['family'],c['seed'],c['mask_rate']):{**c,'arms':{'A5':c['arms']['P7']}} for c in dp['cases']}
    out={'schema':'brute.paired-analysis.v7_0','resamples':B,'seed':SEED,'cluster':'seed within family',
         'scope':'post-burn-in steps; 2x2/planning dual coverage (taken + counterfactual); breadth all-action coverage',
         'smoke_dry_run':smoke,
         'scientific_sha256':{'2x2':s2['scientific_sha256'],'breadth':sb['scientific_sha256'],'planning':sp['scientific_sha256']},
         'complete':{'2x2':d2.get('complete'),'breadth':db.get('complete'),'planning':dp.get('complete')},
         'G6b_dual_coverage_S7_minus_A2':contrast(two,IFO,'S7','A2'),
         'G6b_dual_coverage_SC7_minus_A2':contrast(two,IFO,'SC7','A2'),
         'GP1_i_P7_minus_A5':gp1(pl,a5,PIFO),
         'R_dual_coverage_A5_minus_A2':contrast(two,IFO,'A5','A2'),
         'R_dual_coverage_A4_minus_A2':contrast(two,IFO,'A4','A2'),
         'R_dual_coverage_R6_minus_A2':contrast(two,IFO,'R6','A2'),
         'R_dual_coverage_C6_minus_A2':contrast(two,IFO,'C6','A2'),
         'R_vs_v060_S7_minus_R6':contrast(two,IF,'S7','R6'),
         'R_vs_v060_SC7_minus_C6':contrast(two,IF,'SC7','C6'),
         'R_dual_coverage_S7_minus_A5':contrast(two,IF,'S7','A5'),
         'R_dual_coverage_SC7_minus_A5':contrast(two,IF,'SC7','A5'),
         'R_breadth_coverage_BS7_minus_B5':contrast(br,IB,'BS7','B5',True),
         'R_breadth_coverage_BSC7_minus_B5':contrast(br,IB,'BSC7','B5',True),
         'R_coverage_all_point':{'2x2':{a:coverage(two,list(two),a) for a in ('S7','SC7','R6','C6','A5','A4','A2')},
                                 'breadth':{a:coverage(br,list(br),a,True) for a in ('B5','BS7','BSC7')},
                                 'planning':{'P7':coverage(pl,list(pl),'P7')}}}
    return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints, writes nothing')
    a=ap.parse_args()
    if a.smoke:obj=build(Path(a.study_dir),smoke=True);print(dumps(obj).decode()[:4000]);raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'PAIRED_ANALYSIS_009.json'
    if a.check:check(out.read_bytes()==dumps(obj),'PAIRED_ANALYSIS_009.json does not reproduce');print('PAIRED_ANALYSIS_009 reproduces')
    else:write_new(out,obj);print(dumps(obj).decode()[:3000])
