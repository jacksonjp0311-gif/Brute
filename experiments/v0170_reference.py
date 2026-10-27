"""Second implementation (same author, no `brute` import) for study BRUTE-0170-SEQUENTIAL-MARGIN-019 (GS_ref7, GLV).

Written from experiments/BRUTE_PLAN_019.json (sequential_margin, alphabet3_block, arms, metrics) and
docs/research/BRUTE_DEVIATIONS_019.md (#101) BEFORE brute/seqmargin.py, brute/region3.py and brute/api/certify7.py
existed. NOT an independent or third-party audit: same author.

Method (#101 item 7). Per Moore machine (complete, <= 4 states, start state 0) and trajectory, C[q][c] = number of
OBSERVED bits, over the readings taken in state q, that differ from code c's bit; the least number of flips under which
(machine, emissions) explains readings 0..i with next code c after action b (next state r) is
  cost_b(c) = C[r][c] + sum_{q != r} min_c' C[q][c'],
and the least cost overall is lo_i = sum_q min_c C[q][c]. A region with bound m_i at step i has support
{c : min over machines cost_b(c) <= m_i}; it is empty iff lo_i > m_i, and emptiness is sticky (#101 item 3):
support None at step i iff lo_j > m_j for some j <= i. Arms: m_i = 0 (RG4 / RGNB4_0 / RG4_3), m (RGN4 / RGN4_3),
realized flips (RGN4_or), boundary m(b_i) (RGNB4 / RGNB4_3; b_i = observed bits in readings 0..i).
  k = 2: every transition table (4**8, numpy) as v0160_reference.
  k = 3: canonical partial machines (states numbered by first visit); an undefined transition branches to each used
         state or one new state; pruned when lo > the largest bound any audited arm uses (exact: costs never decrease).

Case formats (the runner writes these keys; '*wall_informational*' keys are ignored):
  main (brute.case.v17_0): the study-018 keys plus 'boundary' (m(0..B)), 'prefix_bits' / 'prefix_flips' (cumulative over
    readings 0..t, 45 entries), 'crossing', 'crossing_bit' (first bit b with running flips > m(b), else None);
    noisy[RGN4 | RGNB4 | RGNB4_0 | RGN4_or] = {'m' (int, or per-step list for RGNB arms), 'support', 'unknown',
    'shared_with'}; certifiers RG4 (frozen rg_arm format) and the four noisy arms (rgn format); summary per arm + SP8.
  alphabet3 (brute.case3.v17_0): seed, family 'rand4a3', eps, mask_rate, steps, burn_in, k (3), eps_bar, delta, B, m,
    boundary, prefix_bits, prefix_flips, realized_flips, crossing, crossing_bit, flip_positions_EVALUATOR_ONLY,
    world_EVALUATOR_ONLY {'delta', 'emit'}, states_EVALUATOR_ONLY, latent_EVALUATOR_ONLY, readings (45, noisy),
    actions (44), truth_EVALUATOR_ONLY (44 x 3), regions[RG4_3 | RGN4_3 | RGNB4_3] = {'m', 'support', 'unknown',
    'shared_with'}, certifiers (rgn format, 3 actions), summary (coverage = certificates / 132).
"""
from __future__ import annotations
import copy,random
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path
import numpy as np
from experiments.brute_common import check,load,VerificationError
from experiments.v0120_reference import steps_sp8,ref_rg,CENSOR
from experiments.v0160_reference import ref_m,tables,mism,strip,_cmp

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_019.json'
N=4;READINGS=45;SLOTS=88;SLOTS3=132;K3=3;MASK=0.35
NOISY_ARMS=('RGN4','RGNB4','RGNB4_0','RGN4_or');ARMS=('RG4',)+NOISY_ARMS
A3_ARMS=('RG4_3','RGN4_3','RGNB4_3')


# ------------------------------------------------------------------ boundary (own implementation)
def ref_boundary(B,eps_bar=0.02,delta=0.01):
    """m(0..B) by linear alpha spending over the running flip count (exact rationals)."""
    p=Fraction(str(eps_bar));d=Fraction(str(delta));q=1-p;m=[0];dist=[Fraction(1)];crossed=Fraction(0)
    for b in range(1,B+1):
        nd=[Fraction(0)]*(len(dist)+1)
        for s,x in enumerate(dist):nd[s]+=x*q;nd[s+1]+=x*p
        mb=m[-1]
        while crossed+sum(nd[mb+1:])>d*b/B:mb+=1
        crossed+=sum(nd[mb+1:]);dist=nd[:mb+1];m.append(mb)
    return m


def prefix_counts(R,F):
    """R = [(noisy reading, latent code)]; cumulative observed bits / flips per reading and the first crossing bit."""
    bits=[];flips=[];b=0;f=0;seq=[]
    for t,(obs,lat) in enumerate(R):
        for j,o in enumerate(obs):
            if o is None:continue
            b+=1;x=int(bool(F[t,j]));f+=x;seq.append(x);check(o==(((lat>>(1-j))&1)^x),f'reading {t} bit {j}: observed {o} vs latent {lat} flip {x}')
        bits.append(b);flips.append(f)
    return bits,flips,seq


def first_crossing(seq,bd):
    s=0
    for b,x in enumerate(seq,start=1):
        s+=x
        if s>bd[b]:return b
    return None


# ------------------------------------------------------------------ costs
def costs_tables(init,acts,obss):
    """k = 2, every 4-state table: per step i ([min cost per code for b = 0, 1], lo_i)."""
    D=tables();n=len(D);ar=np.arange(n);st=np.zeros(n,dtype=np.int64);C=np.zeros((n,N,4),dtype=np.int64)
    C[ar,st]+=mism(init);out=[]
    for a,o in zip(acts,obss):
        mins=C.min(axis=2);base=mins.sum(axis=1);row=[]
        for b in (0,1):
            r=D[ar,st,b];cost=(base-mins[ar,r])[:,None]+C[ar,r];row.append([int(x) for x in cost.min(axis=0)])
        out.append((row,int(base.min())))
        st=D[ar,st,a];C[ar,st]+=mism(o)
    return out


def costs_partial(k,init,acts,obss,mmax):
    """Canonical partial machines with pruning at lo > mmax. Values > mmax are reported as mmax + 1 (only <= m matters)."""
    INF=mmax+1
    Dt=-np.ones((1,N,k),dtype=np.int8);U=np.ones(1,dtype=np.int8);st=np.zeros(1,dtype=np.int64);C=np.zeros((1,N,4),dtype=np.int32)
    C[0,0]+=mism(init).astype(np.int32)
    def prune(Dt,U,st,C):
        keep=C.min(axis=2).sum(axis=1)<=mmax;return Dt[keep],U[keep],st[keep],C[keep]
    Dt,U,st,C=prune(Dt,U,st,C);out=[];peak=len(st)
    for a,o in zip(acts,obss):
        M=len(st)
        if M==0:out.append(([[INF]*4 for _ in range(k)],INF))
        else:
            ar=np.arange(M);mins=C.min(axis=2);base=mins.sum(axis=1);row=[]
            alt=(base[:,None]-mins)[:,:,None]+C            # (M, r, c): next state r
            for b in range(k):
                r=Dt[ar,st,b].astype(np.int64);dfn=r>=0;cost=np.empty((M,4),dtype=np.int64)
                cost[dfn]=alt[ar[dfn],r[dfn]]
                cost[~dfn]=alt[~dfn].min(axis=1)           # any used state, or an unused (new) state = base
                row.append([int(min(x,INF)) for x in cost.min(axis=0)])
            out.append((row,int(min(base.min(),INF))))
            nxt=Dt[ar,st,a].astype(np.int64);dfn=nxt>=0
            parts=[(Dt[dfn],U[dfn],nxt[dfn],C[dfn])]
            for r in range(N):
                sel=(~dfn)&((U>r)|((U==r)&(U<N)))
                if not sel.any():continue
                d2=Dt[sel].copy();d2[np.arange(sel.sum()),st[sel],a]=r;u2=np.maximum(U[sel],r+1).astype(np.int8)
                parts.append((d2,u2,np.full(sel.sum(),r,dtype=np.int64),C[sel].copy()))
            Dt=np.concatenate([p[0] for p in parts]);U=np.concatenate([p[1] for p in parts]);st=np.concatenate([p[2] for p in parts])
            C=np.concatenate([p[3] for p in parts]);C[np.arange(len(st)),st]+=mism(o).astype(np.int32)
            Dt,U,st,C=prune(Dt,U,st,C);peak=max(peak,len(st))
    return out,peak


def supports_for(costs,ms,k):
    """Per step the support (or None) under per-step bounds ms with sticky emptiness."""
    out=[];empty=False
    for i,(row,lo) in enumerate(costs):
        empty=empty or lo>ms[i]
        out.append([None if empty else [c for c in range(4) if row[b][c]<=ms[i]] for b in range(k)])
    return out


def audit_support(rec,ref,where,k):
    S=rec['support'];U=rec['unknown'];check(len(S)==len(ref)==len(U),where+' length')
    for i in range(len(ref)):
        for b in range(k):
            r=ref[i][b];got=S[i][b];u=U[i][b]
            if u==0:check(got==r,f'{where} step {i+1} action {b}: {got} != {r}')
            elif got is not None:check(r is not None and set(r)<=set(got),f'{where} step {i+1} action {b}: {r} not within {got} (unknown {u})')


def ref_cert(steps,truth,sup,m,burn,k):
    out={'m':m,'trace':[]};first=CENSOR;false=0
    for i,(t,a) in enumerate(steps):
        cert=[None]*k
        for b in range(k):
            x=sup[i][b]
            if t>burn and x is not None and len(x)==1:cert[b]=x[0]
        wrong=[cert[b] is not None and cert[b]!=truth[i][b] for b in range(k)];false+=sum(wrong)
        if cert[a] is not None and first==CENSOR:first=t
        out['trace'].append({'step':t,'certificate':cert,'wrong':wrong})
    out.update(first_cert_step=first,false_certificates=false,certificates=sum(x is not None for r in out['trace'] for x in r['certificate']))
    return out


def flip_array(seed,eps):return np.random.default_rng([seed,round(1000*eps),19]).random((READINGS,2))<eps


def audit_noise_common(c,R):
    F=flip_array(c['seed'],c['eps']);check(len(R)==READINGS,'45 readings')
    bits,flips,seq=prefix_counts(R,F);B=bits[-1]
    check(c['B']==B,f'B {c["B"]} != {B}');check(c['realized_flips']==flips[-1],f'realized_flips {c["realized_flips"]} != {flips[-1]}')
    check(c['prefix_bits']==bits,'prefix_bits');check(c['prefix_flips']==flips,'prefix_flips')
    check(c['m']==ref_m(B,c['eps_bar'],c['delta']),f'm {c["m"]} != m_rule({B})')
    bd=ref_boundary(B,c['eps_bar'],c['delta']);check(c['boundary']==bd,'boundary')
    cb=first_crossing(seq,bd);check(c['crossing_bit']==cb and c['crossing']==(cb is not None),f'crossing {c["crossing_bit"]} != {cb}')
    fp=[[t,j] for t,(obs,_) in enumerate(R) for j,o in enumerate(obs) if o is not None and F[t,j]]
    check(c['flip_positions_EVALUATOR_ONLY']==fp,'flip positions')
    return B,flips[-1],bd,bits


# ------------------------------------------------------------------ main block
def readings_main(c):
    tr=c['arms']['SP8']['trace']
    return [(tuple(c['initial_visible']),c['initial_latent_EVALUATOR_ONLY'])]+[(tuple(r['observed']),r['actual_emission_EVALUATOR_ONLY']) for r in tr]


def ref_summary(S,exp):
    f0=next((s['t'] for s in S if s['cert'][s['a']] is not None),CENSOR)
    sp8f=sum(s['cert'][b] is not None and s['cert'][b]!=s['act'][b] for s in S for b in (0,1))
    sp8n=sum(s['cert'][b] is not None for s in S for b in (0,1))
    cert=dict({a:exp[a]['certificates'] for a in ARMS},SP8=sp8n);fal=dict({a:exp[a]['false_certificates'] for a in ARMS},SP8=sp8f)
    return {'certificates':cert,'false':fal,'case_false':{a:v>0 for a,v in fal.items()},
            'coverage':{a:round(v/SLOTS,6) for a,v in cert.items()},
            'first_cert_step':dict({a:exp[a]['first_cert_step'] for a in ARMS},SP8=f0)}


def audit_main(c,plan):
    check(c['schema']=='brute.case.v17_0','schema')
    check(c['mask_rate']==plan['mask_rate'] and c['steps']==plan['actions_per_case'] and c['burn_in']==plan['burn_in'],'case constants')
    check(c['eps'] in tuple(plan['noise_model']['levels'].values()),'eps level');check(c['eps_bar']==0.02 and c['delta']==0.01,'eps_bar / delta')
    burn=c['burn_in'];S=steps_sp8(c);check(len(S)==c['steps'],'SP8 steps')
    B,flips,bd,bits=audit_noise_common(c,readings_main(c))
    costs=costs_tables(tuple(c['initial_visible']),[s['a'] for s in S],[s['obs'] for s in S])
    T=len(S);step_m=[bd[bits[i]] for i in range(T)]
    ms={'RGN4':[c['m']]*T,'RGNB4':step_m,'RGNB4_0':[0]*T,'RGN4_or':[flips]*T}
    mrec={'RGN4':c['m'],'RGNB4':step_m,'RGNB4_0':[0]*T,'RGN4_or':flips}
    check(sorted(c['noisy'])==sorted(NOISY_ARMS),'noisy arm set');exp={}
    audit_support(c['bounded']['4'],supports_for(costs,[0]*T,2),'bounded 4',2)
    truth=[s['act'] for s in S];st=[(s['t'],s['a']) for s in S]
    for arm in NOISY_ARMS:
        rec=c['noisy'][arm];check(rec['m']==mrec[arm],f'{arm} m');audit_support(rec,supports_for(costs,ms[arm],2),arm,2)
        exp[arm]=ref_cert(st,truth,rec['support'],mrec[arm],burn,2)
    exp['RG4']=ref_rg(S,c['bounded'],4,burn)
    check(sorted(c['certifiers'])==sorted(ARMS),'certifier arm set')
    for arm in ARMS:_cmp(c['certifiers'][arm],exp[arm],arm)
    check(c['summary']==ref_summary(S,exp),'summary')


# ------------------------------------------------------------------ alphabet3 block
def _sc(d):
    n=len(d)
    for s in range(n):
        seen={s};todo=[s]
        while todo:
            q=todo.pop()
            for r in d[q]:
                if r not in seen:seen.add(r);todo.append(r)
        if len(seen)<n:return False
    return True


def _minimal(d,e):
    n=len(d);cls=list(e)
    while True:
        sig=[(cls[q],)+tuple(cls[r] for r in d[q]) for q in range(n)];ids={}
        new=[ids.setdefault(s,len(ids)) for s in sig]
        if len(set(new))==len(set(cls)):break
        cls=new
    return len(set(cls))==n


def ref_world3(seed):
    rng=np.random.default_rng([seed,19,1])
    while True:
        d=rng.integers(0,N,(N,K3));e=rng.integers(0,4,N)
        D=[[int(x) for x in row] for row in d];E=[int(x) for x in e]
        if _sc(D) and _minimal(D,E):return D,E


def ref_trajectory3(seed,eps):
    D,E=ref_world3(seed);mask=np.random.default_rng([seed,19,2]).random((READINGS,2))<MASK
    acts=[int(x) for x in np.random.default_rng([seed,19,3]).integers(0,K3,READINGS-1)];F=flip_array(seed,eps)
    states=[0]
    for a in acts:states.append(D[states[-1]][a])
    lat=[E[q] for q in states]
    rd=[[None if mask[t,j] else (((lat[t]>>(1-j))&1)^int(bool(F[t,j]))) for j in (0,1)] for t in range(READINGS)]
    truth=[[E[D[states[i]][b]] for b in range(K3)] for i in range(READINGS-1)]
    return D,E,acts,states,lat,rd,truth


def ref_summary3(exp):
    cert={a:exp[a]['certificates'] for a in A3_ARMS};fal={a:exp[a]['false_certificates'] for a in A3_ARMS}
    return {'certificates':cert,'false':fal,'case_false':{a:v>0 for a,v in fal.items()},
            'coverage':{a:round(v/SLOTS3,6) for a,v in cert.items()},'first_cert_step':{a:exp[a]['first_cert_step'] for a in A3_ARMS}}


def audit_a3(c,plan,return_peak=False):
    check(c['schema']=='brute.case3.v17_0','schema');check(c['family']=='rand4a3' and c['k']==K3,'family / k')
    check(c['mask_rate']==plan['mask_rate']==MASK and c['steps']==plan['actions_per_case'] and c['burn_in']==plan['burn_in'],'case constants')
    check(c['eps'] in (0.0,0.02),'alphabet3 eps');check(c['eps_bar']==0.02 and c['delta']==0.01,'eps_bar / delta')
    D,E,acts,states,lat,rd,truth=ref_trajectory3(c['seed'],c['eps'])
    check(c['world_EVALUATOR_ONLY']=={'delta':D,'emit':E},'world');check(c['actions']==acts,'actions')
    check(c['states_EVALUATOR_ONLY']==states,'states');check(c['latent_EVALUATOR_ONLY']==lat,'latent')
    check(c['readings']==rd,'readings');check(c['truth_EVALUATOR_ONLY']==truth,'truth')
    R=[(tuple(o),l) for o,l in zip(rd,lat)];B,flips,bd,bits=audit_noise_common(c,R)
    T=len(acts);step_m=[bd[bits[i]] for i in range(T)]
    ms={'RG4_3':[0]*T,'RGN4_3':[c['m']]*T,'RGNB4_3':step_m};mrec={'RG4_3':0,'RGN4_3':c['m'],'RGNB4_3':step_m}
    mmax=max(max(v) for v in ms.values())
    costs,peak=costs_partial(K3,tuple(rd[0]),acts,[tuple(o) for o in rd[1:]],mmax)
    check(sorted(c['regions'])==sorted(A3_ARMS),'region arm set');exp={};st=[(i+1,a) for i,a in enumerate(acts)]
    for arm in A3_ARMS:
        rec=c['regions'][arm];check(rec['m']==mrec[arm],f'{arm} m');audit_support(rec,supports_for(costs,ms[arm],K3),arm,K3)
        exp[arm]=ref_cert(st,truth,rec['support'],mrec[arm],c['burn_in'],K3)
    check(sorted(c['certifiers'])==sorted(A3_ARMS),'certifier arm set')
    for arm in A3_ARMS:_cmp(c['certifiers'][arm],exp[arm],arm)
    check(c['summary']==ref_summary3(exp),'summary')
    return peak


def audit_case(c,plan):
    """(ok, message): the first differing field, or (True, None)."""
    try:
        if c.get('schema')=='brute.case3.v17_0':audit_a3(c,plan)
        else:audit_main(c,plan)
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


# ------------------------------------------------------------------ mutation test (GS_ref7)
MAIN_KINDS=('support',)*3+('rgn_cert',)*2+('rg4_cert','wrong','wrong','counts','counts','m','B','flips','boundary','crossing',
                                          'prefix','observed','latent')
A3_KINDS=('a3_support','a3_cert')
KINDS=MAIN_KINDS+A3_KINDS


def _slots(rec,k):
    return [(i,b) for i in range(len(rec['support'])) for b in range(k) if rec['support'][i][b] is not None and rec['unknown'][i][b]==0]


def mutate(cases,k=20,rng_seed=20261030):
    """k single-field errors in k distinct cases (18 main kinds on main cases, 2 alphabet3 kinds on alphabet3 cases)."""
    check(k==len(KINDS),'k must equal len(KINDS)');rng=random.Random(rng_seed)
    mi=[i for i,c in enumerate(cases) if c.get('schema')=='brute.case.v17_0'];ai=[i for i,c in enumerate(cases) if c.get('schema')=='brute.case3.v17_0']
    check(len(mi)>=len(MAIN_KINDS) and len(ai)>=len(A3_KINDS),'too few cases for the mutation test')
    kinds=list(MAIN_KINDS);rng.shuffle(kinds);plan=list(zip(rng.sample(mi,len(MAIN_KINDS)),kinds))+list(zip(rng.sample(ai,len(A3_KINDS)),A3_KINDS))
    out=list(cases);inj=set()
    for i,kind in plan:
        c=copy.deepcopy(cases[i])
        if kind in ('support','a3_support'):
            if kind=='support':
                arm=rng.choice(NOISY_ARMS+('bounded',));rec=c['bounded']['4'] if arm=='bounded' else c['noisy'][arm];kk=2
                if not _slots(rec,kk):rec=c['noisy']['RGNB4']
            else:rec=c['regions'][rng.choice(A3_ARMS)];kk=K3
            s,b=rng.choice(_slots(rec,kk));v=rec['support'][s][b];rec['support'][s][b]=v[1:] if len(v)>1 else [(v[0]+1)%4]
        elif kind in ('rgn_cert','rg4_cert','wrong','a3_cert'):
            if kind=='a3_cert':arm=rng.choice(A3_ARMS);kk=K3
            else:arm=rng.choice(NOISY_ARMS) if kind=='rgn_cert' else 'RG4' if kind=='rg4_cert' else rng.choice(ARMS);kk=2
            r=c['certifiers'][arm]['trace'][rng.randrange(c['steps'])];b=rng.randrange(kk)
            if kind=='wrong':r['wrong'][b]=not r['wrong'][b]
            else:r['certificate'][b]=(r['certificate'][b]+1)%4 if r['certificate'][b] is not None else 0
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
