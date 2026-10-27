"""Second implementation (same author, no `brute` import) for study BRUTE-0130-REGION-SPLIT-015 (GS_ref3, GLV).

Written from experiments/BRUTE_PLAN_015.json (transfer_definition, second_implementation) BEFORE brute/regionsplit.py
and brute/api/certify3.py existed. NOT an independent or third-party audit: same author. Extends
experiments/v0120_reference.py (imported unchanged; it imports no `brute` module): exhaustive numpy bounded supports
(ref_bounded, n ** (2 n) tables, n = 1..5), ref_rg, ref_dlf, the v0.11.0 AT re-implementation (ref_gated_arm) and the
library re-implementations.

Recomputed per case from learner-visible fields and the (verified) recorded bounded supports; *_EVALUATOR_ONLY fields are
read only to mark wrong certificates and the outside-bound flag:
  * bounded supports n = 1..5 on the SP8 and (main block) RSX trajectories, checked against exhaustive enumeration;
  * the RSX action at every step from the reference n = 4 supports and the recorded SP8 LU-R choice;
  * RG2-RG5 (SP8), RSX4 (RG4 on RSX), DLFp / DLFn (SP8), RSXp / RSXn (DLF on RSX), EB / EB2 (SP8), the summary;
  * the 72-library stress entries (AT6 and DLF on SP8, DLF on RSX, per-pair certificate lists);
  * ood5 block: bounded supports n = 1..5 on SP8, RG4 / RG5, summary.

Case format (the learner side writes the same dicts; timing fields '*wall_informational*' excluded):
  case['bounded'] = {'SP8' | 'RSX': {str(n): {'support': [[s0, s1] per step], 'unknown': [[u0, u1] per step]}}}, n = 1..5
      s_b = sorted code list or None (region not 'supported'); entry i = before acting at step i + 1
  case['rsx'] (main block) = {'trace': [{'step', 'action', 'sp8_action', 'passive_action', 'rsx_rule' ('rsx' | 'sp8'),
      'bounded_sizes' [k0, k1], 'certificate' [c0, c1], 'support' [s0, s1], 'observed', 'actual_EVALUATOR_ONLY' [a0, a1],
      'wrong' [w0, w1]}], 'first_cert_step', 'false_certificates', 'certificates', 'rule_counts' {'rsx', 'sp8'}}
      k_b = len(s_b) of the recorded RSX n = 4 support (UNKNOWN codes count as possible; 0 if None). Rule: step <= burn_in -> SP8 choice ('sp8');
      else if max(k0, k1) <= 1 or k0 == k1 -> SP8 choice ('sp8'); else argmax ('rsx'; with two actions a tie between
      the maximisers is k0 == k1, broken by the SP8 choice).
  case['transfer']['RG<n>'] (n = 2..5, SP8 trajectory) and ['RSX4'] (n = 4, RSX trajectory) = v0120 RG format
  case['transfer']['DLFp' | 'DLFn' | 'RSXp' | 'RSXn'] = v0120 DLF format (trajectory 'SP8' or 'RSX', margin 1)
  case['transfer']['EB' | 'EB2'] = {'margin', 'trace': [{'step', 'n_E', 'bound', 'certificate', 'rule', 'wrong'}],
      'first_cert_step', 'false_certificates', 'certificates', 'rg_certificates', 'eb_certificates'}
      n_E(step i) = min{n in 1..4: recorded support at n for action 0 is not None} (None if none); bound =
      min(n_E + margin, 4) (None if n_E is None). Decision: the RG4 decision if it certifies; else if step > burn_in,
      SP8 support S not None, bound not None, support[bound] == [c] and c in S -> c ('eb'); else None.
  ood5 cases: case['transfer'] = {'RG4', 'RG5'} only, no 'rsx', no libraries, no stress.
  case['stress'] = [{'source_family', 'source_seed', 'min_n', 'AT6_false', 'AT6_transfer', 'DLF_false', 'DLF_license',
      'DLF_rg', 'DLF_certs', 'RSX_false', 'RSX_license', 'RSX_rg', 'RSX_certs', 'outside_exact_bound_EVALUATOR_ONLY'}]
      x 72 (24 for smoke); *_certs = [[step, b, code] for every certificate issued] (G_recount input)
  case['summary'] = {'first_cert_step': {arm: int, 'SP8': int}, 'S': {arm: int}, 'false': {arm: int, 'SP8': int}}
"""
from __future__ import annotations
import copy,random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from experiments.brute_common import check,load,VerificationError
from experiments.v0100_reference import ref_library
from experiments.v0110_reference import ref_gated_arm,hyps
from experiments.v0120_reference import ref_bounded,steps_sp8,audit_bounded,ref_rg,ref_dlf,strip,_cmp,_single,CENSOR,FB
from scripts.check_seeds_015 import source_seed,stress_sources,smoke_source,smoke_stress_sources

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_015.json'
NS=(1,2,3,4,5)
MAIN_ARMS=('RG2','RG3','RG4','RG5','RSX4','RSXp','RSXn','DLFp','DLFn','EB','EB2')
OOD5_ARMS=('RG4','RG5')


def steps_rsx(rsx):
    return [{'t':r['step'],'a':r['action'],'cert':list(r['certificate']),'supp':list(r['support']),'obs':tuple(r['observed']),
             'act':list(r['actual_EVALUATOR_ONLY'])} for r in rsx['trace']]


def rsx_choice(t,burn,sizes,sp8_action):
    """(action, rule) of the RSX rule given the two bounded-support sizes."""
    if t<=burn:return sp8_action,'sp8'
    k0,k1=sizes
    if max(k0,k1)<=1 or k0==k1:return sp8_action,'sp8'
    return (0 if k0>k1 else 1),'rsx'


def audit_rsx(rsx,BR4,burn,where='RSX'):
    """BR4 = the recorded RSX n = 4 supports, already checked by audit_bounded against exhaustive enumeration (equal
    where unknown == 0, superset otherwise; the learner's sizes count UNKNOWN codes as possible)."""
    tr=rsx['trace'];S=steps_rsx(rsx);cnt={'rsx':0,'sp8':0}
    for i,r in enumerate(tr):
        check(r['step']==i+1,f'{where} step index')
        sizes=[len(x) if x is not None else 0 for x in BR4['support'][i]]
        check(r['bounded_sizes']==sizes,f'{where} step {i+1} bounded_sizes')
        a,rule=rsx_choice(r['step'],burn,sizes,r['sp8_action'])
        check(r['action']==a and r['rsx_rule']==rule,f'{where} step {i+1} action/rule');cnt[rule]+=1
        w=[r['certificate'][b] is not None and r['certificate'][b]!=r['actual_EVALUATOR_ONLY'][b] for b in (0,1)]
        check(r['wrong']==w,f'{where} step {i+1} wrong')
    first=next((s['t'] for s in S if s['cert'][s['a']] is not None),CENSOR)
    check(rsx['first_cert_step']==first,where+' first_cert_step')
    check(rsx['false_certificates']==sum(sum(r['wrong']) for r in tr),where+' false')
    check(rsx['certificates']==sum(c is not None for r in tr for c in r['certificate']),where+' certificates')
    check(rsx['rule_counts']==cnt,where+' rule_counts')
    return S


def ref_eb(steps,BS,burn,margin):
    out={'margin':margin,'trace':[]};first=CENSOR;false=0
    for i,s in enumerate(steps):
        nE=next((n for n in (1,2,3,4) if BS[str(n)]['support'][i][0] is not None),None)
        bound=min(nE+margin,FB) if nE is not None else None
        cert=[None,None];rule=[None,None]
        for b in (0,1):
            if s['cert'][b] is not None:cert[b],rule[b]=s['cert'][b],'sp8';continue
            if not (s['t']>burn and s['supp'][b] is not None):continue
            g=_single(BS[str(FB)]['support'][i][b])
            if g is not None and g in s['supp'][b]:cert[b],rule[b]=g,'rg';continue
            if bound is None:continue
            e=_single(BS[str(bound)]['support'][i][b])
            if e is not None and e in s['supp'][b]:cert[b],rule[b]=e,'eb'
        wrong=[cert[b] is not None and cert[b]!=s['act'][b] for b in (0,1)];false+=sum(wrong)
        if cert[s['a']] is not None and first==CENSOR:first=s['t']
        out['trace'].append({'step':s['t'],'n_E':nE,'bound':bound,'certificate':cert,'rule':rule,'wrong':wrong})
    out.update(first_cert_step=first,false_certificates=false,certificates=sum(c is not None for x in out['trace'] for c in x['certificate']),
               rg_certificates=sum(r=='rg' for x in out['trace'] for r in x['rule']),
               eb_certificates=sum(r=='eb' for x in out['trace'] for r in x['rule']))
    return out


def certs(arm):return [[x['step'],b,x['certificate'][b]] for x in arm['trace'] for b in (0,1) if x['certificate'][b] is not None]


def libraries_for(c,plan):
    fam=c['family']
    if c.get('smoke'):
        return smoke_source(c['seed']),smoke_source(c['seed'],True),smoke_stress_sources(c['seed'])
    off=c['seed']-plan['heldout_ranges_transfer']['targets'][fam][0]+1
    return source_seed(fam,off,plan),source_seed(fam,off,plan,True),stress_sources(fam,plan)


def _summary(c,S,exp,arms):
    f0=next((s['t'] for s in S if s['cert'][s['a']] is not None),CENSOR)
    sp8f=sum(s['cert'][b] is not None and s['cert'][b]!=s['act'][b] for s in S for b in (0,1))
    first={a:exp[a]['first_cert_step'] for a in arms}
    return {'first_cert_step':dict(first,SP8=f0),'S':{a:f0-first[a] for a in arms},
            'false':dict({a:exp[a]['false_certificates'] for a in arms},SP8=sp8f)}


def audit_case(c,plan):
    """(ok, message): the first differing field, or (True, None)."""
    try:
        check(c['tau6']==plan['tau6']['value'],'tau6');burn=c['burn_in'];init=tuple(c['initial_visible'])
        S=steps_sp8(c);check(len(S)==c['steps']==plan['actions_per_case'],'SP8 steps');T=c['transfer']
        audit_bounded(c['bounded']['SP8'],S,init,NS,'SP8');BS=c['bounded']['SP8'];exp={}
        if c['family']=='ood5':
            check(sorted(c['bounded'])==['SP8'] and 'rsx' not in c and 'stress' not in c,'ood5 layout')
            for n in (4,5):exp[f'RG{n}']=ref_rg(S,BS,n,burn)
            for arm,e in exp.items():_cmp(T[arm],e,arm)
            check(sorted(T)==sorted(OOD5_ARMS),'ood5 arm set');check(c['summary']==_summary(c,S,exp,OOD5_ARMS),'summary')
            return True,None
        check(sorted(c['bounded'])==['RSX','SP8'],'bounded trajectories')
        R=steps_rsx(c['rsx']);check(len(R)==len(S),'RSX steps')
        audit_bounded(c['bounded']['RSX'],R,init,NS,'RSX');BR=c['bounded']['RSX'];audit_rsx(c['rsx'],BR['4'],burn)
        for n in (2,3,4,5):exp[f'RG{n}']=ref_rg(S,BS,n,burn)
        exp['RSX4']=ref_rg(R,BR,4,burn)
        exp['EB']=ref_eb(S,BS,burn,1);exp['EB2']=ref_eb(S,BS,burn,2)
        pos,neg,st=libraries_for(c,plan)
        for key,suf,(sf,ss) in (('pos','p',pos),('neg','n',neg)):
            lib=ref_library(sf,ss);got=c['libraries'][key]
            for k in ('source_family','source_seed','min_n','status','motif_count','motifs'):check(got[k]==lib[k],f'library {key} {k}')
            H,_=hyps(lib);nL=lib['min_n']
            exp['DLF'+suf]=ref_dlf(S,BS,init,burn,H,nL,1,key,'SP8');exp['RSX'+suf]=ref_dlf(R,BR,init,burn,H,nL,1,key,'RSX')
        for arm,e in exp.items():_cmp(T[arm],e,arm)
        check(sorted(T)==sorted(MAIN_ARMS),'transfer arm set')
        check(c['summary']==_summary(c,S,exp,MAIN_ARMS),'summary')
        check(len(c['stress'])==len(st),'stress count');ts=c['true_hidden_state_count_EVALUATOR_ONLY']
        for j,(sf,ss) in enumerate(st):
            lib=ref_library(sf,ss);H,_=hyps(lib);nL=lib['min_n'];at=ref_gated_arm(c,lib,'stress','AT')
            d1=ref_dlf(S,BS,init,burn,H,nL,1,'stress','SP8');d2=ref_dlf(R,BR,init,burn,H,nL,1,'stress','RSX')
            e={'source_family':sf,'source_seed':ss,'min_n':nL,'AT6_false':at['false_certificates'],'AT6_transfer':at['transfer_certificates'],
               'DLF_false':d1['false_certificates'],'DLF_license':d1['license_certificates'],'DLF_rg':d1['rg_certificates'],'DLF_certs':certs(d1),
               'RSX_false':d2['false_certificates'],'RSX_license':d2['license_certificates'],'RSX_rg':d2['rg_certificates'],'RSX_certs':certs(d2),
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


KINDS=('bounded',)*5+('rsx',)*4+('dlf',)*3+('stress',)*3+('rg',)*2+('eb',)*3


def mutate(cases,k=20,rng_seed=20261027):
    """k single-field errors in k distinct main-block cases (plan GS_ref3 mutation test). Returns (mutated copies, injected
    index set)."""
    check(k==len(KINDS),'k must equal len(KINDS)');rng=random.Random(rng_seed)
    main=[i for i,c in enumerate(cases) if c['family']!='ood5'];idx=rng.sample(main,k)
    kinds=list(KINDS);rng.shuffle(kinds);out=list(cases);inj=set()
    for i,kind in zip(idx,kinds):
        c=copy.deepcopy(cases[i])
        if kind=='bounded':
            tj=rng.choice(('SP8','RSX'));n=str(rng.choice(NS));B=c['bounded'][tj][n]
            cand=[(s,b) for s in range(len(B['support'])) for b in (0,1) if B['support'][s][b] is not None and B['unknown'][s][b]==0]
            s,b=rng.choice(cand);v=B['support'][s][b];B['support'][s][b]=v[1:] if len(v)>1 else [(v[0]+1)%4]
        elif kind=='rsx':
            r=c['rsx']['trace'][rng.randrange(c['burn_in'],c['steps'])];r['action']=1-r['action']
        elif kind=='dlf':
            arm=rng.choice(('DLFp','DLFn','RSXp','RSXn'));r=c['transfer'][arm]['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            r['rule'][b]={'sp8':'rg','rg':'license','license':None,None:'license'}[r['rule'][b]]
        elif kind=='stress':
            c['stress'][rng.randrange(len(c['stress']))][rng.choice(('AT6_false','DLF_license','RSX_rg','RSX_false'))]+=1
        elif kind=='rg':
            r=c['transfer'][rng.choice(('RG4','RSX4'))]['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        else:
            r=c['transfer'][rng.choice(('EB','EB2'))]['trace'][rng.randrange(c['steps'])]
            r['n_E']=(r['n_E'] or 0)%4+1
        out[i]=c;inj.add(i)
    return out,inj


def run(cases,plan,workers=2,mutate_k=0,source_sha=None,on_result=None):
    check(plan==load(PLAN),'plan mismatch');bad=count(cases,plan,workers,on_result)
    rep={'schema':'brute.second-implementation-count.v10','study':plan['study'],
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit',
         'cases_checked':len(cases),'mismatching_cases':len(bad),'mismatches':bad,
         'scope':'bounded supports (exhaustive, n = 1..5 on SP8 and RSX); RSX actions; RG2-5, RSX4, DLF, RSX library arms, EB, EB2 (all fields); summary; stress entries; ood5 RG4 / RG5',
         'source_sha256':source_sha}
    if mutate_k:
        mc,inj=mutate(cases,mutate_k);base={b['case'] for b in bad};sub=sorted(inj)
        mb=count([mc[i] for i in sub],plan,workers);flagged={sub[b['case']] for b in mb}
        rep['mutation_test']={'injected':len(inj),'kinds':{k:KINDS.count(k) for k in sorted(set(KINDS))},
                              'detected_injected':len(inj&flagged),'flagged_not_injected':len(flagged-inj-base),
                              'rng':'random.Random(20261027)','passed':inj<=flagged and not (flagged-inj-base)}
    return rep
