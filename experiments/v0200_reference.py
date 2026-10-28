"""Second implementation (same author, no `brute` import) for study BRUTE-0200-LR-ANYTIME-023 (GS_ref10, GLV, GLR (e)).

Written from experiments/BRUTE_PLAN_023.json and docs/research/v0.20.0/LR_LEMMA_023.md BEFORE brute/lrregion.py,
brute/api/certify9.py and experiments/brute_study_023.py existed. NOT an independent or third-party audit: same author.
REUSES the frozen reference functions of v0170_reference (costs_tables, supports_for, audit_support, ref_cert,
ref_boundary, prefix_counts, first_crossing, readings_main), v0160_reference (ref_m, _cmp, mism), v0120_reference
(steps_sp8, ref_rg) and v0190_reference (ref_anytime_boundary). New here:
  * fmin_tables(n, ...): the exact least flip count over every n-state machine (start state 0, all n^(2n) transition
    tables, per-state optimal emission), per step, by numpy enumeration, for every n = 1..4 (stronger than the plan's
    "exhaustive n <= 3 + witness recheck for n = 4"; both are done);
  * ref_D(): D_n in exact integers; ref_T: T_ref = min(m_a(b; 0.02, 0.005), min_n (fmin_n + D_n) - 1);
  * witness re-simulation; the tag-23 flip array; the 023 arm sets; the RGL4 28-action prefix control.

Case format (brute.case.v20_0): the brute.case.v19_0 main keys without perbit (88 actions, 89 readings, B, m, boundary,
prefix_bits, prefix_flips, realized_flips, crossing, crossing_bit, anytime_boundary (m_a at delta 0.01, RGNA4),
anytime_crossing, anytime_crossing_bit, flip_positions_EVALUATOR_ONLY, initial_visible, initial_latent_EVALUATOR_ONLY,
arms.SP8, bounded['4']) plus
  lr = {delta_L 0.005, delta_a 0.005, D [D_1..D_4], anytime_boundary (m_a at delta 0.005, 0..B), anytime_crossing_bit,
        T [per step], attain [n or None], witnesses [[{n, w, d, e}] per step], witness_unknowns [per step]};
  noisy[RGL4 (m = T) | RGNA4 | RGN4_or | RGNB4 (eps 0.02 main only)]; certifiers RG4 / RGL4 / RGNA4 / RGN4_or (+ RGNB4);
  prefix28 (eps 0.02 only): RGL4 on the first 28 actions (m, T, support, unknown, certifier, identical); summary.
"""
from __future__ import annotations
import copy,random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
from experiments.brute_common import check,VerificationError
from experiments.v0120_reference import steps_sp8,ref_rg,CENSOR
from experiments.v0160_reference import ref_m,_cmp,mism
from experiments.v0170_reference import (ref_boundary,prefix_counts,first_crossing,costs_tables,supports_for,audit_support,
                                         ref_cert,readings_main)
from experiments.v0190_reference import ref_anytime_boundary

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_023.json'
N=4;STEPS=88;READINGS=89;SLOTS=176;LATE=(45,88);EARLY=28;PREFIX=28
EPS_BAR=0.02;DELTA=0.01;DELTA_L=0.005;DELTA_A=0.005
H={1:4,2:512,3:139968,4:67108864}


def ref_D():
    """least D with 49^D >= 4 |H_n| / 0.005 (exact integers: 49^D * 5 >= 4 |H_n| * 1000)."""
    out=[]
    for n in (1,2,3,4):
        h=n*n**(2*n)*4**n;check(h==H[n],'|H_n|');D=0
        while 49**D*5<4*h*1000:D+=1
        out.append(D)
    return out


def arms_for(eps,block='main'):
    return ('RG4','RGL4','RGNA4','RGN4_or')+(('RGNB4',) if eps==0.02 and block=='main' else ())


def noisy_for(eps,block='main'):return tuple(a for a in arms_for(eps,block) if a!='RG4')


def flip_array(seed,eps):return np.random.default_rng([seed,round(1000*eps),23]).random((READINGS,2))<eps


def fmin_tables(n,init,acts,obss):
    """Per step i (readings 0..i): least flips over every n-state machine with start 0 (exact enumeration)."""
    nt=n**(2*n);idx=np.arange(nt,dtype=np.int64);D=np.zeros((nt,n,2),dtype=np.int64)
    for q in range(n):
        for a in range(2):D[:,q,a]=(idx//n**(2*q+a))%n
    ar=np.arange(nt);st=np.zeros(nt,dtype=np.int64);C=np.zeros((nt,n,4),dtype=np.int64);C[ar,st]+=mism(init);out=[]
    for a,o in zip(acts,obss):
        out.append(int(C.min(axis=2).sum(axis=1).min()))
        st=D[ar,st,a];C[ar,st]+=mism(o)
    return out


def ref_T(fm,ma,Ds):
    """T_ref per step = min(m_a, min_n (fmin_n + D_n) - 1)."""
    return [min(ma[i],min(fm[n][i]+Ds[n-1] for n in (1,2,3,4))-1) for i in range(len(ma))]


def sim_flips(w,init,acts,obss):
    """flips of the recorded machine (start 0) on readings 0..len(acts)."""
    d=w['d'];e=w['e'];n=w['n'];check(len(d)==n==len(e) and all(len(r)==2 and all(0<=x<n for x in r) for r in d),'witness shape')
    check(all(0<=c<4 for c in e),'witness emission');q=0;f=int(mism(init)[e[0]])
    for a,o in zip(acts,obss):q=d[q][a];f+=int(mism(o)[e[q]])
    return f


def audit_lr(lr,init,acts,obss,bits,B,where='lr'):
    """GS_ref10 on the RGL4 bound; returns T."""
    T=len(acts);Ds=ref_D();check(lr['D']==Ds,where+' D');check(lr['delta_L']==DELTA_L and lr['delta_a']==DELTA_A,where+' deltas')
    ba=ref_anytime_boundary(B,EPS_BAR,DELTA_A);check(lr['anytime_boundary']==ba,where+' anytime boundary (0.005)')
    ma=[ba[bits[i]] for i in range(T)]
    fm={n:fmin_tables(n,init,acts,obss) for n in (1,2,3,4)}
    lo4=[lo for _,lo in costs_tables(tuple(init),acts,obss)];check(fm[4]==lo4,'fmin_4 vs frozen costs_tables')
    Tr=ref_T(fm,ma,Ds);got=lr['T'];check(len(got)==T and len(lr['witnesses'])==T and len(lr['witness_unknowns'])==T,where+' lengths')
    cu=0
    for i in range(T):
        cu+=lr['witness_unknowns'][i];W=lr['witnesses'][i]
        for w in W:
            f=sim_flips(w,init,acts[:i],obss[:i]);check(f<=w['w'],f'{where} step {i+1} witness n={w["n"]} flips {f} > {w["w"]}')
            check(w['w']>=fm[w['n']][i],f'{where} step {i+1} witness below fmin')
        want=min([ma[i]]+[w['w']+Ds[w['n']-1]-1 for w in W]);check(got[i]==want,f'{where} step {i+1} T {got[i]} != witness rule {want}')
        at=W[-1]['n'] if W and want<ma[i] else None;check(lr['attain'][i]==at,f'{where} step {i+1} attain')
        if cu==0:check(got[i]==Tr[i],f'{where} step {i+1} T {got[i]} != T_ref {Tr[i]}')
        else:check(got[i]>=Tr[i],f'{where} step {i+1} T {got[i]} < T_ref {Tr[i]}')
        if i:check(got[i]>=got[i-1],where+' T monotone')
    return got,ma,Tr


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
    bl=ref_anytime_boundary(B,EPS_BAR,DELTA_A);check(c['lr']['anytime_crossing_bit']==first_crossing(seq,bl),'lr anytime crossing')
    fp=[[t,j] for t,(obs,_) in enumerate(R) for j,o in enumerate(obs) if o is not None and F[t,j]]
    check(c['flip_positions_EVALUATOR_ONLY']==fp,'flip positions')
    return B,flips[-1],bd,ba,bits


def _windows(trace):
    per=[sum(x is not None for x in r['certificate']) for r in trace]
    late=sum(p for r,p in zip(trace,per) if LATE[0]<=r['step']<=LATE[1]);early=sum(p for r,p in zip(trace,per) if r['step']<=EARLY)
    return per,late,early


def ref_summary(S,exp,arms):
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
            'first_cert_step':dict({a:exp[a]['first_cert_step'] for a in arms},SP8=f0)}


def audit_prefix(c,S,bits,burn,B):
    """GLR (e): the recorded 28-action RGL4 run equals the reference on the prefix and the 88-step run on 1..28."""
    p=c['prefix28'];check(p['actions']==PREFIX,'prefix length');S28=S[:PREFIX]
    init=tuple(c['initial_visible']);acts=[s['a'] for s in S28];obss=[s['obs'] for s in S28]
    T,_,_=audit_lr(p['lr'],init,acts,obss,bits,B,'prefix28 lr');check(p['m']==T,'prefix28 m')
    audit_support(p,supports_for(costs_tables(init,acts,obss),T,2),'prefix28',2)
    _cmp(p['certifier'],ref_cert([(s['t'],s['a']) for s in S28],[s['act'] for s in S28],p['support'],T,burn,2),'prefix28 certifier')
    full=c['noisy']['RGL4'];ft=c['certifiers']['RGL4']['trace'][:PREFIX]
    same=(p['support']==full['support'][:PREFIX] and p['unknown']==full['unknown'][:PREFIX] and p['m']==full['m'][:PREFIX]
          and [r['certificate'] for r in p['certifier']['trace']]==[r['certificate'] for r in ft])
    check(p['identical']==same,'prefix28 identical flag')
    return same


def audit_main(c,plan):
    check(c['schema']=='brute.case.v20_0','schema')
    check(c['steps']==STEPS and c['burn_in']==8 and c['mask_rate']==0.35,'case constants (as study-021)')
    check(c['eps'] in (0.0,0.01,0.02,0.05),'eps level');check(c['eps_bar']==EPS_BAR and c['delta']==DELTA,'eps_bar / delta')
    block=c.get('block','main');check(block in ('main','stress'),'block');check((block=='stress')==(c['eps']==0.05),'stress iff eps 0.05')
    arms=arms_for(c['eps'],block);noisy=noisy_for(c['eps'],block)
    burn=c['burn_in'];S=steps_sp8(c);check(len(S)==STEPS,'SP8 steps')
    B,flips,bd,ba,bits=audit_noise_common(c,readings_main(c))
    init=tuple(c['initial_visible']);acts=[s['a'] for s in S];obss=[s['obs'] for s in S]
    costs=costs_tables(init,acts,obss)
    T=len(S);mb=[bd[bits[i]] for i in range(T)];ma=[ba[bits[i]] for i in range(T)]
    TL,_,_=audit_lr(c['lr'],init,acts,obss,bits,B)
    ms={'RGL4':TL,'RGNA4':ma,'RGNB4':mb,'RGN4_or':[flips]*T};mrec={'RGL4':TL,'RGNA4':ma,'RGNB4':mb,'RGN4_or':flips}
    check(sorted(c['noisy'])==sorted(noisy),'noisy arm set');exp={}
    audit_support(c['bounded']['4'],supports_for(costs,[0]*T,2),'bounded 4',2)
    truth=[s['act'] for s in S];st=[(s['t'],s['a']) for s in S]
    for arm in noisy:
        rec=c['noisy'][arm];check(rec['m']==mrec[arm],f'{arm} m');audit_support(rec,supports_for(costs,ms[arm],2),arm,2)
        exp[arm]=ref_cert(st,truth,rec['support'],mrec[arm],burn,2)
    exp['RG4']=ref_rg(S,c['bounded'],4,burn)
    check(sorted(c['certifiers'])==sorted(arms),'certifier arm set')
    for arm in arms:_cmp(c['certifiers'][arm],exp[arm],arm)
    check(c['summary']==ref_summary(S,exp,arms),'summary')
    want28=c['eps']==0.02 and block=='main';check(('prefix28' in c)==want28,'prefix28 present iff eps 0.02 main')
    if want28:audit_prefix(c,S,bits,burn,B)


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


# ------------------------------------------------------------------ mutation test (GS_ref10)
KINDS=('support','support','rgl_cert','rgl_cert','rgn_cert','rg4_cert','wrong','counts','T','T','witness','attain','lr_boundary',
       'B','flips','boundary','anytime','crossing','observed','prefix28')


def _slots(rec):
    return [(i,b) for i in range(len(rec['support'])) for b in (0,1) if rec['support'][i][b] is not None and rec['unknown'][i][b]==0]


def mutate(cases,k=20,rng_seed=20261028):
    """k single-field errors in k distinct cases (KINDS, shuffled); witness / prefix28 errors go to cases that have them."""
    check(k==len(KINDS),'k must equal len(KINDS)');rng=random.Random(rng_seed)
    mi=[i for i,c in enumerate(cases) if c.get('schema')=='brute.case.v20_0'];check(len(mi)>=k,'too few cases for the mutation test')
    kinds=list(KINDS);rng.shuffle(kinds);picks=rng.sample(mi,k)
    need={'prefix28':lambda c:'prefix28' in c,'witness':lambda c:any(c['lr']['witnesses']),
          'attain':lambda c:any(a is not None for a in c['lr']['attain'])}
    for kind,ok in need.items():
        j=kinds.index(kind)
        if not ok(cases[picks[j]]):
            el=[i for i in mi if ok(cases[i]) and i not in picks];check(el,f'no case for the {kind} mutation');picks[j]=rng.choice(el)
    out=list(cases);inj=set()
    for i,kind in zip(picks,kinds):
        c=copy.deepcopy(cases[i]);blk=c.get('block','main');NA=noisy_for(c['eps'],blk);AR=arms_for(c['eps'],blk);lr=c['lr']
        if kind=='support':
            rec=c['noisy']['RGL4'] if rng.random()<0.5 else c['noisy'][rng.choice(NA)]
            for alt in (c['noisy']['RGL4'],c['bounded']['4']):
                if not _slots(rec):rec=alt
            s,b=rng.choice(_slots(rec));v=rec['support'][s][b];rec['support'][s][b]=v[1:] if len(v)>1 else [(v[0]+1)%4]
        elif kind in ('rgl_cert','rgn_cert','rg4_cert','wrong'):
            arm={'rgl_cert':'RGL4','rgn_cert':rng.choice([a for a in NA if a!='RGL4']),'rg4_cert':'RG4'}.get(kind) or rng.choice(AR)
            r=c['certifiers'][arm]['trace'][rng.randrange(c['steps'])];b=rng.randrange(2)
            if kind=='wrong':r['wrong'][b]=not r['wrong'][b]
            else:r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        elif kind=='counts':c['certifiers'][rng.choice(AR)][rng.choice(('false_certificates','certificates'))]+=1
        elif kind=='T':j=rng.randrange(len(lr['T']));lr['T'][j]+=rng.choice((-1,1))
        elif kind=='witness':
            j=rng.choice([j for j,W in enumerate(lr['witnesses']) if W]);w=lr['witnesses'][j][-1];w['w']-=1
        elif kind=='attain':
            j=rng.choice([j for j,a in enumerate(lr['attain']) if a is not None]);lr['attain'][j]=None
        elif kind=='lr_boundary':j=rng.randrange(1,len(lr['anytime_boundary']));lr['anytime_boundary'][j]+=1
        elif kind in ('B','flips'):c[{'B':'B','flips':'realized_flips'}[kind]]+=1
        elif kind=='boundary':j=rng.randrange(1,len(c['boundary']));c['boundary'][j]+=1
        elif kind=='anytime':j=rng.randrange(1,len(c['anytime_boundary']));c['anytime_boundary'][j]+=1
        elif kind=='crossing':c['crossing']=not c['crossing']
        elif kind=='prefix28':
            p=c['prefix28'];r=p['certifier']['trace'][rng.randrange(PREFIX)];b=rng.randrange(2)
            r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
        elif kind=='observed':
            R=[c['initial_visible']]+[r['observed'] for r in c['arms']['SP8']['trace']]
            cand=[(t,j) for t,o in enumerate(R) for j in (0,1) if o[j] is not None];t,j=rng.choice(cand);R[t][j]=1-R[t][j]
        out[i]=c;inj.add(i)
    return out,inj
