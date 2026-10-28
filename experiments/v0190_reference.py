"""Second implementation (same author, no `brute` import) for study BRUTE-0190-ANYTIME-021 (GS_ref9, GLV, GAH_prefix_control).

Written from experiments/BRUTE_PLAN_021.json and docs/research/v0.19.0/ANYTIME_LEMMA_021.md BEFORE brute/anytimemargin.py,
brute/api/certify8.py and experiments/brute_study_021.py existed. NOT an independent or third-party audit: same author.
It REUSES the frozen reference functions of experiments/v0170_reference.py (full-table cost enumeration `costs_tables`,
`supports_for`, `audit_support`, `ref_cert`, `ref_boundary`, `prefix_counts`, `first_crossing`), v0160_reference (`ref_m`,
`_cmp`), v0120_reference (`steps_sp8`, `ref_rg`) and v0180_reference (`ref_perbit`); new here: its own anytime boundary
(`ref_anytime_boundary`, written as a dict-of-survivors DP, not the list DP of the planned boundary), the tag-21 flip
array, per-eps arm sets and the 28-action prefix control.

Case format (brute.case.v19_0): the study-020 main keys (88 actions, 89 readings, B, m, boundary, prefix_bits,
prefix_flips, realized_flips, crossing, crossing_bit) plus anytime_boundary (m_a(0..B)), anytime_crossing,
anytime_crossing_bit; noisy[RGNA4 | RGN4_or | RGNB4 (eps 0.01 / 0.02 only)] with per-step m for RGNA4 / RGNB4; certifiers
RG4 / RGNA4 / RGN4_or (+ RGNB4); perbit (RGNA4_bit); prefix28 (eps 0.02 only: RGNA4 on the first 28 actions: m, support,
unknown, certifier, identical); summary per arm + SP8 (study-020 metrics).
"""
from __future__ import annotations
import copy,random
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path
import numpy as np
from experiments.brute_common import check,VerificationError
from experiments.v0120_reference import steps_sp8,ref_rg,CENSOR
from experiments.v0160_reference import ref_m,_cmp
from experiments.v0170_reference import (ref_boundary,prefix_counts,first_crossing,costs_tables,supports_for,audit_support,
                                         ref_cert,readings_main)
from experiments.v0180_reference import ref_perbit

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_021.json'
N=4;STEPS=88;READINGS=89;SLOTS=176;LATE=(45,88);EARLY=28;BITSLOTS=352;PREFIX=28


def arms_for(eps):
    return ('RG4','RGNA4','RGN4_or')+(('RGNB4',) if eps in (0.01,0.02) else ())


def noisy_for(eps):return tuple(a for a in arms_for(eps) if a!='RG4')


def flip_array(seed,eps):return np.random.default_rng([seed,round(1000*eps),21]).random((READINGS,2))<eps


def ref_allowance(b,delta):
    """A(b) = delta * 6 * 113^2 / 355^2 * sum_{j<=b} 1/j^2 (exact)."""
    return Fraction(str(delta))*Fraction(6*113*113,355*355)*sum((Fraction(1,j*j) for j in range(1,b+1)),Fraction(0))


def ref_anytime_boundary(L,eps_bar=0.02,delta=0.01):
    """m_a(0..L): smallest non-decreasing m with P(first crossing by bit b) <= A(b); survivors kept as {flips: prob}."""
    p=Fraction(str(eps_bar));q=1-p;alive={0:Fraction(1)};lost=Fraction(0);m=[0];h=Fraction(0)
    scale=Fraction(str(delta))*Fraction(6*113*113,355*355)
    for b in range(1,L+1):
        h+=Fraction(1,b*b);A=scale*h;nxt={}
        for s,x in alive.items():
            nxt[s]=nxt.get(s,Fraction(0))+x*q;nxt[s+1]=nxt.get(s+1,Fraction(0))+x*p
        mb=m[-1]
        while lost+sum(v for s,v in nxt.items() if s>mb)>A:mb+=1
        lost+=sum(v for s,v in nxt.items() if s>mb);alive={s:v for s,v in nxt.items() if s<=mb};m.append(mb)
        check(lost<=A<Fraction(str(delta)),'anytime spending')
    return m


def bit(c,j):return (c>>(1-j))&1


def audit_noise_common(c,R):
    F=flip_array(c['seed'],c['eps']);check(len(R)==READINGS,'89 readings')
    bits,flips,seq=prefix_counts(R,F);B=bits[-1]
    check(c['B']==B,f'B {c["B"]} != {B}');check(c['realized_flips']==flips[-1],f'realized_flips {c["realized_flips"]} != {flips[-1]}')
    check(c['prefix_bits']==bits,'prefix_bits');check(c['prefix_flips']==flips,'prefix_flips')
    check(c['m']==ref_m(B,c['eps_bar'],c['delta']),f'm {c["m"]} != m_rule({B})')
    bd=ref_boundary(B,c['eps_bar'],c['delta']);check(c['boundary']==bd,'boundary')
    cb=first_crossing(seq,bd);check(c['crossing_bit']==cb and c['crossing']==(cb is not None),f'crossing {c["crossing_bit"]} != {cb}')
    ba=ref_anytime_boundary(B,c['eps_bar'],c['delta']);check(c['anytime_boundary']==ba,'anytime boundary')
    ca=first_crossing(seq,ba);check(c['anytime_crossing_bit']==ca and c['anytime_crossing']==(ca is not None),'anytime crossing')
    fp=[[t,j] for t,(obs,_) in enumerate(R) for j,o in enumerate(obs) if o is not None and F[t,j]]
    check(c['flip_positions_EVALUATOR_ONLY']==fp,'flip positions')
    return B,flips[-1],bd,ba,bits


def _windows(trace):
    per=[sum(x is not None for x in r['certificate']) for r in trace]
    late=sum(p for r,p in zip(trace,per) if LATE[0]<=r['step']<=LATE[1]);early=sum(p for r,p in zip(trace,per) if r['step']<=EARLY)
    return per,late,early


def ref_summary(S,exp,pb,arms):
    f0=next((s['t'] for s in S if s['cert'][s['a']] is not None),CENSOR)
    sp8_trace=[{'step':s['t'],'certificate':s['cert']} for s in S]
    sp8f=sum(s['cert'][b] is not None and s['cert'][b]!=s['act'][b] for s in S for b in (0,1))
    tr=dict({a:exp[a]['trace'] for a in arms},SP8=sp8_trace)
    cert=dict({a:exp[a]['certificates'] for a in arms},SP8=sum(s['cert'][b] is not None for s in S for b in (0,1)))
    fal=dict({a:exp[a]['false_certificates'] for a in arms},SP8=sp8f)
    W={a:_windows(tr[a]) for a in tr}
    return {'certificates':cert,'false':fal,'case_false':{a:v>0 for a,v in fal.items()},
            'coverage':{a:round(v/SLOTS,6) for a,v in cert.items()},
            'certificates_late':{a:W[a][1] for a in W},'coverage_late':{a:round(W[a][1]/(2*(LATE[1]-LATE[0]+1)),6) for a in W},
            'certificates_early28':{a:W[a][2] for a in W},'coverage_early28':{a:round(W[a][2]/(2*EARLY),6) for a in W},
            'per_step':{a:W[a][0] for a in W},
            'first_cert_step':dict({a:exp[a]['first_cert_step'] for a in arms},SP8=f0),
            'perbit':{'certified_bits':pb['certified_bits'],'false_bits':pb['false_bits'],'case_false':pb['false_bits']>0,
                      'coverage':round(pb['certified_bits']/BITSLOTS,6),'late_certified_bits':pb['late_certified_bits'],
                      'late_false_bits':pb['late_false_bits'],'coverage_late':round(pb['late_certified_bits']/(4*(LATE[1]-LATE[0]+1)),6)}}


def audit_prefix(c,S,ba,bits,burn):
    """GAH_prefix_control: the recorded 28-action RGNA4 run equals the reference on the prefix and the 88-step run on 1..28."""
    p=c['prefix28'];check(p['actions']==PREFIX,'prefix length');S28=S[:PREFIX]
    costs=costs_tables(tuple(c['initial_visible']),[s['a'] for s in S28],[s['obs'] for s in S28])
    m=[ba[bits[i]] for i in range(PREFIX)];check(p['m']==m,'prefix28 m')
    audit_support(p,supports_for(costs,m,2),'prefix28',2)
    _cmp(p['certifier'],ref_cert([(s['t'],s['a']) for s in S28],[s['act'] for s in S28],p['support'],m,burn,2),'prefix28 certifier')
    full=c['noisy']['RGNA4'];ft=c['certifiers']['RGNA4']['trace'][:PREFIX]
    same=(p['support']==full['support'][:PREFIX] and p['unknown']==full['unknown'][:PREFIX] and p['m']==full['m'][:PREFIX]
          and [r['certificate'] for r in p['certifier']['trace']]==[r['certificate'] for r in ft])
    check(p['identical']==same,'prefix28 identical flag')
    return same


def audit_main(c,plan):
    check(c['schema']=='brute.case.v19_0','schema')
    check(c['mask_rate']==plan['mask_rate'] and c['steps']==plan['horizon']['steps']==STEPS and c['burn_in']==plan['burn_in'],'case constants')
    check(c['eps'] in (0.0,0.01,0.02,0.05),'eps level');check(c['eps_bar']==0.02 and c['delta']==0.01,'eps_bar / delta')
    arms=arms_for(c['eps']);noisy=noisy_for(c['eps'])
    burn=c['burn_in'];S=steps_sp8(c);check(len(S)==STEPS,'SP8 steps')
    B,flips,bd,ba,bits=audit_noise_common(c,readings_main(c))
    costs=costs_tables(tuple(c['initial_visible']),[s['a'] for s in S],[s['obs'] for s in S])
    T=len(S);mb=[bd[bits[i]] for i in range(T)];ma=[ba[bits[i]] for i in range(T)]
    ms={'RGNA4':ma,'RGNB4':mb,'RGN4_or':[flips]*T};mrec={'RGNA4':ma,'RGNB4':mb,'RGN4_or':flips}
    check(sorted(c['noisy'])==sorted(noisy),'noisy arm set');exp={}
    audit_support(c['bounded']['4'],supports_for(costs,[0]*T,2),'bounded 4',2)
    truth=[s['act'] for s in S];st=[(s['t'],s['a']) for s in S]
    for arm in noisy:
        rec=c['noisy'][arm];check(rec['m']==mrec[arm],f'{arm} m');audit_support(rec,supports_for(costs,ms[arm],2),arm,2)
        exp[arm]=ref_cert(st,truth,rec['support'],mrec[arm],burn,2)
    exp['RG4']=ref_rg(S,c['bounded'],4,burn)
    check(sorted(c['certifiers'])==sorted(arms),'certifier arm set')
    for arm in arms:_cmp(c['certifiers'][arm],exp[arm],arm)
    pb=ref_perbit(st,truth,c['noisy']['RGNA4']['support'],burn);_cmp(c['perbit'],pb,'perbit')
    check(c['summary']==ref_summary(S,exp,pb,arms),'summary')
    check(('prefix28' in c)==(c['eps']==0.02),'prefix28 present iff eps 0.02')
    if c['eps']==0.02:audit_prefix(c,S,ba,bits,burn)


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


# ------------------------------------------------------------------ mutation test (GS_ref9)
KINDS=('support',)*3+('rgn_cert',)*2+('rg4_cert','wrong','wrong','counts','counts','anytime','B','flips','boundary','crossing',
                                     'prefix','observed','latent','perbit','prefix28')


def _slots(rec):
    return [(i,b) for i in range(len(rec['support'])) for b in (0,1) if rec['support'][i][b] is not None and rec['unknown'][i][b]==0]


def mutate(cases,k=20,rng_seed=20261028):
    """k single-field errors in k distinct cases (KINDS, shuffled); the prefix28 error goes to an eps-0.02 case."""
    check(k==len(KINDS),'k must equal len(KINDS)');rng=random.Random(rng_seed)
    mi=[i for i,c in enumerate(cases) if c.get('schema')=='brute.case.v19_0'];check(len(mi)>=k,'too few cases for the mutation test')
    kinds=list(KINDS);rng.shuffle(kinds);picks=rng.sample(mi,k);j28=kinds.index('prefix28')
    if 'prefix28' not in cases[picks[j28]]:
        el=[i for i in mi if 'prefix28' in cases[i] and i not in picks];check(el,'no eps-0.02 case for the prefix28 mutation')
        picks[j28]=rng.choice(el)
    out=list(cases);inj=set()
    for i,kind in zip(picks,kinds):
        c=copy.deepcopy(cases[i]);NA=noisy_for(c['eps']);AR=arms_for(c['eps'])
        if kind=='support':
            arm=rng.choice(NA+('bounded',));rec=c['bounded']['4'] if arm=='bounded' else c['noisy'][arm]
            if not _slots(rec):rec=c['noisy']['RGNA4']
            if not _slots(rec):rec=c['bounded']['4']
            s,b=rng.choice(_slots(rec));v=rec['support'][s][b];rec['support'][s][b]=v[1:] if len(v)>1 else [(v[0]+1)%4]
        elif kind in ('rgn_cert','rg4_cert','wrong'):
            arm=rng.choice(NA) if kind=='rgn_cert' else 'RG4' if kind=='rg4_cert' else rng.choice(AR)
            r=c['certifiers'][arm]['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            if kind=='wrong':r['wrong'][b]=not r['wrong'][b]
            else:r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        elif kind=='perbit':
            r=c['perbit']['trace'][rng.randrange(c['steps'])];b=rng.randrange(2);j=rng.randrange(2)
            r['bits'][b][j]=0 if r['bits'][b][j] is None else (None if rng.random()<0.5 else 1-r['bits'][b][j])
        elif kind=='counts':c['certifiers'][rng.choice(AR)][rng.choice(('false_certificates','certificates'))]+=1
        elif kind in ('B','flips'):c[{'B':'B','flips':'realized_flips'}[kind]]+=1
        elif kind=='boundary':j=rng.randrange(1,len(c['boundary']));c['boundary'][j]+=1
        elif kind=='anytime':j=rng.randrange(1,len(c['anytime_boundary']));c['anytime_boundary'][j]+=1
        elif kind=='crossing':c['crossing']=not c['crossing']
        elif kind=='prefix':j=rng.randrange(len(c['prefix_bits']));c['prefix_bits'][j]+=1
        elif kind=='prefix28':
            p=c['prefix28'];r=p['certifier']['trace'][rng.randrange(PREFIX)];b=rng.randrange(2)
            r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        elif kind=='observed':
            R=[c['initial_visible']]+[r['observed'] for r in c['arms']['SP8']['trace']]
            cand=[(t,j) for t,o in enumerate(R) for j in (0,1) if o[j] is not None];t,j=rng.choice(cand);R[t][j]=1-R[t][j]
        elif kind=='latent':
            tr=c['arms']['SP8']['trace'];cand=[i_ for i_,r in enumerate(tr) if any(x is not None for x in r['observed'])]
            r=tr[rng.choice(cand)];r['actual_emission_EVALUATOR_ONLY']=r['actual_emission_EVALUATOR_ONLY']^3
        out[i]=c;inj.add(i)
    return out,inj
