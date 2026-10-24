"""Frozen evaluator only: paired four-state expansion and out-of-grammar stress.

Hidden truth is never passed to AdequacyLearner. It sees only action and masked
sensor observations. The evaluator reports both conditional and public claims,
and scores predictive distributions using held-out emissions.
"""
from __future__ import annotations
from math import log
from time import perf_counter
from bgr89.worlds import world as old_world,actions
from bgr90.worlds import world as new_world,step as new_step
from bgr90.adequacy import AdequacyLearner

FAMILIES=('cycle3','switch3','unstructured3','unaliased2','ood4','ood5','drift4')
RATES=(.1,.35,.6)


def run_case(seed:int,family:str,mask_rate:float,steps=44,burn_in=8,max_prefixes=160000):
    if family not in FAMILIES or mask_rate not in RATES:raise ValueError('invalid study case')
    truth=(new_world if family in ('ood5','drift4') else old_world)(seed,family)
    hidden=truth.start
    initial=truth.observed(hidden,mask_rate,-1)
    learner=AdequacyLearner(max_states=4,max_prefixes=max_prefixes,smoothing=.08,scope_verified=False)
    learner.initialize(initial)
    records=[];start=perf_counter()
    for index,action in enumerate(actions(seed,steps)):
        forecast=learner.predict(action)
        hidden=(new_step(truth,hidden,action,index) if family=='drift4' else truth.next(hidden,action))
        actual=truth.emission(hidden)
        observed=truth.observed(hidden,mask_rate,index)
        learner.observe(action,observed)
        new_ll=-log(max(1e-12,forecast.probabilities[actual]))
        legacy_ll=None
        if forecast.prior_three_state_certificate is not None:
            old_cert=forecast.prior_three_state_certificate
        else:old_cert=None
        record={'step':index+1,'action':action,'observed':list(observed),
                'actual_emission_EVALUATOR_ONLY':actual,
                'model_status_after':learner.status,
                'legacy_conditional_certificate':old_cert,
                'expanded_conditional_certificate':forecast.conditional_certificate,
                'public_certificate':forecast.public_certificate,
                'support':list(forecast.scoped_support) if forecast.scoped_support is not None else None,
                'probabilities':[round(x,12) for x in forecast.probabilities],
                'heldout_logloss':round(new_ll,10),
                'legacy_wrong_certificate':old_cert is not None and old_cert!=actual,
                'expanded_wrong_certificate':forecast.conditional_certificate is not None and forecast.conditional_certificate!=actual,
                'model_rows_after':learner.support4.count,
                'known_three_state_still_supported':learner.legacy_valid}
        records.append(record)
    diag=learner.diagnostics();time_used=perf_counter()-start
    forecast_records=records[burn_in:]
    conditional=sum(x['expanded_conditional_certificate'] is not None for x in records)
    legacy=sum(x['legacy_conditional_certificate'] is not None for x in records)
    return {'schema':'bgr90.case.v1','seed':seed,'family':family,'mask_rate':mask_rate,
            'true_hidden_state_count_EVALUATOR_ONLY':truth.n,
            'within_proposed_4_state_grammar':family not in ('ood5','drift4'),
            'initial_visible':list(initial),'steps':steps,'burn_in':burn_in,'trace':records,
            'conditional_certificates':conditional,
            'conditional_false_certifications':sum(x['expanded_wrong_certificate'] for x in records),
            'legacy_certificates':legacy,
            'legacy_false_certifications':sum(x['legacy_wrong_certificate'] for x in records),
            'public_certificates':sum(x['public_certificate'] is not None for x in records),
            'mean_logloss_heldout':round(sum(x['heldout_logloss'] for x in forecast_records)/len(forecast_records),8),
            'legacy_contradiction_step':diag['legacy_contradiction_step'],
            'expanded_status':diag['symbolic']['status'],
            'expanded_model_rows':diag['symbolic']['model_rows'],
            'peak_model_rows':diag['symbolic']['max_rows_seen'],
            'model_hypothesis_transitions_examined':diag['symbolic']['transitions_examined'],
            'scope_verified_externally':False,'elapsed_informational':time_used}


def aggregate(cases):
    summary={}
    for family in FAMILIES:
        group=[c for c in cases if c['family']==family]
        if not group:continue
        summary[family]={'cases':len(group),'steps':sum(x['steps'] for x in group),
           'expanded_conditional_certs':sum(x['conditional_certificates'] for x in group),
           'expanded_wrong_conditional_certs':sum(x['conditional_false_certifications'] for x in group),
           'legacy_conditional_certs':sum(x['legacy_certificates'] for x in group),
           'legacy_wrong_conditional_certs':sum(x['legacy_false_certifications'] for x in group),
           'public_certificates':sum(x['public_certificates'] for x in group),
           'contradicted_old_three_state':sum(x['legacy_contradiction_step'] is not None for x in group),
           'contradicted_expanded_four_state':sum(x['expanded_status']=='grammar_contradicted' for x in group),
           'budget_exhausted':sum(x['expanded_status']=='budget_exhausted' for x in group),
           'mean_loss_new':round(sum(x['mean_logloss_heldout'] for x in group)/len(group),6),
           'mean_peak_rows':round(sum(x['peak_model_rows'] for x in group)/len(group),2),
           'max_peak_rows':max(x['peak_model_rows'] for x in group),
           'sum_hypothesis_transitions_examined':sum(x['model_hypothesis_transitions_examined'] for x in group),
           'time_informational_seconds':round(sum(x['elapsed_informational'] for x in group),4)}
    return summary
