"""Finite Boolean causal program induction directly from opaque binary channels.

There is no supplied function name, target channel, source channel or action
semantics. The *hypothesis meta-grammar* remains hand-specified: a stationary,
fully observed, single-target deterministic Boolean transition that depends on
its old value and initially at most one extra channel. v0.88 can expand to two
parents only on a contradiction, if enabled. This is not arbitrary language or
latent-variable discovery. Certifying is always support-based, never prior-based.
"""
from __future__ import annotations
from dataclasses import dataclass
from collections import defaultdict
from math import log
from itertools import combinations
from typing import Sequence

State=tuple[int,...]

class OutsideModelFamily(RuntimeError):
    """Every hypothesis is contradicted; caller must preserve previous state."""

@dataclass(frozen=True, slots=True)
class Program:
    target:int
    parents:tuple[int,...]
    table:int

    def predict(self,s:State)->State:
        index=s[self.target]
        for p in self.parents:index=(index<<1)|s[p]
        value=(self.table>>index)&1
        if value==s[self.target]:return s
        out=list(s);out[self.target]=value
        return tuple(out)

    @property
    def motif(self)->tuple[int,int]:
        return len(self.parents),self.table


def essential_parent(table:int,arity:int,parent_index:int)->bool:
    """Parent positions are 1..arity; bit 0 is the old target coordinate."""
    if not (1<=parent_index<=arity):raise ValueError('parent_index')
    mask=1<<(arity-parent_index)
    for index in range(1<<(arity+1)):
        if index&mask:continue
        if ((table>>index)&1)!=((table>>(index|mask))&1):return True
    return False


def catalogue(n:int,max_parents:int=1, require_essential=True)->tuple[Program,...]:
    if n<2 or n>9:raise ValueError('bounded binary channel width must be 2..9')
    if not 0<=max_parents<=2:raise ValueError('max_parents must be 0..2')
    out=[]
    for target in range(n):
        others=tuple(i for i in range(n) if i!=target)
        for k in range(max_parents+1):
            for parents in combinations(others,k):
                for table in range(1<<(1<<(k+1))):
                    if require_essential and any(not essential_parent(table,k,i+1) for i in range(k)):continue
                    out.append(Program(target,parents,table))
    return tuple(out)


def source_motifs(max_parents=1)->tuple[tuple[int,int],...]:
    return tuple(sorted({p.motif for p in catalogue(3,max_parents)}))


class ProgramLearner:
    """Exact support filtering for action programs on permuted sensor channels.

    Optional source-trained motif priors influence *ranking* of predictions;
    they may not affect support, hard certifications or authority. One action
    can be refit from all recorded observations with a wider grammar after an
    explicit contradiction. Outside-model observations trigger rollback.
    """
    def __init__(self,n:int,actions:int,prior=None,max_parents:int=1,allow_expand=False):
        if actions<1:raise ValueError('at least one action')
        self.n=n;self.actions=actions;self.max_parents=max_parents
        self.allow_expand=allow_expand
        self.prior={} if prior is None else dict(prior)
        self.catalogue=catalogue(n,max_parents)
        self.banks=[self.catalogue for _ in range(actions)]
        self.evidence=[]
        self.expansions=[]
        self.hypotheses_checked=0

    def _validate(self,s):
        if not isinstance(s,(tuple,list)) or len(s)!=self.n or any(x not in (0,1) for x in s):
            raise ValueError('expected finite binary sensor tuple')
        return tuple(s)

    def _weight(self,p:Program):
        return max(0.,self.prior.get(p.motif,1.))

    def _filter(self,bank,old,new):
        self.hypotheses_checked+=len(bank)
        return tuple(program for program in bank if program.predict(old)==new)

    def observe(self,old:State,action:int,new:State):
        old=self._validate(old);new=self._validate(new)
        if not 0<=action<self.actions:raise ValueError('action out of range')
        surviving=self._filter(self.banks[action],old,new)
        expanded=False
        if not surviving and self.allow_expand and self.max_parents<2:
            # Refit from all prior observations for this action. The witness
            # is retained only if some enlarged program explains the history.
            extended=catalogue(self.n,2)
            all_evidence=[(s,t) for a,s,t in self.evidence if a==action]+[(old,new)]
            for s,t in all_evidence:
                extended=self._filter(extended,s,t)
                if not extended:break
            if extended:
                surviving=extended;expanded=True
        if not surviving:
            raise OutsideModelFamily(f'action={action} transition {old}->{new} contradicts the allowed stationary one-target function family; no learning state mutated')
        if expanded:
            self.expansions.append({'after_observation':len(self.evidence)+1,'action':action,
                                    'from_max_parents':1,'to_max_parents':2})
        self.banks[action]=surviving
        self.evidence.append((action,old,new))
        return len(surviving)

    def predict_distribution(self,s:State,action:int):
        s=self._validate(s)
        if not 0<=action<self.actions:raise ValueError('action out of range')
        weights=defaultdict(float);total=0.
        for program in self.banks[action]:
            w=self._weight(program)
            weights[program.predict(s)]+=w;total+=w
        if total<=0:raise OutsideModelFamily('source prior has no support')
        return dict(sorted((out,w/total) for out,w in weights.items()))

    def certify(self,s:State,action:int):
        s=self._validate(s)
        predictions={h.predict(s) for h in self.banks[action]}
        return next(iter(predictions)) if len(predictions)==1 else None

    def posterior_motif(self,action:int):
        if not 0<=action<self.actions:raise ValueError('action out of range')
        totals=defaultdict(float);denom=0.
        for h in self.banks[action]:
            w=self._weight(h);totals[h.motif]+=w;denom+=w
        if denom<=0:raise OutsideModelFamily('posterior support has zero weight')
        return {m:w/denom for m,w in totals.items()}

    def snapshot(self):
        return {'candidate_counts':[len(x) for x in self.banks],
                'evidence_count':len(self.evidence),'expansions':list(self.expansions),
                'checks':self.hypotheses_checked}


# Operator labels for the synthetic *generator and report*, NEVER provided to
# the learner. These are arbitrary examples inside the full truth table space.
OPERATOR_TABLES={
    'toggle':(0,1), 'hold':(0,2),'set0':(0,0),'set1':(0,3),
    'copy':(1,10),'notcopy':(1,5),'xor':(1,6),'xnor':(1,9),
    'and':(1,8),'or':(1,14),'nand':(1,7),'nor':(1,1),
    'imp':(1,11),'reverse_imp':(1,13)
}
