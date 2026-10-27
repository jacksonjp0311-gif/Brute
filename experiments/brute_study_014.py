"""Study BRUTE-0120-BOUNDED-TRANSFER-014 runner (experiments/BRUTE_PLAN_014.json; one block: transfer).

Per target case (family f, seed, mask): the frozen SP8 trajectory (experiments.brute_study_012.run_case_2x2, arm SP8);
bounded supports n = 2..5 on it (brute.boundedtransfer.bounded_supports); RG2-RG5; for the positive and the
wrong-family library: DLF (margin 1), DLF0 (margin 0), the frozen v0.11.0 AT arm and LX trajectory
(experiments.brute_study_013.gated_arm / lx_trajectory imported unchanged), bounded supports on the LX trajectory
(n in dx_bounds(n_L)) and DX = DLF on it; the aliasing stress block (AT6, DLF, DLF0 with every wrong-family library);
the per-arm first certification step and speedup S. Record format: experiments/v0120_reference.py docstring.

The frozen 012 / 013 functions read the study-013 plan dict; experiments.brute_common_014.learner_plan returns it after
asserting every shared constant equals plan 014's. Seeds: scripts/check_seeds_014 (the runner refuses any seed
outside the requested block).
"""
from __future__ import annotations
import argparse,os,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from brute.core.learner import ScopeAttestation
from brute.boundedtransfer import FB,MARGIN,bounded_supports,rg_decide,BoundedTransfer
from brute.evaluation import no_time
from brute.soundtransfer import CENSOR
import experiments.brute_study_012 as S12
import experiments.brute_study_013 as S13
from experiments.brute_common_009 import plan006_keys
from experiments.brute_common_013 import plan_view
from experiments.brute_common_014 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,learner_plan,Checkpoint
from scripts.check_seeds_014 import (check_run_seeds,source_seed,stress_sources,smoke_family,smoke_source,
                                     smoke_stress_sources,TRANSFER_FAMILIES)

NS_SP8=(2,3,4,5)
RG_ARMS=tuple(f'RG{n}' for n in NS_SP8)
ARMS=RG_ARMS+('DLFp','DLFn','DLF0p','DLF0n','ATp','ATn','LXp','LXn','DXp','DXn')
SMOKE_MASK=0.35
SMOKE_BLOCKS={'smoke-transfer':range(7190001,7190009),'smoke-api':range(7190009,7190013),'smoke-drill':range(7190013,7190016)}
BLOCKS=('transfer',)+tuple(SMOKE_BLOCKS)
library=S12.library


def dx_bounds(nL):return sorted({FB,min(nL+1,FB)}|({nL+1} if nL+1<=5 else set()))


def sp8_steps(case):
    """Learner-visible SP8 rows per step: (t, a, cert[2], supp[2], obs) and the evaluator-only actual codes."""
    out=[]
    for r in case['arms']['SP8']['trace']:
        a=r['action'];R={a:r,1-a:r['counterfactual']}
        act={a:r['actual_emission_EVALUATOR_ONLY'],1-a:r['counterfactual_actual_EVALUATOR_ONLY']}
        out.append((r['step'],a,[R[0]['certificate'],R[1]['certificate']],[R[0]['support'],R[1]['support']],tuple(r['observed']),[act[0],act[1]]))
    return out


def lx_steps(lx):
    return [(r['step'],r['action'],list(r['certificate']),list(r['support']),tuple(r['observed']),list(r['actual_EVALUATOR_ONLY'])) for r in lx['trace']]


def _bounded(init,steps,ns):return bounded_supports(init,[s[1] for s in steps],[s[4] for s in steps],ns)


def rg_arm(steps,BS,n,burn):
    out={'n':n,'trace':[]};first=CENSOR;false=0;sup=BS[str(n)]['support']
    for i,(t,a,cert0,supp,obs,act) in enumerate(steps):
        cert=[None,None];rule=[None,None]
        for b in (0,1):cert[b],rule[b]=rg_decide(t,burn,cert0[b],supp[b],sup[i][b])
        wrong=[cert[b] is not None and cert[b]!=act[b] for b in (0,1)];false+=sum(wrong)
        if cert[a] is not None and first==CENSOR:first=t
        out['trace'].append({'step':t,'certificate':cert,'rule':rule,'wrong':wrong})
    out.update(first_cert_step=first,false_certificates=false,certificates=sum(c is not None for x in out['trace'] for c in x['certificate']),
               rg_certificates=sum(r=='rg' for x in out['trace'] for r in x['rule']))
    return out


def dlf_arm(steps,BS,init,burn,H,nL,margin,label,trajectory):
    g=BoundedTransfer(H,nL,init,burn,margin);nb=g.license_bound;tr=g.tracker
    out={'library':label,'trajectory':trajectory,'margin':margin,'min_n':nL,'license_bound':nb,'trace':[]};first=CENSOR;false=0
    for i,(t,a,cert0,supp,obs,act) in enumerate(steps):
        cert=[None,None];rule=[None,None];alive=len(tr.alive)
        for b in (0,1):cert[b],rule[b],_=g.decide(t,b,cert0[b],supp[b],{n:BS[str(n)]['support'][i][b] for n in {FB,nb}})
        wrong=[cert[b] is not None and cert[b]!=act[b] for b in (0,1)];false+=sum(wrong)
        if cert[a] is not None and first==CENSOR:first=t
        out['trace'].append({'step':t,'alive':alive,'certificate':cert,'rule':rule,'wrong':wrong})
        g.observe(t,a,obs)
    out.update(disabled_step=tr.disabled_step,first_cert_step=first,false_certificates=false,
               certificates=sum(c is not None for x in out['trace'] for c in x['certificate']),
               rg_certificates=sum(r=='rg' for x in out['trace'] for r in x['rule']),
               license_certificates=sum(r=='license' for x in out['trace'] for r in x['rule']))
    return out


def sources_for(seed,family,plan,smoke):
    if smoke:return smoke_source(seed),smoke_source(seed,True),smoke_stress_sources(seed)
    off=seed-plan['heldout_ranges_transfer']['targets'][family][0]+1
    return source_seed(family,off,plan),source_seed(family,off,plan,True),stress_sources(family,plan)


def run_case(seed,family,mask_rate,plan,block='transfer'):
    smoke=block!='transfer';P13=learner_plan(plan);tau6=plan['tau6']['value'];burn=plan['burn_in']
    if family not in TRANSFER_FAMILIES:raise ValueError(family)
    c=S12.run_case_2x2(seed,family,mask_rate,P13,tau6,arms=('SP8',),block=block);c['schema']='brute.case.v12_0'
    check(c['steps']==plan['actions_per_case'] and c['burn_in']==burn,'case constants')
    init=tuple(c['initial_visible']);S=sp8_steps(c);t0=perf_counter()
    c['bounded']={'SP8':_bounded(init,S,NS_SP8)};c['bounded_wall_informational']={'SP8':perf_counter()-t0}
    BS=c['bounded']['SP8'];T={f'RG{n}':rg_arm(S,BS,n,burn) for n in NS_SP8}
    pos,neg,stress=sources_for(seed,family,plan,smoke)
    attest=family in P13['in_family_2x2'];p6=plan006_keys(plan_view(P13))
    def att():return ScopeAttestation(p6['declared_family'],'evaluator','synthetic world built inside the family') if attest else None
    c['libraries']={}
    for key,suf,(sf,ss) in (('pos','p',pos),('neg','n',neg)):
        lib,hyp=library(sf,ss);c['libraries'][key]=lib;H=hyp[0];nL=lib['min_n']
        T['DLF'+suf]=dlf_arm(S,BS,init,burn,H,nL,MARGIN,key,'SP8');T['DLF0'+suf]=dlf_arm(S,BS,init,burn,H,nL,0,key,'SP8')
        t1=perf_counter();T['AT'+suf]=S13.gated_arm(c,hyp,key,'AT');T['AT'+suf]['wall_informational']=perf_counter()-t1
        lx=S13.lx_trajectory(seed,family,mask_rate,P13,tau6,att,hyp,key);T['LX'+suf]=lx;L=lx_steps(lx)
        t1=perf_counter();c['bounded']['LX'+suf]=_bounded(init,L,dx_bounds(nL));c['bounded_wall_informational']['LX'+suf]=perf_counter()-t1
        T['DX'+suf]=dlf_arm(L,c['bounded']['LX'+suf],init,burn,H,nL,MARGIN,key,'LX'+suf)
    c['transfer']=T
    f0=next((t for t,a,cert,_,_,_ in S if cert[a] is not None),CENSOR);first={a:T[a]['first_cert_step'] for a in ARMS}
    c['summary']={'first_cert_step':dict(first,SP8=f0),'S':{a:f0-first[a] for a in ARMS}}
    ts=c['true_hidden_state_count_EVALUATOR_ONLY'];c['stress']=[];t1=perf_counter()
    for sf,ss in stress:
        lib,hyp=library(sf,ss);H=hyp[0];nL=lib['min_n'];at=S13.gated_arm(c,hyp,'stress','AT')
        d1=dlf_arm(S,BS,init,burn,H,nL,MARGIN,'stress','SP8');d0=dlf_arm(S,BS,init,burn,H,nL,0,'stress','SP8')
        c['stress'].append({'source_family':sf,'source_seed':ss,'min_n':nL,'AT6_false':at['false_certificates'],'AT6_transfer':at['transfer_certificates'],
            'DLF_false':d1['false_certificates'],'DLF_license':d1['license_certificates'],'DLF_rg':d1['rg_certificates'],
            'DLF0_false':d0['false_certificates'],'DLF0_license':d0['license_certificates'],'outside_exact_bound_EVALUATOR_ONLY':ts>min(nL+1,FB)})
    c['stress_wall_informational']=perf_counter()-t1
    if smoke:c['smoke']=True
    return c


# ------------------------------------------------------------------ jobs
def jobs_for(plan,block):
    if block=='transfer':
        R=plan['heldout_ranges_transfer']['targets']
        return [(block,fam,seed,rate) for fam,(lo,hi) in R.items() for seed in range(lo,hi+1) for rate in plan['mask_rates']]
    if block in SMOKE_BLOCKS:return [(block,smoke_family(s),s,SMOKE_MASK) for s in SMOKE_BLOCKS[block]]
    raise ValueError(block)


def key(job):return '/'.join(map(str,job))


def check_job(job,plan):
    block,fam,seed,rate=job;check(block in BLOCKS,'block '+str(block));check(rate in plan['mask_rates'],'mask rate')
    if block=='transfer':
        check_run_seeds('target',[seed],plan,family=fam);sources_for(seed,fam,plan,False)
    else:
        check_run_seeds('smoke',[seed],plan);check(seed in SMOKE_BLOCKS[block] and smoke_family(seed)==fam,'smoke layout')
        sources_for(seed,fam,plan,True)


def run_job(job,plan):
    block,fam,seed,rate=job;check_job(job,plan);t0=perf_counter()
    c=run_case(seed,fam,rate,plan,block);c['case_wall_informational']=perf_counter()-t0
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
    smoke=block!='transfer'
    result={'schema':'brute.study.v12_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,
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
    check(plan['tau6']['value']==1.645215321642 and plan['tau7']['value']==2.07944154168,'tau values (G13)')
    if block=='transfer':check_freeze()
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
    if a.block!='transfer':check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-014')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.every,a.offset,a.limit))
    else:run(out,a.workers,a.block,a.limit,a.every,a.offset);print('done')
