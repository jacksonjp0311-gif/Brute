"""Independent evidence reconstruction for goal-directed no-reset learning.

No imports of the BGR learner, study policies, goal-value controller, or
reachable-certificate implementation. The simulator is used only to replay
external teacher behavior and reference shortest paths. Causal candidate
banks, predictions, and closed-reachability proofs are implemented anew.
"""
from __future__ import annotations
from collections import deque
from itertools import combinations
from random import Random
from pathlib import Path
from hashlib import sha256
import argparse,json
from bgr60.worlds import factory
ROOT=Path(__file__).resolve().parents[1]

def canonical(o):return json.dumps(o,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def digest(o):return sha256(canonical(o)).hexdigest()


def independent_oracle_distances(world,start):
    distances={start:0};todo=deque([start])
    while todo:
        state=todo.popleft()
        for ai in range(len(world.actions)):
            nxt=world.transition(ai,state)
            if nxt not in distances:
                distances[nxt]=distances[state]+1;todo.append(nxt)
    return distances


def expected_goal(world,seed,start):
    distances=independent_oracle_distances(world,start)
    pool=[s for s,d in distances.items() if d>=2]
    if not pool:pool=[s for s,d in distances.items() if d>=1]
    if not pool:return None,None
    farthest=max(distances[s] for s in pool)
    choices=sorted(s for s in pool if distances[s]==farthest)
    target=Random(seed*1009+711).choice(choices)
    return target,distances[target]


def reference_banks(schema,actions):
    models=[]
    n=len(schema.names)
    for target in range(n):
        other=[i for i in range(n) if i!=target]
        for k in range(min(2,len(other))+1):
            for parent in combinations(other,k):
                models.append((target,parent,{}))
    return [[(t,p,{}) for t,p,d in models] for _ in actions]


def possible(banks,schema,action,state):
    outcomes=set()
    for target,parents,lookup in banks[action]:
        key=(state[target],)+tuple(state[i] for i in parents)
        for value in ((lookup[key],) if key in lookup else schema.domains[target]):
            after=list(state);after[target]=value;outcomes.add(tuple(after))
    return outcomes


def cert(banks,schema,action,state):
    outcomes=possible(banks,schema,action,state)
    return next(iter(outcomes)) if len(outcomes)==1 else None


def closure(banks,schema,actions,start):
    seen={start};q=deque([start]);edges={};boundary=[]
    while q:
        state=q.popleft()
        for ai in range(len(actions)):
            nxt=cert(banks,schema,ai,state)
            if nxt is None:
                boundary.append((state,ai));continue
            edges[(state,ai)]=nxt
            if nxt not in seen:
                seen.add(nxt);q.append(nxt)
    return seen,edges,boundary


def reference_goal_plan(banks,schema,actions,start,goal):
    reachable,edges,boundary=closure(banks,schema,actions,start)
    complete=not boundary
    if goal not in reachable:
        return {'status':'provably_unreachable_in_model_family' if complete else 'abstain_unknown_reachability',
                'plan':None,'reachable_certificate':complete}
    back={start:None};q=deque([start])
    while q:
        s=q.popleft()
        if s==goal:
            route=[];x=s
            while back[x] is not None:
                parent,ai=back[x];route.append(ai);x=parent
            return {'status':'solved','plan':route[::-1],'shortest_claim':complete,
                    'reachable_certificate':complete}
        for ai in range(len(actions)):
            nxt=edges.get((s,ai))
            if nxt is not None and nxt not in back:
                back[nxt]=(s,ai);q.append(nxt)
    raise AssertionError('certified closure graph cannot reach admitted target')


def audit_case(case,budget):
    w=factory(case['seed'],case['family']);schema,actions=w.public()
    rng=Random(case['seed']*931+73)
    init=tuple(rng.choice(d) for d in schema.domains)
    assert case['initial']==list(init),'incorrect initial state'
    goal,oracle_cost=expected_goal(w,case['seed'],init)
    if goal is None:
        assert not case['eligible'] and not case['trace'] and case['goal'] is None
        assert case['registered_budget']==budget
        return {'eligible':False,'actions':0,'certified':0,'plans_replayed':0,'false_certifications':0,
                'shortest_claims_checked':0,'posterior_counts_checked':0,'goal_succeeded':False}
    assert case['eligible'] and case['goal']==list(goal) and case['oracle_initial_shortest']==oracle_cost
    assert case['registered_budget']==budget
    assert len(case['trace'])==case['steps']<=budget
    banks=reference_banks(schema,actions)
    current=init;candidate_checks=0;first_closure=None
    for i,rec in enumerate(case['trace'],start=1):
        assert list(current)==rec['before'],'history discontinuity'
        assert current!=goal,'continued acting after target achieved'
        action=rec['action'];assert 0<=action<len(actions)
        after=w.transition(action,current)
        assert list(after)==rec['after'],'action outcome does not match world'
        updated=[];before_len=len(banks[action]);candidate_checks+=before_len
        for target,parents,lookup in banks[action]:
            if any(current[j]!=after[j] for j in range(len(schema.names)) if j!=target):continue
            inp=(current[target],)+tuple(current[p] for p in parents)
            if inp in lookup and lookup[inp]!=after[target]:continue
            table=dict(lookup);table[inp]=after[target];updated.append((target,parents,table))
        assert updated,'correct teacher incorrectly excluded'
        banks[action]=updated
        assert len(updated)==rec['candidates_after']
        current=after
        if first_closure is None:
            states,edges,boundary=closure(banks,schema,actions,init)
            if not boundary:first_closure=i
    assert case['final']==list(current)
    assert case['reached']==(current==goal)
    assert case['steps_to_goal']==(len(case['trace']) if current==goal else None)
    assert first_closure==case['initial_proof_step']
    assert candidate_checks==case['candidate_checks']
    true_reach=independent_oracle_distances(w,init)
    total=len(true_reach)*len(actions)
    certified=wrong=0
    for state in true_reach:
        for ai in range(len(actions)):
            proposed=cert(banks,schema,ai,state)
            if proposed is not None:
                certified+=1
                if proposed!=w.transition(ai,state):wrong+=1
    assert certified==case['knowledge_certified']
    assert total==case['knowledge_possible']
    assert wrong==case['knowledge_wrong']==0
    full_proof=not closure(banks,schema,actions,init)[-1]
    assert full_proof==case['final_initial_reachable_complete']
    planned=reference_goal_plan(banks,schema,actions,current,goal)
    assert planned==case['final_goal_plan'],'final goal plan was not independently reproduced'
    shortest_claims=0;replayed=0
    if planned['plan'] is not None:
        result=current
        for ai in planned['plan']:result=w.transition(ai,result)
        assert result==goal
        replayed=1
        if planned['shortest_claim']:
            shortest_claims=1
            assert len(planned['plan'])==independent_oracle_distances(w,current)[goal]
    return {'eligible':True,'actions':case['steps'],'certified':certified,'plans_replayed':replayed,
            'false_certifications':wrong,'shortest_claims_checked':shortest_claims,
            'posterior_counts_checked':case['steps'], 'goal_succeeded':case['reached']}


def audit_results(folder,write=False):
    folder=Path(folder);result_file=folder/'RESULTS.json';data=json.loads(result_file.read_text())
    scientific_file=folder/'SCIENTIFIC.json';events_file=folder/'EVENTS.json';seal=json.loads((folder/'SEAL.json').read_text())
    for filename,dig in [('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256'),('EVENTS.json','events_sha256')]:
        assert sha256((folder/filename).read_bytes()).hexdigest()==seal[dig],filename
    assert data['plan']==json.loads((ROOT/'experiments/PLAN.json').read_text())
    assert sha256((ROOT/'experiments/PLAN.json').read_bytes()).hexdigest()==seal['plan_sha256']
    assert sha256((ROOT/'experiments/SOURCE_FREEZE.json').read_bytes()).hexdigest()==seal['source_freeze_sha256']
    source=json.loads((ROOT/'experiments/SOURCE_FREEZE.json').read_text())
    for name,expected in source['files'].items():
        assert sha256((ROOT/name).read_bytes()).hexdigest()==expected,('freeze mismatch',name)
    from experiments.run_study import strip_timing # only JSON projection; never imports learner or prediction code
    assert strip_timing(data)==json.loads(scientific_file.read_text())
    entries=json.loads(events_file.read_text());assert len(entries)==len(data['cases'])==seal['records']
    prev='0'*64;seen_pairs={};rows=[]
    for case,event in zip(data['cases'],entries):
        unsigned={k:v for k,v in event.items() if k!='sha256'}
        assert event['previous']==prev and digest(unsigned)==event['sha256']
        assert event['scientific_sha256']==digest(strip_timing(case))
        prev=event['sha256']
        pair=(case['family'],case['seed'])
        expected=(case['initial'],case['goal'],case['oracle_initial_shortest'],case['eligible'])
        if pair in seen_pairs:assert seen_pairs[pair]==expected,'policies have unpaired goals'
        else:seen_pairs[pair]=expected
        rows.append(audit_case(case,data['plan']['max_actions_per_policy_world']))
    assert prev==seal['previous_event_sha256']
    from bgr86.study import aggregate # formatting and summary only; NO model calculations
    assert aggregate(data['cases'])==data['summary']
    confirmed={'schema':'bgr86.independent-audit.v1','status':'passed',
        'study_id':data['study_id'],'study_sha256':sha256(result_file.read_bytes()).hexdigest(),
        'distinct_worlds':len(seen_pairs),'policy_world_records':len(rows),
        'original_actions_replayed':sum(x['actions'] for x in rows),
        'posterior_observation_updates_independently_checked':sum(x['posterior_counts_checked'] for x in rows),
        'certified_outcomes_independently_checked':sum(x['certified'] for x in rows),
        'false_certifications':sum(x['false_certifications'] for x in rows),
        'terminal_goal_plans_replayed':sum(x['plans_replayed'] for x in rows),
        'shortest_claims_verified':sum(x['shortest_claims_checked'] for x in rows),
        'goal_successes':sum(x['goal_succeeded'] for x in rows),
        'all_paired_goals_match':True,
        'independence_scope':'Separate version-space filtering, goal selection, prediction and teacher BFS; same synthetic world generator. Heuristic policy decisions are recorded and replayed but not independently recomputed.',
        'scientific_limit':'Correctness conditional on finite deterministic local grammar and known fully observed state; no AGI inference.'}
    if write:
        dest=folder/'INDEPENDENT_AUDIT.json'
        if dest.exists():raise RuntimeError('refusing overwrite of existing audit')
        dest.write_text(json.dumps(confirmed,indent=2,sort_keys=True)+'\n')
    return confirmed

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--results-dir',default=str(ROOT/'results/study-001'))
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    print(json.dumps(audit_results(args.results_dir,write=args.write),indent=2,sort_keys=True))
