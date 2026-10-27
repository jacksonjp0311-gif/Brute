"""Study BRUTE-0170-SEQUENTIAL-MARGIN-019 runner (experiments/BRUTE_PLAN_019.json; #101 items 4-8).

Stream transfer = 360 main cases (eps 0 / 0.01 / 0.02), then 120 stress cases (eps 0.05), then 96 alphabet3 cases
(rand4a3 x eps 0 / 0.02), as one stream. Block reproset = main[::3] + alphabet3[::3] (G12).

Main case: the frozen SP8 trajectory (experiments.brute_study_012.trajectory_2x2) on a NoisyWorld proxy that flips
observed bits with the plan-019 flip array; bounded['4'] = frozen RegionSpace(4) supports; RG4 = frozen rg_arm;
noisy[RGN4] = frozen brute.noisyregion supports with m = m_rule(B); noisy[RGNB4] = brute.seqmargin with boundary(B);
noisy[RGNB4_0] = boundary forced to 0 (the RGN4_0 CNF, frozen noisy_supports with m = 0); noisy[RGN4_or] = m = realized
flips (shares RGN4 when flips == m, RGNB4_0 when flips == 0).
alphabet3 case: rand4a3 world (default_rng([seed, 19, 1]), rejection to strongly connected + minimal), mask
default_rng([seed, 19, 2]), actions default_rng([seed, 19, 3]), flips as main; RG4_3 / RGN4_3 / RGNB4_3 via brute.region3.
Record formats: experiments/v0170_reference.py docstring / audit_case. Seeds: scripts/check_seeds_019.
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from brute.core.learner import ScopeAttestation
from brute.boundedtransfer import FB
from brute.noisyregion import m_rule,noisy_supports,rgn_decide
from brute.seqmargin import boundary,crossing_bit,seqmargin_supports
from brute.region3 import K3,rg3_supports,rgn3_supports,rgnb3_supports
from brute.evaluation import no_time
from brute.soundtransfer import CENSOR
import experiments.brute_study_012 as S12
from experiments.brute_study_014 import sp8_steps,_bounded,rg_arm
from experiments.brute_study_018 import NoisyWorld,planned_bits
from experiments.worlds_013 import world
from experiments.brute_common_009 import plan006_keys
from experiments.brute_common_013 import plan_view
from experiments.brute_common_019 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,learner_plan,Checkpoint,TAU6
from scripts.check_seeds_019 import (check_run_seeds,smoke_family,SMOKE_TARGETS,API_TEST,KILL_DRILL,A3_SMOKE,EPS_A3,MAIN_FAMILIES,
                                     A3_FAMILY)

READINGS=45;SLOTS=88;SLOTS3=132;N=4
NOISY_ARMS=('RGN4','RGNB4','RGNB4_0','RGN4_or');ARMS=('RG4',)+NOISY_ARMS;A3_ARMS=('RG4_3','RGN4_3','RGNB4_3')
SMOKE_BLOCKS={'smoke-transfer':SMOKE_TARGETS,'smoke-api':API_TEST,'smoke-drill':KILL_DRILL,'smoke-a3':A3_SMOKE}
BLOCKS=('transfer','main','alphabet3','reproset')+tuple(SMOKE_BLOCKS)+('smoke-all',)   # smoke-all = smoke-transfer + smoke-a3 (orchestrator dry run)


def flip_array(seed,eps):
    """F[row, j], row 0 = initial reading, row i+1 = reading after action i; column j = bit j (#101 item 4, tag 19)."""
    return np.random.default_rng([seed,round(1000*eps),19]).random((READINGS,2))<eps


class NoisyWorld19(NoisyWorld):
    def __init__(self,base,seed,eps):super().__init__(base,seed,eps);self.F=flip_array(seed,eps)


def prefix_data(readings,F):
    """Cumulative observed bits / flips per reading (45 entries) and the flip sequence in observed-bit order."""
    bits=[];flips=[];seq=[];b=f=0
    for t,o in enumerate(readings):
        for j,x in enumerate(o):
            if x is None:continue
            b+=1;y=int(bool(F[t,j]));f+=y;seq.append(y)
        bits.append(b);flips.append(f)
    return bits,flips,seq


def plan_bound(r,bd,bits,T):
    """Deviation #102: the bound in force at step i is bd[bits[i]] (plan sequential_margin). The region space reports
    m_bound only when it rebuilds; after a contradicted or budget-exhausted build it no longer rebuilds (sticky, #101) and
    its m_bound goes stale. Checked equal on every step whose space was still live; the plan bound is what is recorded.
    Contradicted / exhausted steps certify nothing, so no certificate depends on the recorded value."""
    want=[bd[bits[i]] for i in range(T)];live=True
    for i in range(T):
        if live:check(r['m'][i]==want[i],'per-step bound at a live step')
        live=live and r['status'][i]=='supported'
    return want


def cert_arm(steps,truth,sup,m,burn,k):
    """steps: [(t, a)]; RGN-rule certificates (singleton after burn-in), k actions."""
    out={'m':m,'trace':[]};first=CENSOR;false=0
    for i,(t,a) in enumerate(steps):
        cert=[rgn_decide(t,burn,sup[i][b]) for b in range(k)]
        wrong=[cert[b] is not None and cert[b]!=truth[i][b] for b in range(k)];false+=sum(wrong)
        if cert[a] is not None and first==CENSOR:first=t
        out['trace'].append({'step':t,'certificate':cert,'wrong':wrong})
    out.update(first_cert_step=first,false_certificates=false,certificates=sum(c is not None for x in out['trace'] for c in x['certificate']))
    return out


def summary(T,arms,slots,sp8=None):
    out={'certificates':{a:T[a]['certificates'] for a in arms},'false':{a:T[a]['false_certificates'] for a in arms},
         'first_cert_step':{a:T[a]['first_cert_step'] for a in arms}}
    if sp8 is not None:
        S=sp8;out['first_cert_step']['SP8']=next((t for t,a,cert,_,_,_ in S if cert[a] is not None),CENSOR)
        out['false']['SP8']=sum(cert[b] is not None and cert[b]!=act[b] for t,a,cert,_,_,act in S for b in (0,1))
        out['certificates']['SP8']=sum(cert[b] is not None for t,a,cert,_,_,act in S for b in (0,1))
    out['case_false']={a:out['false'][a]>0 for a in out['false']}
    out['coverage']={a:round(out['certificates'][a]/slots,6) for a in out['certificates']}
    return out


def _noise_fields(c,readings,F,eps_bar,delta):
    B=sum(x is not None for o in readings for x in o);bits,flips,seq=prefix_data(readings,F);bd=boundary(B,eps_bar,delta)
    cb=crossing_bit(seq,bd)
    c.update(B=B,m=m_rule(B,eps_bar,delta),boundary=bd,prefix_bits=bits,prefix_flips=flips,realized_flips=flips[-1],crossing=cb is not None,
             crossing_bit=cb)
    return bd,bits


def run_case(seed,family,eps,plan,block='main'):
    P13=learner_plan(plan);burn=plan['burn_in'];rate=plan['mask_rate'];nm=plan['noise_model'];eps_bar=0.02;delta=0.01
    check(eps in tuple(nm['levels'].values()),'eps level')
    v=plan_view(P13);p6=plan006_keys(v);attest=family in P13['in_family_2x2']
    def att():return ScopeAttestation(p6['declared_family'],'evaluator','synthetic world built inside the family') if attest else None
    base=world(seed,family);B=planned_bits(base,rate);W=NoisyWorld19(base,seed,eps)
    t0=perf_counter();truth,initial,sp8=S12.trajectory_2x2('SP8',seed,family,rate,v,p6,TAU6,att,truth=W)
    sp8['arm_wall_informational']=perf_counter()-t0
    check(W.readings==READINGS and W.observed_bits==B,'B recount equals planned B')
    c={'schema':'brute.case.v17_0','block':block,'seed':seed,'family':family,'eps':eps,'mask_rate':rate,
       'in_family_EVALUATOR_ONLY':family in P13['in_family_2x2'],'attested':bool(attest),
       'true_hidden_state_count_EVALUATOR_ONLY':truth.n,'initial_visible':list(initial),
       'initial_latent_EVALUATOR_ONLY':base.emission(base.start),
       'steps':P13['actions_per_case_2x2'],'burn_in':P13['burn_in'],'tau6':TAU6,'tau_v030':v['tau_v030'],
       'eps_bar':eps_bar,'delta':delta,'flip_positions_EVALUATOR_ONLY':W.flips,'arms':{'SP8':sp8}}
    check(c['steps']==plan['actions_per_case'] and c['burn_in']==burn,'case constants')
    init=tuple(initial);S=sp8_steps(c);acts=[s[1] for s in S];obs=[s[4] for s in S];wall={}
    bd,bits=_noise_fields(c,[init]+obs,W.F,eps_bar,delta);check(c['B']==B and c['realized_flips']==len(W.flips),'B / flips recount')
    m=c['m'];flips=c['realized_flips'];T_=len(S)
    t1=perf_counter();c['bounded']={'4':_bounded(init,S,(FB,))[str(FB)]};wall['RG4']=perf_counter()-t1;noisy={}
    t1=perf_counter();r=noisy_supports(init,acts,obs,FB,m);noisy['RGN4']={'m':m,'support':r['support'],'unknown':r['unknown'],'shared_with':None}
    wall['RGN4']=perf_counter()-t1
    t1=perf_counter();r=seqmargin_supports(init,acts,obs,FB,bd)
    noisy['RGNB4']={'m':plan_bound(r,bd,bits,T_),'support':r['support'],'unknown':r['unknown'],'shared_with':None};wall['RGNB4']=perf_counter()-t1
    t1=perf_counter();r=noisy_supports(init,acts,obs,FB,0)
    noisy['RGNB4_0']={'m':[0]*T_,'support':r['support'],'unknown':r['unknown'],'shared_with':None};wall['RGNB4_0']=perf_counter()-t1
    share='RGN4' if flips==m else 'RGNB4_0' if flips==0 else None;t1=perf_counter()
    if share:noisy['RGN4_or']={'m':flips,'support':noisy[share]['support'],'unknown':noisy[share]['unknown'],'shared_with':share}
    else:
        r=noisy_supports(init,acts,obs,FB,flips);noisy['RGN4_or']={'m':flips,'support':r['support'],'unknown':r['unknown'],'shared_with':None}
    wall['RGN4_or']=perf_counter()-t1
    c['noisy']=noisy;c['region_wall_informational']=wall
    T={'RG4':rg_arm(S,{'4':c['bounded']['4']},FB,burn)};st=[(s[0],s[1]) for s in S];tru=[s[5] for s in S]
    for arm in NOISY_ARMS:T[arm]=cert_arm(st,tru,noisy[arm]['support'],noisy[arm]['m'],burn,2)
    c['certifiers']=T;c['summary']=summary(T,ARMS,SLOTS,S)
    return c


# ------------------------------------------------------------------ alphabet3
def _strongly_connected(d):
    n=len(d)
    for s in range(n):
        seen={s};todo=[s]
        while todo:
            for r in d[todo.pop()]:
                if r not in seen:seen.add(r);todo.append(r)
        if len(seen)<n:return False
    return True


def _minimal(d,e):
    """Moore minimisation by partition refinement; minimal iff every state is its own class."""
    part=list(e)
    while True:
        keys=[(part[q],)+tuple(part[r] for r in d[q]) for q in range(len(d))];lab={}
        new=[lab.setdefault(k,len(lab)) for k in keys]
        if len(set(new))==len(set(part)):return len(set(new))==len(d)
        part=new


def world3(seed):
    rng=np.random.default_rng([seed,19,1])
    while True:
        d=[[int(x) for x in row] for row in rng.integers(0,N,(N,K3))];e=[int(x) for x in rng.integers(0,4,N)]
        if _strongly_connected(d) and _minimal(d,e):return d,e


def run_case3(seed,family,eps,plan,block='alphabet3'):
    check(family==A3_FAMILY and eps in EPS_A3,'alphabet3 family / eps');burn=plan['burn_in'];rate=plan['mask_rate'];eps_bar=0.02;delta=0.01
    d,e=world3(seed);mask=np.random.default_rng([seed,19,2]).random((READINGS,2))<rate
    acts=[int(x) for x in np.random.default_rng([seed,19,3]).integers(0,K3,READINGS-1)];F=flip_array(seed,eps)
    states=[0]
    for a in acts:states.append(d[states[-1]][a])
    lat=[e[q] for q in states];rd=[];fp=[]
    for t in range(READINGS):
        row=[]
        for j in (0,1):
            if mask[t,j]:row.append(None);continue
            x=(lat[t]>>(1-j))&1
            if F[t,j]:x^=1;fp.append([t,j])
            row.append(x)
        rd.append(row)
    truth=[[e[d[states[i]][b]] for b in range(K3)] for i in range(READINGS-1)]
    c={'schema':'brute.case3.v17_0','block':block,'seed':seed,'family':family,'eps':eps,'mask_rate':rate,'steps':plan['actions_per_case'],
       'burn_in':burn,'k':K3,'eps_bar':eps_bar,'delta':delta,'flip_positions_EVALUATOR_ONLY':fp,
       'world_EVALUATOR_ONLY':{'delta':d,'emit':e},'states_EVALUATOR_ONLY':states,'latent_EVALUATOR_ONLY':lat,'readings':rd,'actions':acts,
       'truth_EVALUATOR_ONLY':truth}
    check(len(acts)==c['steps'],'actions per case')
    init=tuple(rd[0]);obs=[tuple(o) for o in rd[1:]];bd,bits=_noise_fields(c,rd,F,eps_bar,delta);m=c['m'];wall={};R={}
    t1=perf_counter();r=rg3_supports(init,acts,obs,N);R['RG4_3']={'m':0,'support':r['support'],'unknown':r['unknown'],'shared_with':None}
    wall['RG4_3']=perf_counter()-t1
    t1=perf_counter();r=rgn3_supports(init,acts,obs,m,N);R['RGN4_3']={'m':m,'support':r['support'],'unknown':r['unknown'],'shared_with':None}
    wall['RGN4_3']=perf_counter()-t1
    t1=perf_counter();r=rgnb3_supports(init,acts,obs,bd,N);mb=plan_bound(r,bd,bits,len(acts))
    R['RGNB4_3']={'m':mb,'support':r['support'],'unknown':r['unknown'],'shared_with':None};wall['RGNB4_3']=perf_counter()-t1
    c['regions']=R;c['region_wall_informational']=wall;st=[(i+1,a) for i,a in enumerate(acts)]
    T={arm:cert_arm(st,truth,R[arm]['support'],R[arm]['m'],burn,K3) for arm in A3_ARMS}
    c['certifiers']=T;c['summary']=summary(T,A3_ARMS,SLOTS3)
    return c


# ------------------------------------------------------------------ jobs
def jobs_for(plan,block):
    R=plan['heldout_ranges']['targets'];lv=plan['noise_model']['levels']
    main=[('main',fam,seed,e) for fam in MAIN_FAMILIES for seed in range(R[fam][0],R[fam][1]+1) for e in (lv['eps0_control'],lv['eps1'],lv['eps2'])]
    stress=[('stress',fam,seed,lv['eps5_stress']) for fam in MAIN_FAMILIES for seed in range(R[fam][0],R[fam][1]+1)]
    a,b=R[A3_FAMILY];a3=[('alphabet3',A3_FAMILY,seed,e) for seed in range(a,b+1) for e in EPS_A3]
    if block=='transfer':return main+stress+a3
    if block=='main':return main
    if block=='alphabet3':return a3
    if block=='reproset':return main[::3]+a3[::3]
    if block=='smoke-all':return jobs_for(plan,'smoke-transfer')+jobs_for(plan,'smoke-a3')
    if block in SMOKE_BLOCKS:
        if block=='smoke-a3':E=EPS_A3
        elif block=='smoke-api':E=(lv['eps2'],)
        else:E=tuple(lv.values())
        return [(block,smoke_family(s),s,e) for s in SMOKE_BLOCKS[block] for e in E]
    raise ValueError(block)


def key(job):return '/'.join(map(str,job))


def check_job(job,plan):
    block,fam,seed,eps=job;lv=plan['noise_model']['levels']
    check(block in ('main','stress','alphabet3')+tuple(SMOKE_BLOCKS),'block '+str(block))
    if block=='main':
        check(fam in MAIN_FAMILIES and eps in (lv['eps0_control'],lv['eps1'],lv['eps2']),'main family / eps');check_run_seeds('target',[seed],plan,family=fam)
    elif block=='stress':check(fam in MAIN_FAMILIES and eps==lv['eps5_stress'],'stress eps');check_run_seeds('target',[seed],plan,family=fam)
    elif block=='alphabet3':check(fam==A3_FAMILY and eps in EPS_A3,'alphabet3 eps');check_run_seeds('target',[seed],plan,family=fam)
    else:
        check(eps in (EPS_A3 if block=='smoke-a3' else tuple(lv.values())),'eps');check_run_seeds('smoke',[seed],plan)
        check(seed in SMOKE_BLOCKS[block] and smoke_family(seed)==fam,'smoke layout')


def run_job(job,plan):
    block,fam,seed,eps=job;check_job(job,plan);t0=perf_counter()
    c=(run_case3 if fam==A3_FAMILY else run_case)(seed,fam,eps,plan,block);c['case_wall_informational']=perf_counter()-t0
    return key(job),c


def _job(x):return run_job(*x)


def run_jobs(jobs,plan,workers,ckpt,log=print):
    for j in jobs:check_job(j,plan)
    todo=[j for j in jobs if key(j) not in ckpt.done];log(f'{len(jobs)-len(todo)} cached, {len(todo)} to run',flush=True)
    if workers<=1:
        for j in todo:k_,c=run_job(j,plan);ckpt.add(k_,c);log(f'done {k_} {c["case_wall_informational"]:.1f}s',flush=True)
    else:
        with ProcessPoolExecutor(workers) as ex:
            futs=[ex.submit(_job,(j,plan)) for j in todo]
            for n,fu in enumerate(as_completed(futs)):
                k_,c=fu.result();ckpt.add(k_,c);log(f'done {n+1}/{len(todo)} {k_} {c["case_wall_informational"]:.1f}s',flush=True)
    return [ckpt.done[key(j)] for j in jobs]


HELDOUT=('transfer','main','alphabet3','reproset')


def _select(plan,block,every,offset,limit):
    jobs=jobs_for(plan,block)[offset::every]
    return jobs[:limit] if limit else jobs


def _write(output,plan,block,sel,keys,cases,complete,extra):
    smoke=block not in HELDOUT
    result={'schema':'brute.study.v17_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,
            'job_selection':sel,'job_keys':keys,'cases':cases,**extra}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE),
        'case_count':len(cases),'expected_case_count':len(keys),'complete':complete,'smoke':smoke,'job_selection':sel,
        **({'missing_job_keys':extra['missing_job_keys']} if 'missing_job_keys' in extra else {})})


def seal_partial(output,block,every=1,offset=0,limit=None,reason='stream budget or study cap'):
    output=Path(output);plan=load(PLAN)
    for name in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/name).exists(),'refusing overwrite '+str(output/name))
    jobs=_select(plan,block,every,offset,limit);ck=Checkpoint(output/'CHECKPOINT.jsonl');keys=[key(j) for j in jobs]
    done=[k for k in keys if k in ck.done];missing=[k for k in keys if k not in ck.done]
    _write(output,plan,block,{'every':every,'offset':offset,'limit':limit},keys,[ck.done[k] for k in done],False,
           {'stop_reason':reason,'missing_job_keys':missing,'total_elapsed_informational':None})
    return len(done),len(keys)


def run(output,workers,block,limit=None,every=1,offset=0):
    output=Path(output);plan=load(PLAN)
    if block in HELDOUT:check_freeze()
    for name in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/name).exists(),'refusing overwrite '+str(output/name))
    started=time.perf_counter();jobs=_select(plan,block,every,offset,limit)
    output.mkdir(parents=True,exist_ok=True)
    cases=run_jobs(jobs,plan,workers,Checkpoint(output/'CHECKPOINT.jsonl'))
    _write(output,plan,block,{'every':every,'offset':offset,'limit':limit},[key(j) for j in jobs],cases,True,
           {'total_elapsed_informational':time.perf_counter()-started})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=BLOCKS,default='transfer')
    ap.add_argument('--output');ap.add_argument('--workers',type=int,default=4);ap.add_argument('--limit',type=int)
    ap.add_argument('--every',type=int,default=1);ap.add_argument('--offset',type=int,default=0)
    ap.add_argument('--seal-partial',action='store_true')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.block not in HELDOUT:check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-019')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.every,a.offset,a.limit))
    else:run(out,a.workers,a.block,a.limit,a.every,a.offset);print('done')
