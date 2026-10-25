"""Run pre-registered study BRUTE-030-CHANGEPOINT-005 (experiments/BRUTE_PLAN_005.json).

Arms per case (plan 'arms'):
  A3: ChangePointBruteLearner (Y1k + LU-R), actions from experiment()      [full trace]
  P3: the same learner on the passive sequence, with the frozen v0.1.1 C   [full trace + control trace]
  A2: frozen v0.2.0 ActiveBruteLearner with LU                             [slim trace]
  P2: frozen v0.2.0 ActiveBruteLearner on the passive sequence             [slim trace with probabilities]
  E2: v0.2.0 certification + LU + untaken-branch check (CHECK_RUN 3)        [slim trace]
The extended drift4 block runs A3, A2 and E2 (slim) for G14/R2 only. Before acting, both actions are predicted (dual
coverage); counterfactual certificates are checked against the hidden next emission. Hidden truth never reaches a
learner. No overwrites; SHA-256 seal.
"""
from __future__ import annotations
import argparse,time
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
from brute.changepoint import ChangePointBruteLearner
from brute.evaluation import FAMILIES,STATUS_KEYS,UNIFORM_LOSS,loss,no_time
from experiments.brute_common_005 import (PLAN,FREEZE,STUDY_DIR,DRIFT_STEPS,POST_JUMP_STEPS,load,sha,write_new,
                                          check_freeze,check,is_stale)

MAIN_ARMS=('A3','P3','A2','P2','E2')
EXT_ARMS=('A3','A2','E2')
FULL=('A3','P3')
ACTIVE={'A3':True,'P3':False,'A2':True,'P2':False,'E2':True}
STATUS_KEYS_005=STATUS_KEYS+('ABSTAIN/RESYNC_AMBIGUOUS',)


def _learner(arm,plan,tau,att):
    a=(plan['family_state_cap'],plan['margin_state_cap'],plan['row_budget_family'],plan['row_budget_margin'],
       plan['prediction_smoothing'],plan['open_world_reserve_epsilon'],plan['residual_surprise']['window_W'],tau,att)
    if arm in ('A3','P3'):return ChangePointBruteLearner(*a,resync=True,check_run=0)
    if arm=='E2':return ChangePointBruteLearner(*a,resync=False,check_run=3)
    if arm in ('A2','P2'):return ActiveBruteLearner(*a)
    if arm=='C':return FallbackBruteLearner(*a)
    raise ValueError(arm)


def _r(x):return None if x is None else round(x,12)


def _fc(f,actual,full=True):
    d={'status':f.status.value,'reason':f.reason.value if f.reason else None,'certificate':f.certificate,
       'public_certificate':f.public_certificate,
       'wrong':f.certificate is not None and f.certificate!=actual,
       'public_wrong':f.public_certificate is not None and f.public_certificate!=actual}
    if full:d.update({'support':list(f.support) if f.support is not None else None,
                      'margin_support':list(f.margin_support) if f.margin_support is not None else None,
                      'saturated':f.saturated,'forecast_source':f.forecast_source,
                      'probabilities':[round(x,12) for x in f.probabilities]})
    return d


def _trajectory(arm,seed,family,mask_rate,plan,tau,att):
    truth=(new_world if family in ('ood5','drift4') else old_world)(seed,family)
    hidden=truth.start;initial=truth.observed(hidden,mask_rate,-1)
    L=_learner(arm,plan,tau,att());L.initialize(initial)
    full=arm in FULL;C=None
    if arm=='P3':C=_learner('C',plan,tau,att());C.initialize(initial)
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
        nxt=[new_step(truth,hidden,b,i) if family=='drift4' else truth.next(hidden,b) for b in (0,1)]
        act=[truth.emission(h) for h in nxt]
        hidden=nxt[a];actual=act[a];observed=truth.observed(hidden,mask_rate,i)
        t0=perf_counter();surprise=L.observe(a,observed);dt=perf_counter()-t0;tL+=dt;tO+=dt
        for k,b in suffix.items():b.observe(a,observed)
        rec={'step':i+1,'action':a,'passive_action':pa,'actual_emission_EVALUATOR_ONLY':actual,
             'counterfactual_actual_EVALUATOR_ONLY':act[1-a],'drift_step':family=='drift4' and (i+1) in DRIFT_STEPS,
             **_fc(f,actual,full or arm=='P2'),'public_reason':f.public_reason.value if f.public_reason else None,
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
                'window_status_after':None if W is None else W.status,'window_rows_after':None if W is None else W.count})
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


def run_case_005(seed,family,mask_rate,plan,tau,arms=MAIN_ARMS,attest=None):
    if family not in FAMILIES:raise ValueError(family)
    attest=(family in plan['in_family']) if attest is None else attest
    def att():return ScopeAttestation(plan['declared_family'],'evaluator','synthetic world built inside the family') if attest else None
    out={}
    for arm in arms:truth,initial,out[arm]=_trajectory(arm,seed,family,mask_rate,plan,tau,att)
    return {'schema':'brute.case.v3_0','seed':seed,'family':family,'mask_rate':mask_rate,
            'in_family_EVALUATOR_ONLY':family in plan['in_family'],'attested':bool(attest),
            'true_hidden_state_count_EVALUATOR_ONLY':truth.n,'initial_visible':list(initial),
            'steps':plan['actions_per_case'],'burn_in':plan['burn_in'],'tau':tau,'arms':out}


def _mean(xs):return round(sum(xs)/len(xs),6) if xs else None


def _arm_summary(g,arm,plan):
    T=lambda c:c['arms'][arm]['trace'];B=g[0]['burn_in'];full=arm in FULL
    allsteps=[r for c in g for r in T(c)];post=[r for c in g for r in T(c)[B:]]
    D=lambda c:c['arms'][arm]['diagnostics']
    def cnt(rows,key,cf=False):
        vals=[(r['counterfactual'] if cf else r)[key] for r in rows]
        return sum(v is not None and v is not False for v in vals)
    breakdown={k:0 for k in STATUS_KEYS_005}
    for r in post:
        k=r['status'] if r['reason'] is None else f"{r['status']}/{r['reason']}";breakdown[k]=breakdown.get(k,0)+1
    dual=cnt(post,'certificate')+cnt(post,'certificate',True);n=cnt(post,'certificate')
    drift=g[0]['family']=='drift4'
    pj=[r for r in allsteps if r['step'] in POST_JUMP_STEPS] if drift else []
    stale=[r for r in allsteps if is_stale(r['step'])] if drift else []
    exps=[r['experiment'] for r in post if 'experiment' in r]
    prev={};switch=0
    for c in g:
        tr=T(c)
        for k in range(B,len(tr)):switch+=tr[k]['action']!=tr[k-1]['action']
    per_mask={str(m):{'dual_coverage_post':round(sum((r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None)
                                                   for c in g if c['mask_rate']==m for r in T(c)[B:])/
                                               (2*sum(len(T(c)[B:]) for c in g if c['mask_rate']==m)),6),
                      'logloss_post':_mean([r['logloss'] for c in g if c['mask_rate']==m for r in T(c)[B:]])}
              for m in plan['mask_rates'] if any(c['mask_rate']==m for c in g)}
    s={'certs_all':cnt(allsteps,'certificate'),'false_certs_all':cnt(allsteps,'wrong'),
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
       'min_probability_any_step':min(r['min_probability'] for r in allsteps),
       'cases_with_alarm':sum(D(c)['alarm_step'] is not None for c in g),
       'alarm_steps_post':sum(r['reason']=='RESIDUAL_SURPRISE' for r in post),
       'certificates_retracted':sum(D(c)['certificates_retracted'] for c in g),
       'retraction_reasons':{x:sum(r['reason']==x for c in g for r in c['arms'][arm]['retractions']) for x in RETRACTION_REASONS},
       'retracted_wrong':sum(r['wrong'] for c in g for r in c['arms'][arm]['retractions']),
       'duplicate_issued_pairs':sum(len(c['arms'][arm]['issued'])-len({tuple(x) for x in c['arms'][arm]['issued']}) for c in g),
       'duplicate_retraction_pairs':sum(len(c['arms'][arm]['retractions'])-len({(x['step'],x['certificate']) for x in c['arms'][arm]['retractions']}) for c in g),
       'resync_abstentions_post':sum(r['reason']=='RESYNC_AMBIGUOUS' for r in post)+sum(r['counterfactual']['reason']=='RESYNC_AMBIGUOUS' for r in post),
       'resync_issued':sum(1 for c in g for st,cert in c['arms'][arm]['issued'] if T(c)[st-1]['reason']=='RESYNC_AMBIGUOUS'),
       'family_contradicted_cases':sum(D(c)['family_status']=='grammar_contradicted' for c in g),
       'budget_exhausted_family':sum(D(c)['family_status']=='budget_exhausted' for c in g),
       'budget_exhausted_margin':sum(D(c)['margin_status']=='budget_exhausted' for c in g),
       'peak_rows_family':max(D(c)['family_peak_rows'] for c in g),'peak_rows_margin':max(D(c)['margin_peak_rows'] for c in g),
       'peak_rows_window':max(D(c)['window_peak_rows'] for c in g),'window_restarts':sum(D(c)['window_restarts'] for c in g),
       'peak_rows_lookahead':max(D(c)['lookahead_peak_rows'] for c in g),
       'lookahead_budget_hits':sum(D(c)['lookahead_budget_hits'] for c in g),
       'lookahead_copies':sum(D(c)['lookahead_copies'] for c in g),
       'actions_differing_from_passive':sum(r['action']!=r['passive_action'] for r in allsteps),
       'check_steps_post':sum(e['check'] for e in exps),'check_rate_post':round(sum(e['check'] for e in exps)/len(post),6),
       'switch_rate_post':round(switch/len(post),6),
       'R3_untied_experiments_per_case':round(sum(1 for c in g for r in T(c) if 'experiment' in r and not r['experiment']['tied'])/len(g),6),
       'no_proposal_steps':sum(1 for c in g for r in T(c) if 'experiment' in r and r['experiment']['proposal']=='NO_PROPOSAL'),
       'R2_post_jump':{'certs':sum(r['certificate'] is not None for r in pj),'false':sum(r['wrong'] for r in pj),
                       'counterfactual_certs':sum(r['counterfactual']['certificate'] is not None for r in pj),
                       'counterfactual_false':sum(r['counterfactual']['wrong'] for r in pj)},
       'stale_false_certs':sum(r['wrong']+r['counterfactual']['wrong'] for r in stale),
       'stale_window_certs':sum((r['certificate'] is not None)+(r['counterfactual']['certificate'] is not None) for r in stale),
       'per_mask':per_mask,
       'time_informational_seconds':round(sum(c['arms'][arm]['elapsed_informational'] for c in g),4),
       'R4_mean_experiment_call_informational_seconds':round(sum(c['arms'][arm]['experiment_elapsed_informational'] for c in g)/max(1,sum(c['arms'][arm]['experiment_calls'] for c in g)),6),
       'R4_mean_observe_call_informational_seconds':round(sum(c['arms'][arm]['observe_elapsed_informational'] for c in g)/sum(len(T(c)) for c in g),6)}
    if full:
        s.update({'forecast_source_steps_post':{x:sum(r['forecast_source']==x for r in post) for x in FORECAST_SOURCES},
                  'logloss_suffix_post':{k:_mean([r['logloss_suffix'][k] for r in post]) for k in ('1','2','4')},
                  'R1_mean_log_rows_post':{'family':_mean([log(r['family_rows_after']) for r in post if r['family_rows_after']]),
                                           'margin':_mean([log(r['margin_rows_after']) for r in post if r['margin_rows_after']])}})
    return s


def _passive_equivalence(g):
    """G8a: P3 vs P2 (probabilities, forecast_source identical; P3 certificate == P2 certificate wherever P3 certifies;
    P3 differs only by RESYNC_AMBIGUOUS downgrades). Also the study-004 G8a check P2 vs C."""
    st=diff_prob=diff_cert=other=resync=0;pc_steps=pc_diff=win=0
    for c in g:
        P3=c['arms']['P3'];P2=c['arms']['P2']
        for r,q,k in zip(P3['trace'],P2['trace'],P3['control_trace']):
            st+=1
            diff_prob+=r['probabilities']!=q['probabilities'] or r['forecast_source']!=q['forecast_source']
            if r['certificate'] is not None and r['certificate']!=q['certificate']:diff_cert+=1
            if r['reason']=='RESYNC_AMBIGUOUS':
                resync+=1
                if q['status']!='CERTIFIED':other+=1
            elif any(r[x]!=q[x] for x in ('status','reason','certificate','public_certificate')):other+=1
            pc_steps+=1;win+=q['forecast_source']=='window_n4'
            bad=any(q[x]!=k[x] for x in ('status','reason','certificate','public_certificate'))
            if q['forecast_source']!='window_n4':bad|=q['probabilities']!=k['probabilities'] or q['forecast_source']!=k['forecast_source']
            pc_diff+=bad
    return {'steps':st,'probability_or_source_differences':diff_prob,'certificate_differences':diff_cert,
            'non_resync_differences':other,'resync_downgrades':resync,
            'P2_vs_C':{'steps':pc_steps,'differing_steps':pc_diff,'window_n4_steps':win}}


def aggregate_005(cases,plan,arms=MAIN_ARMS):
    out={}
    for fam in FAMILIES:
        g=[c for c in cases if c['family']==fam]
        if not g:continue
        B=g[0]['burn_in'];o={'cases':len(g),'steps_post_burn_in':sum(len(c['arms'][arms[0]]['trace'][B:]) for c in g)}
        for arm in arms:o[arm]=_arm_summary(g,arm,plan)
        if 'P3' in arms:
            P=lambda c:c['arms']['P3']
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
                'coverage_post':round(sum(r['v090_certificate'] is not None for r in ppost)/len(ppost),6),
                'logloss_post':_mean([r['logloss_v090'] for r in ppost])}
            o['baselines_logloss_post']={'uniform':round(UNIFORM_LOSS,6)}
            o['G8a_passive_equivalence']=_passive_equivalence(g)
        out[fam]=o
    return out


def _job(args):
    seed,fam,rate,plan,tau,arms=args
    return run_case_005(seed,fam,rate,plan,tau,arms)


def jobs_for(plan,tau):
    main=[(seed,fam,rate,plan,tau,MAIN_ARMS) for fam,(lo,hi) in plan['heldout_ranges'].items() for seed in range(lo,hi+1) for rate in plan['mask_rates']]
    x=plan['extended_drift4_block']
    ext=[(seed,'drift4',rate,plan,tau,tuple(x['arms'])) for seed in range(x['range'][0],x['range'][1]+1) for rate in x['mask_rates']]
    return main,ext


def run_cases(plan,tau,workers):
    main,ext=jobs_for(plan,tau);check(tuple(plan['extended_drift4_block']['arms'])==EXT_ARMS,'extended arms differ from plan')
    if workers<=1:return [_job(j) for j in main],[_job(j) for j in ext]
    with ProcessPoolExecutor(workers) as ex:
        res=list(ex.map(_job,main+ext,chunksize=1))
    return res[:len(main)],res[len(main):]


def run(output,calibration_check,workers):
    output=Path(output);plan=load(PLAN);check_freeze();cal=load(calibration_check)
    check(cal['plan_sha256']==sha(PLAN) and cal['freeze_sha256']==sha(FREEZE),'calibration check was made under a different plan/freeze')
    check(cal['tau_reproduced'] is True and cal['tau']==plan['residual_surprise']['tau'],'tau did not reproduce; study must not run')
    for name in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):
        check(not (output/name).exists(),'refusing overwrite '+str(output/name))
    tau=plan['residual_surprise']['tau'];started=time.perf_counter()
    cases,ext=run_cases(plan,tau,workers)
    result={'schema':'brute.study.v3_0','plan':plan,'calibration_check':cal,'cases':cases,'extended_cases':ext,
            'summary':aggregate_005(cases,plan),'extended_summary':aggregate_005(ext,plan,EXT_ARMS),
            'total_elapsed_informational':time.perf_counter()-started}
    output.mkdir(parents=True,exist_ok=True)
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':sha(FREEZE),
        'calibration_check_sha256':sha(calibration_check),'case_count':len(cases),'extended_case_count':len(ext)})
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(STUDY_DIR))
    ap.add_argument('--calibration-check',default=str(STUDY_DIR/'CALIBRATION_CHECK.json'))
    ap.add_argument('--workers',type=int,default=4);a=ap.parse_args()
    run(a.output,a.calibration_check,a.workers);print('done')
