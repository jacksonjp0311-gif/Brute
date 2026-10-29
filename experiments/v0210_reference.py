"""Second implementation (same author, no `brute` import) for study BRUTE-0210-STITCHED-LR-024 (GS_ref10, GLV, GLS (e)).

Written from experiments/BRUTE_PLAN_024.json and docs/research/v0.21.0/STITCHED_LEMMA_024.md BEFORE brute/stitchedregion.py,
brute/api/certify10.py and experiments/brute_study_024.py existed. NOT an independent or third-party audit: same author.
REUSES the frozen v0200_reference (audit_main for every carried arm on the case with the RGL5 fields removed, fmin_tables,
ref_D, sim_flips, flip_array, _windows) and v0170_reference (ref_boundary, costs_tables, supports_for, audit_support,
ref_cert, readings_main, prefix_counts). New here:
  * ref_delta(k) = (1/200) / ((k+1)(k+2)) exact; ref_epoch(i); ref_epochs(); ref_bd(k) = ref_boundary(2*28*2^k, 0.02, delta_k);
  * ref_M(bits): M(i) = max(M(i-1), bd_k(i)[b_i]);  T5_ref = min(M, min_n (fmin_n + D_n) - 1);
  * audit of lr5, the RGL5 supports / certificates / summary entries and prefix28_rgl5 (GLS e1); the v0210 mutation test.

Case format (brute.case.v21_0) = brute.case.v20_0 (v0200_reference docstring) plus
  lr5 = {delta_L, delta_a, D, epochs [{k, H, B, delta 'p/q'}], epoch [k per step], M [per step], T, attain, witnesses,
         witness_unknowns, witness_calls};
  noisy.RGL5 (m = lr5.T); certifiers.RGL5; summary entries RGL5;
  prefix28_rgl5 (eps 0.02 only) = {actions 28, m, support, unknown, lr5, certifier, identical}.
"""
from __future__ import annotations
import copy,random
from fractions import Fraction
from concurrent.futures import ProcessPoolExecutor
from experiments.brute_common import check,VerificationError
from experiments.v0120_reference import steps_sp8
from experiments.v0160_reference import _cmp
from experiments.v0170_reference import ref_boundary,costs_tables,supports_for,audit_support,ref_cert,readings_main,prefix_counts
import experiments.v0200_reference as R20
from experiments.v0200_reference import fmin_tables,ref_D,sim_flips,flip_array,_windows

STEPS=88;READINGS=89;SLOTS=176;LATE=(45,88);EARLY=28;PREFIX=28;H0=28
EPS_BAR=0.02;DELTA=0.01;DELTA_L=0.005;DELTA_A=0.005
NEW_ARM='RGL5'


def ref_delta(k):return Fraction(1,200)/((k+1)*(k+2))


def ref_epoch(i):
    """epoch of 1-based step i: 0 for i <= 28, else least k with i <= 28*2^k."""
    check(isinstance(i,int) and i>=1,'step');k=0
    while i>H0*2**k:k+=1
    return k


def ref_epochs(T=STEPS):
    return [{'k':k,'H':H0*2**k,'B':2*H0*2**k,'delta':str(ref_delta(k))} for k in range(ref_epoch(T)+1)]


_BD={}
def ref_bd(k):
    if k not in _BD:_BD[k]=ref_boundary(2*H0*2**k,EPS_BAR,ref_delta(k))
    return _BD[k]


def ref_M(bits,T):
    """M per step (index i = step i+1, readings 0..i, b = bits[i])."""
    out=[];m=0
    for i in range(T):
        k=ref_epoch(i+1);bd=ref_bd(k);check(bits[i]<len(bd),'bits within B_k');m=max(m,bd[bits[i]]);out.append(m)
    return out


def arms_for(eps,block='main'):return ('RG4','RGL4','RGL5','RGNA4','RGN4_or')+(('RGNB4',) if eps==0.02 else ())
def noisy_for(eps,block='main'):return tuple(a for a in arms_for(eps,block) if a!='RG4')


def audit_lr5(lr,init,acts,obss,bits,where='lr5'):
    T=len(acts);Ds=ref_D();check(lr['D']==Ds,where+' D');check(lr['delta_L']==DELTA_L and lr['delta_a']==DELTA_A,where+' deltas')
    check(lr['epochs']==ref_epochs(T),where+' epochs');check(lr['epoch']==[ref_epoch(i+1) for i in range(T)],where+' epoch per step')
    M=ref_M(bits,T);check(lr['M']==M,where+' stitched margin M')
    fm={n:fmin_tables(n,init,acts,obss) for n in (1,2,3,4)}
    Tr=[min(M[i],min(fm[n][i]+Ds[n-1] for n in (1,2,3,4))-1) for i in range(T)]
    got=lr['T'];check(len(got)==T and len(lr['witnesses'])==T and len(lr['witness_unknowns'])==T and len(lr['attain'])==T,where+' lengths')
    cu=0
    for i in range(T):
        cu+=lr['witness_unknowns'][i];W=lr['witnesses'][i]
        for w in W:
            f=sim_flips(w,init,acts[:i],obss[:i]);check(f<=w['w'],f'{where} step {i+1} witness n={w["n"]} flips {f} > {w["w"]}')
            check(w['w']>=fm[w['n']][i],f'{where} step {i+1} witness below fmin')
        want=min([M[i]]+[w['w']+Ds[w['n']-1]-1 for w in W]);check(got[i]==want,f'{where} step {i+1} T {got[i]} != witness rule {want}')
        at=W[-1]['n'] if W and want<M[i] else None;check(lr['attain'][i]==at,f'{where} step {i+1} attain')
        if cu==0:check(got[i]==Tr[i],f'{where} step {i+1} T {got[i]} != T5_ref {Tr[i]}')
        else:check(got[i]>=Tr[i],f'{where} step {i+1} T {got[i]} < T5_ref {Tr[i]}')
        if i:check(got[i]>=got[i-1],where+' T monotone')
    return got,M,Tr


RGL5_KEYS=('lr5','prefix28_rgl5')


def strip(c):
    """The brute.case.v20_0 view: RGL5 fields and entries removed (for the frozen v0200 audit)."""
    d={k:v for k,v in c.items() if k not in RGL5_KEYS};d['schema']='brute.case.v20_0'
    d['noisy']={a:v for a,v in c['noisy'].items() if a!=NEW_ARM};d['certifiers']={a:v for a,v in c['certifiers'].items() if a!=NEW_ARM}
    d['summary']={k:{a:x for a,x in v.items() if a!=NEW_ARM} for k,v in c['summary'].items()}
    return d


def _arm_summary(S,cert):
    W=_windows(cert['trace']);late=W[1];early=W[2]
    return {'certificates':cert['certificates'],'false':cert['false_certificates'],'case_false':cert['false_certificates']>0,
            'coverage':round(cert['certificates']/SLOTS,6),'certificates_late':late,'coverage_late':round(late/(2*(LATE[1]-LATE[0]+1)),6),
            'certificates_early28':early,'coverage_early28':round(early/(2*EARLY),6),'per_step':W[0],'first_cert_step':cert['first_cert_step']}


def audit_prefix5(c,S,bits,burn):
    p=c['prefix28_rgl5'];check(p['actions']==PREFIX,'prefix28_rgl5 length');S28=S[:PREFIX]
    init=tuple(c['initial_visible']);acts=[s['a'] for s in S28];obss=[s['obs'] for s in S28]
    T,_,_=audit_lr5(p['lr5'],init,acts,obss,bits,'prefix28_rgl5 lr5');check(p['m']==T,'prefix28_rgl5 m')
    audit_support(p,supports_for(costs_tables(init,acts,obss),T,2),'prefix28_rgl5',2)
    _cmp(p['certifier'],ref_cert([(s['t'],s['a']) for s in S28],[s['act'] for s in S28],p['support'],T,burn,2),'prefix28_rgl5 certifier')
    full=c['noisy'][NEW_ARM];ft=c['certifiers'][NEW_ARM]['trace'][:PREFIX]
    same=(p['support']==full['support'][:PREFIX] and p['unknown']==full['unknown'][:PREFIX] and p['m']==full['m'][:PREFIX]
          and [r['certificate'] for r in p['certifier']['trace']]==[r['certificate'] for r in ft])
    check(p['identical']==same,'prefix28_rgl5 identical flag')
    return same


def audit_main(c,plan=None):
    check(c['schema']=='brute.case.v21_0','schema')
    R20.audit_main(strip(c),plan)          # every carried arm, frozen reference
    burn=c['burn_in'];S=steps_sp8(c);F=flip_array(c['seed'],c['eps'])
    bits,_,_=prefix_counts(readings_main(c),F)
    init=tuple(c['initial_visible']);acts=[s['a'] for s in S];obss=[s['obs'] for s in S]
    T5,_,_=audit_lr5(c['lr5'],init,acts,obss,bits)
    rec=c['noisy'][NEW_ARM];check(rec['m']==T5,'RGL5 m');audit_support(rec,supports_for(costs_tables(init,acts,obss),T5,2),NEW_ARM,2)
    exp=ref_cert([(s['t'],s['a']) for s in S],[s['act'] for s in S],rec['support'],T5,burn,2);_cmp(c['certifiers'][NEW_ARM],exp,NEW_ARM)
    want=_arm_summary(S,exp)
    for k,v in want.items():check(c['summary'][k][NEW_ARM]==v,f'summary {k} RGL5')
    check(sorted(c['noisy'])==sorted(noisy_for(c['eps'])),'noisy arm set (v21)');check(sorted(c['certifiers'])==sorted(arms_for(c['eps'])),'certifier arm set (v21)')
    want28=c['eps']==0.02;check(('prefix28_rgl5' in c)==want28,'prefix28_rgl5 present iff eps 0.02')
    if want28:audit_prefix5(c,S,bits,burn)


def audit_case(c,plan=None):
    try:audit_main(c,plan);return True,None
    except (VerificationError,KeyError,IndexError,TypeError,ValueError,AssertionError,ZeroDivisionError) as exc:
        return False,f'{type(exc).__name__}: {exc}'


def _job(x):
    i,c,plan=x;return i,audit_case(c,plan)


def count(cases,plan=None,workers=1):
    jobs=[(i,c,plan) for i,c in enumerate(cases)]
    if workers<=1:outs=[_job(j) for j in jobs]
    else:
        with ProcessPoolExecutor(workers) as ex:outs=list(ex.map(_job,jobs,chunksize=1))
    return [{'case':i,'family':cases[i]['family'],'seed':cases[i]['seed'],'eps':cases[i]['eps'],'first_difference':m}
            for i,(ok,m) in sorted(outs) if not ok]


# ------------------------------------------------------------------ mutation test (GS_ref10)
KINDS=('support5','support5','rgl5_cert','rgl5_cert','wrong5','counts5','T5','T5','M','epoch','epochs_delta','witness5','attain5',
       'prefix28_rgl5','support','rgl_cert','T','B','flips','observed')


def _slots(rec):
    return [(i,b) for i in range(len(rec['support'])) for b in (0,1) if rec['support'][i][b] is not None and rec['unknown'][i][b]==0]


def mutate(cases,k=20,rng_seed=20261029):
    """k single-field errors in k distinct cases (KINDS, shuffled); kinds that need a feature go to cases that have it."""
    check(k==len(KINDS),'k must equal len(KINDS)');rng=random.Random(rng_seed)
    mi=[i for i,c in enumerate(cases) if c.get('schema')=='brute.case.v21_0'];check(len(mi)>=k,'too few cases for the mutation test')
    kinds=list(KINDS);rng.shuffle(kinds);picks=rng.sample(mi,k)
    need={'prefix28_rgl5':lambda c:'prefix28_rgl5' in c,'witness5':lambda c:any(c['lr5']['witnesses']),
          'attain5':lambda c:any(a is not None for a in c['lr5']['attain']),
          'support5':lambda c:bool(_slots(c['noisy'][NEW_ARM])),'support':lambda c:bool(_slots(c['noisy']['RGL4']))}
    for j,kind in enumerate(kinds):
        ok=need.get(kind)
        if ok and not ok(cases[picks[j]]):
            el=[i for i in mi if ok(cases[i]) and i not in picks];check(el,f'no case for the {kind} mutation');picks[j]=rng.choice(el)
    out=list(cases);inj=set()
    for i,kind in zip(picks,kinds):
        c=copy.deepcopy(cases[i]);lr=c['lr5']
        if kind in ('support5','support'):
            rec=c['noisy'][NEW_ARM if kind=='support5' else 'RGL4'];s,b=rng.choice(_slots(rec));v=rec['support'][s][b]
            rec['support'][s][b]=v[1:] if len(v)>1 else [(v[0]+1)%4]
        elif kind in ('rgl5_cert','rgl_cert','wrong5'):
            arm='RGL4' if kind=='rgl_cert' else NEW_ARM;r=c['certifiers'][arm]['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            if kind=='wrong5':r['wrong'][b]=not r['wrong'][b]
            else:r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        elif kind=='counts5':c['certifiers'][NEW_ARM][rng.choice(('false_certificates','certificates'))]+=1
        elif kind=='T5':j=rng.randrange(len(lr['T']));lr['T'][j]+=rng.choice((-1,1))
        elif kind=='T':j=rng.randrange(len(c['lr']['T']));c['lr']['T'][j]+=rng.choice((-1,1))
        elif kind=='M':j=rng.randrange(len(lr['M']));lr['M'][j]+=1
        elif kind=='epoch':j=rng.randrange(len(lr['epoch']));lr['epoch'][j]+=1
        elif kind=='epochs_delta':e=rng.choice(lr['epochs']);e['delta']=str(Fraction(e['delta'])*2)
        elif kind=='witness5':
            j=rng.choice([j for j,W in enumerate(lr['witnesses']) if W]);lr['witnesses'][j][-1]['w']-=1
        elif kind=='attain5':
            j=rng.choice([j for j,a in enumerate(lr['attain']) if a is not None]);lr['attain'][j]=None
        elif kind=='prefix28_rgl5':
            p=c['prefix28_rgl5'];r=p['certifier']['trace'][rng.randrange(PREFIX)];b=rng.randrange(2)
            r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        elif kind in ('B','flips'):c[{'B':'B','flips':'realized_flips'}[kind]]+=1
        elif kind=='observed':
            Rd=[c['initial_visible']]+[r['observed'] for r in c['arms']['SP8']['trace']]
            cand=[(t,j) for t,o in enumerate(Rd) for j in (0,1) if o[j] is not None];t,j=rng.choice(cand);Rd[t][j]=1-Rd[t][j]
        out[i]=c;inj.add(i)
    return out,inj
