"""Independent, non-vectorized replay of canonical observation-state constraints.

No import from bgr90.symbolic or adequacy or quotient. The reference stores
only edges and allowed emissions constrained by the observed trajectory; it
rebuilds them independently for each step and checks against the hidden truth.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from itertools import product
from random import Random
from bgr89.worlds import world as old_world,actions
from bgr90.worlds import world as new_world,step as new_step


def bit_compatible(code,obs):
    return all(b is None or ((code>>(1-i))&1)==b for i,b in enumerate(obs))


@dataclass(frozen=True)
class RefModel:
    paths:tuple[int,...]
    outputs:tuple[frozenset[int],...]
    current:int


def reference_initial(obs):
    return frozenset((RefModel((),(frozenset(i for i in range(4) if bit_compatible(i,obs)),),0),))


def reference_successors(model,action,mask_obs,max_states):
    n=len(model.outputs)
    edge=model.current*2+action
    old=model.paths[edge] if edge<len(model.paths) else -1
    if old==-1:possibilities=range(min(max_states,n+1))
    else:possibilities=(old,)
    for target in possibilities:
        if target>n:continue
        if target==n:
            valid=frozenset(c for c in range(4) if bit_compatible(c,mask_obs))
            outs=model.outputs+(valid,)
        else:
            valid=frozenset(c for c in model.outputs[target] if bit_compatible(c,mask_obs))
            outs=model.outputs[:target]+(valid,)+model.outputs[target+1:]
        if not valid:continue
        # transitions vector is indexed by state/action. New states own two unknown slots.
        edges=list(model.paths)+( [-1,-1] if target==n else [] )
        if old==-1:edges[edge]=target
        yield RefModel(tuple(edges),outs,target)


def ref_initial(obs):
    valid=frozenset(i for i in range(4) if bit_compatible(i,obs))
    return frozenset((RefModel((-1,-1),(valid,),0),))


def ref_support(models,action,max_states):
    all_codes=set()
    for m in models:
        known=m.paths[m.current*2+action]
        if known>=0:all_codes.update(m.outputs[known])
        else:
            for outputs in m.outputs:all_codes.update(outputs)
            if len(m.outputs)<max_states:all_codes.update(range(4))
    return tuple(sorted(all_codes)) if models else None


def ref_observe(models,action,observation,max_states,max_rows):
    new=set()
    for m in models:
        for nxt in reference_successors(m,action,observation,max_states):
            new.add(nxt)
            if len(new)>max_rows:return None,'budget_exhausted'
    if not new:return None,'grammar_contradicted'
    return frozenset(new),'supported'


def audit_case(c,plan):
    family=c['family'];seed=c['seed'];rate=c['mask_rate'];truth=(new_world if family in ('ood5','drift4') else old_world)(seed,family)
    hidden=truth.start;initial=truth.observed(hidden,rate,-1)
    assert list(initial)==c['initial_visible']
    rows=ref_initial(initial);status='supported';conditional=errors=baseline_errors=0;checks=0
    previous_legacy_valid=True;old_broken=None
    for i,(a,record) in enumerate(zip(actions(seed,c['steps']),c['trace'])):
        assert record['step']==i+1 and a==record['action']
        support=ref_support(rows,a,plan['symbolic_state_cap']) if status=='supported' else None
        assert (list(support) if support is not None else None)==record['support'],(seed,family,rate,i,'support mismatch')
        if status=='supported':
            expected=support[0] if len(support)==1 else None
        else:expected=None
        assert expected==record['expanded_conditional_certificate']
        assert record['public_certificate'] is None, 'unattested public certification'
        hidden=new_step(truth,hidden,a,i) if family=='drift4' else truth.next(hidden,a)
        actual=truth.emission(hidden)
        observed=truth.observed(hidden,rate,i)
        assert record['actual_emission_EVALUATOR_ONLY']==actual
        assert record['observed']==list(observed)
        expected_wrong=expected is not None and expected!=actual
        assert record['expanded_wrong_certificate']==expected_wrong
        assert record['legacy_wrong_certificate']==(record['legacy_conditional_certificate'] is not None and record['legacy_conditional_certificate']!=actual)
        if status=='supported':rows,status=ref_observe(rows,a,observed,plan['symbolic_state_cap'],plan['symbolic_partial_row_cap'])
        assert record['model_status_after']==status
        assert record['model_rows_after']==(len(rows) if rows else 0)
        expected_probs=record['probabilities']
        assert len(expected_probs)==4 and abs(sum(expected_probs)-1)<1e-8
        conditional+=expected is not None
        errors+=expected_wrong
        baseline_errors+=record['legacy_wrong_certificate']
        checks+=1
    assert c['conditional_certificates']==conditional
    assert c['conditional_false_certifications']==errors
    assert c['legacy_false_certifications']==baseline_errors
    assert c['expanded_status']==status
    assert c['public_certificates']==0
    return {'predictions_checked':checks,'conditional_certifications_checked':conditional,
            'conditional_false_certifications':errors,'legacy_false_certifications':baseline_errors,
            'public_certifications':0}


def reference_pair_equivalence(trans,emit,s,t):
    n=len(trans)
    for length in range(n+1):
        for word in product((0,1),repeat=length):
            x,y=s,t
            for a in word:x=trans[x][a];y=trans[y][a]
            if emit[x]!=emit[y]:return False
    return True


def independently_count_minimal(trans,emit,start):
    states={start};q=deque([start])
    while q:
        s=q.popleft()
        for t in trans[s]:
            if t not in states:states.add(t);q.append(t)
    # Build pairwise equivalence from brute-force future words.
    remaining=set(states);classes=[]
    while remaining:
        root=min(remaining)
        group={s for s in remaining if reference_pair_equivalence(trans,emit,root,s)}
        classes.append(group);remaining-=group
    return len(classes)
