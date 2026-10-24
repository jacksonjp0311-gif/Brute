"""Proof-gated observable-channel causal role discovery.

A coordinate's role is *certified* only if it holds in EVERY surviving action
program; unsolved roles are explicitly kept as sets. This is representation
inference within a specified finite grammar, not discovery of hidden state
behind aliasing or raw-sensor decoding.
"""
from __future__ import annotations
from .programs import ProgramLearner


def roles(learner:ProgramLearner):
    if not all(learner.banks):raise ValueError('missing action program bank')
    per_action=[]
    for a,bank in enumerate(learner.banks):
        targets=sorted({p.target for p in bank})
        parent_sets={p.parents for p in bank}
        possible_parents=sorted({v for p in bank for v in p.parents})
        necessary_parents=sorted(set.intersection(*(set(p.parents) for p in bank)))
        per_action.append({'action':a,'possible_targets':targets,
                           'certified_target':targets[0] if len(targets)==1 else None,
                           'possible_parent_channels':possible_parents,
                           'necessary_parent_channels':necessary_parents,
                           'exact_parent_set_certified':len(parent_sets)==1,
                           'certified_parent_set':list(next(iter(parent_sets))) if len(parent_sets)==1 else None,
                           'candidate_rules':len(bank)})
    possible_targets={i for a in per_action for i in a['possible_targets']}
    return {'actions':per_action,
            'channels_certified_never_directly_modified':sorted(set(range(learner.n))-possible_targets),
            'meaning':'roles supported under supplied stationary one-target Boolean program class; not hidden latent state discovery'}


def certify_state_projection(learner:ProgramLearner, retained:tuple[int,...]):
    """Can these observed channels reconstruct the future state (using stored static values)?

    If every candidate effect on a retained channel uses only retained
    inputs and every removed channel is certified immutable, projection is
    an autonomous predictive state (plus the removed values frozen at start). This is a theorem relative to the supplied finite grammar.
    The projection does NOT predict discarded raw channels and doesn't prove
    that discarded channels are absent from physical reality.
    """
    indices=tuple(sorted(set(retained)))
    if not indices or any(i not in range(learner.n) for i in indices):
        raise ValueError('nonempty valid retained channel subset required')
    kept=set(indices);counterexamples=[]
    for a,bank in enumerate(learner.banks):
        for rule in bank:
            if rule.target in kept and any(p not in kept for p in rule.parents):
                counterexamples.append({'action':a,'target':rule.target,
                                        'outside_parents':tuple(p for p in rule.parents if p not in kept),
                                        'reason':'retained target depends on removed coordinate'})
                break
            if rule.target not in kept:
                # A removed channel must be provably invariant under EVERY
                # surviving program. Preserve initial static value separately
                # if a caller reconstructs the full observed state.
                arity=len(rule.parents)
                if any(((rule.table>>key)&1)!= (key>>arity) for key in range(1<<(arity+1))):
                    counterexamples.append({'action':a,'target':rule.target,'outside_parents':(),
                                            'reason':'candidate action can change removed channel'})
                    break
    return {'retained':indices,'eliminated':tuple(i for i in range(learner.n) if i not in kept),
            'proved_sufficient':not counterexamples,
            'violating_candidate_actions':tuple(counterexamples),
            'scope':'Projected dynamics are autonomous and removed coordinates are stationary for every surviving causal program; conditional on true model remaining in version spaces'}


def inferred_minimal_projection(learner:ProgramLearner):
    """Deterministically remove coordinates only with a sufficient proof.

    Conservative greedy reduction; not guaranteed globally minimum size.
    """
    kept=list(range(learner.n));attempts=[]
    for i in range(learner.n):
        trial=tuple(x for x in kept if x!=i)
        if not trial:break
        c=certify_state_projection(learner,trial)
        attempts.append({'drop':i,'allowed':c['proved_sufficient']})
        if c['proved_sufficient']:kept=list(trial)
    proof=certify_state_projection(learner,tuple(kept))
    assert proof['proved_sufficient']
    return {'projection':tuple(kept),'dropped':proof['eliminated'],
            'width_original':learner.n,'width_projected':len(kept),
            'proof':proof,'attempted_removals':attempts,
            'optimality_claim':False}
