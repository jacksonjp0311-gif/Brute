"""Study BRUTE-0210-STITCHED-LR-024 runner (experiments/BRUTE_PLAN_024.json; docs/research/v0.21.0/STITCHED_LEMMA_024.md).
Adapted from experiments/brute_study_023.py (frozen, unchanged).

Stream transfer = 360 main cases (eps 0 / 0.01 / 0.02), then 30 stress cases (eps 0.05, first quarter of each family range;
fixed by BRUTE_PLAN_024 cases), one stream. Block reproset = main[::12] (G12, 30 cases; #117 rate-math cut from main[::6] = 60). Each case runs 88 actions (89
readings): every study-023 arm exactly as experiments/brute_study_023.py (same tag-23 flip array: noise model "as
BRUTE_PLAN_023"), plus RGL5 = brute.stitchedregion (stitched LR bound over horizons 28 / 56 / 112, HEADLINE) and, at eps 0.02,
prefix28_rgl5 = RGL5 on the first 28 actions (GLS e1). Record format brute.case.v21_0: experiments/v0210_reference.py
docstring / audit_main. Seeds: scripts/check_seeds_024.
"""
from __future__ import annotations
import argparse,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
from brute.core.learner import ScopeAttestation
from brute.boundedtransfer import FB
from brute.noisyregion import noisy_supports
from brute.seqmargin import seqmargin_supports
from brute.anytimemargin import anytime_boundary,anytime_supports,crossing_bit
from brute.lrregion import lr_supports
from brute.stitchedregion import stitched_supports,epochs as lr5_epochs
from brute.soundtransfer import CENSOR
from brute.evaluation import no_time
import experiments.brute_study_012 as S12
from experiments.brute_study_014 import sp8_steps,_bounded,rg_arm
from experiments.brute_study_018 import NoisyWorld
from experiments.brute_study_019 import prefix_data,plan_bound,cert_arm,_noise_fields
from experiments.worlds_013 import world
from experiments.brute_common_009 import plan006_keys
from experiments.brute_common_013 import plan_view
from experiments.brute_common_024 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,learner_plan,base_plan,Checkpoint,TAU6,STEPS
from scripts.check_seeds_024 import check_run_seeds,smoke_family,SMOKE_TARGETS,API_TEST,KILL_DRILL,MAIN_FAMILIES

READINGS=STEPS+1;SLOTS=2*STEPS;LATE=(45,88);EARLY=28
DELTA_L=0.005;DELTA_A=0.005
PREFIX=28


def arms_for(eps,block='main'):
    """RGNB4 at eps 0.02 only (main; stress is eps 0.05). block is accepted for symmetry and not used."""
    return ('RG4','RGL4','RGL5','RGNA4','RGN4_or')+(('RGNB4',) if eps==0.02 else ())


def noisy_for(eps,block='main'):return tuple(a for a in arms_for(eps,block) if a!='RG4')
SMOKE_BLOCKS={'smoke-transfer':SMOKE_TARGETS,'smoke-api':API_TEST,'smoke-drill':KILL_DRILL}
BLOCKS=('transfer','main','reproset')+tuple(SMOKE_BLOCKS)+('smoke-all',)   # smoke-all = smoke-transfer (orchestrator dry run)


def flip_array(seed,eps):
    """F[row, j], row 0 = initial reading, row i+1 = reading after action i; column j = bit j (BRUTE_PLAN_023 noise_model, tag 23)."""
    return np.random.default_rng([seed,round(1000*eps),23]).random((READINGS,2))<eps


class NoisyWorld23(NoisyWorld):
    def __init__(self,base,seed,eps):super().__init__(base,seed,eps);self.F=flip_array(seed,eps)


def planned_bits(base,rate):
    """B before the first action over the 89 readings (the mask depends only on (seed, step))."""
    return sum(b is not None for step in range(-1,READINGS-1) for b in base.observed(base.start,rate,step))


def _windows(trace):
    per=[sum(x is not None for x in r['certificate']) for r in trace]
    late=sum(p for r,p in zip(trace,per) if LATE[0]<=r['step']<=LATE[1]);early=sum(p for r,p in zip(trace,per) if r['step']<=EARLY)
    return per,late,early


def summary(T,S,ARMS):
    out={'certificates':{a:T[a]['certificates'] for a in ARMS},'false':{a:T[a]['false_certificates'] for a in ARMS},
         'first_cert_step':{a:T[a]['first_cert_step'] for a in ARMS}}
    out["first_cert_step"]["SP8"]=next((t for t,a,cert,_,_,_ in S if cert[a] is not None),CENSOR)
    out['false']['SP8']=sum(cert[b] is not None and cert[b]!=act[b] for t,a,cert,_,_,act in S for b in (0,1))
    out['certificates']['SP8']=sum(cert[b] is not None for t,a,cert,_,_,act in S for b in (0,1))
    tr=dict({a:T[a]['trace'] for a in ARMS},SP8=[{'step':t,'certificate':cert} for t,a,cert,_,_,_ in S]);W={a:_windows(tr[a]) for a in tr}
    out['case_false']={a:out['false'][a]>0 for a in out['false']}
    out['coverage']={a:round(out['certificates'][a]/SLOTS,6) for a in out['certificates']}
    out['certificates_late']={a:W[a][1] for a in W};out['coverage_late']={a:round(W[a][1]/(2*(LATE[1]-LATE[0]+1)),6) for a in W}
    out['certificates_early28']={a:W[a][2] for a in W};out['coverage_early28']={a:round(W[a][2]/(2*EARLY),6) for a in W}
    out['per_step']={a:W[a][0] for a in W}
    return {k:out[k] for k in ('certificates','false','case_false','coverage','certificates_late','coverage_late','certificates_early28',
                               'coverage_early28','per_step','first_cert_step')}


def _lr_record(r,B,bits,init,obs,F):
    bl=anytime_boundary(B,0.02,DELTA_A)
    return {'delta_L':DELTA_L,'delta_a':DELTA_A,'D':r['D'],'anytime_boundary':bl,
            'anytime_crossing_bit':crossing_bit(prefix_data([init]+obs,F)[2],bl),**r['lr']}


def _lr5_record(r):
    T=len(r['m']);L=r['lr']
    return {'delta_L':DELTA_L,'delta_a':DELTA_A,'D':r['D'],'epochs':lr5_epochs(T,DELTA_A),'epoch':L['epoch'],'M':L['M'],'T':L['T'],
            'attain':L['attain'],'witnesses':L['witnesses'],'witness_unknowns':L['witness_unknowns'],'witness_calls':L['witness_calls']}


def run_case(seed,family,eps,plan,block='main'):
    P21=base_plan();P13=learner_plan();burn=P21['burn_in'];rate=P21['mask_rate'];eps_bar=0.02;delta=0.01
    check(eps in (0.0,0.01,0.02,0.05),'eps level')
    v=plan_view(P13);p6=plan006_keys(v);check(p6['actions_per_case']==STEPS,'88-action learner plan');attest=family in P13['in_family_2x2']
    def att():return ScopeAttestation(p6['declared_family'],'evaluator','synthetic world built inside the family') if attest else None
    base=world(seed,family);B=planned_bits(base,rate);W=NoisyWorld23(base,seed,eps)
    t0=perf_counter();truth,initial,sp8=S12.trajectory_2x2('SP8',seed,family,rate,v,p6,TAU6,att,truth=W)
    sp8['arm_wall_informational']=perf_counter()-t0
    check(W.readings==READINGS and W.observed_bits==B,'B recount equals planned B')
    c={'schema':'brute.case.v21_0','block':block,'seed':seed,'family':family,'eps':eps,'mask_rate':rate,
       'in_family_EVALUATOR_ONLY':family in P13['in_family_2x2'],'attested':bool(attest),
       'true_hidden_state_count_EVALUATOR_ONLY':truth.n,'initial_visible':list(initial),
       'initial_latent_EVALUATOR_ONLY':base.emission(base.start),
       'steps':P13['actions_per_case_2x2'],'burn_in':P13['burn_in'],'tau6':TAU6,'tau_v030':v['tau_v030'],
       'eps_bar':eps_bar,'delta':delta,'flip_positions_EVALUATOR_ONLY':W.flips,'arms':{'SP8':sp8}}
    check(c['steps']==P21['horizon']['steps']==STEPS and c['burn_in']==burn,'case constants')
    init=tuple(initial);S=sp8_steps(c);acts=[s[1] for s in S];obs=[s[4] for s in S];wall={}
    bd,bits=_noise_fields(c,[init]+obs,W.F,eps_bar,delta);check(c['B']==B and c['realized_flips']==len(W.flips),'B / flips recount')
    flips=c['realized_flips'];T_=len(S);check(T_==STEPS,'88 SP8 steps')
    ba=anytime_boundary(B,eps_bar,delta);ca=crossing_bit(prefix_data([init]+obs,W.F)[2],ba)
    c.update(anytime_boundary=ba,anytime_crossing=ca is not None,anytime_crossing_bit=ca)
    ARMS=arms_for(eps,block);NA=noisy_for(eps,block)
    t1=perf_counter();c['bounded']={'4':_bounded(init,S,(FB,))[str(FB)]};wall['RG4']=perf_counter()-t1;noisy={}
    t1=perf_counter();r=lr_supports(init,acts,obs,FB,2,eps_bar,DELTA_L,DELTA_A)
    check(r['m']==r['lr']['T'],'RGL4 m is T');c['lr']=_lr_record(r,B,bits,init,obs,W.F)
    noisy['RGL4']={'m':r['m'],'support':r['support'],'unknown':r['unknown'],'shared_with':None};wall['RGL4']=perf_counter()-t1
    c['lr']['step_wall_informational']=round(wall['RGL4']/T_,6)
    t1=perf_counter();r=stitched_supports(init,acts,obs,FB,2,eps_bar,DELTA_L,DELTA_A)
    check(r['m']==r['lr']['T'],'RGL5 m is T5');c['lr5']=_lr5_record(r)
    noisy['RGL5']={'m':r['m'],'support':r['support'],'unknown':r['unknown'],'shared_with':None};wall['RGL5']=perf_counter()-t1
    c['lr5']['step_wall_informational']=round(wall['RGL5']/T_,6)
    t1=perf_counter();r=anytime_supports(init,acts,obs,FB,2,eps_bar,delta)
    noisy['RGNA4']={'m':plan_bound(r,ba,bits,T_),'support':r['support'],'unknown':r['unknown'],'shared_with':None};wall['RGNA4']=perf_counter()-t1
    if 'RGNB4' in NA:
        t1=perf_counter();r=seqmargin_supports(init,acts,obs,FB,bd)
        noisy['RGNB4']={'m':plan_bound(r,bd,bits,T_),'support':r['support'],'unknown':r['unknown'],'shared_with':None};wall['RGNB4']=perf_counter()-t1
    t1=perf_counter();r=noisy_supports(init,acts,obs,FB,flips)
    noisy['RGN4_or']={'m':flips,'support':r['support'],'unknown':r['unknown'],'shared_with':None};wall['RGN4_or']=perf_counter()-t1
    c['noisy']=noisy
    T={'RG4':rg_arm(S,{'4':c['bounded']['4']},FB,burn)};st=[(s[0],s[1]) for s in S];tru=[s[5] for s in S]
    for arm in NA:T[arm]=cert_arm(st,tru,noisy[arm]['support'],noisy[arm]['m'],burn,2)
    c['certifiers']=T;c['summary']=summary(T,S,ARMS)
    if eps==0.02:
        t1=perf_counter();r=lr_supports(init,acts[:PREFIX],obs[:PREFIX],FB,2,eps_bar,DELTA_L,DELTA_A)
        p={'actions':PREFIX,'m':r['m'],'support':r['support'],'unknown':r['unknown'],'lr':_lr_record(r,B,bits,init,obs,W.F)}
        p['certifier']=cert_arm(st[:PREFIX],tru[:PREFIX],p['support'],p['m'],burn,2);full=noisy['RGL4']
        p['identical']=(p['support']==full['support'][:PREFIX] and p['unknown']==full['unknown'][:PREFIX] and p['m']==full['m'][:PREFIX]
                        and [x['certificate'] for x in p['certifier']['trace']]==[x['certificate'] for x in T['RGL4']['trace'][:PREFIX]])
        c['prefix28']=p;wall['prefix28']=perf_counter()-t1
        t1=perf_counter();r=stitched_supports(init,acts[:PREFIX],obs[:PREFIX],FB,2,eps_bar,DELTA_L,DELTA_A)
        p={'actions':PREFIX,'m':r['m'],'support':r['support'],'unknown':r['unknown'],'lr5':_lr5_record(r)}
        p['certifier']=cert_arm(st[:PREFIX],tru[:PREFIX],p['support'],p['m'],burn,2);full=noisy['RGL5']
        p['identical']=(p['support']==full['support'][:PREFIX] and p['unknown']==full['unknown'][:PREFIX] and p['m']==full['m'][:PREFIX]
                        and [x['certificate'] for x in p['certifier']['trace']]==[x['certificate'] for x in T['RGL5']['trace'][:PREFIX]])
        c['prefix28_rgl5']=p;wall['prefix28_rgl5']=perf_counter()-t1
    c['region_wall_informational']=wall
    return c


# ------------------------------------------------------------------ jobs
def jobs_for(plan,block):
    R=plan['heldout_ranges']['targets'];E=(0.0,0.01,0.02)
    main=[('main',fam,seed,e) for fam in MAIN_FAMILIES for seed in range(R[fam][0],R[fam][1]+1) for e in E]
    stress=[('stress',fam,seed,0.05) for fam in MAIN_FAMILIES for seed in range(R[fam][0],R[fam][0]+(R[fam][1]-R[fam][0]+1)//4)]   # BRUTE_PLAN_024 cases.stress = 30 (first quarter)
    if block=='transfer':return main+stress
    if block=='main':return main
    if block=='reproset':return main[::12]   # deviation #117 item 7: rate-math cut 60 -> 30 (subset of the plan's main[::6])
    if block=='smoke-all':return jobs_for(plan,'smoke-transfer')
    if block in SMOKE_BLOCKS:
        Es=(0.02,) if block=='smoke-api' else E+(0.05,)
        return [(block,smoke_family(s),s,e) for s in SMOKE_BLOCKS[block] for e in Es]
    raise ValueError(block)


def key(job):return '/'.join(map(str,job))


def check_job(job,plan):
    block,fam,seed,eps=job
    check(block in ('main','stress')+tuple(SMOKE_BLOCKS),'block '+str(block))
    if block=='main':check(fam in MAIN_FAMILIES and eps in (0.0,0.01,0.02),'main family / eps');check_run_seeds('target',[seed],plan,family=fam)
    elif block=='stress':check(fam in MAIN_FAMILIES and eps==0.05,'stress eps');check_run_seeds('target',[seed],plan,family=fam)
    else:
        check(eps in (0.0,0.01,0.02,0.05),'eps');check_run_seeds('smoke',[seed],plan)
        check(seed in SMOKE_BLOCKS[block] and smoke_family(seed)==fam,'smoke layout')


def run_job(job,plan):
    block,fam,seed,eps=job;check_job(job,plan);t0=perf_counter()
    c=run_case(seed,fam,eps,plan,block);c['case_wall_informational']=perf_counter()-t0
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


HELDOUT=('transfer','main','reproset')


def _select(plan,block,every,offset,limit):
    jobs=jobs_for(plan,block)[offset::every]
    return jobs[:limit] if limit else jobs


def _write(output,plan,block,sel,keys,cases,complete,extra):
    smoke=block not in HELDOUT
    result={'schema':'brute.study.v21_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,
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
    if a.block not in HELDOUT:check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-024')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.every,a.offset,a.limit))
    else:run(out,a.workers,a.block,a.limit,a.every,a.offset);print('done')
