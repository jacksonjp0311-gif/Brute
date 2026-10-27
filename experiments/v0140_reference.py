"""Second implementation (same author, no `brute` import) for study BRUTE-0140-DEFERRED-SPLIT-016 (GS_ref4, GLV).

Written from experiments/BRUTE_PLAN_016.json (transfer_definition, second_implementation) BEFORE brute/deferredsplit.py
and brute/api/certify4.py existed. NOT an independent or third-party audit: same author. Extends
experiments/v0130_reference.py (imported unchanged; it imports no `brute` module).

Recomputed per case from learner-visible fields and the (verified) recorded bounded supports; *_EVALUATOR_ONLY fields are
read only to mark wrong certificates and the outside-bound flag:
  * bounded supports n = 1..5 on the SP8, RSX and (main block) RSXL trajectories, checked against exhaustive enumeration;
  * the RSX action (v0130 rule) and the RSXL action at every step;
  * RG4 / RG5 (SP8), RSXL4 (RG4 on RSXL), RSXLp / RSXLn (DLF margin 1 on RSXL), DLFp / DLFn (SP8, margin 1),
    DLF2p / DLF2n (SP8, margin 2: license bound min(n_L + 2, 4)), RSX4 (RG4 on RSX), EB (margin 1, SP8), the summary;
  * the 72-library stress entries (AT6 and DLF on SP8, DLF on RSXL, per-pair certificate lists);
  * ood5 block: bounded supports n = 1..5 on SP8, RG4 / RG5, summary.

RSXL rule (plan transfer_definition.RSXL_trajectory; reading recorded as deviation #75): let f = the first step at which
RG4 on the RSXL trajectory certifies the TAKEN action (its first_cert_step, CENSOR = 45 if never). At step t <= f the
action is the SP8 LU-R choice ('sp8', deferred = True); at t > f it is the v0130 RSX choice on the recorded RSXL n = 4
support sizes (rule 'rsx' or 'sp8', deferred = False). Hence the RSXL trajectory equals the SP8 trajectory through step f
and S(RSXL4) = S(RG4) (Exact).

Case format (learner side writes the same dicts; '*wall_informational*' keys excluded):
  case['bounded'] = {'SP8' | 'RSX' | 'RSXL': {str(n): {'support', 'unknown'}}} (v0130 format), ood5: {'SP8'} only
  case['rsx'] = v0130 format
  case['rsxl'] = {'trace': [{'step', 'action', 'sp8_action', 'passive_action', 'rsxl_rule' ('rsx' | 'sp8'), 'deferred',
      'bounded_sizes' [k0, k1], 'certificate' [c0, c1], 'support' [s0, s1], 'observed', 'actual_EVALUATOR_ONLY' [a0, a1],
      'wrong' [w0, w1]}], 'first_cert_step', 'false_certificates', 'certificates', 'rule_counts' {'rsx', 'sp8'},
      'switch_step' (first step with deferred False, None if none)}
  case['transfer'][arm] for arm in MAIN_ARMS (v0120 RG / DLF formats; EB v0130 format); ood5: RG4, RG5
  case['stress'] = [{'source_family', 'source_seed', 'min_n', 'AT6_false', 'AT6_transfer', 'DLF_false', 'DLF_license',
      'DLF_rg', 'DLF_certs', 'RSXL_false', 'RSXL_license', 'RSXL_rg', 'RSXL_certs', 'outside_exact_bound_EVALUATOR_ONLY'}]
  case['summary'] = {'first_cert_step': {arm, 'SP8'}, 'S': {arm}, 'false': {arm, 'SP8'}, 'certificates': {arm, 'SP8'}}
"""
from __future__ import annotations
import copy,random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from experiments.brute_common import check,load,VerificationError
from experiments.v0100_reference import ref_library
from experiments.v0110_reference import ref_gated_arm,hyps
from experiments.v0120_reference import steps_sp8,audit_bounded,ref_rg,ref_dlf,_cmp,CENSOR,FB
from experiments.v0130_reference import steps_rsx,rsx_choice,audit_rsx,ref_eb,certs
from scripts.check_seeds_016 import source_seed,stress_sources,smoke_source,smoke_stress_sources

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_016.json'
NS=(1,2,3,4,5)
MAIN_ARMS=('RG4','RG5','RSXL4','RSXLp','RSXLn','DLFp','DLFn','DLF2p','DLF2n','RSX4','EB')
OOD5_ARMS=('RG4','RG5')


def rsxl_choice(t,burn,sizes,sp8_action,deferred):
    """(action, rule) of the RSXL rule at one step; deferred = RG4 has not yet certified the taken action before t."""
    if deferred:return sp8_action,'sp8'
    return rsx_choice(t,burn,sizes,sp8_action)


def audit_rsxl(rsxl,BL,burn,where='RSXL'):
    """BL = the recorded RSXL bounded supports (checked by audit_bounded). Recomputes RG4 on the RSXL trajectory and the
    RSXL action at every step."""
    tr=rsxl['trace'];L=steps_rsx({'trace':tr});rg=ref_rg(L,BL,4,burn);f=rg['first_cert_step'];cnt={'rsx':0,'sp8':0}
    for i,r in enumerate(tr):
        check(r['step']==i+1,f'{where} step index')
        sizes=[len(x) if x is not None else 0 for x in BL['4']['support'][i]]
        check(r['bounded_sizes']==sizes,f'{where} step {i+1} bounded_sizes')
        d=r['step']<=f;check(r['deferred']==d,f'{where} step {i+1} deferred')
        a,rule=rsxl_choice(r['step'],burn,sizes,r['sp8_action'],d)
        check(r['action']==a and r['rsxl_rule']==rule,f'{where} step {i+1} action/rule');cnt[rule]+=1
        w=[r['certificate'][b] is not None and r['certificate'][b]!=r['actual_EVALUATOR_ONLY'][b] for b in (0,1)]
        check(r['wrong']==w,f'{where} step {i+1} wrong')
    first=next((s['t'] for s in L if s['cert'][s['a']] is not None),CENSOR)
    check(rsxl['first_cert_step']==first,where+' first_cert_step')
    check(rsxl['false_certificates']==sum(sum(r['wrong']) for r in tr),where+' false')
    check(rsxl['certificates']==sum(c is not None for r in tr for c in r['certificate']),where+' certificates')
    check(rsxl['rule_counts']==cnt,where+' rule_counts')
    check(rsxl['switch_step']==(f+1 if f<len(tr) else None),where+' switch_step')
    return L


def libraries_for(c,plan):
    fam=c['family']
    if c.get('smoke'):return smoke_source(c['seed']),smoke_source(c['seed'],True),smoke_stress_sources(c['seed'])
    off=c['seed']-plan['heldout_ranges_transfer']['targets'][fam][0]+1
    return source_seed(fam,off,plan),source_seed(fam,off,plan,True),stress_sources(fam,plan)


def _summary(S,exp,arms):
    f0=next((s['t'] for s in S if s['cert'][s['a']] is not None),CENSOR)
    sp8f=sum(s['cert'][b] is not None and s['cert'][b]!=s['act'][b] for s in S for b in (0,1))
    sp8n=sum(s['cert'][b] is not None for s in S for b in (0,1))
    first={a:exp[a]['first_cert_step'] for a in arms}
    return {'first_cert_step':dict(first,SP8=f0),'S':{a:f0-first[a] for a in arms},
            'false':dict({a:exp[a]['false_certificates'] for a in arms},SP8=sp8f),
            'certificates':dict({a:exp[a]['certificates'] for a in arms},SP8=sp8n)}


def audit_case(c,plan):
    """(ok, message): the first differing field, or (True, None)."""
    try:
        check(c['tau6']==plan['tau6']['value'],'tau6');burn=c['burn_in'];init=tuple(c['initial_visible'])
        S=steps_sp8(c);check(len(S)==c['steps']==plan['actions_per_case'],'SP8 steps');T=c['transfer']
        audit_bounded(c['bounded']['SP8'],S,init,NS,'SP8');BS=c['bounded']['SP8'];exp={}
        if c['family']=='ood5':
            check(sorted(c['bounded'])==['SP8'] and 'rsx' not in c and 'rsxl' not in c and 'stress' not in c,'ood5 layout')
            for n in (4,5):exp[f'RG{n}']=ref_rg(S,BS,n,burn)
            for arm,e in exp.items():_cmp(T[arm],e,arm)
            check(sorted(T)==sorted(OOD5_ARMS),'ood5 arm set');check(c['summary']==_summary(S,exp,OOD5_ARMS),'summary')
            return True,None
        check(sorted(c['bounded'])==['RSX','RSXL','SP8'],'bounded trajectories')
        R=steps_rsx(c['rsx']);L=steps_rsx(c['rsxl']);check(len(R)==len(S)==len(L),'RSX / RSXL steps')
        audit_bounded(c['bounded']['RSX'],R,init,NS,'RSX');BR=c['bounded']['RSX'];audit_rsx(c['rsx'],BR['4'],burn)
        audit_bounded(c['bounded']['RSXL'],L,init,NS,'RSXL');BL=c['bounded']['RSXL'];audit_rsxl(c['rsxl'],BL,burn)
        for n in (4,5):exp[f'RG{n}']=ref_rg(S,BS,n,burn)
        exp['RSXL4']=ref_rg(L,BL,4,burn);exp['RSX4']=ref_rg(R,BR,4,burn);exp['EB']=ref_eb(S,BS,burn,1)
        pos,neg,st=libraries_for(c,plan)
        for key,suf,(sf,ss) in (('pos','p',pos),('neg','n',neg)):
            lib=ref_library(sf,ss);got=c['libraries'][key]
            for k in ('source_family','source_seed','min_n','status','motif_count','motifs'):check(got[k]==lib[k],f'library {key} {k}')
            H,_=hyps(lib);nL=lib['min_n']
            exp['DLF'+suf]=ref_dlf(S,BS,init,burn,H,nL,1,key,'SP8');exp['DLF2'+suf]=ref_dlf(S,BS,init,burn,H,nL,2,key,'SP8')
            exp['RSXL'+suf]=ref_dlf(L,BL,init,burn,H,nL,1,key,'RSXL')
        for arm,e in exp.items():_cmp(T[arm],e,arm)
        check(sorted(T)==sorted(MAIN_ARMS),'transfer arm set');check(c['summary']==_summary(S,exp,MAIN_ARMS),'summary')
        check(len(c['stress'])==len(st),'stress count');ts=c['true_hidden_state_count_EVALUATOR_ONLY']
        for j,(sf,ss) in enumerate(st):
            lib=ref_library(sf,ss);H,_=hyps(lib);nL=lib['min_n'];at=ref_gated_arm(c,lib,'stress','AT')
            d1=ref_dlf(S,BS,init,burn,H,nL,1,'stress','SP8');d2=ref_dlf(L,BL,init,burn,H,nL,1,'stress','RSXL')
            e={'source_family':sf,'source_seed':ss,'min_n':nL,'AT6_false':at['false_certificates'],'AT6_transfer':at['transfer_certificates'],
               'DLF_false':d1['false_certificates'],'DLF_license':d1['license_certificates'],'DLF_rg':d1['rg_certificates'],'DLF_certs':certs(d1),
               'RSXL_false':d2['false_certificates'],'RSXL_license':d2['license_certificates'],'RSXL_rg':d2['rg_certificates'],'RSXL_certs':certs(d2),
               'outside_exact_bound_EVALUATOR_ONLY':ts>min(nL+1,FB)}
            _cmp(c['stress'][j],e,f'stress {j}')
        return True,None
    except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError) as exc:
        return False,f'{type(exc).__name__}: {exc}'


def _job(x):
    i,c,plan=x;return i,audit_case(c,plan)


def count(cases,plan,workers=1,on_result=None):
    jobs=[(i,c,plan) for i,c in enumerate(cases)];outs=[]
    if workers<=1:
        for j in jobs:
            outs.append(_job(j))
            if on_result:on_result(outs[-1])
    else:
        with ProcessPoolExecutor(workers) as ex:
            for o in ex.map(_job,jobs,chunksize=1):
                outs.append(o)
                if on_result:on_result(o)
    return [{'case':i,'family':cases[i]['family'],'seed':cases[i]['seed'],'mask_rate':cases[i]['mask_rate'],'first_difference':m}
            for i,(ok,m) in sorted(outs) if not ok]


KINDS=('bounded',)*5+('rsxl',)*4+('dlf',)*3+('stress',)*3+('rg',)*2+('eb',)*1+('dlf2',)*2


def mutate(cases,k=20,rng_seed=20261028):
    """k single-field errors in k distinct main-block cases (plan GS_ref4 mutation test). Returns (mutated copies,
    injected index set)."""
    check(k==len(KINDS),'k must equal len(KINDS)');rng=random.Random(rng_seed)
    main=[i for i,c in enumerate(cases) if c['family']!='ood5'];check(len(main)>=k,'too few main cases for the mutation test')
    idx=rng.sample(main,k);kinds=list(KINDS);rng.shuffle(kinds);out=list(cases);inj=set()
    for i,kind in zip(idx,kinds):
        c=copy.deepcopy(cases[i])
        if kind=='bounded':
            tj=rng.choice(('SP8','RSX','RSXL'));n=str(rng.choice(NS));B=c['bounded'][tj][n]
            cand=[(s,b) for s in range(len(B['support'])) for b in (0,1) if B['support'][s][b] is not None and B['unknown'][s][b]==0]
            s,b=rng.choice(cand);v=B['support'][s][b];B['support'][s][b]=v[1:] if len(v)>1 else [(v[0]+1)%4]
        elif kind=='rsxl':
            r=c['rsxl']['trace'][rng.randrange(c['burn_in'],c['steps'])]
            if rng.random()<0.5:r['action']=1-r['action']
            else:r['deferred']=not r['deferred']
        elif kind=='dlf':
            arm=rng.choice(('DLFp','DLFn','RSXLp','RSXLn'));r=c['transfer'][arm]['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            r['rule'][b]={'sp8':'rg','rg':'license','license':None,None:'license'}[r['rule'][b]]
        elif kind=='dlf2':
            arm=rng.choice(('DLF2p','DLF2n'));r=c['transfer'][arm]['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        elif kind=='stress':
            c['stress'][rng.randrange(len(c['stress']))][rng.choice(('AT6_false','DLF_license','RSXL_rg','RSXL_false'))]+=1
        elif kind=='rg':
            r=c['transfer'][rng.choice(('RG4','RSXL4'))]['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        else:
            r=c['transfer']['EB']['trace'][rng.randrange(c['steps'])];r['n_E']=(r['n_E'] or 0)%4+1
        out[i]=c;inj.add(i)
    return out,inj


def run(cases,plan,workers=2,mutate_k=0,source_sha=None,on_result=None):
    check(plan==load(PLAN),'plan mismatch');bad=count(cases,plan,workers,on_result)
    rep={'schema':'brute.second-implementation-count.v11','study':plan['study'],
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit',
         'cases_checked':len(cases),'mismatching_cases':len(bad),'mismatches':bad,
         'scope':'bounded supports (exhaustive, n = 1..5 on SP8, RSX, RSXL); RSX and RSXL actions; RG4 / RG5, RSXL4, RSX4, DLF / DLF2 / RSXL library arms, EB (all fields); summary; stress entries; ood5 RG4 / RG5',
         'source_sha256':source_sha}
    if mutate_k:
        mc,inj=mutate(cases,mutate_k);base={b['case'] for b in bad};sub=sorted(inj)
        mb=count([mc[i] for i in sub],plan,workers);flagged={sub[b['case']] for b in mb}
        rep['mutation_test']={'injected':len(inj),'kinds':{k:KINDS.count(k) for k in sorted(set(KINDS))},
                              'detected_injected':len(inj&flagged),'flagged_not_injected':len(flagged-inj-base),
                              'rng':'random.Random(20261028)','passed':inj<=flagged and not (flagged-inj-base)}
    return rep
