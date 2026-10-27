"""Exploratory pre-plan diagnostic, part b (run BEFORE BRUTE_PLAN_014, after scripts/diag_license_014.py; SEEN data,
Observed-on-seen, never v0.12.0 evidence). Same inputs as part a (sealed study-013 transfer traces and seen libraries).

Question: how much of the DL1 speedup is TRANSFER? Arms on each SP8 trace (decisions use learner-visible fields only):
  RGn   library-free bounded region: after burn-in, c in the SP8 support and RegionSpace(n) projection == {c},
        n in {2, 3, 4, 5}. RG4 uses the DECLARED family bound (4 states): Exact-sound for every in-family target.
  DLF   the candidate v0.12.0 license: SP8 certificate; else after burn-in with c in the SP8 support, certify c iff
        RegionSpace(4) projection == {c} (RG4) OR (library alive and unanimous on c AND RegionSpace(min(n_L + 1, 4))
        projection == {c}). DLF certificates contain RG4's by construction, so S(DLF) - S(RG4) >= 0.
Transfer value = S(DLF) - S(RG4) on the same case. Stress as part a (all 72 wrong-family libraries per target case;
stress pairs = AT6 licenses >= 1 transfer certificate).

  PYTHONPATH=. python scripts/diag_license_014b.py   -> results/diag-014/LICENSE_DIAG_SEEN_B.json
"""
import json,statistics as st,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from brute.transfer import TransferTracker
from scripts.diag_license_014 import lib,bounded,arm,tcert,CENS,RES,F,ROTATE
from experiments.brute_common_013 import load,PLAN,sha
OUT=ROOT/'results/diag-014/LICENSE_DIAG_SEEN_B.json';FB=4


def rg(case,BS,n):
    false=0;first=CENS;tc=0
    for i,r in enumerate(case['arms']['SP8']['trace']):
        t=r['step'];a=r['action'];R={a:r,1-a:r['counterfactual']}
        act={a:r['actual_emission_EVALUATOR_ONLY'],1-a:r['counterfactual_actual_EVALUATOR_ONLY']}
        for b in (0,1):
            c=R[b]['certificate']
            if c is None and t>case['burn_in'] and R[b]['support'] is not None:
                bs=BS[n][i][b]
                if bs is not None and len(bs)==1 and bs[0] in R[b]['support']:c=bs[0];tc+=1
            if c is not None and c!=act[b]:false+=1
            if b==a and c is not None and first==CENS:first=t
    return false,first,tc


def dlf(case,nL,H,BS,margin=1):
    tr=TransferTracker(H,tuple(case['initial_visible']),case['burn_in']);false=0;first=CENS;tc=0;lic=0;nb=min(nL+margin,FB)
    for i,r in enumerate(case['arms']['SP8']['trace']):
        t=r['step'];a=r['action'];R={a:r,1-a:r['counterfactual']}
        act={a:r['actual_emission_EVALUATOR_ONLY'],1-a:r['counterfactual_actual_EVALUATOR_ONLY']}
        for b in (0,1):
            c=R[b]['certificate']
            if c is None and t>case['burn_in'] and R[b]['support'] is not None:
                g=BS[FB][i][b];p=tr.predict(b);l=BS[nb][i][b]
                if g is not None and len(g)==1 and g[0] in R[b]['support']:c=g[0];tc+=1
                elif p is not None and p in R[b]['support'] and l==(p,):c=p;tc+=1;lic+=1
            if c is not None and c!=act[b]:false+=1
            if b==a and c is not None and first==CENS:first=t
        tr.observe(t,a,tuple(r['observed']))
    return false,first,tc,lic


def ci(v,B=2000,seed=20261026):
    import random;rng=random.Random(seed);k=sorted(set(x[0] for x in v));by={s:[x[1] for x in v if x[0]==s] for s in k};m=[]
    for _ in range(B):
        xs=[y for s in (rng.choice(k) for _ in k) for y in by[s]];m.append(sum(xs)/len(xs))
    m.sort();return round(sum(x[1] for x in v)/len(v),4),round(m[int(.025*B)],4),round(m[int(.975*B)-1],4)


def main():
    plan=load(PLAN);d=load(RES);t0=time.time();rows=[];stress=[]
    for c in d['cases']:
        f=c['family'];off=c['seed']-plan['heldout_ranges_transfer']['targets'][f][0]+1;s0=tcert(c);BS=bounded(c)
        row={'family':f,'seed':c['seed'],'mask':c['mask_rate']}
        for n in (2,3,4,5):fa,fi,tc=rg(c,BS,n);row[f'RG{n}']=(fa,s0-fi,tc)
        for k,g in (('p',f),('n',ROTATE[f])):
            nL,H=lib(plan,g,off);fa,fi,tc,li=dlf(c,nL,H,BS);row['DLF'+k]=(fa,s0-fi,tc,li)
            fa,fi,tc,li=dlf(c,nL,H,BS,0);row['DLF0'+k]=(fa,s0-fi,tc,li)
        rows.append(row)
        for g in F:
            if g==f:continue
            for o in range(1,25):
                nL,H=lib(plan,g,o);fa,_,tca=arm(c,nL,H,None,6);fd,_,_,li=dlf(c,nL,H,BS)
                stress.append({'target':f,'library_family':g,'n_L':nL,'target_states':c['true_hidden_state_count_EVALUATOR_ONLY'],
                               'AT6_false':fa,'AT6_transfer':tca,'DLF_false':fd,'DLF_library_licensed':li})
    def summ(k):
        v=[r[k] for r in rows];return {'false_certificates':sum(x[0] for x in v),'cases_with_false':sum(x[0]>0 for x in v),
            'mean_S':round(st.mean(x[1] for x in v),4),'cases_helped':sum(x[1]>0 for x in v),'cases_hurt':sum(x[1]<0 for x in v),
            'mean_S_by_family':{f:round(st.mean(r[k][1] for r in rows if r['family']==f),4) for f in F},
            **({'library_licensed_certificates':sum(x[3] for x in v)} if len(v[0])>3 else {})}
    tv={k:ci([(r['seed'],r[k][1]-r['RG4'][1]) for r in rows]) for k in ('DLFp','DLFn','DLF0p','DLF0n')}
    sp=[s for s in stress if s['AT6_transfer']>0]
    rep={'schema':'brute.diag.v12_0b','label':'Observed on SEEN data (exploratory, pre-plan); not v0.12.0 evidence',
         'inputs':{'results':'results/study-013/transfer/RESULTS.json','results_sha256':sha(RES)},
         'arms':{k:summ(k) for k in ('RG2','RG3','RG4','RG5','DLFp','DLFn','DLF0p','DLF0n')},
         'transfer_value_vs_RG4_mean_ci95':tv,
         'speedup_vs_SP8_mean_ci95':{k:ci([(r['seed'],r[k][1]) for r in rows]) for k in ('RG4','DLFp','DLFn')},
         'stress':{'pairs':len(stress),'stress_pairs':len(sp),'AT6_false_on_stress':sum(s['AT6_false'] for s in sp),
                   'DLF_false_on_stress':sum(s['DLF_false'] for s in sp),'DLF_false_all_pairs':sum(s['DLF_false'] for s in stress),
                   'DLF_library_licensed_all_pairs':sum(s['DLF_library_licensed'] for s in stress),
                   'pairs_outside_exact_bound':sum(1 for s in stress if s['target_states']>min(s['n_L']+1,FB)),
                   'DLF_false_outside_exact_bound':sum(s['DLF_false'] for s in stress if s['target_states']>min(s['n_L']+1,FB))},
         'wall_informational_s':round(time.time()-t0,1)}
    OUT.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n');print(json.dumps(rep,indent=1))


if __name__=='__main__':main()
