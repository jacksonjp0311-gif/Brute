"""Paired, no-reset predictive-state study with evaluator-only hidden truth.

Full emitted code is used strictly by the scorer. Every learning update sees
only masked visible channels and the action that actually occurred.
"""
from __future__ import annotations
from math import log
from collections import defaultdict
from time import perf_counter
from .latent import LatentLearner,IncompatibleObservation
from .worlds import world,actions
from .baselines import SuffixFrequency

SCORERS=('latent','known_size','suffix1','suffix2','suffix4')
CHECKPOINTS=(8,16,28,44)

def loss(prob,actual):return -log(max(1e-12,prob[actual]))


def run_case(seed:int,family:str,mask_rate:float,steps=44,burn_in=8):
    truth=world(seed,family);hidden=truth.start
    obs=truth.observed(hidden,mask_rate,-1)
    learner=LatentLearner((1,2,3));learner.initialize(obs)
    # A privileged structural upper comparator (knows size but not rules)
    # ONLY used in evaluator and never made available to the primary learner.
    known=LatentLearner((truth.n,)) if truth.n<=3 else None
    if known is not None:known.initialize(obs)
    baselines={f'suffix{k}':SuffixFrequency(k,alpha=0.7) for k in (1,2,4)}
    for baseline in baselines.values():baseline.initialize(obs)
    trace=[];scores=[];model_break=None;certified=cert_errors=0
    start=perf_counter();schedule=actions(seed,steps)
    for t,a in enumerate(schedule):
        predictive={}
        support=()
        prediction=None  # Explicit abstention on every post-contradiction step.
        if model_break is None:
            predictive['latent'],support=learner.predict(a)
            prediction=support[0] if len(support)==1 else None
        if known is not None:predictive['known_size'],_=known.predict(a)
        for name,baseline in baselines.items():predictive[name]=baseline.predict(a)
        hidden=truth.next(hidden,a)
        actual=truth.emission(hidden)          # EVALUATOR ONLY
        visible=truth.observed(hidden,mask_rate,t)
        if model_break is None:
            if prediction is not None:
                certified+=1
                if prediction!=actual:cert_errors+=1
            try:learner.observe(a,visible)
            except IncompatibleObservation:model_break=t+1
        if known is not None:known.observe(a,visible)
        for baseline in baselines.values():baseline.observe(a,visible)
        result={'step':t+1,'action':a,'observed':list(visible),
                'heldout_emission_for_scoring':actual, 'logloss':{},
                'prediction':{name:[round(p,12) for p in prob] for name,prob in predictive.items()},
                'candidate_count':sum(b.count for b in learner.banks.values()),
                'certified':prediction,'incompatible_at_step':model_break==t+1}
        for name,prob in predictive.items():result['logloss'][name]=round(loss(prob,actual),10)
        trace.append(result)
        if t+1>burn_in:scores.append(result)
    avg={}
    for method in SCORERS:
        values=[x['logloss'][method] for x in scores if method in x['logloss']]
        avg[method]=round(sum(values)/len(values),8) if values else None
    snapshot=learner.snapshot() if model_break is None else {'class_models':{str(n):b.count for n,b in learner.banks.items()},'state_count_certified':None,'sensor_relation_certified':None}
    return {'seed':seed,'family':family,'masked_rate':mask_rate,'steps':len(trace),'burn_in':burn_in,
            'initial_visible':list(obs),'trace':trace,'scores':avg,
            'true_n_scoring_only':truth.n,'contradiction_step':model_break,
            'certified':certified,'certification_errors':cert_errors,
            'final_supported_models':{str(n):b.count for n,b in learner.banks.items()},
            'state_count_identified':snapshot['state_count_certified'],
            'sensor_relation_certified':snapshot['sensor_relation_certified'],
            'full_evidence_history':len(learner.history),'model_evaluations':learner.model_evaluations,
            'elapsed_informational':perf_counter()-start}


def aggregate(cases):
    rows={}
    for family in sorted(set(x['family'] for x in cases)):
      for rate in sorted(set(x['masked_rate'] for x in cases)):
        sub=[x for x in cases if x['family']==family and x['masked_rate']==rate]
        if not sub:continue
        scores={k:round(sum(c['scores'][k] for c in sub if c['scores'][k] is not None)/sum(c['scores'][k] is not None for c in sub),7) if any(c['scores'][k] is not None for c in sub) else None for k in SCORERS}
        rows[f'{family}::{rate}']={'worlds':len(sub),'mean_logloss':scores,'certified_predictions':sum(c['certified'] for c in sub),
                                   'false_certifications':sum(c['certification_errors'] for c in sub),
                                   'contradictions':sum(c['contradiction_step'] is not None for c in sub),
                                   'state_count_identified':sum(c['state_count_identified'] is not None for c in sub),
                                   'sensor_relation_certified':sum(c['sensor_relation_certified'] is not None for c in sub)}
    return rows
