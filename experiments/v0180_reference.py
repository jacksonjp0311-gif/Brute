"""Second implementation (same author, no `brute` import) for study BRUTE-0180-HORIZON-020 (GS_ref8, GLV).

Written from experiments/BRUTE_PLAN_020.json and docs/research/BRUTE_DEVIATIONS_020.md (#103) BEFORE brute/perbit.py and
experiments/brute_study_020.py existed. NOT an independent or third-party audit: same author. It REUSES the frozen
reference functions of experiments/v0170_reference.py (full-table cost enumeration `costs_tables`, `supports_for`,
`audit_support`, `ref_cert`, `ref_boundary`, `prefix_counts`, `first_crossing`), v0160_reference (`ref_m`, `_cmp`) and
v0120_reference (`steps_sp8`, `ref_rg`); new here: the 89-reading horizon, the tag-20 flip array, the window metrics
and the per-bit rule (#103 items 4-5).

Case format (brute.case.v18_0): the study-019 main keys (88 actions, 89 readings) with noisy[RGN4 | RGNB4 | RGN4_or]
(no RGNB4_0), certifiers RG4 / RGN4 / RGNB4 / RGN4_or, perbit (RGNB4_bit: trace of per-step [[bit0, bit1] per action]
values or None, wrong flags, counts) and summary per arm + SP8 with certificates, false, case_false, coverage (/176),
certificates_late / coverage_late (steps 45..88, /88), certificates_early28 / coverage_early28 (steps 1..28, /56),
per_step (certificates per step), first_cert_step, and summary['perbit'].
"""
from __future__ import annotations
import copy,random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
from experiments.brute_common import check,VerificationError
from experiments.v0120_reference import steps_sp8,ref_rg,CENSOR
from experiments.v0160_reference import ref_m,_cmp
from experiments.v0170_reference import (ref_boundary,prefix_counts,first_crossing,costs_tables,supports_for,audit_support,
                                         ref_cert,readings_main)

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_020.json'
N=4;STEPS=88;READINGS=89;SLOTS=176;LATE=(45,88);EARLY=28;BITSLOTS=352
NOISY_ARMS=('RGN4','RGNB4','RGN4_or');ARMS=('RG4',)+NOISY_ARMS


def flip_array(seed,eps):return np.random.default_rng([seed,round(1000*eps),20]).random((READINGS,2))<eps


def bit(c,j):return (c>>(1-j))&1


def audit_noise_common(c,R):
    F=flip_array(c['seed'],c['eps']);check(len(R)==READINGS,'89 readings')
    bits,flips,seq=prefix_counts(R,F);B=bits[-1]
    check(c['B']==B,f'B {c["B"]} != {B}');check(c['realized_flips']==flips[-1],f'realized_flips {c["realized_flips"]} != {flips[-1]}')
    check(c['prefix_bits']==bits,'prefix_bits');check(c['prefix_flips']==flips,'prefix_flips')
    check(c['m']==ref_m(B,c['eps_bar'],c['delta']),f'm {c["m"]} != m_rule({B})')
    bd=ref_boundary(B,c['eps_bar'],c['delta']);check(c['boundary']==bd,'boundary')
    cb=first_crossing(seq,bd);check(c['crossing_bit']==cb and c['crossing']==(cb is not None),f'crossing {c["crossing_bit"]} != {cb}')
    fp=[[t,j] for t,(obs,_) in enumerate(R) for j,o in enumerate(obs) if o is not None and F[t,j]]
    check(c['flip_positions_EVALUATOR_ONLY']==fp,'flip positions')
    return B,flips[-1],bd,bits


def ref_perbit(st,truth,sup,burn):
    """Per-bit rule (#103 item 5): bit j of action b certified iff t > burn, support non-empty and unanimous on bit j."""
    out={'trace':[]};n=f=nl=fl=0
    for i,(t,a) in enumerate(st):
        vals=[];wr=[]
        for b in (0,1):
            S=sup[i][b];row=[]
            for j in (0,1):
                v=None
                if t>burn and S:
                    bs={bit(c,j) for c in S}
                    if len(bs)==1:v=bs.pop()
                row.append(v)
            w=[row[j] is not None and row[j]!=bit(truth[i][b],j) for j in (0,1)]
            vals.append(row);wr.append(w)
            k=sum(v is not None for v in row);x=sum(w);n+=k;f+=x
            if LATE[0]<=t<=LATE[1]:nl+=k;fl+=x
        out['trace'].append({'step':t,'bits':vals,'wrong':wr})
    out.update(certified_bits=n,false_bits=f,late_certified_bits=nl,late_false_bits=fl)
    return out


def _windows(trace):
    per=[sum(x is not None for x in r['certificate']) for r in trace]
    late=sum(p for r,p in zip(trace,per) if LATE[0]<=r['step']<=LATE[1]);early=sum(p for r,p in zip(trace,per) if r['step']<=EARLY)
    return per,late,early


def ref_summary(S,exp,pb):
    f0=next((s['t'] for s in S if s['cert'][s['a']] is not None),CENSOR)
    sp8_trace=[{'step':s['t'],'certificate':s['cert']} for s in S]
    sp8f=sum(s['cert'][b] is not None and s['cert'][b]!=s['act'][b] for s in S for b in (0,1))
    tr=dict({a:exp[a]['trace'] for a in ARMS},SP8=sp8_trace)
    cert=dict({a:exp[a]['certificates'] for a in ARMS},SP8=sum(s['cert'][b] is not None for s in S for b in (0,1)))
    fal=dict({a:exp[a]['false_certificates'] for a in ARMS},SP8=sp8f)
    W={a:_windows(tr[a]) for a in tr}
    return {'certificates':cert,'false':fal,'case_false':{a:v>0 for a,v in fal.items()},
            'coverage':{a:round(v/SLOTS,6) for a,v in cert.items()},
            'certificates_late':{a:W[a][1] for a in W},'coverage_late':{a:round(W[a][1]/(2*(LATE[1]-LATE[0]+1)),6) for a in W},
            'certificates_early28':{a:W[a][2] for a in W},'coverage_early28':{a:round(W[a][2]/(2*EARLY),6) for a in W},
            'per_step':{a:W[a][0] for a in W},
            'first_cert_step':dict({a:exp[a]['first_cert_step'] for a in ARMS},SP8=f0),
            'perbit':{'certified_bits':pb['certified_bits'],'false_bits':pb['false_bits'],'case_false':pb['false_bits']>0,
                      'coverage':round(pb['certified_bits']/BITSLOTS,6),'late_certified_bits':pb['late_certified_bits'],
                      'late_false_bits':pb['late_false_bits'],'coverage_late':round(pb['late_certified_bits']/(4*(LATE[1]-LATE[0]+1)),6)}}


def audit_main(c,plan):
    check(c['schema']=='brute.case.v18_0','schema')
    check(c['mask_rate']==plan['mask_rate'] and c['steps']==plan['horizon']['steps']==STEPS and c['burn_in']==plan['burn_in'],'case constants')
    check(c['eps'] in (0.0,0.01,0.02,0.05),'eps level');check(c['eps_bar']==0.02 and c['delta']==0.01,'eps_bar / delta')
    burn=c['burn_in'];S=steps_sp8(c);check(len(S)==STEPS,'SP8 steps')
    B,flips,bd,bits=audit_noise_common(c,readings_main(c))
    costs=costs_tables(tuple(c['initial_visible']),[s['a'] for s in S],[s['obs'] for s in S])
    T=len(S);step_m=[bd[bits[i]] for i in range(T)]
    ms={'RGN4':[c['m']]*T,'RGNB4':step_m,'RGN4_or':[flips]*T};mrec={'RGN4':c['m'],'RGNB4':step_m,'RGN4_or':flips}
    check(sorted(c['noisy'])==sorted(NOISY_ARMS),'noisy arm set');exp={}
    audit_support(c['bounded']['4'],supports_for(costs,[0]*T,2),'bounded 4',2)
    truth=[s['act'] for s in S];st=[(s['t'],s['a']) for s in S]
    for arm in NOISY_ARMS:
        rec=c['noisy'][arm];check(rec['m']==mrec[arm],f'{arm} m');audit_support(rec,supports_for(costs,ms[arm],2),arm,2)
        exp[arm]=ref_cert(st,truth,rec['support'],mrec[arm],burn,2)
    exp['RG4']=ref_rg(S,c['bounded'],4,burn)
    check(sorted(c['certifiers'])==sorted(ARMS),'certifier arm set')
    for arm in ARMS:_cmp(c['certifiers'][arm],exp[arm],arm)
    pb=ref_perbit(st,truth,c['noisy']['RGNB4']['support'],burn);_cmp(c['perbit'],pb,'perbit')
    check(c['summary']==ref_summary(S,exp,pb),'summary')


def audit_case(c,plan):
    """(ok, message): the first differing field, or (True, None)."""
    try:audit_main(c,plan);return True,None
    except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError,ZeroDivisionError) as exc:
        return False,f'{type(exc).__name__}: {exc}'


def _job(x):
    i,c,plan=x;return i,audit_case(c,plan)


def count(cases,plan,workers=1):
    jobs=[(i,c,plan) for i,c in enumerate(cases)]
    if workers<=1:outs=[_job(j) for j in jobs]
    else:
        with ProcessPoolExecutor(workers) as ex:outs=list(ex.map(_job,jobs,chunksize=1))
    return [{'case':i,'family':cases[i]['family'],'seed':cases[i]['seed'],'eps':cases[i]['eps'],'first_difference':m}
            for i,(ok,m) in sorted(outs) if not ok]


# ------------------------------------------------------------------ mutation test (GS_ref8)
KINDS=('support',)*3+('rgn_cert',)*2+('rg4_cert','wrong','wrong','counts','counts','m','B','flips','boundary','crossing',
                                     'prefix','observed','latent','perbit','perbit')


def _slots(rec):
    return [(i,b) for i in range(len(rec['support'])) for b in (0,1) if rec['support'][i][b] is not None and rec['unknown'][i][b]==0]


def mutate(cases,k=20,rng_seed=20261028):
    """k single-field errors in k distinct main cases (KINDS, shuffled)."""
    check(k==len(KINDS),'k must equal len(KINDS)');rng=random.Random(rng_seed)
    mi=[i for i,c in enumerate(cases) if c.get('schema')=='brute.case.v18_0'];check(len(mi)>=k,'too few cases for the mutation test')
    kinds=list(KINDS);rng.shuffle(kinds);out=list(cases);inj=set()
    for i,kind in zip(rng.sample(mi,k),kinds):
        c=copy.deepcopy(cases[i])
        if kind=='support':
            arm=rng.choice(NOISY_ARMS+('bounded',));rec=c['bounded']['4'] if arm=='bounded' else c['noisy'][arm]
            if not _slots(rec):rec=c['noisy']['RGNB4']
            s,b=rng.choice(_slots(rec));v=rec['support'][s][b];rec['support'][s][b]=v[1:] if len(v)>1 else [(v[0]+1)%4]
        elif kind in ('rgn_cert','rg4_cert','wrong'):
            arm=rng.choice(NOISY_ARMS) if kind=='rgn_cert' else 'RG4' if kind=='rg4_cert' else rng.choice(ARMS)
            r=c['certifiers'][arm]['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            if kind=='wrong':r['wrong'][b]=not r['wrong'][b]
            else:r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        elif kind=='perbit':
            r=c['perbit']['trace'][rng.randrange(c['steps'])];b=rng.randrange(2);j=rng.randrange(2)
            r['bits'][b][j]=0 if r['bits'][b][j] is None else (None if rng.random()<0.5 else 1-r['bits'][b][j])
        elif kind=='counts':c['certifiers'][rng.choice(ARMS)][rng.choice(('false_certificates','certificates'))]+=1
        elif kind in ('m','B','flips'):c[{'m':'m','B':'B','flips':'realized_flips'}[kind]]+=1
        elif kind=='boundary':j=rng.randrange(1,len(c['boundary']));c['boundary'][j]+=1
        elif kind=='crossing':c['crossing']=not c['crossing']
        elif kind=='prefix':j=rng.randrange(len(c['prefix_bits']));c['prefix_bits'][j]+=1
        elif kind=='observed':
            R=[c['initial_visible']]+[r['observed'] for r in c['arms']['SP8']['trace']]
            cand=[(t,j) for t,o in enumerate(R) for j in (0,1) if o[j] is not None];t,j=rng.choice(cand);R[t][j]=1-R[t][j]
        elif kind=='latent':
            tr=c['arms']['SP8']['trace'];cand=[i_ for i_,r in enumerate(tr) if any(x is not None for x in r['observed'])]
            r=tr[rng.choice(cand)];r['actual_emission_EVALUATOR_ONLY']=r['actual_emission_EVALUATOR_ONLY']^3
        out[i]=c;inj.add(i)
    return out,inj
