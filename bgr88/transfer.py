"""Hierarchical empirical-Bayes transfer over permutation-invariant Boolean motifs.

Source priors are estimated using only actual action-observation histories, not
teacher laws. The source and target share only the public Boolean program
meta-grammar; target channel and action permutations are unknown to learner.
The motif prior is a *soft* ranking and NEVER shrinks hypothesis support.
"""
from __future__ import annotations
from collections import Counter,defaultdict
from dataclasses import dataclass
from math import exp,log
from .programs import ProgramLearner,source_motifs,catalogue
from .environments import make_world,walk


def motif_multiplicities(n,max_parents=1):
    counts=Counter(p.motif for p in catalogue(n,max_parents))
    return counts


def uniform_program_prior(n):
    return {m:1. for m in motif_multiplicities(n)}


def uniform_motif_prior(n):
    m=motif_multiplicities(n)
    return {motif:1/count for motif,count in m.items()}


def motif_program_weights(masses,n):
    count=motif_multiplicities(n)
    result={m:float(masses.get(m,0))/c for m,c in count.items()}
    return result


@dataclass(frozen=True)
class SourcePrior:
    weights:dict[tuple[int,int],float]
    learned_mass:dict[tuple[int,int],float]
    source_worlds:int
    source_observations:int
    n:int
    source_category:str
    iteration_count:int
    entropy_nats:float

    def summary(self):
        top=sorted(self.learned_mass.items(),key=lambda p:(-p[1],p[0]))
        return {'source_worlds':self.source_worlds,'source_observations':self.source_observations,
                'source_category':self.source_category,'iterations':self.iteration_count,
                'mass_by_motif':[{'arity':m[0],'truth_table_int':m[1], 'mass':round(w,8)} for m,w in top],
                'prior_entropy_nats':round(self.entropy_nats,7)}


def source_evidence(seed:int,category:str,worlds:int,steps:int,n:int=5):
    """Original no-reset source histories, with no hidden laws or identity map."""
    if n<4 or worlds<1 or steps<1:raise ValueError('invalid source cohort')
    examples=[]
    for i in range(worlds):
        training_seed=seed+17*i
        world=make_world(training_seed,category,active=4,distractors=n-4)
        actual=walk(world,steps,training_seed)
        examples.append({'source_id':i,'sensor_width':n,'action_count':len(world.actions),
                         'initial':list(world.initial),
                         'trace':[[list(s),a,list(t)] for s,a,t in actual]})
    return examples


def train_from_evidence(examples,category='unspecified',iterations:int=24,
                        alpha:float=.4,prior_strength:float=.82):
    """Learn motif prior using only the supplied raw source histories.

    This input, unlike a simulator model object, is sufficient for audit and
    to produce exactly the published learned prior offline.
    """
    if not examples or iterations<1 or alpha<=0 or not 0<=prior_strength<=1:
        raise ValueError('invalid learner budget')
    n=examples[0]['sensor_width'];count=motif_multiplicities(n)
    motifs=tuple(sorted(count));factors_list=[];seen=0
    for case in examples:
        if case['sensor_width']!=n:raise ValueError('mixed channel widths')
        learner=ProgramLearner(n,case['action_count'])
        last=tuple(case['initial'])
        for row in case['trace']:
            s,a,t=row;s=tuple(s);t=tuple(t)
            if s!=last:raise ValueError('source history reset/discontinuity')
            learner.observe(s,a,t);last=t;seen+=1
        for bank in learner.banks:
            counts=Counter(p.motif for p in bank)
            factors_list.append(tuple(counts.get(m,0)/count[m] for m in motifs))
    posterior={m:1/len(motifs) for m in motifs}
    for _ in range(iterations):
        nxt={m:alpha for m in motifs}
        for factors in factors_list:
            denom=sum(posterior[m]*factors[j] for j,m in enumerate(motifs))
            if denom<=0:raise AssertionError('source data outside hypothesis family')
            for j,m in enumerate(motifs):nxt[m]+=posterior[m]*factors[j]/denom
        total=sum(nxt.values());posterior={m:nxt[m]/total for m in motifs}
    transfer={m:prior_strength*posterior[m]+(1-prior_strength)/len(motifs) for m in motifs}
    ent=-sum(v*log(v) for v in posterior.values())
    return SourcePrior(motif_program_weights(transfer,n),posterior,len(examples),seen,
                       n,category,iterations,ent)


def source_train(seed:int,category:str='related',worlds:int=120,steps:int=18,
                 n:int=5,iterations:int=24,alpha:float=.4,prior_strength:float=.82):
    return train_from_evidence(source_evidence(seed,category,worlds,steps,n),category,
                               iterations,alpha,prior_strength)
