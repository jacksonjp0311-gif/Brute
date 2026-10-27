"""Study BRUTE-0160-NOISY-OBSERVATION-018 runner (experiments/BRUTE_PLAN_018.json; stream transfer = 360 main cases
(eps 0 / 0.01 / 0.02) followed by 120 stress cases (eps 0.05), as one stream; #97 item 7).

Per case: the frozen SP8 trajectory (experiments.brute_study_012.trajectory_2x2) on a NoisyWorld proxy whose observed()
flips observed bits with the plan-018 flip array (#97 item 5); the noise-free emission stays the scoring truth
(actual_emission_EVALUATOR_ONLY). Then: bounded['4'] = frozen RegionSpace(4) supports on the noisy readings; RG4 = frozen
rg_arm; noisy[RGN4 | RGN4_0 | RGN4_or] = brute.noisyregion supports with m = m_rule(B) | 0 | realized flips (#97 item 6:
RGN4_or shares the RGN4 / RGN4_0 supports when flips equals that m); certifiers; summary. Record format:
experiments/v0160_reference.py docstring / audit_case. Seeds: scripts/check_seeds_018.
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
from brute.evaluation import no_time
from brute.soundtransfer import CENSOR
import experiments.brute_study_012 as S12
from experiments.brute_study_014 import sp8_steps,_bounded,rg_arm
from experiments.worlds_013 import world
from experiments.brute_common_009 import plan006_keys
from experiments.brute_common_013 import plan_view
from experiments.brute_common_018 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,learner_plan,Checkpoint,TAU6
from scripts.check_seeds_018 import check_run_seeds,smoke_family,SMOKE_TARGETS,API_TEST,KILL_DRILL

READINGS=45;SLOTS=88
RGN_ARMS=('RGN4','RGN4_0','RGN4_or');ARMS=('RG4',)+RGN_ARMS
SMOKE_BLOCKS={'smoke-transfer':SMOKE_TARGETS,'smoke-api':API_TEST,'smoke-drill':KILL_DRILL}
BLOCKS=('transfer','main')+tuple(SMOKE_BLOCKS)


def flip_array(seed,eps):
    """#97 item 5: F[row, j], row 0 = initial reading, row i+1 = reading after action i; column j = bit j."""
    return np.random.default_rng([seed,round(1000*eps),18]).random((READINGS,2))<eps


class NoisyWorld:
    """Proxy for a frozen HiddenWorldK: observed() returns the frozen masked reading with observed bits flipped by F."""
    def __init__(self,base,seed,eps):
        self._base=base;self.eps=eps;self.F=flip_array(seed,eps);self.flips=[];self.observed_bits=0;self.readings=0
    def __getattr__(self,k):return getattr(self._base,k)
    def observed(self,hidden,rate,step):
        o=self._base.observed(hidden,rate,step);row=step+1;check(row==self.readings,'readings in order');self.readings+=1
        out=[]
        for j,b in enumerate(o):
            if b is None:out.append(None);continue
            self.observed_bits+=1
            if self.F[row,j]:out.append(1-b);self.flips.append([row,j])
            else:out.append(b)
        return tuple(out)


def planned_bits(base,rate):
    """B before the first action: the mask depends only on (seed, step), so count non-None bits of the frozen readings."""
    return sum(b is not None for step in range(-1,READINGS-1) for b in base.observed(base.start,rate,step))


def rgn_arm(steps,sup,m,burn):
    out={'m':m,'trace':[]};first=CENSOR;false=0
    for i,(t,a,cert0,supp,obs,act) in enumerate(steps):
        cert=[rgn_decide(t,burn,sup[i][b]) for b in (0,1)]
        wrong=[cert[b] is not None and cert[b]!=act[b] for b in (0,1)];false+=sum(wrong)
        if cert[a] is not None and first==CENSOR:first=t
        out['trace'].append({'step':t,'certificate':cert,'wrong':wrong})
    out.update(first_cert_step=first,false_certificates=false,certificates=sum(c is not None for x in out['trace'] for c in x['certificate']))
    return out


def summary(S,T):
    f0=next((t for t,a,cert,_,_,_ in S if cert[a] is not None),CENSOR)
    sp8f=sum(cert[b] is not None and cert[b]!=act[b] for t,a,cert,_,_,act in S for b in (0,1))
    sp8n=sum(cert[b] is not None for t,a,cert,_,_,act in S for b in (0,1))
    out={'certificates':{a:T[a]['certificates'] for a in ARMS},'false':{a:T[a]['false_certificates'] for a in ARMS},
         'first_cert_step':{a:T[a]['first_cert_step'] for a in ARMS}}
    out['certificates']['SP8']=sp8n;out['false']['SP8']=sp8f;out['first_cert_step']['SP8']=f0
    out['case_false']={a:out['false'][a]>0 for a in out['false']}
    out['coverage']={a:round(out['certificates'][a]/SLOTS,6) for a in out['certificates']}
    return out


def run_case(seed,family,eps,plan,block='main'):
    P13=learner_plan(plan);burn=plan['burn_in'];rate=plan['mask_rate'];nm=plan['noise_model']
    tr=plan['tolerant_region'];eps_bar=0.02;delta=0.01
    check(eps in tuple(nm['levels'].values()),'eps level')
    v=plan_view(P13);p6=plan006_keys(v);attest=family in P13['in_family_2x2']
    def att():return ScopeAttestation(p6['declared_family'],'evaluator','synthetic world built inside the family') if attest else None
    base=world(seed,family);B=planned_bits(base,rate);m=m_rule(B,eps_bar,delta);W=NoisyWorld(base,seed,eps)
    t0=perf_counter();truth,initial,sp8=S12.trajectory_2x2('SP8',seed,family,rate,v,p6,TAU6,att,truth=W)
    sp8['arm_wall_informational']=perf_counter()-t0
    check(W.readings==READINGS and W.observed_bits==B,'B recount equals planned B')
    c={'schema':'brute.case.v16_0','block':block,'seed':seed,'family':family,'eps':eps,'mask_rate':rate,
       'in_family_EVALUATOR_ONLY':family in P13['in_family_2x2'],'attested':bool(attest),
       'true_hidden_state_count_EVALUATOR_ONLY':truth.n,'initial_visible':list(initial),
       'initial_latent_EVALUATOR_ONLY':base.emission(base.start),
       'steps':P13['actions_per_case_2x2'],'burn_in':P13['burn_in'],'tau6':TAU6,'tau_v030':v['tau_v030'],
       'eps_bar':eps_bar,'delta':delta,'B':B,'m':m,'realized_flips':len(W.flips),'flip_positions_EVALUATOR_ONLY':W.flips,
       'arms':{'SP8':sp8}}
    check(c['steps']==plan['actions_per_case'] and c['burn_in']==burn,'case constants')
    init=tuple(initial);S=sp8_steps(c);acts=[s[1] for s in S];obs=[s[4] for s in S];wall={}
    t1=perf_counter();c['bounded']={'4':_bounded(init,S,(FB,))[str(FB)]};wall['RG4']=perf_counter()-t1
    flips=c['realized_flips'];ms={'RGN4':m,'RGN4_0':0,'RGN4_or':flips};noisy={}
    for arm in RGN_ARMS:
        share=None
        if arm=='RGN4_or':share='RGN4' if flips==m else 'RGN4_0' if flips==0 else None
        t1=perf_counter()
        if share:r=noisy[share];noisy[arm]={'m':flips,'support':r['support'],'unknown':r['unknown'],'shared_with':share}
        else:
            r=noisy_supports(init,acts,obs,FB,ms[arm]);noisy[arm]={'m':ms[arm],'support':r['support'],'unknown':r['unknown'],'shared_with':None}
        wall[arm]=perf_counter()-t1
    c['noisy']=noisy;c['region_wall_informational']=wall
    T={'RG4':rg_arm(S,{'4':c['bounded']['4']},FB,burn)}
    for arm in RGN_ARMS:T[arm]=rgn_arm(S,noisy[arm]['support'],noisy[arm]['m'],burn)
    c['certifiers']=T;c['summary']=summary(S,T)
    return c


# ------------------------------------------------------------------ jobs
def jobs_for(plan,block):
    R=plan['heldout_ranges']['targets'];lv=plan['noise_model']['levels']
    main=[('main',fam,seed,e) for fam,(a,b) in R.items() for seed in range(a,b+1) for e in (lv['eps0_control'],lv['eps1'],lv['eps2'])]
    stress=[('stress',fam,seed,lv['eps5_stress']) for fam,(a,b) in R.items() for seed in range(a,b+1)]
    if block=='transfer':return main+stress
    if block=='main':return main
    if block in SMOKE_BLOCKS:
        E=tuple(lv.values()) if block!='smoke-api' else (lv['eps2'],)
        return [(block,smoke_family(s),s,e) for s in SMOKE_BLOCKS[block] for e in E]
    raise ValueError(block)


def key(job):return '/'.join(map(str,job))


def check_job(job,plan):
    block,fam,seed,eps=job;lv=plan['noise_model']['levels']
    check(block in ('main','stress')+tuple(SMOKE_BLOCKS),'block '+str(block))
    if block=='main':check(eps in (lv['eps0_control'],lv['eps1'],lv['eps2']),'main eps');check_run_seeds('target',[seed],plan,family=fam)
    elif block=='stress':check(eps==lv['eps5_stress'],'stress eps');check_run_seeds('target',[seed],plan,family=fam)
    else:
        check(eps in tuple(lv.values()),'eps');check_run_seeds('smoke',[seed],plan)
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


def _select(plan,block,every,offset,limit):
    jobs=jobs_for(plan,block)[offset::every]
    return jobs[:limit] if limit else jobs


def _write(output,plan,block,sel,keys,cases,complete,extra):
    smoke=block not in ('transfer','main')
    result={'schema':'brute.study.v16_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,
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
    if block in ('transfer','main'):check_freeze()
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
    if a.block not in ('transfer','main'):check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-018')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.every,a.offset,a.limit))
    else:run(out,a.workers,a.block,a.limit,a.every,a.offset);print('done')
