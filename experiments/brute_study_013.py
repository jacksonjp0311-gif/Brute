"""Run pre-registered study BRUTE-0110-SOUND-TRANSFER-013 (experiments/BRUTE_PLAN_013.json).

Blocks and arms (plan arms_by_block):
  2x2       J10, J9, SP8, A4, A2: the frozen study-012 case code (experiments/brute_study_012.run_case_2x2), unchanged
  big78     SP8_78 = brute.bigstate.big(SP8) on experiments/worlds_013.moore78 (frozen study-012 case code)
  transfer  SP8 target trajectory (frozen study-012 code) + TR / AT / AT4 / DR (brute.soundtransfer.GatedTransfer, post
            hoc on the SP8 trace, learner-visible fields only) + LX (a new SP8 trajectory whose actions are chosen by
            brute.soundtransfer.lx_choose; certificates are SP8's own), each with the positive (p) and the
            wrong-family (n) library (brute.transfer.learn_motifs on the fully observed source, frozen study-012 code)
Every action is predicted before acting. Hidden truth never reaches a learner. Seeds: every job (and source) is
checked by scripts/check_seeds_013.check_run_seeds BEFORE its world is generated. Resumable checkpoints;
RESULTS/SCIENTIFIC/SEAL refuse to overwrite.
"""
from __future__ import annotations
import argparse,os,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from bgr89.worlds import actions
from brute.core.learner import ScopeAttestation
from brute.align import AlignedSyncLearner
from brute.transfer import TransferTracker
from brute.soundtransfer import GatedTransfer,lx_choose,MODES,CENSOR
from brute.evaluation import no_time
import experiments.brute_study_009 as S9
import experiments.brute_study_012 as S12
from experiments.worlds_013 import world,next_hidden
from experiments.brute_common_013 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,plan_view,
                                          plan006_keys,Checkpoint)
from scripts.check_seeds_013 import check_run_seeds,source_seed,ROTATE,TRANSFER_FAMILIES

ARMS_2X2=('J10','J9','SP8','A4','A2')
ARMS_BIG78=('SP8_78',)
GATED_ARMS=tuple(m+s for m in MODES for s in 'pn')
LX_ARMS=('LXp','LXn')
SMOKE_MASK=0.35
BLOCKS=('2x2','big78','transfer')
library=S12.library


def gated_arm(case,hyp,label,mode):
    """TR / AT / AT4 / DR on the SP8 trace of `case` (trace format: experiments/v0110_reference docstring)."""
    H,st=hyp;g=GatedTransfer(H,tuple(case['initial_visible']),case['burn_in'],mode);tr=g.tracker
    out={'library':label,'mode':mode,'M':g.M,'hypotheses_initial':tr.n0,'hypothesis_status':st,'alive_after_initial':len(tr.alive),
         'disabled_step':tr.disabled_step,'trace':[]}
    first=CENSOR;false=0
    for r in case['arms']['SP8']['trace']:
        t=r['step'];a=r['action'];R={a:r,1-a:r['counterfactual']};alive=len(tr.alive);conf=g.confirmations
        cert=[None,None];rule=[None,None]
        for b in (0,1):cert[b],rule[b]=g.decide(t,b,R[b]['certificate'],R[b]['support'])
        act={a:r['actual_emission_EVALUATOR_ONLY'],1-a:r['counterfactual_actual_EVALUATOR_ONLY']}
        wrong=[cert[b] is not None and cert[b]!=act[b] for b in (0,1)];false+=sum(wrong)
        if cert[a] is not None and first==CENSOR:first=t
        out['trace'].append({'step':t,'alive':alive,'confirmations':conf,'certificate':cert,'rule':rule,'wrong':wrong})
        g.observe(t,a,tuple(r['observed']),r['support'])
    out['disabled_step']=tr.disabled_step;out['first_cert_step']=first;out['false_certificates']=false
    out['certificates']=sum(c is not None for s in out['trace'] for c in s['certificate'])
    out['transfer_certificates']=sum(x=='transfer' for s in out['trace'] for x in s['rule'])
    out['disagreements']=sum(x=='dr-disagree' for s in out['trace'] for x in s['rule'])
    return out


def lx_trajectory(seed,family,mask_rate,plan,tau6,att,hyp,label):
    """LX arm: a new SP8 trajectory (frozen AlignedSyncLearner, CTR) on the same world / mask; the library chooses the
    action (brute.soundtransfer.lx_choose); the tracker is filtered by this trajectory's own observations."""
    v=plan_view(plan);p6=plan006_keys(v);H,st=hyp
    truth=world(seed,family);hidden=truth.start;initial=truth.observed(hidden,mask_rate,-1)
    L=AlignedSyncLearner(*S9._base(p6),tau6,att(),policy='LU-R',rule='CTR',surprise_fraction=v['surprise_fraction'],
                         recency_window=v['recency_window'],burn_in=v['burn_in'])
    L.initialize(initial);tr=TransferTracker(H,tuple(initial),v['burn_in'])
    out={'library':label,'hypotheses_initial':tr.n0,'hypothesis_status':st,'alive_after_initial':len(tr.alive),'trace':[]}
    first=CENSOR;false=0;cnt={'lx-split':0,'lx-plan':0,'sp8':0};t0=perf_counter()
    for i,pa in enumerate(actions(seed,p6['actions_per_case'])):
        exp=L.experiment(pa);sa=exp['action'];fs=(L.predict(0),L.predict(1));n=len(tr.alive)
        a,rule,vv,big,pred=lx_choose(tr,sa,L._certifiable_after);L.record_issued(fs[a]);cnt[rule]+=1
        nxt=[next_hidden(truth,hidden,b,i) for b in (0,1)];act=[truth.emission(h) for h in nxt]
        hidden=nxt[a];observed=truth.observed(hidden,mask_rate,i);L.observe(a,observed)
        cert=[fs[0].certificate,fs[1].certificate];wrong=[cert[b] is not None and cert[b]!=act[b] for b in (0,1)];false+=sum(wrong)
        if cert[a] is not None and first==CENSOR:first=i+1
        out['trace'].append({'step':i+1,'action':a,'sp8_action':sa,'passive_action':pa,'lx_rule':rule,'alive':n,'largest_group':big,
            'prediction':pred,'v':vv,'certificate':cert,'public_certificate':[fs[0].public_certificate,fs[1].public_certificate],
            'support':[list(f.support) if f.support is not None else None for f in fs],'solver_unknown':[f.solver_unknown for f in fs],
            'observed':list(observed),'actual_EVALUATOR_ONLY':act,'wrong':wrong})
        tr.observe(i+1,a,tuple(observed))
    out.update(disabled_step=tr.disabled_step,first_cert_step=first,false_certificates=false,rule_counts=cnt,
               certificates=sum(c is not None for s in out['trace'] for c in s['certificate']),
               public_wrong=sum(s['public_certificate'][b] is not None and s['public_certificate'][b]!=s['actual_EVALUATOR_ONLY'][b] for s in out['trace'] for b in (0,1)),
               diagnostics=L.diagnostics(),wall_informational=perf_counter()-t0)
    L.close();return out


def run_case_transfer(seed,family,mask_rate,plan,tau6,block='transfer',offset=None,smoke_sources=None):
    if family not in TRANSFER_FAMILIES:raise ValueError(family)
    c=S12.run_case_2x2(seed,family,mask_rate,plan,tau6,arms=('SP8',),block=block);c['schema']='brute.case.v11_0'
    if smoke_sources:pos,neg=smoke_sources
    else:
        off=seed-plan['heldout_ranges_transfer']['targets'][family][0]+1
        pos=source_seed(family,off,plan,False);neg=source_seed(family,off,plan,True)
    attest=family in plan['in_family_2x2'];p6=plan006_keys(plan_view(plan))
    def att():return ScopeAttestation(p6['declared_family'],'evaluator','synthetic world built inside the family') if attest else None
    c['libraries']={};c['transfer']={}
    for key_,suf,(sf,ss) in (('pos','p',pos),('neg','n',neg)):
        lib,hyp=library(sf,ss);c['libraries'][key_]=lib
        for mode in MODES:
            t0=perf_counter();c['transfer'][mode+suf]=gated_arm(c,hyp,key_,mode);c['transfer'][mode+suf]['wall_informational']=perf_counter()-t0
        c['transfer']['LX'+suf]=lx_trajectory(seed,family,mask_rate,plan,tau6,att,hyp,key_)
    if smoke_sources:c['smoke']=True;c['offset']=offset
    return c


# ------------------------------------------------------------------ jobs
def jobs_for(plan,block):
    if block not in BLOCKS:raise ValueError(block)
    R={'2x2':plan['heldout_ranges_2x2'],'big78':plan['heldout_ranges_big78'],'transfer':plan['heldout_ranges_transfer']['targets']}[block]
    return [(block,fam,seed,rate) for fam,(lo,hi) in R.items() for seed in range(lo,hi+1) for rate in plan['mask_rates']]


def smoke_jobs(plan,block):
    """Smoke jobs (seeds 6190001-6190030, mask 0.35). 2x2: 6190001-6190016 (2 per family); kill drill
    (BRUTE_SMOKE_DRILL): 6190025-6190027. big78: 6190017-6190020. transfer: targets 6190001-6190008 (2 per family),
    sources 6190021-6190028 (same offset)."""
    lo,hi=plan['smoke_seeds']['range'];J=[]
    if block=='2x2':
        if os.environ.get('BRUTE_SMOKE_DRILL'):
            fams=list(plan['heldout_ranges_2x2'])[:3];J=[('smoke-2x2',f,lo+24+n,SMOKE_MASK) for n,f in enumerate(fams)]
        else:
            s=lo
            for fam in plan['heldout_ranges_2x2']:
                for _ in range(2):J.append(('smoke-2x2',fam,s,SMOKE_MASK));s+=1
    elif block=='big78':J=[('smoke-big78','moore78',lo+16+n,SMOKE_MASK) for n in range(4)]
    elif block=='transfer':
        s=lo
        for fam in TRANSFER_FAMILIES:
            for _ in range(2):J.append(('smoke-transfer',fam,s,SMOKE_MASK));s+=1
    else:raise ValueError(block)
    check(all(lo<=j[2]<=hi for j in J),'smoke seeds exhausted');return J


def key(job):return '/'.join(map(str,job))


def _smoke_sources(job,plan):
    block,fam,seed,rate=job;lo=plan['smoke_seeds']['range'][0];off=seed-lo+1;s=lo+20+off-1
    check_run_seeds('smoke',[s],plan);return off,((fam,s),(ROTATE[fam],s))


def check_job(job,plan):
    block,fam,seed,rate=job
    if block.startswith('smoke'):
        check_run_seeds('smoke',[seed],plan)
        if block=='smoke-transfer':_smoke_sources(job,plan)
        return
    if block=='transfer':
        check_run_seeds('target',[seed],plan,family=fam);off=seed-plan['heldout_ranges_transfer']['targets'][fam][0]+1
        source_seed(fam,off,plan,False);source_seed(fam,off,plan,True);return
    return check_run_seeds(block,[seed],plan,family=fam)


def run_job(job,plan):
    block,fam,seed,rate=job;check_job(job,plan);t0=perf_counter();tau6=plan['tau6']['value']
    if block.endswith('2x2'):c=S12.run_case_2x2(seed,fam,rate,plan,tau6,arms=ARMS_2X2,block=block)
    elif block.endswith('big78'):c=S12.run_case_big78(seed,rate,plan,tau6,arms=ARMS_BIG78,block=block)
    elif block=='smoke-transfer':
        off,ss=_smoke_sources(job,plan);c=run_case_transfer(seed,fam,rate,plan,tau6,block=block,offset=off,smoke_sources=ss)
    elif block=='transfer':c=run_case_transfer(seed,fam,rate,plan,tau6,block=block)
    else:raise ValueError(block)
    c['case_wall_informational']=perf_counter()-t0
    return key(job),c


def _job(x):return run_job(*x)


def run_jobs(jobs,plan,workers,ckpt,log=print):
    for j in jobs:check_job(j,plan)
    todo=[j for j in jobs if key(j) not in ckpt.done];log(f'{len(jobs)-len(todo)} cached, {len(todo)} to run',flush=True)
    if workers<=1:
        for j in todo:k_,c=run_job(j,plan);ckpt.add(k_,c);log('done '+k_,flush=True)
    else:
        with ProcessPoolExecutor(workers) as ex:
            futs=[ex.submit(_job,(j,plan)) for j in todo]
            for n,fu in enumerate(as_completed(futs)):
                k_,c=fu.result();ckpt.add(k_,c);log(f'done {n+1}/{len(todo)} {k_} {c["case_wall_informational"]:.1f}s',flush=True)
    return [ckpt.done[key(j)] for j in jobs]


def _select(plan,block,smoke,every,offset,limit):
    jobs=(smoke_jobs(plan,block) if smoke else jobs_for(plan,block))[offset::every]
    return jobs[:limit] if limit else jobs


def _write(output,plan,block,smoke,sel,keys,cases,complete,extra):
    result={'schema':'brute.study.v11_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,
            'job_selection':sel,'job_keys':keys,'cases':cases,**extra}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE),
        'case_count':len(cases),'expected_case_count':len(keys),'complete':complete,'smoke':smoke,'job_selection':sel,
        **({'missing_job_keys':extra['missing_job_keys']} if 'missing_job_keys' in extra else {})})


def seal_partial(output,block,smoke=False,every=1,offset=0,limit=None,reason='stream budget or study cap'):
    output=Path(output);plan=load(PLAN)
    for name in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/name).exists(),'refusing overwrite '+str(output/name))
    jobs=_select(plan,block,smoke,every,offset,limit);ck=Checkpoint(output/'CHECKPOINT.jsonl');keys=[key(j) for j in jobs]
    done=[k for k in keys if k in ck.done];missing=[k for k in keys if k not in ck.done]
    _write(output,plan,block,smoke,{'every':every,'offset':offset,'limit':limit},keys,[ck.done[k] for k in done],False,
           {'stop_reason':reason,'missing_job_keys':missing,'total_elapsed_informational':None})
    return len(done),len(keys)


def run(output,workers,block,limit=None,smoke=False,every=1,offset=0):
    output=Path(output);plan=load(PLAN)
    check(plan['tau6']['value']==1.645215321642 and plan['tau7']['value']==2.07944154168,'tau values (G13)')
    if not smoke:check_freeze()
    for name in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/name).exists(),'refusing overwrite '+str(output/name))
    started=time.perf_counter();jobs=_select(plan,block,smoke,every,offset,limit)
    output.mkdir(parents=True,exist_ok=True)
    cases=run_jobs(jobs,plan,workers,Checkpoint(output/'CHECKPOINT.jsonl'))
    _write(output,plan,block,smoke,{'every':every,'offset':offset,'limit':limit},[key(j) for j in jobs],cases,True,
           {'total_elapsed_informational':time.perf_counter()-started})


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--block',choices=BLOCKS,default='2x2')
    ap.add_argument('--output');ap.add_argument('--workers',type=int,default=3);ap.add_argument('--limit',type=int)
    ap.add_argument('--smoke',action='store_true');ap.add_argument('--every',type=int,default=1);ap.add_argument('--offset',type=int,default=0)
    ap.add_argument('--seal-partial',action='store_true')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.smoke:check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-013')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.smoke,a.every,a.offset,a.limit))
    else:run(out,a.workers,a.block,a.limit,a.smoke,a.every,a.offset);print('done')
