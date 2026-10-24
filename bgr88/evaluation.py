"""No-reset, trace-paired source-to-target structural transfer evaluation.

A learner sees only current observations and action ids. Frozen random action
histories are shared by all predictors to isolate predictive transfer, NOT to
claim that transfer improves active experiment choice. The evaluator queries
all unseen state/action pairs off-policy strictly for scoring and never feeds
those counterfactual outcomes back to the learner.
"""
from __future__ import annotations
from collections import Counter
from itertools import product
from math import exp,log
from time import perf_counter
from .environments import make_world,walk
from .programs import ProgramLearner,source_motifs
from .transfer import uniform_motif_prior,uniform_program_prior
from .representation import roles,inferred_minimal_projection

POLICIES=('hierarchical_transfer','source_transfer','scratch_motif','scratch_program','wrong_transfer','persistence')
CHECKPOINTS=(0,2,4,8,14)


def normalize(programs,weights):
    out={};total=0.
    for p in programs:
        w=weights.get(p.motif,1.)
        total+=w
        after=p.predict
        # directly storing program weight only, no teacher access
        out[p]=w
    if total<=0:raise RuntimeError('empty prior support')
    return out,total


def prediction(bank,s,prior):
    weights={};total=0.
    for program in bank:
        w=prior.get(program.motif,1.)
        target=program.predict(s)
        weights[target]=weights.get(target,0.)+w
        total+=w
    if total<=0:raise RuntimeError('unsupported program bank')
    return {s:w/total for s,w in weights.items()}


def evidence_logbf(learner,transfer,scratch):
    """Log Bayes factor of transfer vs scratch for deterministic action traces.

    Action programs are independent under each hierarchical prior. The bank
    contains all consistent programs, and each motif's prior weight is always
    positive; model comparison can never silently discard the scratch model.
    """
    total=0.
    for bank in learner.banks:
        vt=sum(transfer.get(p.motif,1.) for p in bank)
        vu=sum(scratch.get(p.motif,1.) for p in bank)
        nt=sum(transfer.get(p.motif,1.) for p in learner.catalogue)
        nu=sum(scratch.get(p.motif,1.) for p in learner.catalogue)
        if min(vt,vu,nt,nu)<=0:raise RuntimeError('zero-supported prior')
        total+=log(vt/nt)-log(vu/nu)
    return total


def adaptive_gate(logbf):
    if logbf>40:return 1-1e-16
    if logbf< -40:return 1e-16
    return 1/(1+exp(-logbf))


def mixture(p,q,weight):
    outcomes=set(p)|set(q)
    return {s:weight*p.get(s,0)+(1-weight)*q.get(s,0) for s in outcomes}


def all_binary_states(n):return tuple(product((0,1),repeat=n))


def world_record(seed,category,transfer_prior,wrong_prior,checkpoint_steps=CHECKPOINTS,
                 width=5,actions=3):
    world=make_world(seed,category,active=4,distractors=width-4,actions=actions)
    trace=walk(world,max(checkpoint_steps),seed)
    learner=ProgramLearner(width,actions)
    scratch=uniform_motif_prior(width)
    scratch_program=uniform_program_prior(width)
    if any(w<=0 for w in transfer_prior.values()):raise ValueError('transfer cannot eliminate motif support')
    unobserved_queries=[];seen=set();rows=[]
    science_start=perf_counter()
    for checkpoint in checkpoint_steps:
        while len(learner.evidence)<checkpoint:
            t=len(learner.evidence)
            before,a,after=trace[t]
            learner.observe(before,a,after)
            seen.add((before,a))
        log_bf=evidence_logbf(learner,transfer_prior,scratch)
        trust=adaptive_gate(log_bf)
        metrics={p:{'queries':0,'negative_log_likelihood_sum':0.,'brier_sum':0.,'top1_correct':0,'probability_correct_sum':0.} for p in POLICIES}
        certified=wrong=0
        for s in all_binary_states(width):
            for a in range(actions):
                if (s,a) in seen:continue # truly unobserved input pair only
                truth=world.transition(s,a) # privileged evaluation ONLY
                support=learner.certify(s,a)
                if support is not None:
                    certified+=1
                    wrong+=int(support!=truth)
                bank=learner.banks[a]
                pt=prediction(bank,s,transfer_prior)
                pu=prediction(bank,s,scratch)
                pprog=prediction(bank,s,scratch_program)
                pw=prediction(bank,s,wrong_prior)
                ph=mixture(pt,pu,trust)
                preds={'hierarchical_transfer':ph,'source_transfer':pt,'scratch_motif':pu,
                       'scratch_program':pprog,'wrong_transfer':pw,'persistence':{s:1.}}
                for policy,p in preds.items():
                    prob=p.get(truth,0.)
                    rec=metrics[policy]
                    rec['queries']+=1
                    rec['negative_log_likelihood_sum']+=-log(max(1e-12,prob))
                    rec['brier_sum']+=1-2*prob+sum(v*v for v in p.values())
                    rec['top1_correct']+=int(max(p.items(),key=lambda kv:(kv[1],kv[0]))[0]==truth)
                    rec['probability_correct_sum']+=prob
        assert wrong==0, 'an uncertified out-of-grammar world was falsely certified'
        role=roles(learner)
        for a,item in enumerate(role['actions']):
            actual=world.actions[a]
            assert actual.target in item['possible_targets']
            if item['certified_target'] is not None:assert item['certified_target']==actual.target
            assert set(item['necessary_parent_channels']).issubset(actual.parents)
        projection=inferred_minimal_projection(learner)
        # Genuine evaluator test of certified projection: if dropped channel
        # ever changes under a sampled truth program or influences a retained
        # target, a proof has violated its model-family assumption.
        for action,true_program in enumerate(world.actions):
            if true_program.target not in projection['projection']:
                # All missing targets must be globally stationary.
                assert all(true_program.predict(bits)[true_program.target]==bits[true_program.target]
                           for bits in all_binary_states(width))
            else:
                assert all(p in projection['projection'] for p in true_program.parents)

        assert len({v['queries'] for v in metrics.values()})==1
        rows.append({'step':checkpoint,'posterior_sizes':[len(b) for b in learner.banks],
                     'trust_source':trust,'log_bayes_factor':log_bf,
                     'certified_unseen':certified,'incorrect_certified_unseen':wrong,
                     'metrics':metrics,
                     'certified_action_targets':sum(x['certified_target'] is not None for x in role['actions']),
                     'certified_parent_sets':sum(x['exact_parent_set_certified'] for x in role['actions']),
                     'certified_static_channels':len(role['channels_certified_never_directly_modified']),
                     'projected_width':projection['width_projected'],
                     'projected_dropped':list(projection['dropped'])})
    return {'seed':seed,'category':category,'width':width,'actions':actions,
            'initial':list(world.initial),
            'trace':[{'before':list(s),'action':a,'after':list(t)} for s,a,t in trace],
            'rule_family_known':'stationary one-target Boolean function, up to one parent (no operator labels or coordinate correspondence)',
            'teacher_true_programs_evaluator_only':[{'target':p.target,'parents':list(p.parents),'table':p.table} for p in world.actions],
            'sensor_permutation_evaluator_only':list(world.permutation),
            'checkpoint_rows':rows,
            'hypothesis_checks':learner.hypotheses_checked,
            'wall_time_informational':perf_counter()-science_start}


def summarize(cases,checkpoints=CHECKPOINTS):
    by={}
    for group in sorted(set(c['category'] for c in cases)):
        per_group=[c for c in cases if c['category']==group]
        by[group]={'worlds':len(per_group),'checkpoint_metrics':{}}
        for t in checkpoints:
            r=[next(item for item in c['checkpoint_rows'] if item['step']==t) for c in per_group]
            data={}
            for p in POLICIES:
                # Macro-average within world, then average worlds (not
                # treating 90 correlated state queries as independent draws).
                q=sum(x['metrics'][p]['queries'] for x in r)
                scores=[x['metrics'][p] for x in r]
                data[p]={
                  'mean_world_logloss':sum(s['negative_log_likelihood_sum']/s['queries'] for s in scores)/len(scores),
                  'mean_world_brier':sum(s['brier_sum']/s['queries'] for s in scores)/len(scores),
                  'macro_world_top1_accuracy':sum(s['top1_correct']/s['queries'] for s in scores)/len(scores),
                  'macro_world_true_probability':sum(s['probability_correct_sum']/s['queries'] for s in scores)/len(scores),
                  'unseen_queries':q}
            by[group]['checkpoint_metrics'][str(t)]={
                'policies':data,
                'certified_unseen':sum(x['certified_unseen'] for x in r),
                'false_certifications':sum(x['incorrect_certified_unseen'] for x in r),
                'mean_source_trust':sum(x['trust_source'] for x in r)/len(r),
                'certified_action_targets':sum(x['certified_action_targets'] for x in r),
                'certified_parent_sets':sum(x['certified_parent_sets'] for x in r),
                'mean_projected_width':sum(x['projected_width'] for x in r)/len(r),
                'certified_static_channels':sum(x['certified_static_channels'] for x in r)}
    return by
