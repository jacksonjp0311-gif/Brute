"""Run pre-registered study BRUTE-090-WINDOW-011 (experiments/BRUTE_PLAN_011.json).

Block and arms (plan arms_by_block): 2x2 only
  J9  brute.jumpwindow.WindowSyncLearner (study-010 SP8 trace format + per-step hull_union / hull_unknown of the
      jump-window hull, recorded as J8 recorded its hull in study-010)
  SP8 brute.align.AlignedSyncLearner (study-010 trace code, unchanged)
  A4 (frozen, full) and A2 (frozen, slim) via the frozen study-006 trajectory code
Every action is predicted before acting (dual / all-action coverage). Hidden truth never reaches a learner.
Seeds: every job is checked by scripts/check_seeds_011.check_run_seeds BEFORE its world is generated (held-out jobs
against their family range, smoke jobs against 4190001-4190030 / 3190001-3190030); a violation raises
VerificationError. Resumable: every finished case is appended to <output>/CHECKPOINT.jsonl; a restart skips finished
cases. RESULTS.json, SCIENTIFIC.json and SEAL.json refuse to overwrite.
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
from brute.align import AlignedSyncLearner
from brute.evaluation import loss,no_time
import experiments.brute_study_006 as S6
import experiments.brute_study_009 as S9
import experiments.brute_study_007 as S7
from experiments.brute_study_005 import _r
from experiments.worlds_011 import world,next_hidden,FAMILIES_2X2
from experiments.brute_common_011 import (PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,plan_view,
                                          plan006_keys,Checkpoint)
from scripts.check_seeds_011 import check_run_seeds

ARMS_2X2=('J9','SP8','A4','A2')
DRIFT=S7.DRIFT
SMOKE_MASK=0.35
BLOCKS=('2x2',)
_fc=S9._fc   # frozen study-009 forecast fields (A5 fields + cert_rule)


def trajectory_2x2(arm,seed,family,mask_rate,v,p6,tau6,att):
    """J9 / SP8: the study-010 trace (same fields, same order of calls); J9 adds hull_union / hull_unknown,
    recorded after the step's predicts and before acting (family supported before the forecast, else None / 0)."""
    truth=world(seed,family);hidden=truth.start;initial=truth.observed(hidden,mask_rate,-1)
    kw=dict(surprise_fraction=v['surprise_fraction'],recency_window=v['recency_window'],burn_in=v['burn_in'])
    if arm=='J9':L=WindowSyncLearner(*S9._base(p6),tau6,att(),policy='LU-R',rule='CTR',window_K=v['jump_window_K'],**kw)
    elif arm=='SP8':L=AlignedSyncLearner(*S9._base(p6),tau6,att(),policy='LU-R',rule='CTR',**kw)
    else:raise ValueError(arm)
    L.initialize(initial)
    suffix={k:SuffixFrequency(k,0.7) for k in (1,2,4)}
    for b in suffix.values():b.initialize(initial)
    recs=[];tL=tE=tO=0.;nE=0
    for i,pa in enumerate(actions(seed,p6['actions_per_case'])):
        t0=perf_counter();exp=L.experiment(pa);tE+=perf_counter()-t0;nE+=1;a=exp['action']
        fs=(L.predict(0),L.predict(1));f=fs[a];L.record_issued(f)
        hull=L.hull_record() if arm=='J9' else None;tL+=perf_counter()-t0
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
        if arm=='J9':rec['hull_union'],rec['hull_unknown']=hull
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
        if arm in ('J9','SP8'):truth,initial,out[arm]=trajectory_2x2(arm,seed,family,mask_rate,v,p6,tau6,att)
        elif arm in ('A4','A2'):truth,initial,out[arm]=S6._trajectory(arm,seed,family,mask_rate,p6,tau6,att)
        else:raise ValueError(arm)
        out[arm]['arm_wall_informational']=perf_counter()-t0
    return {'schema':'brute.case.v9_0','block':block,'seed':seed,'family':family,'mask_rate':mask_rate,
            'in_family_EVALUATOR_ONLY':family in plan['in_family_2x2'],'attested':bool(attest),
            'true_hidden_state_count_EVALUATOR_ONLY':truth.n,'initial_visible':list(initial),
            'steps':plan['actions_per_case_2x2'],'burn_in':plan['burn_in'],'tau6':tau6,'tau_v030':v['tau_v030'],'arms':out}


# ------------------------------------------------------------------ jobs
def jobs_for(plan,block):
    """Ordered held-out job list of one block (G12 re-runs every index divisible by 3 of each block)."""
    if block not in BLOCKS:raise ValueError(block)
    J=[]
    for fam,(lo,hi) in plan['heldout_ranges_2x2'].items():
        for seed in range(lo,hi+1):
            for rate in plan['mask_rates']:J.append((block,fam,seed,rate))
    return J


def smoke_jobs(plan,block):
    """Smoke jobs: seeds 4190001-4190030 only, mask 0.35: 4190001-4190016 (2 per family). 4190025-4190027 are the
    kill drill (BRUTE_SMOKE_DRILL); 4190017-4190024 and 4190028-4190030 stay free."""
    check(block=='2x2',block);lo,hi=plan['smoke_seeds']['range'];J=[]
    if os.environ.get('BRUTE_SMOKE_DRILL'):
        fams=list(plan['heldout_ranges_2x2'])[:3];J=[('smoke-2x2',f,lo+24+n,SMOKE_MASK) for n,f in enumerate(fams)]
    else:
        s=lo
        for fam in plan['heldout_ranges_2x2']:
            for _ in range(2):J.append(('smoke-2x2',fam,s,SMOKE_MASK));s+=1
    check(all(lo<=j[2]<=hi for j in J),'smoke seeds exhausted');return J


def key(job):return '/'.join(map(str,job))


def check_job(job,plan):
    block,fam,seed,rate=job
    if block.startswith('smoke'):return check_run_seeds('smoke',[seed],plan)
    return check_run_seeds(block,[seed],plan,family=fam)


def run_job(job,plan):
    block,fam,seed,rate=job;check_job(job,plan);t0=perf_counter()
    check(block.endswith('2x2'),block);c=run_case_2x2(seed,fam,rate,plan,plan['tau6']['value'],block=block)
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
    result={'schema':'brute.study.v9_0','plan':plan,'block':block,'smoke':smoke,'complete':complete,
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
    if a.smoke:check(not Path(out).resolve().is_relative_to(STUDY_DIR.resolve()),'smoke output must not be inside results/study-011')
    if a.seal_partial:print('sealed partial',seal_partial(out,a.block,a.smoke,a.every,a.offset,a.limit))
    else:run(out,a.workers,a.block,a.limit,a.smoke,a.every,a.offset);print('done')
