"""Run pre-registered study BRUTE-020-ACTIVE-004 (experiments/BRUTE_PLAN_004.json).

Each case runs three learners on one world:
  A: brute.active.ActiveBruteLearner, with actions chosen by experiment() (default = passive action);
  P: the same learner on the fixed passive action sequence;
  C: the frozen v0.1.1 FallbackBruteLearner on the passive sequence.
Before acting, both actions are predicted (dual coverage). Counterfactual certificates are checked against the hidden
next emission for that action. Hidden truth never reaches a learner. No overwrites; SHA-256 seal.
"""
from __future__ import annotations
import argparse,time,os
from math import log
from pathlib import Path
from time import perf_counter
from concurrent.futures import ProcessPoolExecutor
from bgr89.worlds import world as old_world,actions
from bgr89.baselines import SuffixFrequency
from bgr90.worlds import world as new_world,step as new_step
from brute.core.learner import ScopeAttestation
from brute.fallback import FallbackBruteLearner,RETRACTION_REASONS
from brute.active import ActiveBruteLearner,FORECAST_SOURCES
from brute.evaluation import FAMILIES,STATUS_KEYS,UNIFORM_LOSS,loss,no_time
from experiments.brute_common_004 import PLAN,FREEZE,STUDY_DIR,DRIFT_STEPS,POST_JUMP_STEPS,load,sha,write_new,check_freeze,check

ARMS=('A','P')


def _learner(cls,plan,tau,att):
    return cls(plan['family_state_cap'],plan['margin_state_cap'],plan['row_budget_family'],plan['row_budget_margin'],
               plan['prediction_smoothing'],plan['open_world_reserve_epsilon'],plan['residual_surprise']['window_W'],tau,att)


def _r(x):return None if x is None else round(x,12)


def _fc(f,actual):
    return {'status':f.status.value,'reason':f.reason.value if f.reason else None,'certificate':f.certificate,
            'public_certificate':f.public_certificate,'support':list(f.support) if f.support is not None else None,
            'margin_support':list(f.margin_support) if f.margin_support is not None else None,'saturated':f.saturated,
            'forecast_source':f.forecast_source,'probabilities':[round(x,12) for x in f.probabilities],
            'wrong':f.certificate is not None and f.certificate!=actual,
            'public_wrong':f.public_certificate is not None and f.public_certificate!=actual}


def _trajectory(arm,seed,family,mask_rate,plan,tau,att):
    truth=(new_world if family in ('ood5','drift4') else old_world)(seed,family)
    hidden=truth.start;initial=truth.observed(hidden,mask_rate,-1)
    L=_learner(ActiveBruteLearner,plan,tau,att());L.initialize(initial)
    C=None
    if arm=='P':C=_learner(FallbackBruteLearner,plan,tau,att());C.initialize(initial)
    suffix={k:SuffixFrequency(k,0.7) for k in (1,2,4)}
    for b in suffix.values():b.initialize(initial)
    recs=[];ctrl=[];tL=tC=0.
    for i,pa in enumerate(actions(seed,plan['actions_per_case'])):
        t0=perf_counter()
        exp=L.experiment(pa) if arm=='A' else None
        a=exp['action'] if exp else pa
        fs=(L.predict(0),L.predict(1));f=fs[a];L.record_issued(f);tL+=perf_counter()-t0
        if C is not None:
            t0=perf_counter();g=C.predict(a);C.record_issued(g);tC+=perf_counter()-t0
        base={k:b.predict(a) for k,b in suffix.items()}
        nxt=[new_step(truth,hidden,b,i) if family=='drift4' else truth.next(hidden,b) for b in (0,1)]
        act=[truth.emission(h) for h in nxt]
        hidden=nxt[a];actual=act[a];observed=truth.observed(hidden,mask_rate,i)
        v090=f.support[0] if f.support is not None and len(f.support)==1 else None
        t0=perf_counter();surprise=L.observe(a,observed);tL+=perf_counter()-t0
        for k,b in suffix.items():b.observe(a,observed)
        W=L.window_learner
        rec={'step':i+1,'action':a,'passive_action':pa,'observed':list(observed),'actual_emission_EVALUATOR_ONLY':actual,
             'counterfactual_actual_EVALUATOR_ONLY':act[1-a],
             'drift_step':family=='drift4' and (i+1) in DRIFT_STEPS,
             **_fc(f,actual),'public_reason':f.public_reason.value if f.public_reason else None,
             'counterfactual':_fc(fs[1-a],act[1-a]),
             'residual_before':_r(f.residual),'surprise':_r(surprise),'residual_after':_r(L.residual),
             'alarm_after':L.alarm_step is not None,
             'v090_certificate':v090,'v090_wrong':v090 is not None and v090!=actual,
             'logloss':round(loss(f.probabilities,actual),10),
             'logloss_v090':round(loss(f.v090_probabilities,actual),10),
             'logloss_suffix':{str(k):round(loss(p,actual),10) for k,p in base.items()},
             'min_probability':round(min(min(fs[0].probabilities),min(fs[1].probabilities)),12),
             'family_status_after':L.support.status,'margin_status_after':L.margin.status,
             'family_rows_after':L.support.count,'margin_rows_after':L.margin.count,
             'window_status_after':None if W is None else W.status,'window_rows_after':None if W is None else W.count}
        if exp:rec['experiment']={'scores':exp['scores'],'score':exp['score'],'tied':exp['tied']}
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
         'elapsed_informational':tL}
    if C is not None:
        out.update(control_trace=ctrl,control_diagnostics=C.diagnostics(),control_elapsed_informational=tC,
                   control_issued=[list(x) for x in C.issued])
    return truth,initial,out


def run_case_004(seed,family,mask_rate,plan,tau,attest=None):
    if family not in FAMILIES:raise ValueError(family)
    attest=(family in plan['in_family']) if attest is None else attest
    def att():return ScopeAttestation(plan['declared_family'],'evaluator','synthetic world built inside the family') if attest else None
    arms={}
    for arm in ARMS:truth,initial,arms[arm]=_trajectory(arm,seed,family,mask_rate,plan,tau,att)
    return {'schema':'brute.case.v2_0','seed':seed,'family':family,'mask_rate':mask_rate,
            'in_family_EVALUATOR_ONLY':family in plan['in_family'],'attested':bool(attest),
            'true_hidden_state_count_EVALUATOR_ONLY':truth.n,'initial_visible':list(initial),
            'steps':plan['actions_per_case'],'burn_in':plan['burn_in'],'tau':tau,'arms':arms}


def _mean(xs):return round(sum(xs)/len(xs),6) if xs else None


def _arm_summary(g,arm,plan):
    T=lambda c:c['arms'][arm]['trace'];B=g[0]['burn_in']
    allsteps=[r for c in g for r in T(c)];post=[r for c in g for r in T(c)[B:]]
    D=lambda c:c['arms'][arm]['diagnostics']
    def cnt(rows,key,cf=False):
        # certificates are codes 0..3 (0 is a valid code): count 'is not None'; wrong flags are booleans
        vals=[(r['counterfactual'] if cf else r)[key] for r in rows]
        return sum(v is not None and v is not False for v in vals)
    breakdown={k:0 for k in STATUS_KEYS}
    for r in post:
        k=r['status'] if r['reason'] is None else f"{r['status']}/{r['reason']}";breakdown[k]=breakdown.get(k,0)+1
    dual=cnt(post,'certificate')+cnt(post,'certificate',True)
    n=cnt(post,'certificate')
    dup_issued=sum(len(c['arms'][arm]['issued'])-len({tuple(x) for x in c['arms'][arm]['issued']}) for c in g)
    dup_ret=sum(len(c['arms'][arm]['retractions'])-len({(x['step'],x['certificate']) for x in c['arms'][arm]['retractions']}) for c in g)
    pj=[r for c in g for r in T(c) if r['step'] in POST_JUMP_STEPS] if g[0]['family']=='drift4' else []
    per_mask={str(m):{'dual_coverage_post':round(sum((r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None)
                                                   for c in g if c['mask_rate']==m for r in T(c)[B:])/
                                               (2*sum(len(T(c)[B:]) for c in g if c['mask_rate']==m)),6),
                      'logloss_post':_mean([r['logloss'] for c in g if c['mask_rate']==m for r in T(c)[B:]])}
              for m in plan['mask_rates'] if any(c['mask_rate']==m for c in g)}
    return {'certs_all':cnt(allsteps,'certificate'),'false_certs_all':cnt(allsteps,'wrong'),
            'false_certs_drift_steps':sum(r['wrong'] for r in allsteps if r['drift_step']),
            'false_certs_non_drift_steps':sum(r['wrong'] for r in allsteps if not r['drift_step']),
            'counterfactual_certs_all':cnt(allsteps,'certificate',True),'counterfactual_false_certs_all':cnt(allsteps,'wrong',True),
            'counterfactual_false_certs_drift_steps':sum(r['counterfactual']['wrong'] for r in allsteps if r['drift_step']),
            'counterfactual_false_certs_non_drift_steps':sum(r['counterfactual']['wrong'] for r in allsteps if not r['drift_step']),
            'public_certs_all':cnt(allsteps,'public_certificate')+cnt(allsteps,'public_certificate',True),
            'public_false_certs_all':cnt(allsteps,'public_wrong')+cnt(allsteps,'public_wrong',True),
            'dual_certified_pairs_post':dual,'dual_coverage_post':round(dual/(2*len(post)),6),
            'on_policy_coverage_post':round(n/len(post),6),
            'selective_risk_post':round(cnt(post,'wrong')/n,6) if n else None,
            'status_breakdown_post':breakdown,'logloss_post':_mean([r['logloss'] for r in post]),
            'logloss_suffix_post':{k:_mean([r['logloss_suffix'][k] for r in post]) for k in ('1','2','4')},
            'min_probability_any_step':min(r['min_probability'] for r in allsteps),
            'cases_with_alarm':sum(D(c)['alarm_step'] is not None for c in g),
            'alarm_steps_post':sum(r['reason']=='RESIDUAL_SURPRISE' for r in post),
            'certificates_retracted':sum(D(c)['certificates_retracted'] for c in g),
            'retraction_reasons':{x:sum(r['reason']==x for c in g for r in c['arms'][arm]['retractions']) for x in RETRACTION_REASONS},
            'retracted_wrong':sum(r['wrong'] for c in g for r in c['arms'][arm]['retractions']),
            'duplicate_issued_pairs':dup_issued,'duplicate_retraction_pairs':dup_ret,
            'family_contradicted_cases':sum(D(c)['family_status']=='grammar_contradicted' for c in g),
            'budget_exhausted_family':sum(D(c)['family_status']=='budget_exhausted' for c in g),
            'budget_exhausted_margin':sum(D(c)['margin_status']=='budget_exhausted' for c in g),
            'peak_rows_family':max(D(c)['family_peak_rows'] for c in g),'peak_rows_margin':max(D(c)['margin_peak_rows'] for c in g),
            'peak_rows_window':max(D(c)['window_peak_rows'] for c in g),'window_restarts':sum(D(c)['window_restarts'] for c in g),
            'peak_rows_lookahead':max(D(c)['lookahead_peak_rows'] for c in g),
            'lookahead_budget_hits':sum(D(c)['lookahead_budget_hits'] for c in g),
            'lookahead_copies':sum(D(c)['lookahead_copies'] for c in g),
            'forecast_source_steps_post':{s:sum(r['forecast_source']==s for r in post) for s in FORECAST_SOURCES},
            'actions_differing_from_passive':sum(r['action']!=r['passive_action'] for r in allsteps),
            'R1_mean_log_rows_post':{'family':_mean([log(r['family_rows_after']) for r in post if r['family_rows_after']]),
                                     'margin':_mean([log(r['margin_rows_after']) for r in post if r['margin_rows_after']])},
            'R2_post_jump':{'certs':sum(r['certificate'] is not None for r in pj),'false':sum(r['wrong'] for r in pj),
                            'counterfactual_certs':sum(r['counterfactual']['certificate'] is not None for r in pj),
                            'counterfactual_false':sum(r['counterfactual']['wrong'] for r in pj)},
            'per_mask':per_mask,
            'time_informational_seconds':round(sum(c['arms'][arm]['elapsed_informational'] for c in g),4)}


def aggregate_004(cases,plan):
    out={}
    for fam in FAMILIES:
        g=[c for c in cases if c['family']==fam]
        if not g:continue
        B=g[0]['burn_in'];P=lambda c:c['arms']['P']
        cpost=[r for c in g for r in P(c)['control_trace'][B:]];call=[r for c in g for r in P(c)['control_trace']]
        pall=[r for c in g for r in P(c)['trace']];ppost=[r for c in g for r in P(c)['trace'][B:]]
        eq_diff=0;eq_steps=0;win=0
        for c in g:
            for r,q in zip(P(c)['trace'],P(c)['control_trace']):
                eq_steps+=1;win+=r['forecast_source']=='window_n4'
                bad=any(r[k]!=q[k] for k in ('status','reason','certificate','public_certificate'))
                if r['forecast_source']!='window_n4':bad|=r['probabilities']!=q['probabilities'] or r['forecast_source']!=q['forecast_source']
                eq_diff+=bad
        out[fam]={'cases':len(g),'steps_post_burn_in':len(ppost),
            'A':_arm_summary(g,'A',plan),'P':_arm_summary(g,'P',plan),
            'C_v011':{'certs_all':sum(r['certificate'] is not None for r in call),'false_certs_all':sum(r['wrong'] for r in call),
                      'public_certs_all':sum(r['public_certificate'] is not None for r in call),
                      'coverage_post':round(sum(r['certificate'] is not None for r in cpost)/len(cpost),6),
                      'logloss_post':_mean([r['logloss'] for r in cpost]),
                      'min_probability_any_step':min(r['min_probability'] for r in call),
                      'cases_with_alarm':sum(P(c)['control_diagnostics']['alarm_step'] is not None for c in g),
                      'per_mask_logloss_post':{str(m):_mean([r['logloss'] for c in g if c['mask_rate']==m for r in P(c)['control_trace'][B:]]) for m in plan['mask_rates']},
                      'time_informational_seconds':round(sum(P(c)['control_elapsed_informational'] for c in g),4)},
            'v0.90':{'certs_all':sum(r['v090_certificate'] is not None for r in pall),
                     'false_certs_all':sum(r['v090_wrong'] for r in pall),
                     'false_certs_drift_steps':sum(r['v090_wrong'] for r in pall if r['drift_step']),
                     'coverage_post':round(sum(r['v090_certificate'] is not None for r in ppost)/len(ppost),6),
                     'logloss_post':_mean([r['logloss_v090'] for r in ppost])},
            'baselines_logloss_post':{'uniform':round(UNIFORM_LOSS,6)},
            'G8a_passive_equivalence':{'steps':eq_steps,'differing_steps':eq_diff,'window_n4_steps':win}}
    return out


def _job(args):
    seed,fam,rate,plan,tau=args
    return run_case_004(seed,fam,rate,plan,tau)


def run_cases(plan,tau,workers):
    jobs=[(seed,fam,rate,plan,tau) for fam,(lo,hi) in plan['heldout_ranges'].items() for seed in range(lo,hi+1) for rate in plan['mask_rates']]
    if workers<=1:return [_job(j) for j in jobs]
    with ProcessPoolExecutor(workers) as ex:return list(ex.map(_job,jobs,chunksize=1))


def run(output,calibration_check,workers):
    output=Path(output);plan=load(PLAN);check_freeze();cal=load(calibration_check)
    check(cal['plan_sha256']==sha(PLAN) and cal['freeze_sha256']==sha(FREEZE),'calibration check was made under a different plan/freeze')
    check(cal['tau_reproduced'] is True and cal['tau']==plan['residual_surprise']['tau'],'tau did not reproduce; study must not run')
    for name in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):
        check(not (output/name).exists(),'refusing overwrite '+str(output/name))
    tau=plan['residual_surprise']['tau'];started=time.perf_counter()
    cases=run_cases(plan,tau,workers)   # order is deterministic (ex.map preserves job order)
    result={'schema':'brute.study.v2_0','plan':plan,'calibration_check':cal,'cases':cases,'summary':aggregate_004(cases,plan),
            'total_elapsed_informational':time.perf_counter()-started}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':sha(FREEZE),
        'calibration_check_sha256':sha(calibration_check),'case_count':len(cases)})
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(STUDY_DIR))
    ap.add_argument('--calibration-check',default=str(STUDY_DIR/'CALIBRATION_CHECK.json'))
    ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
    run(a.output,a.calibration_check,a.workers);print('done')
