"""Run pre-registered study BRUTE-050-REGION-007 (experiments/BRUTE_PLAN_007.json).

Blocks and arms (plan arms_by_block):
  2x2      A5 (RegionBruteLearner, LU-R), M5 (RegionBruteLearner, M policy)   [full trace, solver_unknown, volumes]
           A4 (frozen ResumeBruteLearner through the frozen study-006 trajectory, full)  A2 (frozen v0.2.0, slim)
  breadth  B5 (BreadthBruteLearner LU-R_k), BM5 (M policy), BP5 (passive)        [full breadth trace]
  stress   B5 with conf_budget 20 on big6 at mask 0.35 (GX3 only)
Every action is predicted before acting (dual / all-action coverage). Hidden truth never reaches a learner.
Resumable: every finished case is appended to <output>/CHECKPOINT.jsonl; a restart skips finished cases. RESULTS.json,
SCIENTIFIC.json and SEAL.json refuse to overwrite. Run receipts: ledger 'run_start'/'run_end' (scripts/append_ledger.py).
"""
from __future__ import annotations
import argparse,time
from math import log
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor,as_completed
from bgr89.worlds import actions
from bgr89.baselines import SuffixFrequency
from brute.core.learner import ScopeAttestation
from brute.region_learner import RegionBruteLearner
from brute.breadth import BreadthBruteLearner
from brute.region import codes_mask,PRODUCTION_CONF_BUDGET
from brute.evaluation import loss,no_time
import experiments.brute_study_006 as S6
from experiments.brute_study_005 import _r
from experiments.worlds_006 import world,next_hidden
from experiments.worlds_007 import FAMILIES_2X2,FAMILIES_BREADTH,breadth_world,passive_actions,minimal_states
from experiments.brute_common_007 import PLAN,FREEZE,STUDY_DIR,load,sha,write_new,check_freeze,check,plan006_keys,Checkpoint

ARMS_2X2=('A5','M5','A4','A2')
ARMS_BREADTH=('B5','BM5','BP5')
DRIFT=(12,23,34)


def _fc(f,actual):
    return {'status':f.status.value,'reason':f.reason.value if f.reason else None,'certificate':f.certificate,
            'public_certificate':f.public_certificate,'wrong':f.certificate is not None and f.certificate!=actual,
            'public_wrong':f.public_certificate is not None and f.public_certificate!=actual,
            'support':list(f.support) if f.support is not None else None,
            'margin_support':list(f.margin_support) if f.margin_support is not None else None,
            'saturated':f.saturated,'forecast_source':f.forecast_source,
            'probabilities':[round(x,12) for x in f.probabilities],'solver_unknown':f.solver_unknown}


def region_learner(arm,p6,tau6,att,conf_budget=PRODUCTION_CONF_BUDGET):
    base=(p6['family_state_cap'],p6['margin_state_cap'],p6['row_budget_family'],p6['row_budget_margin'],
          p6['prediction_smoothing'],p6['open_world_reserve_epsilon'],p6['residual_surprise']['window_W'])
    return RegionBruteLearner(*base,tau6,att(),conf_budget=conf_budget,policy='M' if arm=='M5' else 'LU-R')


def trajectory_region(arm,seed,family,mask_rate,p6,tau6,att,conf_budget=PRODUCTION_CONF_BUDGET):
    """A5 / M5 full trace (the study-006 A4 full-trace fields plus solver_unknown, experiment volumes and rule)."""
    truth=world(seed,family);hidden=truth.start;initial=truth.observed(hidden,mask_rate,-1)
    L=region_learner(arm,p6,tau6,att,conf_budget);L.initialize(initial)
    suffix={k:SuffixFrequency(k,0.7) for k in (1,2,4)}
    for b in suffix.values():b.initialize(initial)
    recs=[];tL=tE=tO=0.;nE=0
    for i,pa in enumerate(actions(seed,p6['actions_per_case'])):
        t0=perf_counter();exp=L.experiment(pa);tE+=perf_counter()-t0;nE+=1;a=exp['action']
        fs=(L.predict(0),L.predict(1));f=fs[a];L.record_issued(f);tL+=perf_counter()-t0
        base={k:b.predict(a) for k,b in suffix.items()}
        nxt=[next_hidden(truth,hidden,b,i) for b in (0,1)];act=[truth.emission(h) for h in nxt]
        hidden=nxt[a];actual=act[a];observed=truth.observed(hidden,mask_rate,i)
        t0=perf_counter();surprise=L.observe(a,observed);dt=perf_counter()-t0;tL+=dt;tO+=dt
        for k,b in suffix.items():b.observe(a,observed)
        W=L.window_learner;v090=f.support[0] if f.support is not None and len(f.support)==1 else None
        rec={'step':i+1,'action':a,'passive_action':pa,'actual_emission_EVALUATOR_ONLY':actual,
             'counterfactual_actual_EVALUATOR_ONLY':act[1-a],'drift_step':family=='drift4' and (i+1) in DRIFT,
             **_fc(f,actual),'public_reason':f.public_reason.value if f.public_reason else None,
             'counterfactual':_fc(fs[1-a],act[1-a]),'logloss':round(loss(f.probabilities,actual),10),
             'min_probability':round(min(min(fs[0].probabilities),min(fs[1].probabilities)),12),
             'alarm_after':L.alarm_step is not None,'observed':list(observed),'residual_before':_r(f.residual),
             'surprise':_r(surprise),'residual_after':_r(L.residual),'v090_certificate':v090,
             'v090_wrong':v090 is not None and v090!=actual,'logloss_v090':round(loss(f.v090_probabilities,actual),10),
             'logloss_suffix':{str(k):round(loss(p,actual),10) for k,p in base.items()},
             'family_status_after':L.support.status,'margin_status_after':L.margin.status,
             'family_rows_after':None,'margin_rows_after':None,
             'window_status_after':None if W is None else W.status,'window_rows_after':None,'resumes_after':L.resumes,
             'experiment':{'scores':exp['scores'],'score':exp['score'],'tied':exp['tied'],'check':exp.get('check',False),
                           'proposal':exp.get('proposal'),'volumes':exp['volumes'],'rule':exp['policy']}}
        recs.append(rec)
    rets=[dict(r,actual_EVALUATOR_ONLY=recs[r['step']-1]['actual_emission_EVALUATOR_ONLY'],
               wrong=r['certificate']!=recs[r['step']-1]['actual_emission_EVALUATOR_ONLY']) for r in L.retractions()]
    out={'trace':recs,'retractions':rets,'issued':[list(x) for x in L.issued],'diagnostics':L.diagnostics(),
         'elapsed_informational':tL,'experiment_calls':nE,'experiment_elapsed_informational':tE,'observe_elapsed_informational':tO}
    L.close();return truth,initial,out


def run_case_2x2(seed,family,mask_rate,plan,tau6,arms=ARMS_2X2,conf_budget=PRODUCTION_CONF_BUDGET):
    if family not in FAMILIES_2X2:raise ValueError(family)
    p6=plan006_keys(plan);attest=family in plan['in_family_2x2']
    def att():return ScopeAttestation(p6['declared_family'],'evaluator','synthetic world built inside the family') if attest else None
    out={}
    for arm in arms:
        t0=perf_counter()
        if arm in ('A5','M5'):truth,initial,out[arm]=trajectory_region(arm,seed,family,mask_rate,p6,tau6,att,conf_budget)
        else:truth,initial,out[arm]=S6._trajectory(arm,seed,family,mask_rate,p6,tau6,att)
        out[arm]['arm_wall_informational']=perf_counter()-t0
    return {'schema':'brute.case.v5_0','block':'2x2','seed':seed,'family':family,'mask_rate':mask_rate,
            'in_family_EVALUATOR_ONLY':family in plan['in_family_2x2'],'attested':bool(attest),
            'true_hidden_state_count_EVALUATOR_ONLY':truth.n,'initial_visible':list(initial),
            'steps':plan['actions_per_case_2x2'],'burn_in':plan['burn_in'],'tau6':tau6,'tau_v030':plan['tau_v030'],'arms':out}


# ------------------------------------------------------------------ breadth
def trajectory_breadth(arm,w,mask_rate,plan,tau,attested,conf_budget=PRODUCTION_CONF_BUDGET):
    lb=plan['breadth_worlds']['learner_bounds'][w.family];k=w.k;s=w.s;m=w.m
    att=ScopeAttestation(lb['declared'],'evaluator','synthetic world built inside the family') if attested else None
    L=BreadthBruteLearner(lb['family'],lb['margin'],k,s,plan['open_world_reserve_epsilon'],plan['window_W'],tau,att,
                          policy='M' if arm=='BM5' else 'LU-R',conf_budget=conf_budget)
    check(L.family==lb['declared'],'declared family string differs from plan')
    hidden=w.start;initial=w.observed(hidden,mask_rate,-1);L.initialize(initial)
    recs=[];tL=0.
    for i,pa in enumerate(passive_actions(w.seed,plan['actions_per_case_breadth'],k)):
        t0=perf_counter();exp=L.experiment(pa) if arm!='BP5' else None;a=exp['action'] if exp else pa
        fs=[L.predict(b) for b in range(k)];f=fs[a];L.record_issued(f)
        nxt=[w.next(hidden,b) for b in range(k)];act=[w.emission(h) for h in nxt]
        hidden=nxt[a];observed=w.observed(hidden,mask_rate,i);surprise=L.observe(a,observed);tL+=perf_counter()-t0
        rec={'step':i+1,'passive_action':pa,'action':a,
             'forecasts':[dict(_fc(g,act[b]),actual_EVALUATOR_ONLY=act[b]) for b,g in enumerate(fs)],
             'observed':list(observed),'logloss':round(loss(f.probabilities,act[a]),10),
             'min_probability':round(min(min(g.probabilities) for g in fs),12),'surprise':_r(surprise),
             'residual_after':_r(L.residual),'alarm_after':L.alarm_step is not None,
             'family_status_after':L.support.status,'margin_status_after':L.margin.status}
        if exp:rec['experiment']={k_:exp[k_] for k_ in ('scores','score','tied','volumes','rule','proposal')}
        recs.append(rec)
    acts={r['step']:r['forecasts'][r['action']]['actual_EVALUATOR_ONLY'] for r in recs}
    rets=[dict(r,actual_EVALUATOR_ONLY=acts[r['step']],wrong=r['certificate']!=acts[r['step']]) for r in L.retractions()]
    out={'trace':recs,'issued':[list(x) for x in L.issued],'retractions':rets,'diagnostics':L.diagnostics(),
         'elapsed_informational':tL}
    L.close();return initial,out


def run_case_breadth(seed,family,mask_rate,plan,tau,arms=ARMS_BREADTH,conf_budget=PRODUCTION_CONF_BUDGET,calibration=False,block='breadth'):
    if family not in FAMILIES_BREADTH:raise ValueError(family)
    w=breadth_world(seed,family);attested=plan['breadth_worlds']['learner_bounds'][family]['attested'];out={}
    for arm in arms:initial,out[arm]=trajectory_breadth(arm,w,mask_rate,plan,tau,attested,conf_budget)
    c={'schema':'brute.case.breadth.v1','block':block,'family':family,'seed':seed,'mask_rate':mask_rate,
       'burn_in':plan['burn_in'],'k':w.k,'s':w.s,'attested':attested,'initial_visible':list(initial),
       'steps':plan['actions_per_case_breadth'],'tau':tau,'conf_budget':conf_budget,
       'true_hidden_state_count_EVALUATOR_ONLY':w.n,'minimal_state_count_EVALUATOR_ONLY':minimal_states(w),
       'in_family_EVALUATOR_ONLY':family in plan['in_family_breadth'],'arms':out}
    if calibration:c['calibration']=True
    return c


# ------------------------------------------------------------------ jobs
def jobs_for(plan):
    """Ordered job list (the run index of a job is its position; G12 re-runs every index divisible by 3)."""
    J=[]
    for fam,(lo,hi) in plan['heldout_ranges_2x2'].items():
        for seed in range(lo,hi+1):
            for rate in plan['mask_rates']:J.append(('2x2',fam,seed,rate))
    for fam,(lo,hi) in plan['heldout_ranges_breadth'].items():
        for seed in range(lo,hi+1):
            for rate in plan['mask_rates']:J.append(('breadth',fam,seed,rate))
    x=plan['stress_block']
    for seed in range(x['range'][0],x['range'][1]+1):
        for rate in x['mask_rates']:J.append(('stress',x['family'],seed,rate))
    return J


def key(job):return '/'.join(map(str,job))


def run_job(job,plan,tau6,tau7):
    block,fam,seed,rate=job
    if block=='2x2':return run_case_2x2(seed,fam,rate,plan,tau6)
    if block=='breadth':return run_case_breadth(seed,fam,rate,plan,tau7)
    x=plan['stress_block']
    return run_case_breadth(seed,fam,rate,plan,tau7,tuple(x['arms']),x['conf_budget'],block='stress')


def _job(args):
    job,plan,tau6,tau7=args;t0=perf_counter();c=run_job(job,plan,tau6,tau7);c['case_wall_informational']=perf_counter()-t0
    return key(job),c


def run_jobs(jobs,plan,tau6,tau7,workers,ckpt,log=print):
    todo=[j for j in jobs if key(j) not in ckpt.done];log(f'{len(jobs)-len(todo)} cached, {len(todo)} to run')
    if workers<=1:
        for j in todo:k_,c=_job((j,plan,tau6,tau7));ckpt.add(k_,c);log('done '+k_)
    else:
        with ProcessPoolExecutor(workers) as ex:
            futs=[ex.submit(_job,(j,plan,tau6,tau7)) for j in todo]
            for n,fu in enumerate(as_completed(futs)):
                k_,c=fu.result();ckpt.add(k_,c);log(f'done {n+1}/{len(todo)} {k_} {c["case_wall_informational"]:.1f}s')
    return [ckpt.done[key(j)] for j in jobs]


def run(output,calibration,workers,limit=None,smoke=False,every=1,offset=0):
    """every/offset select a subset of the ordered jobs (G12 repro: every=3, offset=0)."""
    output=Path(output);plan=load(PLAN)
    if not smoke:check_freeze()
    cal=load(calibration)
    if not smoke:check(cal['plan_sha256']==sha(PLAN) and cal['freeze_sha256']==sha(FREEZE),'calibration made under a different plan/freeze')
    for name in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):check(not (output/name).exists(),'refusing overwrite '+str(output/name))
    tau6=plan['tau6']['value'];tau7=cal['tau7'];started=time.perf_counter()
    jobs=jobs_for(plan)[offset::every]
    if limit:jobs=jobs[:limit]
    output.mkdir(parents=True,exist_ok=True)
    allc=run_jobs(jobs,plan,tau6,tau7,workers,Checkpoint(output/'CHECKPOINT.jsonl'))
    cases=[c for c in allc if c['block'] in ('2x2','breadth')];stress=[c for c in allc if c['block']=='stress']
    result={'schema':'brute.study.v5_0','plan':plan,'calibration':cal,'job_selection':{'every':every,'offset':offset,'limit':limit},
            'job_keys':[key(j) for j in jobs],'cases':cases,'stress_cases':stress,
            'total_elapsed_informational':time.perf_counter()-started}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':None if smoke else sha(FREEZE),
        'calibration_sha256':sha(calibration),'case_count':len(cases),'stress_case_count':len(stress),
        'job_selection':{'every':every,'offset':offset,'limit':limit}})
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(STUDY_DIR))
    ap.add_argument('--calibration',default=str(STUDY_DIR/'CALIBRATION_007.json'))
    ap.add_argument('--workers',type=int,default=6);ap.add_argument('--limit',type=int);ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--every',type=int,default=1);ap.add_argument('--offset',type=int,default=0)
    a=ap.parse_args();run(a.output,a.calibration,a.workers,a.limit,a.smoke,a.every,a.offset);print('done')
