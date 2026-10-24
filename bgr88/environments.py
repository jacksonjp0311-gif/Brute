"""Finite causal-task generators for testing alignment-free structural transfer.

The true programs and sensor permutation exist ONLY in the evaluator. Agents
receive the opaque observed Boolean vector, action indices, and real successor
observations. Every episode starts at one state and has no mid-run reset.
"""
from __future__ import annotations
from dataclasses import dataclass
from random import Random
from .programs import Program,OPERATOR_TABLES,State

SCHEDULE={
    'related':(('toggle',45),('xor',35),('copy',20)),
    'shifted':(('and',35),('or',35),('nand',30)),
    'mixed':(('toggle',10),('xor',10),('copy',10),('notcopy',10),('and',10),('or',10),('nand',10),('nor',10),('set1',10),('set0',10))
}

@dataclass(frozen=True)
class CausalWorld:
    width:int
    active:int
    actions:tuple[Program,...]
    initial:State
    public_action_names:tuple[str,...]
    permutation:tuple[int,...]
    category:str
    seed:int

    def transition(self,s:State,action:int):
        if len(s)!=self.width or action not in range(len(self.actions)):
            raise ValueError('invalid state/action')
        return self.actions[action].predict(s)

    def public(self):
        return {'channels':self.width,'actions':len(self.actions),
                'action_names':self.public_action_names,
                'observation':'unlabeled binary-channel vector; channel correspondence is unknown'}


def make_world(seed:int,category='related',active=4,distractors=1,actions=3):
    if category not in SCHEDULE:raise ValueError('unknown category')
    if active<3 or distractors<0 or active+distractors>9:raise ValueError('world width')
    rng=Random(seed*155921+19)
    n=active+distractors
    permutation=list(range(n));rng.shuffle(permutation)
    core=tuple(permutation[:active])
    rules=[]
    names=[]
    motifs,weights=zip(*SCHEDULE[category]);total=sum(weights)
    for a in range(actions):
        target=rng.choice(core)
        i=rng.randrange(total);which=next(mot for mot,weight in SCHEDULE[category] if (i:=i-weight)<0)
        arity,table=OPERATOR_TABLES[which]
        parents=() if arity==0 else (rng.choice([p for p in core if p!=target]),)
        rules.append(Program(target,parents,table))
        names.append('opaque-action-'+str(rng.randrange(10**9,10**10)))
    order=list(range(actions));rng.shuffle(order)
    programs=tuple(rules[i] for i in order)
    scrambled_names=tuple(names[i] for i in order)
    initial=tuple(rng.randrange(2) for _ in range(n))
    return CausalWorld(n,active,programs,initial,scrambled_names,tuple(permutation),category,seed)


def walk(world:CausalWorld,steps:int,seed:int):
    """Unprivileged random action schedule, same for every compared model."""
    rng=Random(seed*8191+73)
    state=world.initial
    trace=[]
    for t in range(steps):
        action=rng.randrange(len(world.actions))
        after=world.transition(state,action)
        trace.append((state,action,after))
        state=after
    return tuple(trace)


def ood_two_target_trace():
    """Synthetic contradiction: one action changes two observed coordinates."""
    return (0,0,0,0),(1,1,0,0)


def ood_xor_three_truth():
    """Generator-only three-input (self and two parents) transition function."""
    return Program(0,(1,2),0b10010110)
