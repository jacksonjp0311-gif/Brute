"""Second implementation (same author, no `brute` import) for study BRUTE-0220-BETTING-CS-025 (GS_ref11, GLV, GBC (e)).

Written from experiments/BRUTE_PLAN_025.json, experiments/BRUTE_PLAN_025_A1.json and
docs/research/v0.22.0/BETTING_LEMMA_025.md BEFORE brute/bettingregion.py, brute/api/certify11.py and
experiments/brute_study_025.py existed. NOT an independent or third-party audit: same author.
REUSES the frozen v0210_reference (audit_lr5, audit_prefix5), v0200_reference (audit_noise_common, audit_lr, audit_prefix,
fmin_tables, sim_flips, flip_array, ref_summary), v0190_reference (ref_anytime_boundary) and v0170_reference
(costs_tables, supports_for, audit_support, ref_cert, readings_main, prefix_counts). New here:
  * ref_levels(): p_j, delta_Lj, delta_cj and D^j_n in exact integers; ref_lambdas(p); ref_K(j, t, b) exact Fraction;
  * audit_b6: m_a0 at delta 1/400, T0 (level-0 witness rule), sticky activation K_j(T0(i'), b(i')) >= 800 for i' <= i,
    D_eff, T6 (witness rule with D_eff), eps_hat_u, against T_ref = min(m_a0, min_n (fmin_n + D_eff_n) - 1);
  * the study-025 arm sets (RGNA4 is not a study-025 arm), prefix28_rgb6, and the v0220 mutation test.

Case format (brute.case.v22_0) = brute.case.v21_0 (v0210_reference docstring) WITHOUT the RGNA4 entries in noisy /
certifiers / summary (the case-level anytime_boundary fields are kept), plus
  b6 = {delta '1/100', delta_a0 '1/400', levels [{j, p 'a/b', delta_L 'a/b', delta_c 'a/b' or None, D [4]}],
        lambdas {j: ['a/b' x4]}, anytime_boundary (m_a0, 0..B), M [m_a0 per step], T0 [per step], T [per step],
        active [[j...] per step], eps_hat_u ['a/b' per step], K {j: [float(K_j(T0, b)) rounded 6 per step]},
        attain, witnesses, witness_unknowns, witness_calls};
  noisy.RGB6 (m = b6.T); certifiers.RGB6; summary entries RGB6;
  prefix28_rgb6 (eps 0.02 only) = {actions 28, m, support, unknown, b6, certifier, identical}.
"""
from __future__ import annotations
import copy,random
from fractions import Fraction as Fr
from concurrent.futures import ProcessPoolExecutor
from experiments.brute_common import check,VerificationError
from experiments.v0120_reference import steps_sp8,ref_rg
from experiments.v0160_reference import _cmp
from experiments.v0170_reference import costs_tables,supports_for,audit_support,ref_cert,readings_main,prefix_counts
from experiments.v0190_reference import ref_anytime_boundary
import experiments.v0200_reference as R20
import experiments.v0210_reference as R21
from experiments.v0200_reference import fmin_tables,sim_flips,ref_summary

STEPS=88;READINGS=89;SLOTS=176;LATE=(45,88);EARLY=28;PREFIX=28
EPS_BAR=0.02;DELTA=Fr(1,100);DELTA_A0=Fr(1,400);THRESH=800
NEW_ARM='RGB6'
H={1:4,2:512,3:139968,4:67108864}
LEVELS=((0,Fr(1,50),Fr(1,400),None),(1,Fr(1,100),Fr(1,800),Fr(1,800)),(2,Fr(1,200),Fr(1,800),Fr(1,800)))


def ref_Dp(p,dL):
    """least D with ((1-p)/p)^D >= 4 |H_n| / dL, exact integers."""
    r=(1-p)/p;out=[]
    for n in (1,2,3,4):
        h=n*n**(2*n)*4**n;check(h==H[n],'|H_n|');D=0
        while r**D<4*h/dL:D+=1
        out.append(D)
    return out


def ref_levels():
    tot=DELTA_A0+sum(dL+(dc or 0) for _,_,dL,dc in LEVELS);check(tot==DELTA,'delta split sums to 1/100')
    check(DELTA_A0+sum(dc or 0 for *_,dc in LEVELS)==DELTA/2,'count/betting side delta/2')
    return [{'j':j,'p':str(p),'delta_L':str(dL),'delta_c':None if dc is None else str(dc),'D':ref_Dp(p,dL)} for j,p,dL,dc in LEVELS]


def ref_lambdas(p):return [Fr(l,4)/(1-p) for l in (1,2,3,4)]


def ref_K(p,t,b):
    check(0<=t,'count');u=max(b-t,0);return sum((1+l*p)**u*(1-l*(1-p))**min(t,b) for l in ref_lambdas(p))/4


def arms_for(eps,block='main'):return ('RG4','RGB6','RGL4','RGL5','RGN4_or')+(('RGNB4',) if eps==0.02 else ())
def noisy_for(eps,block='main'):return tuple(a for a in arms_for(eps,block) if a!='RG4')


def audit_b6(b6,init,acts,obss,bits,B,where='b6'):
    """GS_ref11 on the RGB6 bound; returns T6."""
    T=len(acts);L=ref_levels();check(b6['levels']==L,where+' levels');check(b6['delta']=='1/100' and b6['delta_a0']=='1/400',where+' deltas')
    check(b6['lambdas']=={str(j):[str(x) for x in ref_lambdas(p)] for j,p,_,dc in LEVELS if dc},where+' lambdas')
    ba=ref_anytime_boundary(B,EPS_BAR,DELTA_A0);check(b6['anytime_boundary']==ba,where+' anytime boundary (1/400)')
    ma=[ba[bits[i]] for i in range(T)];check(b6['M']==ma,where+' M')
    D={l['j']:l['D'] for l in L};fm={n:fmin_tables(n,init,acts,obss) for n in (1,2,3,4)}
    for k in ('T0','T','active','eps_hat_u','attain','witnesses','witness_unknowns'):check(len(b6[k])==T,f'{where} {k} length')
    act=set();cu=0;T0=b6['T0'];got=b6['T']
    for i in range(T):
        cu+=b6['witness_unknowns'][i];W=b6['witnesses'][i]
        for w in W:
            f=sim_flips(w,init,acts[:i],obss[:i]);check(f<=w['w'],f'{where} step {i+1} witness n={w["n"]} flips {f} > {w["w"]}')
            check(w['w']>=fm[w['n']][i],f'{where} step {i+1} witness below fmin')
        t0=min([ma[i]]+[w['w']+D[0][w['n']-1]-1 for w in W]);check(T0[i]==t0,f'{where} step {i+1} T0 {T0[i]} != witness rule {t0}')
        t0r=min(ma[i],min(fm[n][i]+D[0][n-1] for n in (1,2,3,4))-1);check(T0[i]>=t0r,f'{where} step {i+1} T0 below T0_ref')
        for j,p,_,dc in LEVELS:
            if dc is None:continue
            K=ref_K(p,T0[i],bits[i]);check(b6['K'][str(j)][i]==round(float(K),6),f'{where} step {i+1} K_{j}')
            if K>=THRESH:act.add(j)
        check(b6['active'][i]==sorted(act),f'{where} step {i+1} active levels')
        lv=[0]+sorted(act);De=[min(D[j][n] for j in lv) for n in range(4)]
        check(b6['eps_hat_u'][i]==str(min(p for j,p,_,_ in LEVELS if j in lv)),f'{where} step {i+1} eps_hat_u')
        want=min([ma[i]]+[w['w']+De[w['n']-1]-1 for w in W]);check(got[i]==want,f'{where} step {i+1} T {got[i]} != witness rule {want}')
        at=W[-1]['n'] if W and want<ma[i] else None;check(b6['attain'][i]==at,f'{where} step {i+1} attain')
        Tr=min(ma[i],min(fm[n][i]+De[n-1] for n in (1,2,3,4))-1)
        if cu==0:check(got[i]==Tr,f'{where} step {i+1} T {got[i]} != T6_ref {Tr}')
        else:check(got[i]>=Tr,f'{where} step {i+1} T {got[i]} < T6_ref {Tr}')
        if cu==0 and not act:check(T0[i]==t0r,f'{where} step {i+1} T0 != T0_ref')
    return got


B6_KEYS=('b6','prefix28_rgb6')


def _arm_summary(S,cert):return R21._arm_summary(S,cert)


def audit_prefix6(c,S,bits,burn,B):
    p=c['prefix28_rgb6'];check(p['actions']==PREFIX,'prefix28_rgb6 length');S28=S[:PREFIX]
    init=tuple(c['initial_visible']);acts=[s['a'] for s in S28];obss=[s['obs'] for s in S28]
    T=audit_b6(p['b6'],init,acts,obss,bits,B,'prefix28_rgb6 b6');check(p['m']==T,'prefix28_rgb6 m')
    audit_support(p,supports_for(costs_tables(init,acts,obss),T,2),'prefix28_rgb6',2)
    _cmp(p['certifier'],ref_cert([(s['t'],s['a']) for s in S28],[s['act'] for s in S28],p['support'],T,burn,2),'prefix28_rgb6 certifier')
    full=c['noisy'][NEW_ARM];ft=c['certifiers'][NEW_ARM]['trace'][:PREFIX]
    same=(p['support']==full['support'][:PREFIX] and p['unknown']==full['unknown'][:PREFIX] and p['m']==full['m'][:PREFIX]
          and [r['certificate'] for r in p['certifier']['trace']]==[r['certificate'] for r in ft])
    check(p['identical']==same,'prefix28_rgb6 identical flag')
    return same


def audit_main(c,plan=None):
    check(c['schema']=='brute.case.v22_0','schema')
    check(c['steps']==STEPS and c['burn_in']==8 and c['mask_rate']==0.35,'case constants (as study-021)')
    check(c['eps'] in (0.0,0.01,0.02,0.05),'eps level');check(c['eps_bar']==EPS_BAR and c['delta']==0.01,'eps_bar / delta')
    block=c.get('block','main')
    if block in ('main','stress'):check((block=='stress')==(c['eps']==0.05),'stress iff eps 0.05')
    arms=arms_for(c['eps'],block);noisy=noisy_for(c['eps'],block)
    burn=c['burn_in'];S=steps_sp8(c);check(len(S)==STEPS,'SP8 steps')
    B,flips,bd,ba,bits=R20.audit_noise_common(c,readings_main(c))
    init=tuple(c['initial_visible']);acts=[s['a'] for s in S];obss=[s['obs'] for s in S]
    costs=costs_tables(init,acts,obss);T=len(S);mb=[bd[bits[i]] for i in range(T)]
    TL,_,_=R20.audit_lr(c['lr'],init,acts,obss,bits,B)
    T5,_,_=R21.audit_lr5(c['lr5'],init,acts,obss,bits)
    T6=audit_b6(c['b6'],init,acts,obss,bits,B)
    ms={'RGL4':TL,'RGL5':T5,'RGB6':T6,'RGNB4':mb,'RGN4_or':[flips]*T};mrec={'RGL4':TL,'RGL5':T5,'RGB6':T6,'RGNB4':mb,'RGN4_or':flips}
    check(sorted(c['noisy'])==sorted(noisy),'noisy arm set (v22)');exp={}
    audit_support(c['bounded']['4'],supports_for(costs,[0]*T,2),'bounded 4',2)
    truth=[s['act'] for s in S];st=[(s['t'],s['a']) for s in S]
    for arm in noisy:
        rec=c['noisy'][arm];check(rec['m']==mrec[arm],f'{arm} m');audit_support(rec,supports_for(costs,ms[arm],2),arm,2)
        exp[arm]=ref_cert(st,truth,rec['support'],mrec[arm],burn,2)
    exp['RG4']=ref_rg(S,c['bounded'],4,burn)
    check(sorted(c['certifiers'])==sorted(arms),'certifier arm set (v22)')
    for arm in arms:_cmp(c['certifiers'][arm],exp[arm],arm)
    check(c['summary']==ref_summary(S,exp,arms),'summary')
    want28=c['eps']==0.02
    for k in ('prefix28','prefix28_rgl5','prefix28_rgb6'):check((k in c)==want28,k+' present iff eps 0.02')
    if want28:R20.audit_prefix(c,S,bits,burn,B);R21.audit_prefix5(c,S,bits,burn);audit_prefix6(c,S,bits,burn,B)


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


# ------------------------------------------------------------------ mutation test (GS_ref11)
KINDS=('support6','support6','rgb6_cert','rgb6_cert','wrong6','counts6','T6','T6','T0','active','eps_hat','K','witness6','attain6',
       'prefix28_rgb6','support5','rgl5_cert','support','T','flips')


def _slots(rec):
    return [(i,b) for i in range(len(rec['support'])) for b in (0,1) if rec['support'][i][b] is not None and rec['unknown'][i][b]==0]


def mutate(cases,k=20,rng_seed=20261030):
    """k single-field errors in k distinct cases (KINDS, shuffled); kinds that need a feature go to cases that have it."""
    check(k==len(KINDS),'k must equal len(KINDS)');rng=random.Random(rng_seed)
    mi=[i for i,c in enumerate(cases) if c.get('schema')=='brute.case.v22_0'];check(len(mi)>=k,'too few cases for the mutation test')
    kinds=list(KINDS);rng.shuffle(kinds);picks=rng.sample(mi,k)
    need={'prefix28_rgb6':lambda c:'prefix28_rgb6' in c,'witness6':lambda c:any(c['b6']['witnesses']),
          'attain6':lambda c:any(a is not None for a in c['b6']['attain']),
          'support6':lambda c:bool(_slots(c['noisy'][NEW_ARM])),'support5':lambda c:bool(_slots(c['noisy']['RGL5'])),
          'support':lambda c:bool(_slots(c['noisy']['RGL4']))}
    for j,kind in enumerate(kinds):
        ok=need.get(kind)
        if ok and not ok(cases[picks[j]]):
            el=[i for i in mi if ok(cases[i]) and i not in picks];check(el,f'no case for the {kind} mutation');picks[j]=rng.choice(el)
    out=list(cases);inj=set()
    for i,kind in zip(picks,kinds):
        c=copy.deepcopy(cases[i]);b6=c['b6']
        if kind in ('support6','support5','support'):
            rec=c['noisy'][{'support6':NEW_ARM,'support5':'RGL5','support':'RGL4'}[kind]];s,b=rng.choice(_slots(rec));v=rec['support'][s][b]
            rec['support'][s][b]=v[1:] if len(v)>1 else [(v[0]+1)%4]
        elif kind in ('rgb6_cert','rgl5_cert','wrong6'):
            arm='RGL5' if kind=='rgl5_cert' else NEW_ARM;r=c['certifiers'][arm]['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            if kind=='wrong6':r['wrong'][b]=not r['wrong'][b]
            else:r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        elif kind=='counts6':c['certifiers'][NEW_ARM][rng.choice(('false_certificates','certificates'))]+=1
        elif kind=='T6':j=rng.randrange(len(b6['T']));b6['T'][j]+=rng.choice((-1,1))
        elif kind=='T0':j=rng.randrange(len(b6['T0']));b6['T0'][j]+=1
        elif kind=='T':j=rng.randrange(len(c['lr']['T']));c['lr']['T'][j]+=rng.choice((-1,1))
        elif kind=='active':j=rng.randrange(len(b6['active']));b6['active'][j]=sorted(set(b6['active'][j])^{1})
        elif kind=='eps_hat':j=rng.randrange(len(b6['eps_hat_u']));b6['eps_hat_u'][j]='1/200'
        elif kind=='K':j=rng.randrange(len(b6['K']['1']));b6['K']['1'][j]=round(b6['K']['1'][j]+0.5,6)
        elif kind=='witness6':
            j=rng.choice([j for j,W in enumerate(b6['witnesses']) if W]);b6['witnesses'][j][-1]['w']-=1
        elif kind=='attain6':
            j=rng.choice([j for j,a in enumerate(b6['attain']) if a is not None]);b6['attain'][j]=None
        elif kind=='prefix28_rgb6':
            p=c['prefix28_rgb6'];r=p['certifier']['trace'][rng.randrange(PREFIX)];b=rng.randrange(2)
            r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        elif kind=='flips':c['realized_flips']+=1
        out[i]=c;inj.add(i)
    return out,inj
