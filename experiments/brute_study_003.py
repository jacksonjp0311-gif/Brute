"""Run pre-registered study BRUTE-011-FALLBACK-003 (experiments/BRUTE_PLAN_003.json).

Every case runs, on one action/observation trace: Brute v0.1.1 (brute.fallback.FallbackBruteLearner),
the frozen v0.1.0 learner as a control (same tau), the v0.90 expanded certificate (from the shared
<=4 support), the v0.89 catalogue, an ablation (v0.1.1 without the suffix-1 tier) and suffix
baselines. Hidden truth never reaches a learner. No overwrites; SHA-256 seal.
"""
from __future__ import annotations
import argparse,time
from math import log
from pathlib import Path
from time import perf_counter
from bgr89.worlds import world as old_world,actions
from bgr89.baselines import SuffixFrequency
from bgr90.worlds import world as new_world,step as new_step
from brute.core.learner import BruteLearner,ScopeAttestation
from brute.fallback import FallbackBruteLearner,FORECAST_SOURCES,RETRACTION_REASONS
from brute.evaluation import FAMILIES,STATUS_KEYS,UNIFORM_LOSS,loss,no_time
from experiments.brute_common_003 import PLAN,FREEZE,STUDY_DIR,DRIFT_STEPS,load,sha,write_new,check_freeze,check


def _learner(cls,plan,tau,att):
    return cls(plan['family_state_cap'],plan['margin_state_cap'],plan['row_budget_family'],plan['row_budget_margin'],
               plan['prediction_smoothing'],plan['open_world_reserve_epsilon'],plan['residual_surprise']['window_W'],tau,att)


def run_case_003(seed,family,mask_rate,plan,tau,attest=None):
    if family not in FAMILIES:raise ValueError(family)
    truth=(new_world if family in ('ood5','drift4') else old_world)(seed,family)
    attest=(family in plan['in_family']) if attest is None else attest
    def att():return ScopeAttestation(plan['declared_family'],'evaluator','synthetic world built inside the family') if attest else None
    hidden=truth.start;initial=truth.observed(hidden,mask_rate,-1)
    L=_learner(FallbackBruteLearner,plan,tau,att());C=_learner(BruteLearner,plan,tau,att())
    L.initialize(initial);C.initialize(initial)
    suffix={k:SuffixFrequency(k,0.7) for k in (1,2,4)}
    for b in suffix.values():b.initialize(initial)
    records=[];control=[];tL=tC=0.
    for i,a in enumerate(actions(seed,plan['actions_per_case'])):
        t0=perf_counter();f=L.predict(a);L.record_issued(f);t1=perf_counter()
        g=C.predict(a);C.record_issued(g);t2=perf_counter();tL+=t1-t0;tC+=t2-t1
        base={k:b.predict(a) for k,b in suffix.items()}
        hidden=new_step(truth,hidden,a,i) if family=='drift4' else truth.next(hidden,a)
        actual=truth.emission(hidden);observed=truth.observed(hidden,mask_rate,i)
        v090_cert=f.support[0] if f.support is not None and len(f.support)==1 else None
        t0=perf_counter();surprise=L.observe(a,observed);t1=perf_counter();sc=C.observe(a,observed);t2=perf_counter()
        tL+=t1-t0;tC+=t2-t1
        for k,b in suffix.items():b.observe(a,observed)
        records.append({'step':i+1,'action':a,'observed':list(observed),'actual_emission_EVALUATOR_ONLY':actual,
            'drift_step':family=='drift4' and (i+1) in DRIFT_STEPS,
            'status':f.status.value,'reason':f.reason.value if f.reason else None,
            'certificate':f.certificate,'public_certificate':f.public_certificate,
            'public_reason':f.public_reason.value if f.public_reason else None,
            'support':list(f.support) if f.support is not None else None,
            'margin_support':list(f.margin_support) if f.margin_support is not None else None,
            'saturated':f.saturated,'forecast_source':f.forecast_source,
            'probabilities':[round(x,12) for x in f.probabilities],
            'residual_before':None if f.residual is None else round(f.residual,12),
            'surprise':round(surprise,12),
            'residual_after':None if L.residual is None else round(L.residual,12),
            'alarm_after':L.alarm_step is not None,
            'brute_wrong':f.certificate is not None and f.certificate!=actual,
            'public_wrong':f.public_certificate is not None and f.public_certificate!=actual,
            'v090_certificate':v090_cert,'v090_wrong':v090_cert is not None and v090_cert!=actual,
            'legacy_certificate':f.legacy_certificate,
            'legacy_wrong':f.legacy_certificate is not None and f.legacy_certificate!=actual,
            'logloss_brute':round(loss(f.probabilities,actual),10),
            'logloss_ablation':round(loss(f.ablation_probabilities,actual),10),
            'logloss_v090':round(loss(f.v090_probabilities,actual),10),
            'logloss_v089':None if f.legacy_probabilities is None else round(loss(f.legacy_probabilities,actual),10),
            'logloss_suffix':{str(k):round(loss(p,actual),10) for k,p in base.items()},
            'min_probability':round(min(f.probabilities),12),
            'family_status_after':L.support.status,'margin_status_after':L.margin.status,
            'family_rows_after':L.support.count,'margin_rows_after':L.margin.count})
        control.append({'step':i+1,'status':g.status.value,'reason':g.reason.value if g.reason else None,
            'certificate':g.certificate,'public_certificate':g.public_certificate,
            'probabilities':[round(x,12) for x in g.probabilities],'surprise':round(sc,12),
            'residual_after':None if C.residual is None else round(C.residual,12),'alarm_after':C.alarm_step is not None,
            'brute_wrong':g.certificate is not None and g.certificate!=actual,
            'public_wrong':g.public_certificate is not None and g.public_certificate!=actual,
            'logloss_brute':round(loss(g.probabilities,actual),10),'min_probability':round(min(g.probabilities),12)})
    retractions=[dict(r,actual_EVALUATOR_ONLY=records[r['step']-1]['actual_emission_EVALUATOR_ONLY'],
                      wrong=r['certificate']!=records[r['step']-1]['actual_emission_EVALUATOR_ONLY']) for r in L.retractions()]
    return {'schema':'brute.case.v1_1','seed':seed,'family':family,'mask_rate':mask_rate,
            'in_family_EVALUATOR_ONLY':family in plan['in_family'],'attested':bool(attest),
            'true_hidden_state_count_EVALUATOR_ONLY':truth.n,'initial_visible':list(initial),
            'steps':plan['actions_per_case'],'burn_in':plan['burn_in'],'tau':tau,'trace':records,'control_trace':control,
            'retractions':retractions,'diagnostics':L.diagnostics(),'control_diagnostics':C.diagnostics(),
            'elapsed_v011_informational':tL,'elapsed_v010_informational':tC}


def _mean(xs):return round(sum(xs)/len(xs),6) if xs else None


def _arm(g,key,steps_fn=lambda c:c['trace']):
    allsteps=[r for c in g for r in steps_fn(c)]
    post=[r for c in g for r in steps_fn(c)[c['burn_in']:]]
    drift={(c['seed'],c['mask_rate'],r['step']) for c in g for r in c['trace'] if r['drift_step']}
    def isdrift(c,r):return (c['seed'],c['mask_rate'],r['step']) in drift
    n=sum(r['certificate'] is not None for r in post)
    breakdown={k:0 for k in STATUS_KEYS}
    for r in post:
        k=r['status'] if r['reason'] is None else f"{r['status']}/{r['reason']}";breakdown[k]=breakdown.get(k,0)+1
    diag='diagnostics' if key=='v0.1.1' else 'control_diagnostics'
    return {'certs_all':sum(r['certificate'] is not None for r in allsteps),
            'false_certs_all':sum(r['brute_wrong'] for r in allsteps),
            'false_certs_drift_steps':sum(r['brute_wrong'] for c in g for r in steps_fn(c) if isdrift(c,r)),
            'false_certs_non_drift_steps':sum(r['brute_wrong'] for c in g for r in steps_fn(c) if not isdrift(c,r)),
            'public_certs_all':sum(r['public_certificate'] is not None for r in allsteps),
            'public_false_certs_all':sum(r['public_wrong'] for r in allsteps),
            'coverage_post':round(n/len(post),6),
            'selective_risk_post':round(sum(r['brute_wrong'] for r in post)/n,6) if n else None,
            'status_breakdown_post':breakdown,
            'logloss_post':_mean([r['logloss_brute'] for r in post]),
            'min_probability_any_step':min(r['min_probability'] for r in allsteps),
            'cases_with_alarm':sum(c[diag]['alarm_step'] is not None for c in g),
            'alarm_steps_post':sum(r['reason']=='RESIDUAL_SURPRISE' for r in post),
            'certificates_retracted':sum(c[diag]['certificates_retracted'] for c in g),
            'budget_exhausted_family':sum(c[diag]['family_status']=='budget_exhausted' for c in g),
            'budget_exhausted_margin':sum(c[diag]['margin_status']=='budget_exhausted' for c in g),
            'peak_rows_family':max(c[diag]['family_peak_rows'] for c in g),
            'peak_rows_margin':max(c[diag]['margin_peak_rows'] for c in g)}


def aggregate_003(cases,plan):
    out={}
    for fam in FAMILIES:
        g=[c for c in cases if c['family']==fam]
        if not g:continue
        post=[r for c in g for r in c['trace'][c['burn_in']:]]
        allsteps=[r for c in g for r in c['trace']]
        lv=[r for c in g for r in c['trace'][c['burn_in']:] if r['logloss_v089'] is not None]
        # R2 loss decomposition (post-burn-in)
        phases={}
        def add(name,r):
            p=phases.setdefault(name,[0,0.]);p[0]+=1;p[1]+=r['logloss_brute']
        for r in post:
            if r['status']=='OUT_OF_FAMILY' and r['reason']=='FAMILY_CONTRADICTED':add('after_contradiction/'+r['forecast_source'],r)
            elif r['family_status_after']=='grammar_contradicted':add('contradiction_step',r)
            else:add('before_contradiction/'+(r['status'] if r['reason'] is None else r['status']+'/'+r['reason']),r)
        margin_after=[r for r in post if r['forecast_source']=='margin_n5']
        rets=[x for c in g for x in c['retractions']]
        wrong_never_retracted=sum(r['brute_wrong'] for c in g if c['diagnostics']['contradiction_step'] is None for r in c['trace'])
        per_mask={str(m):{'v0.1.1':_mean([r['logloss_brute'] for c in g if c['mask_rate']==m for r in c['trace'][c['burn_in']:]]),
                          'v0.1.0':_mean([r['logloss_brute'] for c in g if c['mask_rate']==m for r in c['control_trace'][c['burn_in']:]])}
                  for m in plan['mask_rates']}
        drift_keys={(c['seed'],c['mask_rate'],r['step']) for c in g for r in c['trace'] if r['drift_step']}
        out[fam]={'cases':len(g),'steps_all':len(allsteps),'steps_post_burn_in':len(post),
          'v0.1.1':_arm(g,'v0.1.1'),'v0.1.0':_arm(g,'v0.1.0',lambda c:c['control_trace']),
          'v0.90':{'certs_all':sum(r['v090_certificate'] is not None for r in allsteps),
                   'false_certs_all':sum(r['v090_wrong'] for r in allsteps),
                   'false_certs_drift_steps':sum(r['v090_wrong'] for c in g for r in c['trace'] if r['drift_step']),
                   'coverage_post':round(sum(r['v090_certificate'] is not None for r in post)/len(post),6),
                   'logloss_post':_mean([r['logloss_v090'] for r in post])},
          'v0.89':{'certs_all':sum(r['legacy_certificate'] is not None for r in allsteps),
                   'false_certs_all':sum(r['legacy_wrong'] for r in allsteps),
                   'coverage_post':round(sum(r['legacy_certificate'] is not None for r in post)/len(post),6),
                   'valid_steps_post':len(lv),'logloss_valid_steps':_mean([r['logloss_v089'] for r in lv]),
                   'v011_logloss_on_v089_valid_steps':_mean([r['logloss_brute'] for r in lv])},
          'baselines_logloss_post':{'uniform':round(UNIFORM_LOSS,6),**{f'suffix{k}':_mean([r['logloss_suffix'][k] for r in post]) for k in ('1','2','4')}},
          'ablation_logloss_post':_mean([r['logloss_ablation'] for r in post]),
          'logloss_post_per_mask':per_mask,
          'loss_decomposition_post':{k:{'steps':v[0],'mean_logloss':round(v[1]/v[0],6)} for k,v in sorted(phases.items())},
          'forecast_source_steps_post':{s:sum(r['forecast_source']==s for r in post) for s in FORECAST_SOURCES},
          'margin_fallback_actual_outside_support_post':sum(r['actual_emission_EVALUATOR_ONLY'] not in r['margin_support'] for r in margin_after),
          'margin_fallback_steps_post':len(margin_after),
          'retraction_reasons':{x:sum(r['reason']==x for r in rets) for x in RETRACTION_REASONS},
          'retracted_wrong':sum(r['wrong'] for r in rets),
          'wrong_certs_in_never_contradicted_cases':wrong_never_retracted,
          'family_contradicted_cases':sum(c['diagnostics']['family_status']=='grammar_contradicted' for c in g),
          'margin_contradicted_cases':sum(c['diagnostics']['margin_status']=='grammar_contradicted' for c in g),
          'drift_steps_all':len(drift_keys),
          'time_v011_informational_seconds':round(sum(c['elapsed_v011_informational'] for c in g),4),
          'time_v010_informational_seconds':round(sum(c['elapsed_v010_informational'] for c in g),4)}
    return out


def run(output,calibration_check):
    output=Path(output);plan=load(PLAN);check_freeze();cal=load(calibration_check)
    check(cal['plan_sha256']==sha(PLAN) and cal['freeze_sha256']==sha(FREEZE),'calibration check was made under a different plan/freeze')
    check(cal['tau_reproduced'] is True and cal['tau']==plan['residual_surprise']['tau'],'tau did not reproduce; study must not run')
    for name in ('RESULTS.json','SCIENTIFIC.json','SEAL.json'):
        check(not (output/name).exists(),'refusing overwrite '+str(output/name))
    tau=plan['residual_surprise']['tau'];cases=[];started=time.perf_counter()
    for fam,(lo,hi) in plan['heldout_ranges'].items():
        for seed in range(lo,hi+1):
            for rate in plan['mask_rates']:cases.append(run_case_003(seed,fam,rate,plan,tau))
        print('study-003 completed',fam,len(cases),'cases',flush=True)
    result={'schema':'brute.study.v1_1','plan':plan,'calibration_check':cal,'cases':cases,'summary':aggregate_003(cases,plan),
            'total_elapsed_informational':time.perf_counter()-started}
    write_new(output/'RESULTS.json',result);write_new(output/'SCIENTIFIC.json',no_time(result))
    write_new(output/'SEAL.json',{'study':plan['study'],'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),'plan_sha256':sha(PLAN),'freeze_sha256':sha(FREEZE),
        'calibration_check_sha256':sha(calibration_check),'case_count':len(cases)})
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(STUDY_DIR))
    ap.add_argument('--calibration-check',default=str(STUDY_DIR/'CALIBRATION_CHECK.json'));a=ap.parse_args()
    run(a.output,a.calibration_check);print('done')
