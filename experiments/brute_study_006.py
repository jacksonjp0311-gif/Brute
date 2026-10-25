"""Run pre-registered study BRUTE-040-GEOMETRY-006 (experiments/BRUTE_PLAN_006.json).

Arms per main case (plan 'arms'):
  A4: ResumeBruteLearner (Y1k + LU-R + tau6 + resume), actions from experiment()           [full trace]
  P4: the same learner on the passive sequence, with the frozen v0.1.1 C (tau 1.4331)     [full trace + control trace]
  D2: candidate LU2-R (depth 2), tau6 + resume                                              [slim trace]
  F2: candidate 2-step fibre certification, tau6 + resume                                   [slim trace]
  A3: frozen v0.3.0 ChangePointBruteLearner (tau 1.4331, no resume)                         [slim trace]
  A2: frozen v0.2.0 ActiveBruteLearner                                                      [slim trace]
  E2: v0.2.0 certification + LU + CHECK_RUN 3                                               [slim trace]
The D78 drift4 block runs A2 and E2 (slim) for G14' only. Both actions are predicted before acting (dual coverage);
counterfactual certificates are checked against the hidden next emission. Hidden truth never reaches a learner.
Run receipts: the caller appends ledger 'run_start'/'run_end' entries (scripts/append_ledger.py). No overwrites.
"""
from __future__ import annotations
import argparse,time
from math import log
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor
from bgr89.worlds import actions
from bgr89.baselines import SuffixFrequency
from brute.core.learner import ScopeAttestation
from brute.fallback import FallbackBruteLearner
from brute.active import ActiveBruteLearner
from brute.changepoint import ChangePointBruteLearner
from brute.resume import ResumeBruteLearner
from brute.evaluation import UNIFORM_LOSS,loss,no_time
import experiments.brute_study_005 as S5
from experiments.brute_study_005 import _fc,_r,_mean
from experiments.worlds_006 import world,next_hidden,FAMILIES_006
from experiments.brute_common_006 import PLAN,FREEZE,STUDY_DIR,DRIFT_STEPS,load,sha,write_new,check_freeze,check

MAIN_ARMS=('A4','P4','D2','F2','A3','A2','E2')
D78_ARMS=('A2','E2')
FULL=('A4','P4')
ACTIVE={'A4':True,'P4':False,'D2':True,'F2':True,'A3':True,'A2':True,'E2':True}
RESUME_ARMS=('A4','P4','D2','F2')
S5.FULL=FULL   # in this process only: the frozen study-005 summary treats A4/P4 as the full arms


def _learner(arm,plan,tau6,att):
    tc=plan['residual_surprise']['tau_v030']
    base=(plan['family_state_cap'],plan['margin_state_cap'],plan['row_budget_family'],plan['row_budget_margin'],
          plan['prediction_smoothing'],plan['open_world_reserve_epsilon'],plan['residual_surprise']['window_W'])
    if arm in ('A4','P4'):return ResumeBruteLearner(*base,tau6,att,resync=True,check_run=0)
    if arm=='D2':return ResumeBruteLearner(*base,tau6,att,resync=True,check_run=0,depth=2)
    if arm=='F2':return ResumeBruteLearner(*base,tau6,att,resync=True,check_run=0,fibre_w=2)
    if arm=='A3':return ChangePointBruteLearner(*base,tc,att,resync=True,check_run=0)
    if arm=='E2':return ChangePointBruteLearner(*base,tc,att,resync=False,check_run=3)
    if arm=='A2':return ActiveBruteLearner(*base,tc,att)
    if arm=='C':return FallbackBruteLearner(*base,tc,att)
    raise ValueError(arm)


def _trajectory(arm,seed,family,mask_rate,plan,tau6,att):
    truth=world(seed,family)
    hidden=truth.start;initial=truth.observed(hidden,mask_rate,-1)
    L=_learner(arm,plan,tau6,att());L.initialize(initial)
    full=arm in FULL;C=None
    if arm=='P4':C=_learner('C',plan,tau6,att());C.initialize(initial)
    suffix={k:SuffixFrequency(k,0.7) for k in (1,2,4)} if full else {}
    for b in suffix.values():b.initialize(initial)
    recs=[];ctrl=[];tL=tC=tE=tO=0.;nE=0
    for i,pa in enumerate(actions(seed,plan['actions_per_case'])):
        t0=perf_counter()
        exp=L.experiment(pa) if ACTIVE[arm] else None
        if exp is not None:tE+=perf_counter()-t0;nE+=1
        a=exp['action'] if exp else pa
        fs=(L.predict(0),L.predict(1));f=fs[a];L.record_issued(f);tL+=perf_counter()-t0
        if C is not None:
            t0=perf_counter();g=C.predict(a);C.record_issued(g);tC+=perf_counter()-t0
        base={k:b.predict(a) for k,b in suffix.items()}
        nxt=[next_hidden(truth,hidden,b,i) for b in (0,1)]
        act=[truth.emission(h) for h in nxt]
        hidden=nxt[a];actual=act[a];observed=truth.observed(hidden,mask_rate,i)
        t0=perf_counter();surprise=L.observe(a,observed);dt=perf_counter()-t0;tL+=dt;tO+=dt
        for k,b in suffix.items():b.observe(a,observed)
        rec={'step':i+1,'action':a,'passive_action':pa,'actual_emission_EVALUATOR_ONLY':actual,
             'counterfactual_actual_EVALUATOR_ONLY':act[1-a],'drift_step':family=='drift4' and (i+1) in DRIFT_STEPS,
             **_fc(f,actual,full),'public_reason':f.public_reason.value if f.public_reason else None,
             'counterfactual':_fc(fs[1-a],act[1-a],full),
             'logloss':round(loss(f.probabilities,actual),10),
             'min_probability':round(min(min(fs[0].probabilities),min(fs[1].probabilities)),12),
             'alarm_after':L.alarm_step is not None}
        if full:
            W=L.window_learner
            v090=f.support[0] if f.support is not None and len(f.support)==1 else None
            rec.update({'observed':list(observed),'residual_before':_r(f.residual),'surprise':_r(surprise),
                'residual_after':_r(L.residual),'v090_certificate':v090,'v090_wrong':v090 is not None and v090!=actual,
                'logloss_v090':round(loss(f.v090_probabilities,actual),10),
                'logloss_suffix':{str(k):round(loss(p,actual),10) for k,p in base.items()},
                'family_status_after':L.support.status,'margin_status_after':L.margin.status,
                'family_rows_after':L.support.count,'margin_rows_after':L.margin.count,
                'window_status_after':None if W is None else W.status,'window_rows_after':None if W is None else W.count,
                'resumes_after':L.resumes})
        if not full and arm in ('D2','F2'):rec['observed']=list(observed)   # GR1b replays D2/F2 from the trace
        if exp:rec['experiment']={'scores':exp['scores'],'score':exp['score'],'tied':exp['tied'],
                                  'check':exp.get('check',False),'proposal':exp.get('proposal')}
        recs.append(rec)
        if C is not None:
            t0=perf_counter();sc=C.observe(a,observed);tC+=perf_counter()-t0
            ctrl.append({'step':i+1,'status':g.status.value,'reason':g.reason.value if g.reason else None,
                'certificate':g.certificate,'public_certificate':g.public_certificate,'forecast_source':g.forecast_source,
                'probabilities':[round(x,12) for x in g.probabilities],'surprise':_r(sc),'residual_after':_r(C.residual),
                'alarm_after':C.alarm_step is not None,'wrong':g.certificate is not None and g.certificate!=actual,
                'public_wrong':g.public_certificate is not None and g.public_certificate!=actual,
                'logloss':round(loss(g.probabilities,actual),10),'min_probability':round(min(g.probabilities),12)})
    rets=[dict(r,actual_EVALUATOR_ONLY=recs[r['step']-1]['actual_emission_EVALUATOR_ONLY'],
               wrong=r['certificate']!=recs[r['step']-1]['actual_emission_EVALUATOR_ONLY']) for r in L.retractions()]
    out={'trace':recs,'retractions':rets,'issued':[list(x) for x in L.issued],'diagnostics':L.diagnostics(),
         'elapsed_informational':tL,'experiment_calls':nE,'experiment_elapsed_informational':tE,
         'observe_elapsed_informational':tO}
    if C is not None:
        out.update(control_trace=ctrl,control_diagnostics=C.diagnostics(),control_elapsed_informational=tC,
                   control_issued=[list(x) for x in C.issued])
    return truth,initial,out


def run_case_006(seed,family,mask_rate,plan,tau6,arms=MAIN_ARMS):
    if family not in FAMILIES_006:raise ValueError(family)
    attest=family in plan['in_family']
    def att():return ScopeAttestation(plan['declared_family'],'evaluator','synthetic world built inside the family') if attest else None
    out={}
    for arm in arms:truth,initial,out[arm]=_trajectory(arm,seed,family,mask_rate,plan,tau6,att)
    return {'schema':'brute.case.v4_0','seed':seed,'family':family,'mask_rate':mask_rate,
            'in_family_EVALUATOR_ONLY':family in plan['in_family'],'attested':bool(attest),
            'true_hidden_state_count_EVALUATOR_ONLY':truth.n,'initial_visible':list(initial),
            'steps':plan['actions_per_case'],'burn_in':plan['burn_in'],'tau6':tau6,
            'tau_v030':plan['residual_surprise']['tau_v030'],'arms':out}


def _resume_summary(g,arm):
    """Alarm/resume metrics read from diagnostics (cases_with_alarm in the frozen summary reads the CURRENT alarm_step,
    which a resume clears, so the G5 count uses first_alarm_step)."""
    D=lambda c:c['arms'][arm]['diagnostics'];B=g[0]['burn_in']
    after=[r for c in g for r in c['arms'][arm]['trace'] if D(c)['resume_steps'] and r['step']>D(c)['resume_steps'][0]]
    return {'cases_with_any_alarm':sum(D(c)['first_alarm_step'] is not None for c in g),
            'cases_with_any_alarm_post_burn_in':sum(any(s>B for s in D(c)['alarm_steps']) for c in g),
            'cases_with_resume':sum(bool(D(c)['resume_steps']) for c in g),'resumes':sum(len(D(c)['resume_steps']) for c in g),
            'alarms_set':sum(len(D(c)['alarm_steps']) for c in g),
            'certs_after_first_resume':sum((r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None) for r in after),
            'false_certs_after_first_resume':sum(r['wrong']+r['counterfactual']['wrong'] for r in after),
            'public_certs_after_first_alarm':sum((r['public_certificate'] is not None)+(r['counterfactual']['public_certificate'] is not None)
                for c in g for r in c['arms'][arm]['trace'] if D(c)['first_alarm_step'] is not None and r['step']>D(c)['first_alarm_step'])}


def _passive_equivalence_006(g):
    """G8a: P4 vs v0.1.1 control before the first step where their alarm states differ (plan G8 (a))."""
    st=diff_prob=other=resync=win=checked=0
    for c in g:
        P=c['arms']['P4'];div=False
        for r,q in zip(P['trace'],P['control_trace']):
            st+=1
            if r['forecast_source']!='window_n4':diff_prob+=r['probabilities']!=q['probabilities'] or r['forecast_source']!=q['forecast_source']
            else:win+=1;diff_prob+=q['forecast_source']!='suffix1'
            if not div:
                checked+=1
                if r['reason']=='RESYNC_AMBIGUOUS':
                    resync+=1;other+=q['status']!='CERTIFIED'
                elif any(r[x]!=q[x] for x in ('status','reason','certificate','public_certificate')):other+=1
            if r['alarm_after']!=q['alarm_after']:div=True
    return {'steps':st,'probability_or_source_differences':diff_prob,'window_n4_steps':win,
            'decision_steps_checked_before_alarm_divergence':checked,'non_resync_differences':other,'resync_downgrades':resync}


def aggregate_006(cases,plan,arms=MAIN_ARMS):
    out={}
    for fam in FAMILIES_006:
        g=[c for c in cases if c['family']==fam]
        if not g:continue
        B=g[0]['burn_in'];o={'cases':len(g),'steps_post_burn_in':sum(len(c['arms'][arms[0]]['trace'][B:]) for c in g)}
        for arm in arms:
            o[arm]=S5._arm_summary(g,arm,plan)
            if arm in RESUME_ARMS:o[arm]['resume']=_resume_summary(g,arm)
        if 'P4' in arms:
            P=lambda c:c['arms']['P4']
            cpost=[r for c in g for r in P(c)['control_trace'][B:]];call=[r for c in g for r in P(c)['control_trace']]
            pall=[r for c in g for r in P(c)['trace']];ppost=[r for c in g for r in P(c)['trace'][B:]]
            o['C_v011']={'certs_all':sum(r['certificate'] is not None for r in call),'false_certs_all':sum(r['wrong'] for r in call),
                'public_certs_all':sum(r['public_certificate'] is not None for r in call),
                'coverage_post':round(sum(r['certificate'] is not None for r in cpost)/len(cpost),6),
                'logloss_post':_mean([r['logloss'] for r in cpost]),
                'min_probability_any_step':min(r['min_probability'] for r in call),
                'cases_with_alarm':sum(P(c)['control_diagnostics']['alarm_step'] is not None for c in g),
                'time_informational_seconds':round(sum(P(c)['control_elapsed_informational'] for c in g),4)}
            o['v0.90']={'certs_all':sum(r['v090_certificate'] is not None for r in pall),
                'false_certs_all':sum(r['v090_wrong'] for r in pall),
                'false_certs_drift_steps':sum(r['v090_wrong'] for r in pall if r['drift_step']),
                'false_certs_non_drift_steps':sum(r['v090_wrong'] for r in pall if not r['drift_step']),
                'coverage_post':round(sum(r['v090_certificate'] is not None for r in ppost)/len(ppost),6),
                'logloss_post':_mean([r['logloss_v090'] for r in ppost])}
            o['baselines_logloss_post']={'uniform':round(UNIFORM_LOSS,6)}
            o['G8a_passive_equivalence']=_passive_equivalence_006(g)
            o['true_hidden_state_counts']=sorted({c['true_hidden_state_count_EVALUATOR_ONLY'] for c in g})
        out[fam]=o
    return out


def _job(args):
    seed,fam,rate,plan,tau6,arms=args
    return run_case_006(seed,fam,rate,plan,tau6,arms)


def jobs_for(plan,tau6):
    main=[(seed,fam,rate,plan,tau6,MAIN_ARMS) for fam,(lo,hi) in plan['heldout_ranges'].items() for seed in range(lo,hi+1) for rate in plan['mask_rates']]
    x=plan['D78_block']
    d78=[(seed,x['family'],rate,plan,tau6,tuple(x['arms'])) for seed in range(x['range'][0],x['range'][1]+1) for rate in x['mask_rates']]
    return main,d78


def run_cases(plan,tau6,workers,limit=None):
    main,d78=jobs_for(plan,tau6);check(tuple(plan['D78_block']['arms'])==D78_ARMS,'D78 arms differ from plan')
    if limit:main,d78=main[::max(1,len(main)//limit)][:limit],d78[:limit]
    jobs=main+d78
    if workers<=1:res=[_job(j) for j in jobs]
    else:
        with ProcessPoolExecutor(workers) as ex:res=list(ex.map(_job,jobs,chunksize=1))
    return res[:len(main)],res[len(main):]


def run(output,calibration,workers,limit=None,smoke=False):
    output=Path(output);plan=load(PLAN)
    if not smoke:check_freeze()
    cal=load(calibration)
    if not smoke:check(cal['plan_sha256']==sha(PLAN) and cal['freeze_sha256']==sha(FREEZE),'calibration made under a different plan/freeze')
    for name in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):
        check(not (output/name).exists(),'refusing overwrite '+str(output/name))
    tau6=cal['tau6'];started=time.perf_counter()
    cases,d78=run_cases(plan,tau6,workers,limit)
    result={'schema':'brute.study.v4_0','plan':plan,'calibration':cal,'cases':cases,'d78_cases':d78,
            'summary':aggregate_006(cases,plan),'d78_summary':aggregate_006(d78,plan,D78_ARMS),
            'total_elapsed_informational':time.perf_counter()-started}
    output.mkdir(parents=True,exist_ok=True)
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),
        'freeze_sha256':None if smoke else sha(FREEZE),'calibration_sha256':sha(calibration),
        'case_count':len(cases),'d78_case_count':len(d78)})
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(STUDY_DIR))
    ap.add_argument('--calibration',default=str(STUDY_DIR/'CALIBRATION_006.json'))
    ap.add_argument('--workers',type=int,default=4);ap.add_argument('--limit',type=int);ap.add_argument('--smoke',action='store_true')
    a=ap.parse_args();run(a.output,a.calibration,a.workers,a.limit,a.smoke);print('done')
