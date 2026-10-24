"""Reachability-relative competence, reusing immutable v0.81 no-reset traces."""
import json,hashlib
from pathlib import Path
from collections import deque
from random import Random
from bgr60.worlds import factory
from bgr60.generalist import GeneralLearner
ROOT=Path(__file__).resolve().parents[1]

def reachable(world,start):
    visited={start};q=deque([start])
    while q:
        s=q.popleft()
        for a in range(len(world.actions)):
            t=world.transition(a,s)
            if t not in visited:visited.add(t);q.append(t)
    return tuple(sorted(visited))

def evaluate(case):
    world=factory(case['seed'],case['family']);schema,actions=world.public()
    initial=tuple(Random(case['seed']*931+73).choice(d) for d in ()) # replaced below with single persistent RNG
    rng=Random(case['seed']*931+73)
    initial=tuple(rng.choice(d) for d in schema.domains)
    assert tuple(case['trace'][0]['before'])==initial
    states=reachable(world,initial)
    learner=GeneralLearner(schema,actions)
    for i,rec in enumerate(case['trace']):
        b=tuple(rec['before']);t=tuple(rec['after']);a=rec['action']
        assert world.transition(a,b)==t
        if i:assert tuple(case['trace'][i-1]['after'])==b
        learner.observe(a,b,t)
    oracle=GeneralLearner(schema,actions)
    for s in states:
        for a in range(len(actions)):oracle.observe(a,s,world.transition(a,s))
    total=len(states)*len(actions)
    certified=oracle_certified=incorrect=0
    missing=[]
    for s in states:
        for a in range(len(actions)):
            truth=world.transition(a,s)
            p=learner.certified(a,s);q=oracle.certified(a,s)
            if p is not None:
                certified+=1;incorrect+=p!=truth
            if q is not None:oracle_certified+=1
            if p is None and q is not None:missing.append((s,a))
    # Evaluate goal-directed competence from the terminal state, without reset.
    terminal=tuple(case['trace'][-1]['after'])
    goals=sorted(s for s in states if s!=terminal)
    solved=shortest=0;abstained=0
    for goal in goals:
        result=learner.plan(terminal,goal)
        if result['actions'] is None:abstained+=1;continue
        at=terminal
        for a in result['actions']:at=world.transition(a,at)
        assert at==goal
        solved+=1
        if len(result['actions'])==oracle_distance(world,terminal,goal):shortest+=1
    return {'seed':case['seed'],'family':case['family'],'policy':case['policy'],
            'reachable_states':len(states),'total_states':len(schema.all_states()),
            'reachable_state_actions':total,'oracle_certified':oracle_certified,
            'learner_certified':certified,'incorrect':incorrect,'missing_oracle_certifications':len(missing),
            'reachable_complete':certified==total,'oracle_reachable_complete':oracle_certified==total,
            'terminal_goals':len(goals),'solved':solved,'shortest':shortest,'abstained':abstained,
            'global_identified':learner.identified()}

def oracle_distance(world,start,goal):
    if start==goal:return 0
    q=deque([(start,0)]);seen={start}
    while q:
        s,d=q.popleft()
        for a in range(len(world.actions)):
            t=world.transition(a,s)
            if t==goal:return d+1
            if t not in seen:seen.add(t);q.append((t,d+1))
    return None

def run():
    cases=json.loads((ROOT/'results/PREDECESSOR_CASES.json').read_text())
    records=[evaluate(c) for c in cases]
    summary={}
    for p in ('epistemic','active','random','cyclic'):
        sub=[r for r in records if r['policy']==p]
        summary[p]={k:sum(r[k] for r in sub) for k in ('reachable_state_actions','oracle_certified','learner_certified','incorrect','missing_oracle_certifications','reachable_complete','oracle_reachable_complete','terminal_goals','solved','shortest','abstained')}
    out={'schema':'bgr82.reachable-competence.v1','study_type':'posthoc reanalysis of existing v0.81 histories; not a new held-out cohort','records':records,'summary':summary,'limitations':['oracle knows complete reachable graph','learner is given full typed states','goal evaluation from terminal state uses model-certified transitions','no new exploration policy or cross-domain transfer']}
    p=ROOT/'results/REACHABLE_STUDY.json';p.write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':run()
