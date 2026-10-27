"""Second implementation (same author, no `brute` import) for study BRUTE-0120-BOUNDED-TRANSFER-014 (GS_ref, GLV).

Written from experiments/BRUTE_PLAN_014.json (transfer_definition, second_implementation) BEFORE brute/boundedtransfer.py
and brute/api/certify2.py existed. NOT an independent or third-party audit: same author.

Bounded supports by EXHAUSTIVE enumeration (ref_bounded): for n states every complete transition table
d: (state, action) -> state with start state 0 (n ** (2 n) tables; 9,765,625 for n = 5) is simulated along the recorded
actions with numpy. Per table the codes still allowed at a visited state are the AND of the observation masks seen there
(unvisited states allow all 4 codes); a table is feasible iff no allowed set is empty; the projection for action b is the
OR over feasible tables of the allowed set at d(current state, b). Emissions factor per state, and symmetry breaking in
the learner's SAT encoding removes only relabelings, so this is the same projection (no solver, no budget).

Libraries / hypotheses / tracker: the frozen v0100_reference / v0110_reference re-implementations (ref_library,
ref_hypotheses, RefTracker). AT: v0110_reference.ref_gated_arm (mode 'AT'). LX: v0110_reference.ref_lx_audit.
RG / DLF / DLF0 / DX decisions, rules, summaries and the 72-library stress counts are recomputed from learner-visible
trace fields and the (verified) recorded bounded supports; *_EVALUATOR_ONLY fields are read only to mark wrong
certificates and the outside-bound flag.

Case format (the learner side writes the same dicts; timing fields '*wall_informational*' excluded):
  case['bounded'] = {'SP8' | 'LXp' | 'LXn': {str(n): {'support': [[s0, s1] per step], 'unknown': [[u0, u1] per step]}}}
      s_b = sorted code list or None (region not 'supported'); step i = before acting at step i + 1
  case['transfer']['RG<n>'] = {'n', 'trace': [{'step', 'certificate', 'rule', 'wrong'}], 'first_cert_step',
      'false_certificates', 'certificates', 'rg_certificates'}
  case['transfer']['DLF<p|n>' | 'DLF0<p|n>' | 'DX<p|n>'] = {'library', 'trajectory', 'margin', 'min_n', 'license_bound',
      'trace': [{'step', 'alive', 'certificate', 'rule', 'wrong'}], 'disabled_step', 'first_cert_step',
      'false_certificates', 'certificates', 'rg_certificates', 'license_certificates'}
  case['transfer']['AT<p|n>'] = v0.11.0 gated arm (mode 'AT'); case['transfer']['LX<p|n>'] = v0.11.0 LX arm
  case['stress'] = [{'source_family', 'source_seed', 'min_n', 'AT6_false', 'AT6_transfer', 'DLF_false',
      'DLF_license', 'DLF_rg', 'DLF0_false', 'DLF0_license', 'outside_exact_bound_EVALUATOR_ONLY'} x 72 (24 for smoke)]
  case['summary'] = {'first_cert_step': {arm: int}, 'S': {arm: int}}
  rules: 'sp8' (SP8 certificate), 'rg' (bounded region at FB = 4 is {c}), 'license' (library unanimous, region at
  min(n_L + margin, 4) is {c}), None.
"""
from __future__ import annotations
import copy,random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
from experiments.brute_common import check,load,VerificationError
from experiments.v0100_reference import ref_library
from experiments.v0110_reference import RefTracker,ref_gated_arm,ref_lx_audit,hyps
from scripts.check_seeds_014 import source_seed,stress_sources,smoke_source,smoke_stress_sources

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_014.json'
CENSOR=45;FB=4;NS_SP8=(2,3,4,5)
RG_ARMS=tuple(f'RG{n}' for n in NS_SP8)
ARMS=RG_ARMS+('DLFp','DLFn','DLF0p','DLF0n','ATp','ATn','LXp','LXn','DXp','DXn')
_T={}


def mask(obs):
    m=0
    for c in range(4):
        if all(b is None or ((c>>(1-j))&1)==b for j,b in enumerate(obs)):m|=1<<c
    return m


def tables(n):
    if n not in _T:
        N=n**(2*n);idx=np.arange(N,dtype=np.int64);D=np.empty((N,2*n),np.uint8)
        for k in range(2*n):D[:,k]=(idx//(n**k))%n
        _T[n]=D
    return _T[n]


def ref_bounded(n,init,acts,obss):
    """[[s0, s1] per step]: exhaustive projection before each recorded action (s_b sorted list or None if infeasible)."""
    D=tables(n);st=np.zeros(len(D),np.uint8);A=np.full((len(D),n),15,np.uint8);A[:,0]&=mask(init)
    k=A[:,0]!=0;D=D[k];st=st[k];A=A[k];out=[]
    for a,o in zip(acts,obss):
        if len(D)==0:out.append([None,None]);continue
        I=np.arange(len(D));s2=st.astype(np.int64)*2;row=[]
        for b in (0,1):
            v=int(np.bitwise_or.reduce(A[I,D[I,s2+b]]));row.append([c for c in range(4) if v>>c&1])
        out.append(row)
        st=D[I,s2+a];A[I,st]&=mask(o);k=A[I,st]!=0
        if not k.all():D=D[k];st=st[k];A=A[k]
    return out


def steps_sp8(case):
    out=[]
    for r in case['arms']['SP8']['trace']:
        a=r['action'];R={a:r,1-a:r['counterfactual']}
        out.append({'t':r['step'],'a':a,'cert':[R[0]['certificate'],R[1]['certificate']],'supp':[R[0]['support'],R[1]['support']],
                    'obs':tuple(r['observed']),'act':[r['actual_emission_EVALUATOR_ONLY'] if a==0 else r['counterfactual_actual_EVALUATOR_ONLY'],
                                                     r['actual_emission_EVALUATOR_ONLY'] if a==1 else r['counterfactual_actual_EVALUATOR_ONLY']]})
    return out


def steps_lx(lx):
    return [{'t':r['step'],'a':r['action'],'cert':list(r['certificate']),'supp':list(r['support']),'obs':tuple(r['observed']),
             'act':list(r['actual_EVALUATOR_ONLY'])} for r in lx['trace']]


def dx_bounds(nL):return sorted({FB,min(nL+1,FB)}|({nL+1} if nL+1<=5 else set()))


def audit_bounded(rec,steps,init,ns,where):
    acts=[s['a'] for s in steps];obss=[s['obs'] for s in steps]
    check(sorted(rec)==sorted(str(n) for n in ns),where+' bounded keys')
    for n in ns:
        ref=ref_bounded(n,init,acts,obss);got=rec[str(n)];check(len(got['support'])==len(steps)==len(got['unknown']),f'{where} n={n} length')
        for i,(g,u,e) in enumerate(zip(got['support'],got['unknown'],ref)):
            for b in (0,1):
                w=f'{where} n={n} step {i+1} b={b}'
                if u[b]==0:check(g[b]==e[b],w+' support')
                else:check(g[b] is None or e[b] is None or set(e[b])<=set(g[b]),w+' support superset')


def _single(s):return s[0] if s is not None and len(s)==1 else None


def ref_rg(steps,BS,n,burn):
    out={'n':n,'trace':[]};first=CENSOR;false=0
    for i,s in enumerate(steps):
        cert=[None,None];rule=[None,None]
        for b in (0,1):
            if s['cert'][b] is not None:cert[b],rule[b]=s['cert'][b],'sp8'
            elif s['t']>burn and s['supp'][b] is not None:
                c=_single(BS[str(n)]['support'][i][b])
                if c is not None and c in s['supp'][b]:cert[b],rule[b]=c,'rg'
        wrong=[cert[b] is not None and cert[b]!=s['act'][b] for b in (0,1)];false+=sum(wrong)
        if cert[s['a']] is not None and first==CENSOR:first=s['t']
        out['trace'].append({'step':s['t'],'certificate':cert,'rule':rule,'wrong':wrong})
    out.update(first_cert_step=first,false_certificates=false,certificates=sum(c is not None for x in out['trace'] for c in x['certificate']),
               rg_certificates=sum(r=='rg' for x in out['trace'] for r in x['rule']))
    return out


def ref_dlf(steps,BS,init,burn,H,nL,margin,label,trajectory):
    nb=min(nL+margin,FB);tr=RefTracker(H,tuple(init))
    out={'library':label,'trajectory':trajectory,'margin':margin,'min_n':nL,'license_bound':nb,'trace':[]};first=CENSOR;false=0
    for i,s in enumerate(steps):
        cert=[None,None];rule=[None,None];alive=len(tr.alive)
        for b in (0,1):
            if s['cert'][b] is not None:cert[b],rule[b]=s['cert'][b],'sp8';continue
            if not (s['t']>burn and s['supp'][b] is not None):continue
            g=_single(BS[str(FB)]['support'][i][b])
            if g is not None and g in s['supp'][b]:cert[b],rule[b]=g,'rg';continue
            p=tr.pred(b) if tr.alive else None
            if p is not None and p in s['supp'][b] and BS[str(nb)]['support'][i][b]==[p]:cert[b],rule[b]=p,'license'
        wrong=[cert[b] is not None and cert[b]!=s['act'][b] for b in (0,1)];false+=sum(wrong)
        if cert[s['a']] is not None and first==CENSOR:first=s['t']
        out['trace'].append({'step':s['t'],'alive':alive,'certificate':cert,'rule':rule,'wrong':wrong})
        tr.step(s['t'],s['a'],s['obs'])
    out.update(disabled_step=tr.disabled,first_cert_step=first,false_certificates=false,
               certificates=sum(c is not None for x in out['trace'] for c in x['certificate']),
               rg_certificates=sum(r=='rg' for x in out['trace'] for r in x['rule']),
               license_certificates=sum(r=='license' for x in out['trace'] for r in x['rule']))
    return out


def strip(d):
    if isinstance(d,dict):return {k:strip(v) for k,v in d.items() if 'wall_informational' not in k}
    if isinstance(d,list):return [strip(v) for v in d]
    return d


def _cmp(got,exp,where):
    got=strip(got)
    for k in exp:check(k in got,f'{where} missing {k}');check(got[k]==exp[k],f'{where} {k}')
    check(set(got)==set(exp),f'{where} extra keys {sorted(set(got)-set(exp))}')


def libraries_for(c,plan):
    fam=c['family']
    if c.get('smoke'):
        pos=smoke_source(c['seed']);neg=smoke_source(c['seed'],True);st=smoke_stress_sources(c['seed'])
    else:
        off=c['seed']-plan['heldout_ranges_transfer']['targets'][fam][0]+1
        pos=source_seed(fam,off,plan);neg=source_seed(fam,off,plan,True);st=stress_sources(fam,plan)
    return pos,neg,st


def audit_case(c,plan):
    """(ok, message): the first differing field, or (True, None)."""
    try:
        check(c['tau6']==plan['tau6']['value'],'tau6');burn=c['burn_in'];init=tuple(c['initial_visible'])
        S=steps_sp8(c);check(len(S)==c['steps']==plan['actions_per_case'],'SP8 steps');T=c['transfer']
        audit_bounded(c['bounded']['SP8'],S,init,NS_SP8,'SP8');BS=c['bounded']['SP8']
        exp={};first={}
        for n in NS_SP8:exp[f'RG{n}']=ref_rg(S,BS,n,burn)
        pos,neg,st=libraries_for(c,plan)
        for key,suf,(sf,ss) in (('pos','p',pos),('neg','n',neg)):
            lib=ref_library(sf,ss);got=c['libraries'][key]
            for k in ('source_family','source_seed','min_n','status','motif_count','motifs'):check(got[k]==lib[k],f'library {key} {k}')
            H,_=hyps(lib);nL=lib['min_n']
            exp['DLF'+suf]=ref_dlf(S,BS,init,burn,H,nL,1,key,'SP8');exp['DLF0'+suf]=ref_dlf(S,BS,init,burn,H,nL,0,key,'SP8')
            exp['AT'+suf]=ref_gated_arm(c,lib,key,'AT')
            lx=T['LX'+suf];ref_lx_audit(lx,c,lib,key);L=steps_lx(lx)
            audit_bounded(c['bounded']['LX'+suf],L,init,dx_bounds(nL),'LX'+suf)
            exp['DX'+suf]=ref_dlf(L,c['bounded']['LX'+suf],init,burn,H,nL,1,key,'LX'+suf)
        for arm,e in exp.items():_cmp(T[arm],e,arm)
        check(sorted(T)==sorted(ARMS),'transfer arm set')
        for arm in ARMS:first[arm]=exp[arm]['first_cert_step'] if arm in exp else T[arm]['first_cert_step']
        f0=next((s['t'] for s in S if s['cert'][s['a']] is not None),CENSOR)
        check(c['summary']=={'first_cert_step':dict(first,SP8=f0),'S':{a:f0-first[a] for a in ARMS}},'summary')
        check(len(c['stress'])==len(st),'stress count')
        ts=c['true_hidden_state_count_EVALUATOR_ONLY']
        for j,(sf,ss) in enumerate(st):
            lib=ref_library(sf,ss);H,_=hyps(lib);nL=lib['min_n'];at=ref_gated_arm(c,lib,'stress','AT')
            d1=ref_dlf(S,BS,init,burn,H,nL,1,'stress','SP8');d0=ref_dlf(S,BS,init,burn,H,nL,0,'stress','SP8')
            e={'source_family':sf,'source_seed':ss,'min_n':nL,'AT6_false':at['false_certificates'],'AT6_transfer':at['transfer_certificates'],
               'DLF_false':d1['false_certificates'],'DLF_license':d1['license_certificates'],'DLF_rg':d1['rg_certificates'],
               'DLF0_false':d0['false_certificates'],'DLF0_license':d0['license_certificates'],'outside_exact_bound_EVALUATOR_ONLY':ts>min(nL+1,FB)}
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


KINDS=('bounded',)*6+('dlf',)*6+('stress',)*4+('rg',)*2+('dx',)*2


def mutate(cases,k=20,rng_seed=20261026):
    """k single-field errors in k distinct cases (plan GS_ref mutation test). Returns (mutated copies, injected index set)."""
    check(k==len(KINDS),'k must equal len(KINDS)');rng=random.Random(rng_seed);idx=rng.sample(range(len(cases)),k)
    kinds=list(KINDS);rng.shuffle(kinds);out=list(cases);inj=set()
    for i,kind in zip(idx,kinds):
        c=copy.deepcopy(cases[i])
        if kind=='bounded':
            n=str(rng.choice(NS_SP8));B=c['bounded']['SP8'][n]
            cand=[(s,b) for s in range(len(B['support'])) for b in (0,1) if B['support'][s][b] is not None and B['unknown'][s][b]==0]
            s,b=rng.choice(cand);v=B['support'][s][b];B['support'][s][b]=v[1:] if len(v)>1 else [(v[0]+1)%4]
        elif kind=='dlf':
            arm=rng.choice(('DLFp','DLFn'));r=c['transfer'][arm]['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            r['rule'][b]={'sp8':'rg','rg':'license','license':None,None:'license'}[r['rule'][b]]
        elif kind=='stress':
            c['stress'][rng.randrange(len(c['stress']))][rng.choice(('AT6_false','DLF_license','DLF_rg','DLF_false'))]+=1
        elif kind=='rg':
            r=c['transfer']['RG4']['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        else:
            c['transfer'][rng.choice(('DXp','DXn'))]['first_cert_step']+=1
        out[i]=c;inj.add(i)
    return out,inj


def run(cases,plan,workers=2,mutate_k=0,source_sha=None,on_result=None):
    check(plan==load(PLAN),'plan mismatch');bad=count(cases,plan,workers,on_result)
    rep={'schema':'brute.second-implementation-count.v9','study':plan['study'],
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit',
         'cases_checked':len(cases),'mismatching_cases':len(bad),'mismatches':bad,
         'scope':'bounded supports (exhaustive, n = 2..5 on SP8, dx_bounds on LX); RG2-5, DLF, DLF0, AT, LX, DX (all fields); summary; stress counts',
         'source_sha256':source_sha}
    if mutate_k:
        mc,inj=mutate(cases,mutate_k);base={b['case'] for b in bad};sub=sorted(inj)
        mb=count([mc[i] for i in sub],plan,workers);flagged={sub[b['case']] for b in mb}
        rep['mutation_test']={'injected':len(inj),'kinds':{k:KINDS.count(k) for k in sorted(set(KINDS))},
                              'detected_injected':len(inj&flagged),'flagged_not_injected':len(flagged-inj-base),
                              'rng':'random.Random(20261026)','passed':inj<=flagged and not (flagged-inj-base)}
    return rep
