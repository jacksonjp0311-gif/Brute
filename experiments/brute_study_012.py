"""Run pre-registered study BRUTE-0100-SUPPORT-TRANSFER-012 (experiments/BRUTE_PLAN_012.json).

Blocks and arms (plan arms_by_block):
  2x2       J10 brute.supportwindow.SupportWindowLearner (study-011 J9 trace format, hull_union = supW), J9 (frozen,
            unchanged trace), SP8 (frozen study-010/011 trace code), A4 / A2 via the frozen study-006 trajectory code
  big78     J10_78 / SP8_78 = brute.bigstate.big(J10 / SP8) on experiments/worlds_012.moore78 (attested family
            deterministic-moore<=8/stationary)
  transfer  SP8 on the frozen family world of each target seed, plus TRp / TRn (brute.transfer.TransferTracker inside
            that SP8 trajectory, learner-visible fields only) with the positive / negative-control source library
            (brute.transfer.learn_motifs on the fully observed source, mask 0.0, 60 passive steps)
Every action is predicted before acting (dual / all-action coverage). Hidden truth never reaches a learner.
Seeds: every job (and every transfer source) is checked by scripts/check_seeds_012.check_run_seeds BEFORE its world is
generated; a violation raises VerificationError. Resumable checkpoints; RESULTS/SCIENTIFIC/SEAL refuse to overwrite.
"""
from __future__ import annotations
import argparse,os,time
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from bgr89.worlds import actions
from bgr89.baselines import SuffixFrequency
from brute.core.learner import ScopeAttestation
from brute.jumpwindow import WindowSyncLearner
from brute.supportwindow import SupportWindowLearner
from brute.bigstate import big
from brute.transfer import learn_motifs,expand,TransferTracker
from brute.align import AlignedSyncLearner
from brute.evaluation import loss,no_time
import experiments.brute_study_006 as S6
import experiments.brute_study_009 as S9
import experiments.brute_study_007 as S7
from experiments.brute_study_005 import _r
from experiments.worlds_012 import world,next_hidden,FAMILIES_2X2,moore78,source_codes
from experiments.brute_common_012 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,plan_view,
                                          plan006_keys,Checkpoint)
from scripts.check_seeds_012 import check_run_seeds,source_seed,ROTATE,TRANSFER_FAMILIES

ARMS_2X2=('J10','J9','SP8','A4','A2')
ARMS_BIG78=('J10_78','SP8_78')
ARMS_TRANSFER=('SP8','TRp','TRn')
LEARNERS={'J10':SupportWindowLearner,'J9':WindowSyncLearner,'SP8':AlignedSyncLearner}
WINDOWED=('J10','J9')
SOURCE_STEPS=60
BIG_FAMILY='deterministic-moore<=8/stationary'
DRIFT=S7.DRIFT
SMOKE_MASK=0.35
BLOCKS=('2x2','big78','transfer')
_fc=S9._fc   # frozen study-009 forecast fields (A5 fields + cert_rule)


def trajectory_2x2(arm,seed,family,mask_rate,v,p6,tau6,att,truth=None):
    """J10 / J9 / SP8 (and their big78 wrappers J10_78 / SP8_78): the study-011 trace (same fields, same order of
    calls); J10 / J9 add hull_union / hull_unknown (J10: supW), recorded after the step's predicts and before acting."""
    truth=truth or world(seed,family);hidden=truth.start;initial=truth.observed(hidden,mask_rate,-1)
    kw=dict(surprise_fraction=v['surprise_fraction'],recency_window=v['recency_window'],burn_in=v['burn_in'])
    base_arm=arm[:-3] if arm.endswith('_78') else arm
    if base_arm not in LEARNERS:raise ValueError(arm)
    cls=LEARNERS[base_arm];cls=big(cls) if arm.endswith('_78') else cls
    if base_arm in WINDOWED:kw['window_K']=v['jump_window_K']
    L=cls(*S9._base(p6),tau6,att(),policy='LU-R',rule='CTR',**kw)
    L.initialize(initial)
    suffix={k:SuffixFrequency(k,0.7) for k in (1,2,4)}
    for b in suffix.values():b.initialize(initial)
    recs=[];tL=tE=tO=0.;nE=0
    for i,pa in enumerate(actions(seed,p6['actions_per_case'])):
        t0=perf_counter();exp=L.experiment(pa);tE+=perf_counter()-t0;nE+=1;a=exp['action']
        fs=(L.predict(0),L.predict(1));f=fs[a];L.record_issued(f)
        hull=L.hull_record() if base_arm in WINDOWED else None;tL+=perf_counter()-t0
        base_={k:b.predict(a) for k,b in suffix.items()}
        nxt=[next_hidden(truth,hidden,b,i) for b in (0,1)];act=[truth.emission(h) for h in nxt]
        hidden=nxt[a];actual=act[a];observed=truth.observed(hidden,mask_rate,i)
        t0=perf_counter();surprise=L.observe(a,observed);dt=perf_counter()-t0;tL+=dt;tO+=dt
        for k,b in suffix.items():b.observe(a,observed)
        W=L.window_learner;v090=f.support[0] if f.support is not None and len(f.support)==1 else None
        E={'scores':exp['scores'],'score':exp['score'],'tied':exp['tied'],'check':exp.get('check',False),
           'proposal':exp.get('proposal'),'volumes':exp['volumes'],'rule':exp['policy']}
        rec={'step':i+1,'action':a,'passive_action':pa,'actual_emission_EVALUATOR_ONLY':actual,
             'counterfactual_actual_EVALUATOR_ONLY':act[1-a],'drift_step':family=='drift4' and (i+1) in DRIFT,
             **_fc(f,actual),'public_reason':f.public_reason.value if f.public_reason else None,
             'counterfactual':_fc(fs[1-a],act[1-a]),'logloss':round(loss(f.probabilities,actual),10),
             'min_probability':round(min(min(fs[0].probabilities),min(fs[1].probabilities)),12),
             'alarm_after':L.alarm_step is not None,'observed':list(observed),'residual_before':_r(f.residual),
             'surprise':_r(surprise),'residual_after':_r(L.residual),'v090_certificate':v090,
             'v090_wrong':v090 is not None and v090!=actual,'logloss_v090':round(loss(f.v090_probabilities,actual),10),
             'logloss_suffix':{str(k):round(loss(p,actual),10) for k,p in base_.items()},
             'family_status_after':L.support.status,'margin_status_after':L.margin.status,
             'family_rows_after':None,'margin_rows_after':None,
             'window_status_after':None if W is None else W.status,'window_rows_after':None,'resumes_after':L.resumes,
             'experiment':E}
        if base_arm in WINDOWED:rec['hull_union'],rec['hull_unknown']=hull
        recs.append(rec)
    rets=[dict(r,actual_EVALUATOR_ONLY=recs[r['step']-1]['actual_emission_EVALUATOR_ONLY'],
               wrong=r['certificate']!=recs[r['step']-1]['actual_emission_EVALUATOR_ONLY']) for r in L.retractions()]
    out={'trace':recs,'retractions':rets,'issued':[list(x) for x in L.issued],'diagnostics':L.diagnostics(),
         'elapsed_informational':tL,'experiment_calls':nE,'experiment_elapsed_informational':tE,'observe_elapsed_informational':tO}
    L.close();return truth,initial,out


def run_case_2x2(seed,family,mask_rate,plan,tau6,arms=ARMS_2X2,block='2x2'):
    if family not in FAMILIES_2X2:raise ValueError(family)
    v=plan_view(plan);p6=plan006_keys(v);attest=family in plan['in_family_2x2']
    def att():return ScopeAttestation(p6['declared_family'],'evaluator','synthetic world built inside the family') if attest else None
    out={}
    for arm in arms:
        t0=perf_counter()
        if arm in LEARNERS:truth,initial,out[arm]=trajectory_2x2(arm,seed,family,mask_rate,v,p6,tau6,att)
        elif arm in ('A4','A2'):truth,initial,out[arm]=S6._trajectory(arm,seed,family,mask_rate,p6,tau6,att)
        else:raise ValueError(arm)
        out[arm]['arm_wall_informational']=perf_counter()-t0
    return {'schema':'brute.case.v10_0','block':block,'seed':seed,'family':family,'mask_rate':mask_rate,
            'in_family_EVALUATOR_ONLY':family in plan['in_family_2x2'],'attested':bool(attest),
            'true_hidden_state_count_EVALUATOR_ONLY':truth.n,'initial_visible':list(initial),
            'steps':plan['actions_per_case_2x2'],'burn_in':plan['burn_in'],'tau6':tau6,'tau_v030':v['tau_v030'],'arms':out}


def run_case_big78(seed,mask_rate,plan,tau6,arms=ARMS_BIG78,block='big78'):
    """J10_78 / SP8_78 on moore78(seed); attested family deterministic-moore<=8/stationary (in family by construction)."""
    v=plan_view(plan);p6=plan006_keys(v)
    def att():return ScopeAttestation(BIG_FAMILY,'evaluator','synthetic world built inside the family')
    out={}
    for arm in arms:
        t0=perf_counter();truth,initial,out[arm]=trajectory_2x2(arm,seed,'moore78',mask_rate,v,p6,tau6,att,truth=moore78(seed))
        out[arm]['arm_wall_informational']=perf_counter()-t0
    return {'schema':'brute.case.v10_0','block':block,'seed':seed,'family':'moore78','mask_rate':mask_rate,
            'in_family_EVALUATOR_ONLY':True,'attested':True,'declared_family':BIG_FAMILY,
            'true_hidden_state_count_EVALUATOR_ONLY':truth.n,'initial_visible':list(initial),
            'steps':plan['actions_per_case_2x2'],'burn_in':plan['burn_in'],'tau6':tau6,'tau_v030':v['tau_v030'],'arms':out}


_LIB={};_HYP={}


def library(source_family,source_seed_):
    """brute.transfer.learn_motifs on the fully observed source (60 frozen passive steps); memoised per process."""
    k=(source_family,source_seed_)
    if k not in _LIB:
        acts=list(actions(source_seed_,SOURCE_STEPS));t0=perf_counter()
        L=learn_motifs(source_codes(source_seed_,source_family,SOURCE_STEPS,acts),acts)
        H,st=expand(L);_HYP[k]=(H,st)
        _LIB[k]=dict({'source_family':source_family,'source_seed':source_seed_},**L,learn_wall_informational=perf_counter()-t0)
    return _LIB[k],_HYP[k]


def tr_arm(case,lib,hyp,label):
    """TR arm (transfer_definition.TR_arm) on the SP8 trace of `case`: learner-visible fields only for the decisions;
    the *_EVALUATOR_ONLY actuals are read afterwards to mark wrong certificates."""
    H,st=hyp;burn=case['burn_in'];tr=TransferTracker(H,tuple(case['initial_visible']),burn)
    out={'library':label,'hypotheses_initial':tr.n0,'hypothesis_status':st,'alive_after_initial':len(tr.alive),'disabled_step':tr.disabled_step,'trace':[]}
    first=45;false=0
    for r in case['arms']['SP8']['trace']:
        t=r['step'];a=r['action'];R={a:r,1-a:r['counterfactual']};alive=len(tr.alive)
        cert=[None,None];rule=[None,None]
        for b in (0,1):cert[b],rule[b]=tr.decide(t,b,R[b]['certificate'],R[b]['support'])
        act={a:r['actual_emission_EVALUATOR_ONLY'],1-a:r['counterfactual_actual_EVALUATOR_ONLY']}
        wrong=[cert[b] is not None and cert[b]!=act[b] for b in (0,1)];false+=sum(wrong)
        if cert[a] is not None and first==45:first=t
        out['trace'].append({'step':t,'alive':alive,'certificate':cert,'rule':rule,'wrong':wrong})
        tr.observe(t,a,tuple(r['observed']))
    out['disabled_step']=tr.disabled_step;out['first_cert_step']=first;out['false_certificates']=false
    out['transfer_certificates']=sum(x=='transfer' for s in out['trace'] for x in s['rule'])
    return out


def run_case_transfer(seed,family,mask_rate,plan,tau6,block='transfer',offset=None,smoke_sources=None):
    """SP8 target trajectory + TRp / TRn. Source seeds: transfer_definition.pairs (scripts/check_seeds_012.source_seed),
    or smoke_sources = ((pos_family, seed), (neg_family, seed)) for smoke jobs."""
    if family not in TRANSFER_FAMILIES:raise ValueError(family)
    c=run_case_2x2(seed,family,mask_rate,plan,tau6,arms=('SP8',),block=block)
    if smoke_sources:pos,neg=smoke_sources
    else:
        off=seed-plan['heldout_ranges_transfer']['targets'][family][0]+1
        pos=source_seed(family,off,plan,False);neg=source_seed(family,off,plan,True)
    c['libraries']={};c['transfer']={}
    for key_,arm,(sf,ss) in (('pos','TRp',pos),('neg','TRn',neg)):
        t0=perf_counter();lib,hyp=library(sf,ss);c['libraries'][key_]=lib
        c['transfer'][arm]=tr_arm(c,lib,hyp,key_);c['transfer'][arm]['wall_informational']=perf_counter()-t0
    if smoke_sources:c['smoke']=True;c['offset']=offset
    return c


# ------------------------------------------------------------------ jobs
def jobs_for(plan,block):
    """Ordered held-out job list of one block (G12 re-runs every index divisible by 3 of 2x2 and transfer)."""
    if block not in BLOCKS:raise ValueError(block)
    R={'2x2':plan['heldout_ranges_2x2'],'big78':plan['heldout_ranges_big78'],'transfer':plan['heldout_ranges_transfer']['targets']}[block]
    J=[]
    for fam,(lo,hi) in R.items():
        for seed in range(lo,hi+1):
            for rate in plan['mask_rates']:J.append((block,fam,seed,rate))
    return J


def smoke_jobs(plan,block):
    """Smoke jobs (seeds 5190001-5190030 only, mask 0.35). 2x2: 5190001-5190016 (2 per family); kill drill
    (BRUTE_SMOKE_DRILL): 5190025-5190027. big78: 5190017-5190020. transfer: targets 5190001-5190008 (2 per family),
    sources 5190021-5190028 (same offset)."""
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
    if block.endswith('2x2'):c=run_case_2x2(seed,fam,rate,plan,tau6,block=block)
    elif block.endswith('big78'):c=run_case_big78(seed,rate,plan,tau6,block=block)
    elif block=='smoke-transfer':
        off,ss=_smoke_sources(job,plan);c=run_case_transfer(seed,fam,rate,plan,tau6,block=block,offset=off,smoke_sources=ss)
    elif block=='transfer':c=run_case_transfer(seed,fam,rate,plan,tau6,block=block)
    else:raise ValueError(block)
    c['case_wall_informational']=perf_counter()-t0
    return key(job),c


def _job(x):return run_job(*x)


def run_jobs(jobs,plan,workers,ckpt,log=print):
    for j in jobs:check_job(j,plan)          # every seed asserted before any world is generated
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
    result={'schema':'brute.study.v10_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,
            'job_selection':sel,'job_keys':keys,'cases':cases,**extra}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'block':block,'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE),
        'case_count':len(cases),'expected_case_count':len(keys),'complete':complete,'smoke':smoke,'job_selection':sel,
        **({'missing_job_keys':extra['missing_job_keys']} if 'missing_job_keys' in extra else {})})


def seal_partial(output,block,smoke=False,every=1,offset=0,limit=None,reason='stream budget or study cap'):
    """Seal a stopped stream AS IT IS (stop_rule): RESULTS/SCIENTIFIC/SEAL from the finished checkpoint cases only,
    marked complete=False with the missing job keys. No case is run."""
    output=Path(output);plan=load(PLAN)
    for name in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/name).exists(),'refusing overwrite '+str(output/name))
    jobs=_select(plan,block,smoke,every,offset,limit);ck=Checkpoint(output/'CHECKPOINT.jsonl');keys=[key(j) for j in jobs]
    done=[k for k in keys if k in ck.done];missing=[k for k in keys if k not in ck.done]
    _write(output,plan,block,smoke,{'every':every,'offset':offset,'limit':limit},keys,[ck.done[k] for k in done],False,
           {'stop_reason':reason,'missing_job_keys':missing,'total_elapsed_informational':None})
    return len(done),len(keys)


def run(output,workers,block,limit=None,smoke=False,every=1,offset=0):
    """every/offset select a subset of the ordered jobs (G12 repro: every=3, offset=0)."""
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
    ap.add_argument('--seal-partial',action='store_true',help='seal the finished checkpoint cases of a stopped stream (no run)')
    a=ap.parse_args();out=a.output or str(STUDY_DIR/a.block)
    if a.smoke:check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-012')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.smoke,a.every,a.offset,a.limit))
    else:run(out,a.workers,a.block,a.limit,a.smoke,a.every,a.offset);print('done')
