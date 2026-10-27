"""Second implementation (same author, no `brute` import) for study BRUTE-0150-BOUNDED-LOOKAHEAD-017 (GS_ref5, GLV).

Written from experiments/BRUTE_PLAN_017.json (transfer_definition, H_rgl, H_att_exact, arms_by_block) and
docs/research/BRUTE_DEVIATIONS_017.md (#88 lookahead score, #89 RSXL5, #91 carried arms) BEFORE brute/boundedlookahead.py
and brute/api/certify5.py existed. NOT an independent or third-party audit: same author. Extends
experiments/v0140_reference.py (imported unchanged; it imports no `brute` module).

Recomputed per case from learner-visible fields and the (verified) recorded bounded supports; *_EVALUATOR_ONLY fields are
read only to mark wrong certificates and the outside-bound flag:
  * everything v0140_reference checks (bounded supports n = 1..5 on SP8, RSX, RSXL; RSX / RSXL actions; RG4 / RG5,
    RSXL4, RSX4, RSXLp / RSXLn, DLFp / DLFn, DLF2p / DLF2n, EB; the 72-library stress entries);
  * bounded supports n = 1..5 on the RGLX and RGL trajectories (exhaustive);
  * the RGL lookahead (#88) at every step where it is computed: den_a = |RG4 support for a| and num_a = the number of
    outcomes o in it after which the exhaustive n = 4 version space, extended by the fully observed step (a, o), has a
    single-code next-reading projection for some b in {0, 1} (checked whenever the recorded unknown count is 0);
  * the RGLX action (RGL while RG4 has not certified the taken action at an earlier step, then the v0130 RSX choice) and
    the RGL4 action (RGL throughout); RGLX4 / RGL4 = RG4 on those trajectories;
  * DLFa_p / DLFa_n (attested license: the library is used only when n_L + 1 >= FB = 4; then frozen-format DLF margin 1,
    else RG4 decisions in DLF format with alive None and license_bound None);
  * ood5 block: bounded supports n = 1..5 on SP8 and RSXL5; RG4 / RG5 on SP8; RSXL5 (#89: the RSXL rule with RG5 and
    the n = 5 support sizes) = RG5 on the RSXL5 trajectory; summary.

Case format (learner side writes the same dicts; '*wall_informational*' keys excluded), additions to v0140:
  case['bounded'] keys: main 'SP8', 'RSX', 'RSXL', 'RGLX', 'RGL'; ood5 'SP8', 'RSXL5'
  case['rglx'] / case['rgl'] = {'trace': [{'step', 'action', 'sp8_action', 'passive_action', 'rule' ('rgl' | 'sp8' |
      'rsx'), 'deferred', 'bounded_sizes' [k0, k1], 'lookahead' (None or {'num': [n0, n1], 'den': [d0, d1],
      'unknown': [u0, u1]}), 'certificate', 'support', 'observed', 'actual_EVALUATOR_ONLY', 'wrong'}],
      'first_cert_step', 'false_certificates', 'certificates', 'rule_counts' {'rgl', 'rsx', 'sp8'}, 'switch_step',
      'lookahead_steps'}
      'deferred' is True while the lookahead rule is in force (RGL: always; RGLX: t <= RG4's first taken-action
      certificate step); 'lookahead' is computed iff deferred and t > burn_in.
  case['rsxl5'] (ood5) = the v0140 RSXL format with sizes from n = 5
  case['transfer'][arm]: main MAIN_ARMS; ood5 OOD5_ARMS. DLFa_*: the v0120 DLF format plus 'attested' (bool).
"""
from __future__ import annotations
import copy,random
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path
import numpy as np
from experiments.brute_common import check,load,VerificationError
from experiments.v0100_reference import ref_library
from experiments.v0110_reference import ref_gated_arm,hyps
from experiments.v0120_reference import steps_sp8,audit_bounded,ref_rg,ref_dlf,_cmp,CENSOR,FB,mask,tables
from experiments.v0130_reference import steps_rsx,rsx_choice,audit_rsx,ref_eb,certs
from experiments.v0140_reference import audit_rsxl
from scripts.check_seeds_017 import source_seed,stress_sources,smoke_source,smoke_stress_sources

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_017.json'
NS=(1,2,3,4,5)
MAIN_ARMS=('RG4','RG5','RGLX4','RGL4','RSXL4','RSXLp','RSXLn','DLFp','DLFn','DLFa_p','DLFa_n','DLF2p','DLF2n','RSX4','EB')
OOD5_ARMS=('RG4','RG5','RSXL5')
MARGIN=1


# ------------------------------------------------------------------ exhaustive lookahead
def _proj(D,st,A,b):
    """bitmask of next codes after action b over the machine set (0 if empty)."""
    if len(D)==0:return 0
    I=np.arange(len(D));return int(np.bitwise_or.reduce(A[I,D[I,st.astype(np.int64)*2+b]]))


def ref_lookahead(n,init,acts,obss):
    """[[(num_0, den_0), (num_1, den_1)] per step] by exhaustive enumeration of n-state tables (H_rgl, #88): den_a =
    |projection for a|; num_a = outcomes o after which the version space extended by (a, o) has a single-code
    projection for some b."""
    D=tables(n);st=np.zeros(len(D),np.uint8);A=np.full((len(D),n),15,np.uint8);A[:,0]&=mask(init)
    k=A[:,0]!=0;D=D[k];st=st[k];A=A[k];out=[]
    for a_taken,o_taken in zip(acts,obss):
        row=[]
        for a in (0,1):
            v=_proj(D,st,A,a);O=[c for c in range(4) if v>>c&1];num=0
            if O:
                I=np.arange(len(D));nx=D[I,st.astype(np.int64)*2+a]
                for o in O:
                    keep=(A[I,nx]>>o)&1==1;D2=D[keep];n2=nx[keep];A2=A[keep].copy();J=np.arange(len(D2));A2[J,n2]&=np.uint8(1<<o)
                    if any(bin(_proj(D2,n2,A2,b)).count('1')==1 for b in (0,1)):num+=1
            row.append((num,len(O)))
        out.append(row)
        if len(D):
            I=np.arange(len(D));st=D[I,st.astype(np.int64)*2+a_taken];A[I,st]&=mask(o_taken);k=A[I,st]!=0
            if not k.all():D=D[k];st=st[k];A=A[k]
    return out


def rgl_choice(t,burn,look,sp8_action):
    """(action, rule) of RGL given look = {'num', 'den'} (or None at burn-in)."""
    if t<=burn:return sp8_action,'sp8'
    s=[Fraction(look['num'][b],look['den'][b]) if look['den'][b] else Fraction(0) for b in (0,1)]
    if s[0]==s[1]:return sp8_action,'sp8'
    return (0 if s[0]>s[1] else 1),'rgl'


def audit_rgl(tr_,BL,init,burn,mode,where):
    """mode 'rglx' | 'rgl'. BL = the recorded bounded supports on this trajectory (checked by audit_bounded)."""
    tr=tr_['trace'];L=steps_rsx({'trace':tr});rg=ref_rg(L,BL,4,burn);f=rg['first_cert_step'];cnt={'rgl':0,'rsx':0,'sp8':0}
    ex=ref_lookahead(4,init,[s['a'] for s in L],[s['obs'] for s in L]);looks=0
    for i,r in enumerate(tr):
        t=r['step'];check(t==i+1,f'{where} step index')
        sizes=[len(x) if x is not None else 0 for x in BL['4']['support'][i]]
        check(r['bounded_sizes']==sizes,f'{where} step {t} bounded_sizes')
        d=True if mode=='rgl' else t<=f;check(r['deferred']==d,f'{where} step {t} deferred')
        lk=r['lookahead']
        if d and t>burn:
            check(lk is not None and sorted(lk)==['den','num','unknown'],f'{where} step {t} lookahead missing');looks+=1
            for b in (0,1):
                if BL['4']['unknown'][i][b]==0:check(lk['den'][b]==sizes[b]==ex[i][b][1],f'{where} step {t} b={b} den')
                if BL['4']['unknown'][i][b]==0 and lk['unknown'][b]==0:check(lk['num'][b]==ex[i][b][0],f'{where} step {t} b={b} num')
                check(0<=lk['num'][b]<=lk['den'][b],f'{where} step {t} b={b} num range')
            a,rule=rgl_choice(t,burn,lk,r['sp8_action'])
        else:
            check(lk is None,f'{where} step {t} lookahead must be None')
            a,rule=(rsx_choice(t,burn,sizes,r['sp8_action']) if not d else (r['sp8_action'],'sp8'))
        check(r['action']==a and r['rule']==rule,f'{where} step {t} action/rule');cnt[rule]+=1
        w=[r['certificate'][b] is not None and r['certificate'][b]!=r['actual_EVALUATOR_ONLY'][b] for b in (0,1)]
        check(r['wrong']==w,f'{where} step {t} wrong')
    first=next((s['t'] for s in L if s['cert'][s['a']] is not None),CENSOR)
    check(tr_['first_cert_step']==first,where+' first_cert_step')
    check(tr_['false_certificates']==sum(sum(r['wrong']) for r in tr),where+' false')
    check(tr_['certificates']==sum(c is not None for r in tr for c in r['certificate']),where+' certificates')
    check(tr_['rule_counts']==cnt,where+' rule_counts');check(tr_['lookahead_steps']==looks,where+' lookahead_steps')
    check(tr_['switch_step']==((f+1 if f<len(tr) else None) if mode=='rglx' else None),where+' switch_step')
    return L


def audit_rsxl_n(rsxl,BL,burn,n,where):
    """audit_rsxl with RG_n and the n-state support sizes (#89)."""
    tr=rsxl['trace'];L=steps_rsx({'trace':tr});rg=ref_rg(L,BL,n,burn);f=rg['first_cert_step'];cnt={'rsx':0,'sp8':0}
    for i,r in enumerate(tr):
        check(r['step']==i+1,f'{where} step index')
        sizes=[len(x) if x is not None else 0 for x in BL[str(n)]['support'][i]]
        check(r['bounded_sizes']==sizes,f'{where} step {i+1} bounded_sizes')
        d=r['step']<=f;check(r['deferred']==d,f'{where} step {i+1} deferred')
        a,rule=(r['sp8_action'],'sp8') if d else rsx_choice(r['step'],burn,sizes,r['sp8_action'])
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


def ref_dlfa(steps,BS,init,burn,H,nL,label):
    """Attested license (H_att_exact): the library only when n_L + 1 >= FB."""
    if nL+MARGIN>=FB:
        e=ref_dlf(steps,BS,init,burn,H,nL,MARGIN,label,'SP8');e['attested']=True;return e
    rg=ref_rg(steps,BS,FB,burn)
    return {'library':label,'trajectory':'SP8','margin':MARGIN,'min_n':nL,'license_bound':None,'attested':False,
            'trace':[{'step':x['step'],'alive':None,'certificate':x['certificate'],'rule':x['rule'],'wrong':x['wrong']} for x in rg['trace']],
            'disabled_step':None,'first_cert_step':rg['first_cert_step'],'false_certificates':rg['false_certificates'],
            'certificates':rg['certificates'],'rg_certificates':rg['rg_certificates'],'license_certificates':0}


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
        for n in (4,5):exp[f'RG{n}']=ref_rg(S,BS,n,burn)
        if c['family']=='ood5':
            check(sorted(c['bounded'])==['RSXL5','SP8'] and not {'rsx','rsxl','rglx','rgl','stress'}&set(c),'ood5 layout')
            X=steps_rsx(c['rsxl5']);check(len(X)==len(S),'RSXL5 steps')
            audit_bounded(c['bounded']['RSXL5'],X,init,NS,'RSXL5');BX=c['bounded']['RSXL5'];audit_rsxl_n(c['rsxl5'],BX,burn,5,'RSXL5')
            exp['RSXL5']=ref_rg(X,BX,5,burn)
            for arm,e in exp.items():_cmp(T[arm],e,arm)
            check(sorted(T)==sorted(OOD5_ARMS),'ood5 arm set');check(c['summary']==_summary(S,exp,OOD5_ARMS),'summary')
            return True,None
        check(sorted(c['bounded'])==['RGL','RGLX','RSX','RSXL','SP8'],'bounded trajectories')
        R=steps_rsx(c['rsx']);L=steps_rsx(c['rsxl']);G=steps_rsx(c['rglx']);Q=steps_rsx(c['rgl'])
        check(len(R)==len(S)==len(L)==len(G)==len(Q),'trajectory lengths')
        audit_bounded(c['bounded']['RSX'],R,init,NS,'RSX');BR=c['bounded']['RSX'];audit_rsx(c['rsx'],BR['4'],burn)
        audit_bounded(c['bounded']['RSXL'],L,init,NS,'RSXL');BL=c['bounded']['RSXL'];audit_rsxl(c['rsxl'],BL,burn)
        audit_bounded(c['bounded']['RGLX'],G,init,NS,'RGLX');BG=c['bounded']['RGLX'];audit_rgl(c['rglx'],BG,init,burn,'rglx','RGLX')
        audit_bounded(c['bounded']['RGL'],Q,init,NS,'RGL');BQ=c['bounded']['RGL'];audit_rgl(c['rgl'],BQ,init,burn,'rgl','RGL')
        exp['RSXL4']=ref_rg(L,BL,4,burn);exp['RSX4']=ref_rg(R,BR,4,burn);exp['EB']=ref_eb(S,BS,burn,1)
        exp['RGLX4']=ref_rg(G,BG,4,burn);exp['RGL4']=ref_rg(Q,BQ,4,burn)
        pos,neg,st=libraries_for(c,plan)
        for key,suf,(sf,ss) in (('pos','p',pos),('neg','n',neg)):
            lib=ref_library(sf,ss);got=c['libraries'][key]
            for k in ('source_family','source_seed','min_n','status','motif_count','motifs'):check(got[k]==lib[k],f'library {key} {k}')
            H,_=hyps(lib);nL=lib['min_n']
            exp['DLF'+suf]=ref_dlf(S,BS,init,burn,H,nL,1,key,'SP8');exp['DLF2'+suf]=ref_dlf(S,BS,init,burn,H,nL,2,key,'SP8')
            exp['RSXL'+suf]=ref_dlf(L,BL,init,burn,H,nL,1,key,'RSXL');exp['DLFa_'+suf]=ref_dlfa(S,BS,init,burn,H,nL,key)
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
    except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError,ZeroDivisionError) as exc:
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


KINDS=('bounded',)*4+('rsxl',)*2+('rglx',)*3+('rgl',)*2+('dlf',)*2+('dlfa',)*2+('stress',)*2+('rg',)*2+('eb',)*1


def _look_step(tr,burn,steps):
    cand=[r for r in tr['trace'] if r['lookahead'] is not None]
    return cand or [tr['trace'][burn]]


def mutate(cases,k=20,rng_seed=20261029):
    """k single-field errors in k distinct main-block cases (plan GS_ref5 mutation test). Returns (mutated copies,
    injected index set)."""
    check(k==len(KINDS),'k must equal len(KINDS)');rng=random.Random(rng_seed)
    main=[i for i,c in enumerate(cases) if c['family']!='ood5'];check(len(main)>=k,'too few main cases for the mutation test')
    idx=rng.sample(main,k);kinds=list(KINDS);rng.shuffle(kinds);out=list(cases);inj=set()
    for i,kind in zip(idx,kinds):
        c=copy.deepcopy(cases[i])
        if kind=='bounded':
            tj=rng.choice(('SP8','RSX','RSXL','RGLX','RGL'));n=str(rng.choice(NS));B=c['bounded'][tj][n]
            cand=[(s,b) for s in range(len(B['support'])) for b in (0,1) if B['support'][s][b] is not None and B['unknown'][s][b]==0]
            s,b=rng.choice(cand);v=B['support'][s][b];B['support'][s][b]=v[1:] if len(v)>1 else [(v[0]+1)%4]
        elif kind=='rsxl':
            r=c['rsxl']['trace'][rng.randrange(c['burn_in'],c['steps'])]
            if rng.random()<0.5:r['action']=1-r['action']
            else:r['deferred']=not r['deferred']
        elif kind in ('rglx','rgl'):
            r=rng.choice(_look_step(c[kind],c['burn_in'],c['steps']));u=rng.random()
            if r['lookahead'] is not None and u<0.5:
                b=rng.randrange(2);L=r['lookahead'];L['num'][b]=(L['num'][b]+1)%(L['den'][b]+1) if L['den'][b] else 1
            else:r['action']=1-r['action']
        elif kind=='dlf':
            arm=rng.choice(('DLFp','DLFn','RSXLp','RSXLn'));r=c['transfer'][arm]['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            r['rule'][b]={'sp8':'rg','rg':'license','license':None,None:'license'}[r['rule'][b]]
        elif kind=='dlfa':
            arm=rng.choice(('DLFa_p','DLFa_n'));r=c['transfer'][arm]['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        elif kind=='stress':
            c['stress'][rng.randrange(len(c['stress']))][rng.choice(('AT6_false','DLF_license','RSXL_rg','RSXL_false'))]+=1
        elif kind=='rg':
            r=c['transfer'][rng.choice(('RG4','RGLX4','RGL4','RSXL4'))]['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        else:
            r=c['transfer']['EB']['trace'][rng.randrange(c['steps'])];r['n_E']=(r['n_E'] or 0)%4+1
        out[i]=c;inj.add(i)
    return out,inj


def run(cases,plan,workers=2,mutate_k=0,source_sha=None,on_result=None):
    check(plan==load(PLAN),'plan mismatch');bad=count(cases,plan,workers,on_result)
    rep={'schema':'brute.second-implementation-count.v12','study':plan['study'],
         'wording':'second implementation by the same author, no brute import; not an independent or third-party audit',
         'cases_checked':len(cases),'mismatching_cases':len(bad),'mismatches':bad,
         'scope':'bounded supports (exhaustive, n = 1..5 on SP8, RSX, RSXL, RGLX, RGL; ood5 SP8, RSXL5); RSX / RSXL / RGLX / RGL actions; RGL lookahead scores (exhaustive n = 4); RG4 / RG5, RGLX4, RGL4, RSXL4, RSX4, DLF / DLF2 / DLFa / RSXL library arms, EB; summary; stress entries; ood5 RG4 / RG5 / RSXL5',
         'source_sha256':source_sha}
    if mutate_k:
        mc,inj=mutate(cases,mutate_k);base={b['case'] for b in bad};sub=sorted(inj)
        mb=count([mc[i] for i in sub],plan,workers);flagged={sub[b['case']] for b in mb}
        rep['mutation_test']={'injected':len(inj),'kinds':{k:KINDS.count(k) for k in sorted(set(KINDS))},
                              'detected_injected':len(inj&flagged),'flagged_not_injected':len(flagged-inj-base),
                              'rng':'random.Random(20261029)','passed':inj<=flagged and not (flagged-inj-base)}
    return rep
