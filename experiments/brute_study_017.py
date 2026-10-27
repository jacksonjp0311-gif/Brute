"""Study BRUTE-0150-BOUNDED-LOOKAHEAD-017 runner (experiments/BRUTE_PLAN_017.json; blocks: transfer = 360 main cases followed
by 72 ood5 cases, as one stream).

Per main target case: everything the study-016 runner records (frozen functions imported from
experiments.brute_study_016: SP8, RSX, RSXL trajectories; RG4 / RG5, RSXL4, RSXLp / RSXLn, DLFp / DLFn, DLF2p / DLF2n,
RSX4, EB; the 72-library stress block) plus two new trajectories on new frozen SP8 learners with the same world / mask:
  RGLX: actions by brute.boundedlookahead.rglx_choose (RGL lookahead while RG4 has not certified the taken action at an
        earlier step, then the frozen RSX choice);
  RGL:  actions by brute.boundedlookahead.rgl_choose throughout;
bounded supports n = 1..5 on both; RGLX4 / RGL4 = RG4 on them; DLFa_p / DLFa_n (attested license, H_att_exact).
ood5 cases: SP8 + bounded n = 1..5 + RG4 / RG5, and the RSXL5 trajectory (#89: rsxl_n_trajectory with n = 5) + bounded
n = 1..5 + RSXL5 = RG5 on it. Record format: experiments/v0150_reference.py docstring. Seeds: scripts/check_seeds_017.
"""
from __future__ import annotations
import argparse,os,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from bgr89.worlds import actions
from brute.core.learner import ScopeAttestation
from brute.align import AlignedSyncLearner
from brute.region import RegionSpace
from brute.boundedtransfer import FB,MARGIN,region_supports,rg_decide,dlf_decide
from brute.regionsplit import bounded_sizes
from brute.deferredsplit import rsxl_choose
from brute.boundedlookahead import lookahead,rgl_choose,rglx_choose,needs_lookahead,attested_license_bound
from brute.evaluation import no_time
from brute.soundtransfer import CENSOR
import experiments.brute_study_009 as S9
import experiments.brute_study_012 as S12
import experiments.brute_study_013 as S13
from experiments.brute_study_014 import sp8_steps,lx_steps,_bounded,rg_arm,dlf_arm
from experiments.brute_study_016 import rsx_trajectory,rsxl_trajectory,dlf2_arm,eb_arm,certs
from experiments.worlds_013 import world,next_hidden
from experiments.brute_common_009 import plan006_keys
from experiments.brute_common_013 import plan_view
from experiments.brute_common_017 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,learner_plan,Checkpoint
from scripts.check_seeds_017 import (check_run_seeds,source_seed,stress_sources,smoke_family,smoke_source,
                                     smoke_stress_sources,TRANSFER_FAMILIES)

NS=(1,2,3,4,5)
MAIN_ARMS=('RG4','RG5','RGLX4','RGL4','RSXL4','RSXLp','RSXLn','DLFp','DLFn','DLFa_p','DLFa_n','DLF2p','DLF2n','RSX4','EB')
OOD5_ARMS=('RG4','RG5','RSXL5')
SMOKE_MASK=0.35
SMOKE_BLOCKS={'smoke-transfer':list(range(8390001,8390009))+[8390016,8390017],'smoke-api':range(8390009,8390013),
              'smoke-drill':range(8390013,8390016)}
BLOCKS=('transfer',)+tuple(SMOKE_BLOCKS)
library=S12.library


def _learner(seed,family,mask_rate,P13,tau6,att):
    v=plan_view(P13);p6=plan006_keys(v)
    truth=world(seed,family);hidden=truth.start;initial=truth.observed(hidden,mask_rate,-1)
    L=AlignedSyncLearner(*S9._base(p6),tau6,att(),policy='LU-R',rule='CTR',surprise_fraction=v['surprise_fraction'],
                         recency_window=v['recency_window'],burn_in=v['burn_in'])
    L.initialize(initial);return p6,truth,hidden,initial,L


def rsxl_n_trajectory(seed,family,mask_rate,P13,tau6,att,burn,n):
    """RSXL with family bound n (#89): rsxl_choose on the online RegionSpace(n) sizes, certified_before from RG_n (frozen
    rg_decide on the RegionSpace(n) support of the taken action). n = 4 equals brute_study_016.rsxl_trajectory (tested)."""
    p6,truth,hidden,initial,L=_learner(seed,family,mask_rate,P13,tau6,att);R=RegionSpace(n);R.initialize(tuple(initial))
    out={'trace':[]};first=CENSOR;false=0;cnt={'rsx':0,'sp8':0};cb=False;switch=None;t0=perf_counter()
    try:
        for i,pa in enumerate(actions(seed,p6['actions_per_case'])):
            sa=L.experiment(pa)['action'];fs=(L.predict(0),L.predict(1));rs=region_supports(R)
            sizes=bounded_sizes(rs);a,rule=rsxl_choose(i+1,burn,sizes,sa,cb);L.record_issued(fs[a]);cnt[rule]+=1
            if cb and switch is None:switch=i+1
            deferred=not cb
            sup=[list(f.support) if f.support is not None else None for f in fs]
            if not cb and rg_decide(i+1,burn,fs[a].certificate,sup[a],rs[a][0])[0] is not None:cb=True
            nxt=[next_hidden(truth,hidden,b,i) for b in (0,1)];act=[truth.emission(h) for h in nxt]
            hidden=nxt[a];observed=truth.observed(hidden,mask_rate,i);L.observe(a,observed);R.observe(a,tuple(observed))
            cert=[fs[0].certificate,fs[1].certificate];wrong=[cert[b] is not None and cert[b]!=act[b] for b in (0,1)];false+=sum(wrong)
            if cert[a] is not None and first==CENSOR:first=i+1
            out['trace'].append({'step':i+1,'action':a,'sp8_action':sa,'passive_action':pa,'rsxl_rule':rule,'deferred':deferred,
                'bounded_sizes':sizes,'certificate':cert,'support':sup,
                'observed':list(observed),'actual_EVALUATOR_ONLY':act,'wrong':wrong})
    finally:R.close()
    out.update(first_cert_step=first,false_certificates=false,certificates=sum(c is not None for s in out['trace'] for c in s['certificate']),
               rule_counts=cnt,switch_step=switch)
    L.close();out['wall_informational']=perf_counter()-t0
    return out


def rgl_trajectory(seed,family,mask_rate,P13,tau6,att,burn,mode):
    """mode 'rglx' | 'rgl' (#88). A new frozen SP8 learner; RegionSpace(4) online; lookahead computed iff
    needs_lookahead; certified_before from RG4 (frozen rg_decide) on the taken action. Learner-visible only."""
    if mode not in ('rglx','rgl'):raise ValueError(mode)
    p6,truth,hidden,initial,L=_learner(seed,family,mask_rate,P13,tau6,att);R=RegionSpace(FB);R.initialize(tuple(initial))
    out={'trace':[]};first=CENSOR;false=0;cnt={'rgl':0,'rsx':0,'sp8':0};cb=False;switch=None;looks=0;lw=0.0;t0=perf_counter()
    try:
        for i,pa in enumerate(actions(seed,p6['actions_per_case'])):
            t=i+1;sa=L.experiment(pa)['action'];fs=(L.predict(0),L.predict(1));rs=region_supports(R);sizes=bounded_sizes(rs)
            look=None
            if needs_lookahead(t,burn,cb,mode):
                t1=perf_counter();look=lookahead(R,rs);lw+=perf_counter()-t1;looks+=1
            if mode=='rgl':a,rule=rgl_choose(t,burn,look,sa);deferred=True
            else:
                a,rule=rglx_choose(t,burn,sizes,look,sa,cb);deferred=not cb
                if cb and switch is None:switch=t
            L.record_issued(fs[a]);cnt[rule]+=1
            sup=[list(f.support) if f.support is not None else None for f in fs]
            if not cb and rg_decide(t,burn,fs[a].certificate,sup[a],rs[a][0])[0] is not None:cb=True
            nxt=[next_hidden(truth,hidden,b,i) for b in (0,1)];act=[truth.emission(h) for h in nxt]
            hidden=nxt[a];observed=truth.observed(hidden,mask_rate,i);L.observe(a,observed);R.observe(a,tuple(observed))
            cert=[fs[0].certificate,fs[1].certificate];wrong=[cert[b] is not None and cert[b]!=act[b] for b in (0,1)];false+=sum(wrong)
            if cert[a] is not None and first==CENSOR:first=t
            out['trace'].append({'step':t,'action':a,'sp8_action':sa,'passive_action':pa,'rule':rule,'deferred':deferred,
                'bounded_sizes':sizes,'lookahead':look,'certificate':cert,'support':sup,
                'observed':list(observed),'actual_EVALUATOR_ONLY':act,'wrong':wrong})
    finally:R.close()
    out.update(first_cert_step=first,false_certificates=false,certificates=sum(c is not None for s in out['trace'] for c in s['certificate']),
               rule_counts=cnt,switch_step=switch,lookahead_steps=looks)
    L.close();out['wall_informational']=perf_counter()-t0;out['lookahead_wall_informational']=lw
    return out


def dlfa_arm(steps,BS,init,burn,H,nL,label):
    """Attested license (H_att_exact): the frozen dlf_arm (margin 1) when attested_license_bound(n_L, 1, FB); else RG
    decisions (frozen dlf_decide with library_alive None) in DLF format."""
    if attested_license_bound(nL,MARGIN,FB):
        e=dlf_arm(steps,BS,init,burn,H,nL,MARGIN,label,'SP8');e['attested']=True;return e
    out={'library':label,'trajectory':'SP8','margin':MARGIN,'min_n':nL,'license_bound':None,'attested':False,'trace':[]};first=CENSOR;false=0
    for i,(t,a,cert0,supp,obs,act) in enumerate(steps):
        cert=[None,None];rule=[None,None]
        for b in (0,1):cert[b],rule[b],_=dlf_decide(t,burn,cert0[b],supp[b],BS[str(FB)]['support'][i][b],None,None,None)
        wrong=[cert[b] is not None and cert[b]!=act[b] for b in (0,1)];false+=sum(wrong)
        if cert[a] is not None and first==CENSOR:first=t
        out['trace'].append({'step':t,'alive':None,'certificate':cert,'rule':rule,'wrong':wrong})
    out.update(disabled_step=None,first_cert_step=first,false_certificates=false,
               certificates=sum(c is not None for x in out['trace'] for c in x['certificate']),
               rg_certificates=sum(r=='rg' for x in out['trace'] for r in x['rule']),license_certificates=0)
    return out


def sources_for(seed,family,plan,smoke):
    if smoke:return smoke_source(seed),smoke_source(seed,True),smoke_stress_sources(seed)
    off=seed-plan['heldout_ranges_transfer']['targets'][family][0]+1
    return source_seed(family,off,plan),source_seed(family,off,plan,True),stress_sources(family,plan)


def _summary(S,T,arms):
    f0=next((t for t,a,cert,_,_,_ in S if cert[a] is not None),CENSOR)
    sp8f=sum(cert[b] is not None and cert[b]!=act[b] for t,a,cert,_,_,act in S for b in (0,1))
    sp8n=sum(cert[b] is not None for t,a,cert,_,_,act in S for b in (0,1))
    first={a:T[a]['first_cert_step'] for a in arms}
    return {'first_cert_step':dict(first,SP8=f0),'S':{a:f0-first[a] for a in arms},
            'false':dict({a:T[a]['false_certificates'] for a in arms},SP8=sp8f),
            'certificates':dict({a:T[a]['certificates'] for a in arms},SP8=sp8n)}


def _traj(c,name,tr,init,where):
    X=lx_steps(tr);t1=perf_counter();c['bounded'][name]=_bounded(init,X,NS);c['bounded_wall_informational'][name]=perf_counter()-t1
    B=c['bounded'][name]
    for i,r in enumerate(tr['trace']):
        check([len(x) if x is not None else 0 for x in B[str(where)]['support'][i]]==r['bounded_sizes'],f'{name} online / replay n={where} sizes step {i+1}')
    return X,B


def run_case(seed,family,mask_rate,plan,block='transfer'):
    smoke=block!='transfer';P13=learner_plan(plan);tau6=plan['tau6']['value'];burn=plan['burn_in']
    if family not in TRANSFER_FAMILIES+('ood5',):raise ValueError(family)
    c=S12.run_case_2x2(seed,family,mask_rate,P13,tau6,arms=('SP8',),block=block);c['schema']='brute.case.v15_0'
    check(c['steps']==plan['actions_per_case'] and c['burn_in']==burn,'case constants')
    init=tuple(c['initial_visible']);S=sp8_steps(c);t0=perf_counter()
    c['bounded']={'SP8':_bounded(init,S,NS)};c['bounded_wall_informational']={'SP8':perf_counter()-t0};BS=c['bounded']['SP8']
    if smoke:c['smoke']=True
    attest=family in P13['in_family_2x2'];p6=plan006_keys(plan_view(P13))
    def att():return ScopeAttestation(p6['declared_family'],'evaluator','synthetic world built inside the family') if attest else None
    T={f'RG{n}':rg_arm(S,BS,n,burn) for n in (4,5)}
    if family=='ood5':
        c['rsxl5']=rsxl_n_trajectory(seed,family,mask_rate,P13,tau6,att,burn,5);X,BX=_traj(c,'RSXL5',c['rsxl5'],init,5)
        T['RSXL5']=rg_arm(X,BX,5,burn);f=T['RSXL5']['first_cert_step']
        check(c['rsxl5']['switch_step']==(f+1 if f<len(X) else None),'RSXL5 online switch step equals replayed RG5 first certificate + 1')
        c['transfer']=T;c['summary']=_summary(S,T,OOD5_ARMS);return c
    c['rsx']=rsx_trajectory(seed,family,mask_rate,P13,tau6,att,burn);R,BR=_traj(c,'RSX',c['rsx'],init,4)
    c['rsxl']=rsxl_trajectory(seed,family,mask_rate,P13,tau6,att,burn);X,BX=_traj(c,'RSXL',c['rsxl'],init,4)
    T['RSXL4']=rg_arm(X,BX,4,burn);f=T['RSXL4']['first_cert_step']
    check(c['rsxl']['switch_step']==(f+1 if f<len(X) else None),'RSXL online switch step equals replayed RG4 first certificate + 1')
    c['rglx']=rgl_trajectory(seed,family,mask_rate,P13,tau6,att,burn,'rglx');G,BG=_traj(c,'RGLX',c['rglx'],init,4)
    T['RGLX4']=rg_arm(G,BG,4,burn);f=T['RGLX4']['first_cert_step']
    check(c['rglx']['switch_step']==(f+1 if f<len(G) else None),'RGLX online switch step equals replayed RG4 first certificate + 1')
    c['rgl']=rgl_trajectory(seed,family,mask_rate,P13,tau6,att,burn,'rgl');Q,BQ=_traj(c,'RGL',c['rgl'],init,4)
    T['RGL4']=rg_arm(Q,BQ,4,burn)
    T['RSX4']=rg_arm(R,BR,4,burn);T['EB']=eb_arm(S,BS,burn,1)
    pos,neg,stress=sources_for(seed,family,plan,smoke);c['libraries']={}
    for key_,suf,(sf,ss) in (('pos','p',pos),('neg','n',neg)):
        lib,hyp=library(sf,ss);c['libraries'][key_]=lib;H=hyp[0];nL=lib['min_n']
        T['DLF'+suf]=dlf_arm(S,BS,init,burn,H,nL,MARGIN,key_,'SP8');T['DLF2'+suf]=dlf2_arm(S,BS,init,burn,H,nL,2,key_,'SP8')
        T['RSXL'+suf]=dlf_arm(X,BX,init,burn,H,nL,MARGIN,key_,'RSXL');T['DLFa_'+suf]=dlfa_arm(S,BS,init,burn,H,nL,key_)
    c['transfer']=T;c['summary']=_summary(S,T,MAIN_ARMS)
    ts=c['true_hidden_state_count_EVALUATOR_ONLY'];c['stress']=[];t1=perf_counter()
    for sf,ss in stress:
        lib,hyp=library(sf,ss);H=hyp[0];nL=lib['min_n'];at=S13.gated_arm(c,hyp,'stress','AT')
        d1=dlf_arm(S,BS,init,burn,H,nL,MARGIN,'stress','SP8');d2=dlf_arm(X,BX,init,burn,H,nL,MARGIN,'stress','RSXL')
        c['stress'].append({'source_family':sf,'source_seed':ss,'min_n':nL,'AT6_false':at['false_certificates'],'AT6_transfer':at['transfer_certificates'],
            'DLF_false':d1['false_certificates'],'DLF_license':d1['license_certificates'],'DLF_rg':d1['rg_certificates'],'DLF_certs':certs(d1),
            'RSXL_false':d2['false_certificates'],'RSXL_license':d2['license_certificates'],'RSXL_rg':d2['rg_certificates'],'RSXL_certs':certs(d2),
            'outside_exact_bound_EVALUATOR_ONLY':ts>min(nL+1,FB)})
    c['stress_wall_informational']=perf_counter()-t1
    return c


# ------------------------------------------------------------------ jobs
def jobs_for(plan,block):
    if block=='transfer':
        R=plan['heldout_ranges_transfer']['targets'];lo,hi=plan['heldout_ranges_transfer']['ood5_targets']
        main=[(block,fam,seed,rate) for fam,(a,b) in R.items() for seed in range(a,b+1) for rate in plan['mask_rates']]
        return main+[(block,'ood5',seed,rate) for seed in range(lo,hi+1) for rate in plan['mask_rates']]
    if block in SMOKE_BLOCKS:return [(block,smoke_family(s),s,SMOKE_MASK) for s in SMOKE_BLOCKS[block]]
    raise ValueError(block)


def key(job):return '/'.join(map(str,job))


def check_job(job,plan):
    block,fam,seed,rate=job;check(block in BLOCKS,'block '+str(block));check(rate in plan['mask_rates'],'mask rate')
    if block=='transfer':
        if fam=='ood5':check_run_seeds('ood5',[seed],plan)
        else:check_run_seeds('target',[seed],plan,family=fam);sources_for(seed,fam,plan,False)
    else:
        check_run_seeds('smoke',[seed],plan);check(seed in SMOKE_BLOCKS[block] and smoke_family(seed)==fam,'smoke layout')
        if fam!='ood5':sources_for(seed,fam,plan,True)


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
    smoke=block not in ('transfer','ood5')
    result={'schema':'brute.study.v15_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,
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
    check(plan['tau6']['value']==1.645215321642 and 'tau7' not in plan,'tau6 value (G13)')
    if block in ('transfer','ood5'):check_freeze()
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
    if a.block not in ('transfer','ood5'):check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-017')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.every,a.offset,a.limit))
    else:run(out,a.workers,a.block,a.limit,a.every,a.offset);print('done')
