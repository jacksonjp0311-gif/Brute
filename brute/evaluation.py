"""Brute study-002 evaluator. Hidden truth never reaches BruteLearner.

Every case runs three predictors side by side on one action/observation trace:
Brute v0.1.0, the v0.90 control (<=4 symbolic support certificate, same as
bgr90.AdequacyLearner) and the v0.89 n<=3 catalogue, plus suffix baselines.
"""
from __future__ import annotations
from math import log
from time import perf_counter
from bgr89.worlds import world as old_world,actions
from bgr89.baselines import SuffixFrequency
from bgr90.worlds import world as new_world,step as new_step
from brute.core.learner import BruteLearner,ScopeAttestation,Status

FAMILIES=('cycle3','switch3','unstructured3','unaliased2','ood4','ood5','drift4')
IN_FAMILY=('cycle3','switch3','unstructured3','unaliased2','ood4')
UNIFORM_LOSS=log(4)
STATUS_KEYS=('CERTIFIED','POSSIBLE_SET','ABSTAIN/MARGIN_DISAGREES','ABSTAIN/BOUND_SATURATED',
             'ABSTAIN/BUDGET_EXHAUSTED','OUT_OF_FAMILY/FAMILY_CONTRADICTED','OUT_OF_FAMILY/RESIDUAL_SURPRISE','ERROR/INTERNAL')


def loss(prob,actual):return -log(max(1e-12,prob[actual]))


def status_key(f):
    return f.status.value if f.reason is None else f'{f.status.value}/{f.reason.value}'


def run_case(seed,family,mask_rate,plan,tau,attest=None):
    if family not in FAMILIES:raise ValueError(family)
    truth=(new_world if family in ('ood5','drift4') else old_world)(seed,family)
    attest=(family in plan['in_family']) if attest is None else attest
    att=ScopeAttestation(plan['declared_family'],'evaluator','synthetic world built inside the family') if attest else None
    hidden=truth.start;initial=truth.observed(hidden,mask_rate,-1)
    L=BruteLearner(plan['family_state_cap'],plan['margin_state_cap'],plan['row_budget_family'],
                   plan['row_budget_margin'],plan['prediction_smoothing'],plan['open_world_reserve_epsilon'],
                   plan['residual_surprise']['window_W'],tau,att)
    L.initialize(initial)
    suffix={k:SuffixFrequency(k,0.7) for k in (1,2,4)}
    for b in suffix.values():b.initialize(initial)
    records=[];started=perf_counter()
    for i,a in enumerate(actions(seed,plan['actions_per_case'])):
        f=L.predict(a);L.record_issued(f)
        base={k:b.predict(a) for k,b in suffix.items()}
        hidden=new_step(truth,hidden,a,i) if family=='drift4' else truth.next(hidden,a)
        actual=truth.emission(hidden);observed=truth.observed(hidden,mask_rate,i)
        v090_cert=f.support[0] if f.support is not None and len(f.support)==1 else None
        surprise=L.observe(a,observed)
        for k,b in suffix.items():b.observe(a,observed)
        records.append({'step':i+1,'action':a,'observed':list(observed),'actual_emission_EVALUATOR_ONLY':actual,
            'status':f.status.value,'reason':f.reason.value if f.reason else None,
            'certificate':f.certificate,'public_certificate':f.public_certificate,
            'public_reason':f.public_reason.value if f.public_reason else None,
            'support':list(f.support) if f.support is not None else None,
            'margin_support':list(f.margin_support) if f.margin_support is not None else None,
            'saturated':f.saturated,'probabilities':[round(x,12) for x in f.probabilities],
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
            'logloss_v090':round(loss(f.v090_probabilities,actual),10),
            'logloss_v089':None if f.legacy_probabilities is None else round(loss(f.legacy_probabilities,actual),10),
            'logloss_suffix':{str(k):round(loss(p,actual),10) for k,p in base.items()},
            'min_probability':round(min(f.probabilities),12),
            'family_status_after':L.support.status,'margin_status_after':L.margin.status,
            'family_rows_after':L.support.count,'margin_rows_after':L.margin.count})
    d=L.diagnostics()
    return {'schema':'brute.case.v1','seed':seed,'family':family,'mask_rate':mask_rate,
            'in_family_EVALUATOR_ONLY':family in plan['in_family'],'attested':bool(attest),
            'true_hidden_state_count_EVALUATOR_ONLY':truth.n,'initial_visible':list(initial),
            'steps':plan['actions_per_case'],'burn_in':plan['burn_in'],'tau':tau,'trace':records,
            'diagnostics':d,'elapsed_informational':perf_counter()-started}


def _mean(xs):return round(sum(xs)/len(xs),6) if xs else None


def aggregate(cases):
    out={}
    for fam in FAMILIES:
        g=[c for c in cases if c['family']==fam]
        if not g:continue
        allsteps=[r for c in g for r in c['trace']]
        post=[r for c in g for r in c['trace'][c['burn_in']:]]
        def cov(key):return round(sum(r[key] is not None for r in post)/len(post),6)
        def risk(key,wrong):
            n=sum(r[key] is not None for r in post)
            return round(sum(r[wrong] for r in post)/n,6) if n else None
        breakdown={k:0 for k in STATUS_KEYS}
        for r in post:
            k=r['status'] if r['reason'] is None else f"{r['status']}/{r['reason']}"
            breakdown[k]=breakdown.get(k,0)+1
        lv=[r for r in post if r['logloss_v089'] is not None]
        out[fam]={'cases':len(g),'steps_all':len(allsteps),'steps_post_burn_in':len(post),
          'brute_certs_all':sum(r['certificate'] is not None for r in allsteps),
          'brute_false_certs_all':sum(r['brute_wrong'] for r in allsteps),
          'public_certs_all':sum(r['public_certificate'] is not None for r in allsteps),
          'public_false_certs_all':sum(r['public_wrong'] for r in allsteps),
          'v090_certs_all':sum(r['v090_certificate'] is not None for r in allsteps),
          'v090_false_certs_all':sum(r['v090_wrong'] for r in allsteps),
          'v089_certs_all':sum(r['legacy_certificate'] is not None for r in allsteps),
          'v089_false_certs_all':sum(r['legacy_wrong'] for r in allsteps),
          'coverage_post':{'brute':cov('certificate'),'v090':cov('v090_certificate'),'v089':cov('legacy_certificate')},
          'selective_risk_post':{'brute':risk('certificate','brute_wrong'),'v090':risk('v090_certificate','v090_wrong'),
                                 'v089':risk('legacy_certificate','legacy_wrong')},
          'status_breakdown_post':breakdown,
          'logloss_post':{'brute':_mean([r['logloss_brute'] for r in post]),'v090':_mean([r['logloss_v090'] for r in post]),
                          'uniform':round(UNIFORM_LOSS,6),
                          **{f'suffix{k}':_mean([r['logloss_suffix'][k] for r in post]) for k in ('1','2','4')}},
          'logloss_v089_valid_steps':{'steps':len(lv),'v089':_mean([r['logloss_v089'] for r in lv]),
                                      'brute':_mean([r['logloss_brute'] for r in lv])},
          'min_probability_any_step':min(r['min_probability'] for r in allsteps),
          'cases_with_alarm':sum(c['diagnostics']['alarm_step'] is not None for c in g),
          'alarm_steps_post':sum(r['reason']=='RESIDUAL_SURPRISE' for r in post),
          'family_contradicted_cases':sum(c['diagnostics']['family_status']=='grammar_contradicted' for c in g),
          'margin_contradicted_cases':sum(c['diagnostics']['margin_status']=='grammar_contradicted' for c in g),
          'v089_contradicted_cases':sum(c['diagnostics']['legacy_contradiction_step'] is not None for c in g),
          'certificates_retracted':sum(c['diagnostics']['certificates_retracted'] for c in g),
          'budget_exhausted_family':sum(c['diagnostics']['family_status']=='budget_exhausted' for c in g),
          'budget_exhausted_margin':sum(c['diagnostics']['margin_status']=='budget_exhausted' for c in g),
          'peak_rows_family':max(c['diagnostics']['family_peak_rows'] for c in g),
          'peak_rows_margin':max(c['diagnostics']['margin_peak_rows'] for c in g),
          'time_informational_seconds':round(sum(c['elapsed_informational'] for c in g),4)}
    return out


def no_time(obj):
    """Strip EVERY wall-clock key (F10): any key ending in '_informational' or '_informational_seconds'."""
    if isinstance(obj,dict):return {k:no_time(v) for k,v in obj.items() if not (k.endswith('_informational') or k.endswith('_informational_seconds'))}
    if isinstance(obj,list):return [no_time(v) for v in obj]
    return obj
