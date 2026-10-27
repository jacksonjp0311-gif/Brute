"""Exploratory pre-plan diagnostic for v0.12.0 (run BEFORE BRUTE_PLAN_014; SEEN data only, Observed-on-seen, never
v0.12.0 evidence). Inputs: the sealed study-013 transfer block (results/study-013/transfer/RESULTS.json, 288 target
cases, already scored for v0.11.0) and the study-013 source libraries (96 seen source worlds 6150001-6150096), plus
results/study-013/HEARTBEAT_013.jsonl.

Arms, post hoc on each SP8 trace (learner-visible fields only for decisions; *_EVALUATOR_ONLY only for scoring):
  AT6   frozen v0.11.0 AT rule (library unanimous on c, c in SP8 support, after burn-in, >= 6 confirmations)
  BKu   bank unanimity: union of all four family libraries at the case offset (p) / of the three other families (n)
  DLm   bounded-region license, margin m in {0, 1}: after burn-in, library alive and unanimous on c, c in SP8 support,
        AND the projection of the next code over EVERY complete Moore machine with <= n_L + m states consistent with the
        target evidence (brute.region.RegionSpace(n_L + m), UNKNOWN counts as possible) is exactly {c}. n_L = library
        min_n. Exact: no false DLm certificate when the true machine has <= n_L + m states.
  BR1   ablation: as DL1 without the library-unanimity condition (n_L still read from the library)
Stress: every (target case, wrong-family library at any of the 24 offsets) pair where AT6 issues >= 1 transfer
certificate; DL1 is run with that wrong library.

  PYTHONPATH=. python scripts/diag_license_014.py   -> results/diag-014/LICENSE_DIAG_SEEN.json
"""
import json,statistics as st,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from brute.transfer import TransferTracker
from brute.region import RegionSpace
import experiments.brute_study_012 as S12
from scripts.check_seeds_013 import TRANSFER_FAMILIES as F,ROTATE
from experiments.brute_common_013 import load,PLAN,sha
OUT=ROOT/'results/diag-014/LICENSE_DIAG_SEEN.json';RES=ROOT/'results/study-013/transfer/RESULTS.json';CENS=45


def lib(plan,f,off):
    L,(H,s)=S12.library(f,plan['heldout_ranges_transfer']['sources'][0]-1+24*F.index(f)+off);return L['min_n'],H


def bounded(case,ns=(2,3,4,5)):
    out={}
    for n in ns:
        R=RegionSpace(n);R.initialize(tuple(case['initial_visible']));seq=[]
        for r in case['arms']['SP8']['trace']:
            seq.append(tuple(R.predict_support(b) for b in (0,1)));R.observe(r['action'],tuple(r['observed']))
        R.close();out[n]=seq
    return out


def arm(case,nL,H,BS=None,M=0,margin=0,need_lib=True):
    tr=TransferTracker(H,tuple(case['initial_visible']),case['burn_in']);false=0;first=CENS;tc=0;conf=0
    for i,r in enumerate(case['arms']['SP8']['trace']):
        t=r['step'];a=r['action'];R={a:r,1-a:r['counterfactual']}
        act={a:r['actual_emission_EVALUATOR_ONLY'],1-a:r['counterfactual_actual_EVALUATOR_ONLY']}
        for b in (0,1):
            c=R[b]['certificate']
            if c is None and t>case['burn_in'] and R[b]['support'] is not None and conf>=M:
                p=tr.predict(b);bs=BS[nL+margin][i][b] if BS else None
                if not need_lib and bs is not None and len(bs)==1:p=bs[0]
                if p is not None and p in R[b]['support'] and (BS is None or bs==(p,)):c=p;tc+=1
            if c is not None and c!=act[b]:false+=1
            if b==a and c is not None and first==CENS:first=t
        p=tr.predict(a);o=tuple(r['observed'])
        if p is not None and r['support'] is not None and len(r['support'])>=2 and None not in o and o[0]*2+o[1]==p:conf+=1
        tr.observe(t,a,o)
    return false,first,tc


def tcert(case):
    for r in case['arms']['SP8']['trace']:
        if r['certificate'] is not None:return r['step']
    return CENS


def summary(v):
    return {'cases':len(v),'false_certificates':sum(x[0] for x in v),'cases_with_false':sum(x[0]>0 for x in v),
            'mean_S':round(st.mean(x[1] for x in v),4),'cases_helped':sum(x[1]>0 for x in v),'cases_hurt':sum(x[1]<0 for x in v),
            'transfer_certificates':sum(x[2] for x in v)}


def heartbeat():
    L=[json.loads(l) for l in open(ROOT/'results/study-013/HEARTBEAT_013.jsonl')];out=[]
    for i,l in enumerate(L):
        if l['gap_s'] and l['gap_s']>10:
            out.append({'wall':l['wall'],'gap_wall_s':l['gap_s'],'gap_monotonic_s':round(l['monotonic']-L[i-1]['monotonic'],3)})
    return {'beats':len(L),'gaps_over_10s':out,'reading':'monotonic gap == wall gap: CLOCK_MONOTONIC kept running, so the '
            'watchdog process itself was not scheduled or was blocked (each beat does write + fsync + /proc reads); a clock jump '
            'is excluded (Observed). Cause (I/O stall in fsync vs. host deschedule) is not identified (Open).'}


def main():
    plan=load(PLAN);d=load(RES);t0=time.time();res={};fam={};stress=[]
    for c in d['cases']:
        f=c['family'];off=c['seed']-plan['heldout_ranges_transfer']['targets'][f][0]+1;s0=tcert(c);BS=bounded(c)
        bank={'p':[h for g in F for h in lib(plan,g,off)[1]],'n':[h for g in F if g!=f for h in lib(plan,g,off)[1]]}
        for k,g in (('p',f),('n',ROTATE[f])):
            nL,H=lib(plan,g,off)
            runs={'AT6':arm(c,nL,H,None,6),'DL0':arm(c,nL,H,BS,0,0),'DL1':arm(c,nL,H,BS,0,1),'BR1':arm(c,nL,H,BS,0,1,False),
                  'BKu':arm(c,nL,sorted(set(bank[k])))}
            for a_,(fa,fi,tc) in runs.items():
                res.setdefault(a_+k,[]).append((fa,s0-fi,tc));fam.setdefault(a_+k,{}).setdefault(f,[]).append(s0-fi)
        for g in F:
            if g==f:continue
            for o in range(1,25):
                nL,H=lib(plan,g,o);fa,fi,tc=arm(c,nL,H,None,6)
                fd,fid,tcd=arm(c,nL,H,BS,0,1);fd0,_,_=arm(c,nL,H,BS,0,0)
                stress.append({'target':f,'seed':c['seed'],'mask':c['mask_rate'],'library_family':g,'offset':o,'n_L':nL,'target_states':c['true_hidden_state_count_EVALUATOR_ONLY'],
                               'AT6_false':fa,'AT6_transfer':tc,'DL1_false':fd,'DL1_transfer':tcd,'DL0_false':fd0})
    sp=[s for s in stress if s['AT6_transfer']>0]
    rep={'schema':'brute.diag.v12_0','inputs':{'results':'results/study-013/transfer/RESULTS.json','results_sha256':sha(RES)},
         'label':'Observed on SEEN data (exploratory, pre-plan); not v0.12.0 evidence',
         'arms':{k:summary(v) for k,v in sorted(res.items())},
         'mean_S_by_family':{k:{f:round(st.mean(v),4) for f,v in fv.items()} for k,fv in sorted(fam.items())},
         'stress':{'all_pairs':len(stress),'stress_pairs_AT6_licenses':len(sp),
                   'AT6_false_on_stress':sum(s['AT6_false'] for s in sp),'AT6_stress_pairs_with_false':sum(s['AT6_false']>0 for s in sp),
                   'DL1_false_on_stress':sum(s['DL1_false'] for s in sp),'DL1_false_all_pairs':sum(s['DL1_false'] for s in stress),
                   'DL0_false_all_pairs':sum(s['DL0_false'] for s in stress),'DL0_pairs_with_false':sum(s['DL0_false']>0 for s in stress),
                   'DL1_transfer_on_stress':sum(s['DL1_transfer'] for s in sp),
                   'stress_pairs_by_target_library':{f'{a}<-{b}':sum(1 for s in sp if (s['target'],s['library_family'])==(a,b)) for a in F for b in F if a!=b},
                   'pairs_outside_exact_bound_DL1':sum(1 for s in stress if s['target_states']>s['n_L']+1),
                   'DL1_false_outside_exact_bound':sum(s['DL1_false'] for s in stress if s['target_states']>s['n_L']+1)},
         'heartbeat_013':heartbeat(),'wall_informational_s':round(time.time()-t0,1)}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({k:rep[k] for k in ('arms','stress')},indent=1))


if __name__=='__main__':main()
