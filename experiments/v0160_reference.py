"""Second implementation (same author, no `brute` import) for study BRUTE-0160-NOISY-OBSERVATION-018 (GS_ref6, GLV).

Written from experiments/BRUTE_PLAN_018.json (noise_model, tolerant_region, arms, metrics) and
docs/research/BRUTE_DEVIATIONS_018.md (#97) BEFORE brute/noisyregion.py and brute/api/certify6.py existed. NOT an
independent or third-party audit: same author.

Method (exhaustive, numpy): every transition table of a complete 4-state, 2-action machine with start state 0
(4**8 = 65536 tables; machines with fewer states embed as unreachable states). Along the recorded trajectory each table
has a deterministic state path; per table keep C[q][c] = the number of OBSERVED bits whose value differs from code c's
bit over the readings taken in state q. The cost of an emission table e is sum_q C[q][e[q]] (additive per state), so the
least number of flips under which (table, e) explains the data with next code c after action b (next state r) is
  cost_b(c) = C[r][c] + sum_{q != r} min_c' C[q][c'].
RGN_4(m) support for action b = {c : min over tables of cost_b(c) <= m}; the region is empty iff min over tables of
sum_q min_c C[q][c] > m (then the support is None). m = 0 is the frozen hard-clause region RegionSpace(4).

Case format (brute.case.v16_0; the runner writes these keys; '*wall_informational*' keys are ignored):
  seed, family, eps, mask_rate, steps (44), burn_in (8), eps_bar (0.02), delta (0.01), B, m, realized_flips,
  initial_visible (noisy, None = masked), initial_latent_EVALUATOR_ONLY (code),
  arms.SP8 (the frozen trajectory_2x2 record on the noisy world: trace[i].observed is the noisy reading after action i,
      actual_emission_EVALUATOR_ONLY / counterfactual_actual_EVALUATOR_ONLY the latent codes),
  bounded['4'] = {'support': [[s0, s1] per step], 'unknown': [[u0, u1]]} (frozen RegionSpace(4), noisy observations),
  noisy[arm] for arm in RGN4, RGN4_0, RGN4_or = {'m', 'support', 'unknown', 'shared_with' (None | arm)},
  certifiers: RG4 (frozen rg_arm format) and RGN4 / RGN4_0 / RGN4_or = {'m', 'trace': [{'step', 'certificate',
      'wrong'}], 'first_cert_step', 'false_certificates', 'certificates'},
  summary = {'certificates', 'false', 'case_false', 'coverage' (certificates / 88, round 6), 'first_cert_step'} per arm
      (RG4, RGN4, RGN4_0, RGN4_or, SP8).

Checks per case: the flip array (default_rng([seed, round(1000*eps), 18]).random((45, 2)) < eps; #97 item 5)
reproduces every observed bit from the latent code; realized_flips, B and m (own exact-rational m rule); every RGN
support and the RG4 bounded support (equal when the slot's unknown count is 0, else the reference support must be a
subset); RGN certificates (#97 item 1: t > burn_in and singleton support), RG4 (frozen rule: SP8 passthrough, burn-in,
singleton in the SP8 support), wrong flags, counts and the summary.
"""
from __future__ import annotations
import copy,random
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from math import comb
from pathlib import Path
import numpy as np
from experiments.brute_common import check,load,VerificationError
from experiments.v0120_reference import steps_sp8,ref_rg,CENSOR

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_018.json'
N=4;READINGS=45;SLOTS=88
RGN_ARMS=('RGN4','RGN4_0','RGN4_or')
ARMS=('RG4',)+RGN_ARMS
_D=None


def ref_m(B,eps_bar=0.02,delta=0.01):
    """Smallest m with P(Bin(B, eps_bar) > m) <= delta, exact rationals (own implementation)."""
    p=Fraction(str(eps_bar));d=Fraction(str(delta));q=1-p;cdf=Fraction(0)
    for m in range(B+1):
        cdf+=comb(B,m)*p**m*q**(B-m)
        if 1-cdf<=d:return m
    return B


def tables():
    global _D
    if _D is None:
        idx=np.arange(4**(2*N),dtype=np.int64);D=np.zeros((len(idx),N,2),dtype=np.int64)
        for q in range(N):
            for a in range(2):D[:,q,a]=(idx>>(2*(2*q+a)))&3
        _D=D
    return _D


def mism(obs):
    return np.array([sum(1 for j,o in enumerate(obs) if o is not None and ((c>>(1-j))&1)!=o) for c in range(4)],dtype=np.int64)


def ref_costs(init,acts,obss):
    """Per step i (before reading i+1): ([min cost per code for b = 0, for b = 1], least total cost)."""
    D=tables();n=len(D);ar=np.arange(n);st=np.zeros(n,dtype=np.int64);C=np.zeros((n,N,4),dtype=np.int64)
    C[ar,st]+=mism(init);out=[]
    for a,o in zip(acts,obss):
        mins=C.min(axis=2);base=mins.sum(axis=1);row=[]
        for b in (0,1):
            r=D[ar,st,b];cost=(base-mins[ar,r])[:,None]+C[ar,r];row.append([int(x) for x in cost.min(axis=0)])
        out.append((row,int(base.min())))
        st=D[ar,st,a];C[ar,st]+=mism(o)
    return out


def support_at(costs,i,b,m):
    row,lo=costs[i]
    return None if lo>m else [c for c in range(4) if row[b][c]<=m]


def flip_array(seed,eps):return np.random.default_rng([seed,round(1000*eps),18]).random((READINGS,2))<eps


def readings(c):
    """[(noisy reading, latent code)] for the 45 readings (row 0 = initial)."""
    tr=c['arms']['SP8']['trace']
    return [(tuple(c['initial_visible']),c['initial_latent_EVALUATOR_ONLY'])]+[(tuple(r['observed']),r['actual_emission_EVALUATOR_ONLY']) for r in tr]


def audit_noise(c):
    F=flip_array(c['seed'],c['eps']);R=readings(c);check(len(R)==READINGS,'45 readings');B=0;flips=0
    for t,(obs,lat) in enumerate(R):
        check(len(obs)==2 and lat in range(4),f'reading {t} shape')
        for j,o in enumerate(obs):
            if o is None:continue
            B+=1;lb=(lat>>(1-j))&1;f=bool(F[t,j]);flips+=f
            check(o==(lb^int(f)),f'reading {t} bit {j}: observed {o}, latent {lb}, flip {f}')
    check(c['B']==B,f'B {c["B"]} != {B}');check(c['realized_flips']==flips,f'realized_flips {c["realized_flips"]} != {flips}')
    check(c['m']==ref_m(B,c['eps_bar'],c['delta']),f'm {c["m"]} != m_rule({B})')
    return B,flips


def audit_support(rec,costs,m,where):
    S=rec['support'];U=rec['unknown'];check(len(S)==len(costs)==len(U),where+' length')
    for i in range(len(costs)):
        for b in (0,1):
            ref=support_at(costs,i,b,m);got=S[i][b];u=U[i][b]
            if u==0:check(got==ref,f'{where} step {i+1} action {b}: {got} != {ref}')
            elif got is not None:check(ref is not None and set(ref)<=set(got),f'{where} step {i+1} action {b}: {ref} not within {got} (unknown {u})')


def ref_rgn(S,sup,m,burn):
    out={'m':m,'trace':[]};first=CENSOR;false=0
    for i,s in enumerate(S):
        cert=[None,None]
        for b in (0,1):
            x=sup[i][b]
            if s['t']>burn and x is not None and len(x)==1:cert[b]=x[0]
        wrong=[cert[b] is not None and cert[b]!=s['act'][b] for b in (0,1)];false+=sum(wrong)
        if cert[s['a']] is not None and first==CENSOR:first=s['t']
        out['trace'].append({'step':s['t'],'certificate':cert,'wrong':wrong})
    out.update(first_cert_step=first,false_certificates=false,certificates=sum(x is not None for r in out['trace'] for x in r['certificate']))
    return out


def ref_summary(S,exp):
    f0=next((s['t'] for s in S if s['cert'][s['a']] is not None),CENSOR)
    sp8f=sum(s['cert'][b] is not None and s['cert'][b]!=s['act'][b] for s in S for b in (0,1))
    sp8n=sum(s['cert'][b] is not None for s in S for b in (0,1))
    cert=dict({a:exp[a]['certificates'] for a in ARMS},SP8=sp8n);fal=dict({a:exp[a]['false_certificates'] for a in ARMS},SP8=sp8f)
    return {'certificates':cert,'false':fal,'case_false':{a:v>0 for a,v in fal.items()},
            'coverage':{a:round(v/SLOTS,6) for a,v in cert.items()},
            'first_cert_step':dict({a:exp[a]['first_cert_step'] for a in ARMS},SP8=f0)}


def strip(x):
    if isinstance(x,dict):return {k:strip(v) for k,v in x.items() if 'wall_informational' not in k}
    if isinstance(x,list):return [strip(v) for v in x]
    return x


def _cmp(got,exp,where):
    got=strip(got)
    for k in exp:check(k in got,f'{where} missing {k}');check(got[k]==exp[k],f'{where} {k}')
    check(set(got)==set(exp),f'{where} extra keys {sorted(set(got)-set(exp))}')


def audit_case(c,plan):
    """(ok, message): the first differing field, or (True, None)."""
    try:
        check(c['mask_rate']==plan['mask_rate'] and c['steps']==plan['actions_per_case'] and c['burn_in']==plan['burn_in'],'case constants')
        check(c['eps'] in tuple(plan['noise_model']['levels'].values()),'eps level')
        check(c['eps_bar']==0.02 and c['delta']==0.01,'eps_bar / delta')
        burn=c['burn_in'];S=steps_sp8(c);check(len(S)==c['steps'],'SP8 steps')
        B,flips=audit_noise(c)
        costs=ref_costs(tuple(c['initial_visible']),[s['a'] for s in S],[s['obs'] for s in S])
        check(sorted(c['noisy'])==sorted(RGN_ARMS),'noisy arm set')
        ms={'RGN4':c['m'],'RGN4_0':0,'RGN4_or':flips};exp={}
        audit_support(c['bounded']['4'],costs,0,'bounded 4')
        for arm in RGN_ARMS:
            rec=c['noisy'][arm];check(rec['m']==ms[arm],f'{arm} m');audit_support(rec,costs,ms[arm],arm)
            exp[arm]=ref_rgn(S,rec['support'],ms[arm],burn)
        exp['RG4']=ref_rg(S,c['bounded'],4,burn)
        check(sorted(c['certifiers'])==sorted(ARMS),'certifier arm set')
        for arm in ARMS:_cmp(c['certifiers'][arm],exp[arm],arm)
        check(c['summary']==ref_summary(S,exp),'summary')
        return True,None
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


KINDS=('support',)*4+('rgn_cert',)*3+('rg4_cert',)*2+('wrong',)*2+('counts',)*2+('m','B','flips')+('observed',)*2+('latent','summary')


def _slots(rec):
    return [(i,b) for i in range(len(rec['support'])) for b in (0,1) if rec['support'][i][b] is not None and rec['unknown'][i][b]==0]


def mutate(cases,k=20,rng_seed=20261029):
    """k single-field errors in k distinct cases (plan GS_ref6 mutation test). Returns (mutated copies, injected set)."""
    check(k==len(KINDS),'k must equal len(KINDS)');rng=random.Random(rng_seed);check(len(cases)>=k,'too few cases for the mutation test')
    idx=rng.sample(range(len(cases)),k);kinds=list(KINDS);rng.shuffle(kinds);out=list(cases);inj=set()
    for i,kind in zip(idx,kinds):
        c=copy.deepcopy(cases[i])
        if kind=='support':
            arm=rng.choice(RGN_ARMS+('bounded',));rec=c['bounded']['4'] if arm=='bounded' else c['noisy'][arm]
            cand=_slots(rec)
            if not cand:rec=c['noisy']['RGN4'];cand=_slots(rec)
            s,b=rng.choice(cand);v=rec['support'][s][b];rec['support'][s][b]=v[1:] if len(v)>1 else [(v[0]+1)%4]
        elif kind in ('rgn_cert','rg4_cert','wrong'):
            arm=rng.choice(RGN_ARMS) if kind=='rgn_cert' else 'RG4' if kind=='rg4_cert' else rng.choice(ARMS)
            r=c['certifiers'][arm]['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            if kind=='wrong':r['wrong'][b]=not r['wrong'][b]
            else:r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        elif kind=='counts':
            c['certifiers'][rng.choice(ARMS)][rng.choice(('false_certificates','certificates'))]+=1
        elif kind in ('m','B','flips'):c[{'m':'m','B':'B','flips':'realized_flips'}[kind]]+=1
        elif kind=='observed':
            R=[c['initial_visible']]+[r['observed'] for r in c['arms']['SP8']['trace']]
            cand=[(t,j) for t,o in enumerate(R) for j in (0,1) if o[j] is not None];t,j=rng.choice(cand);R[t][j]=1-R[t][j]
        elif kind=='latent':
            tr=c['arms']['SP8']['trace'];cand=[i_ for i_,r in enumerate(tr) if any(x is not None for x in r['observed'])]
            r=tr[rng.choice(cand)];r['actual_emission_EVALUATOR_ONLY']=r['actual_emission_EVALUATOR_ONLY']^3
        else:
            a=rng.choice(ARMS);c['summary']['coverage'][a]=round(c['summary']['coverage'][a]+1/SLOTS,6)
        out[i]=c;inj.add(i)
    return out,inj
