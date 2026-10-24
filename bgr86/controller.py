"""Goal-conditioned information routing over a partially identified finite world.

The teacher model, true reachability, and any ability to reset the world are
absent. Only public state/action alphabets, current observation, an externally
provided goal and the learner's hypothesis version spaces are available.

There are three different claims:
- certified: every surviving model agrees on the transition;
- robust: every possible outcome leads to a winning state within a finite bound;
- heuristic: scores uncertain experiments to improve expected goal attainment.
Heuristic probabilities NEVER certify any transition or guarantee safety.
"""
from __future__ import annotations
from collections import Counter,deque
from dataclasses import dataclass,asdict
from bgr60.generalist import GeneralLearner

State=tuple[int,...]


def allowed_outcomes(learner:GeneralLearner, state:State,action:int,allowed=None,cache=None):
    key=(state,action)
    if cache is not None and key in cache:return cache[key]
    outcome=learner.possible_outcomes(action,state)
    answer=None if not outcome or (allowed is not None and not all(allowed(x) for x in outcome)) else frozenset(outcome)
    if cache is not None:cache[key]=answer
    return answer


def robust_goal_depth(learner:GeneralLearner,goal:State,allowed=None,cache=None):
    """Exact strong-predecessor fixed point in the rectangular uncertainty model.

    This is a conservative overapproximation of persistent model uncertainty,
    so a 'winning' claim is sound if the teacher remains in every version space.
    It is not globally optimal Bayes-adaptive planning.
    """
    learner.schema.validate(goal)
    states=learner.schema.all_states()
    depth={goal:0}
    for _ in range(len(states)):
        newly={}
        for state in states:
            if state in depth or (allowed and not allowed(state)):continue
            candidates=[]
            for a in range(len(learner.actions)):
                outcomes=allowed_outcomes(learner,state,a,allowed,cache)
                if outcomes is not None and all(t in depth for t in outcomes):
                    candidates.append(1+max(depth[t] for t in outcomes))
            if candidates:newly[state]=min(candidates)
        if not newly:break
        depth.update(newly)
    return depth


def optimistic_distances(learner:GeneralLearner, goal:State,allowed=None,cache=None):
    """Lower bounds on goal steps if some candidate outcomes are favorable.

    This graph is an optimism heuristic only. Never assert that an optimistic
    edge is known, safe in an unrestricted world, or executable as a plan.
    """
    reverse={goal:[]}
    for s in learner.schema.all_states():
        if allowed is not None and not allowed(s):continue
        for a in range(len(learner.actions)):
            outcomes=allowed_outcomes(learner,s,a,allowed,cache)
            if outcomes is None:continue
            for nxt in outcomes:reverse.setdefault(nxt,[]).append(s)
    d={goal:0};q=deque([goal])
    while q:
        s=q.popleft()
        for p in reverse.get(s,()):
            if p not in d:d[p]=d[s]+1;q.append(p)
    return d


def certified_routes(learner:GeneralLearner,start:State,max_states=120,allowed=None,cache=None):
    paths={start:()};q=deque([start])
    while q and len(paths)<max_states:
        s=q.popleft()
        for a in range(len(learner.actions)):
            outcomes=allowed_outcomes(learner,s,a,allowed,cache)
            if outcomes is None or len(outcomes)!=1:continue
            t=next(iter(outcomes))
            if t in paths:continue
            paths[t]=paths[s]+(a,);q.append(t)
    return paths


@dataclass
class GoalDiagnostics:
    calls:int=0
    calls_with_robust_plan:int=0
    calls_with_certified_plan:int=0
    scored_unknown_experiments:int=0
    selected_experiment_routes:int=0
    rejected_unsafe_actions:int=0
    fallback_calls:int=0
    model_outcome_evaluations:int=0
    goal_value_calculations:int=0
    computed_routes:int=0
    last_decision:str=''
    last_score:float=0.0
    def data(self):return asdict(self)


class GoalValueExplorer:
    """Finite heuristic for experiments with goal-relevant consequences.

    Three priorities: certified route to goal, robust winning action, then
    goal-weighted exploration from certified frontiers. All exploratory
    transitions remain uncertain even when they have high scores.
    """
    def __init__(self, goal:State,allowed_state=None,lookahead_depth=5,
                 route_penalty=.13,exposure_weight=.12,risk_penalty=.5,
                 candidate_limit=240,frontier_limit=120):
        self.goal=tuple(goal);self.allowed_state=allowed_state
        self.lookahead_depth=lookahead_depth;self.route_penalty=route_penalty
        self.exposure_weight=exposure_weight;self.risk_penalty=risk_penalty
        self.candidate_limit=candidate_limit;self.frontier_limit=frontier_limit
        self.stats=GoalDiagnostics()

    def choose(self,learner:GeneralLearner,state:State,visits:Counter,step:int=0):
        learner.schema.validate(state);learner.schema.validate(self.goal)
        self.stats.calls+=1
        if state==self.goal:
            self.stats.last_decision='goal_reached';return None
        if self.allowed_state and (not self.allowed_state(state) or not self.allowed_state(self.goal)):
            self.stats.last_decision='scope_refusal';return None

        cache={}  # One evidence epoch: cache belongs to this action selection only.
        # Prefer an actual certified path. This is safe under the finite model
        # family and does not treat the optimistic reachability graph as fact.
        routes=certified_routes(learner,state,self.frontier_limit,self.allowed_state,cache)
        self.stats.computed_routes+=len(routes)
        if self.goal in routes:
            route=routes[self.goal]
            assert route
            self.stats.calls_with_certified_plan+=1
            self.stats.last_decision='certified_goal_route'
            self.stats.last_score=1e3
            return route[0]

        # Robust nondeterministic policy, if one is provably available.
        winning=robust_goal_depth(learner,self.goal,self.allowed_state,cache)
        self.stats.goal_value_calculations+=len(winning)
        if state in winning:
            choices=[]
            for a in range(len(learner.actions)):
                outcomes=allowed_outcomes(learner,state,a,self.allowed_state,cache)
                self.stats.model_outcome_evaluations+=1
                if outcomes and all(x in winning for x in outcomes):
                    worst=1+max(winning[x] for x in outcomes)
                    if worst<=winning[state]:choices.append((worst,len(outcomes),a))
            if choices:
                self.stats.calls_with_robust_plan+=1
                self.stats.last_decision='robust_goal_action';self.stats.last_score=999
                return min(choices)[-1]

        distances=optimistic_distances(learner,self.goal,self.allowed_state,cache)
        # Stochastic-looking outcome weights are a scoring heuristic; static
        # hypotheses are not independent random draws in a real environment.
        value={self.goal:1.0};states=learner.schema.all_states()
        for h in range(max(1,self.lookahead_depth)):
            new={self.goal:1.0}
            for s in states:
                if s==self.goal or (self.allowed_state and not self.allowed_state(s)):continue
                best=0.0
                for a in range(len(learner.actions)):
                    outcomes=allowed_outcomes(learner,s,a,self.allowed_state,cache)
                    self.stats.model_outcome_evaluations+=1
                    if outcomes is not None:
                        score=sum(value.get(t,0.0) for t in outcomes)/len(outcomes)
                        best=max(best,score)
                new[s]=best
            value=new
        self.stats.goal_value_calculations+=len(states)*self.lookahead_depth
        scored=[];checks=0
        for target,route in routes.items():
            for a in range(len(learner.actions)):
                checks+=1
                if checks>self.candidate_limit:break
                outcomes=allowed_outcomes(learner,target,a,self.allowed_state,cache)
                self.stats.model_outcome_evaluations+=1
                if outcomes is None:
                    self.stats.rejected_unsafe_actions+=1;continue
                if len(outcomes)==1:continue
                self.stats.scored_unknown_experiments+=1
                immediate=sum(t==self.goal for t in outcomes)/len(outcomes)
                mean_future=sum(value.get(t,0.0) for t in outcomes)/len(outcomes)
                avg_distance=sum(1/(1+distances[t]) if t in distances else 0 for t in outcomes)/len(outcomes)
                danger=sum(t not in distances for t in outcomes)/len(outcomes)
                nonrepeated=1/(1+visits[(target,a)])
                # Value prioritizes goal progress over raw number of
                # syntactically distinct hypotheses. No certification occurs.
                score=5*immediate+3*mean_future+avg_distance \
                    +self.exposure_weight*nonrepeated \
                    -self.risk_penalty*danger \
                    -self.route_penalty*len(route)-.06*visits[(target,a)]
                scored.append((score,-len(route),-visits[(target,a)],-a,target,route,a))
            if checks>self.candidate_limit:break
        if scored:
            winner=max(scored);route=winner[-2]
            result=route[0] if route else winner[-1]
            possible=allowed_outcomes(learner,state,result,self.allowed_state,cache)
            if possible is None:raise AssertionError('planned unauthorized action')
            self.stats.selected_experiment_routes+=int(bool(route))
            self.stats.last_score=winner[0]
            self.stats.last_decision='move_to_goal_relevant_experiment' if route else 'goal_relevant_experiment'
            return result

        self.stats.fallback_calls+=1
        actions=[]
        for a in range(len(learner.actions)):
            if allowed_outcomes(learner,state,a,self.allowed_state,cache) is not None:
                actions.append(a)
        if not actions:
            self.stats.last_decision='abstain_no_safe_action';return None
        self.stats.last_decision='fallback_certified_or_min_visit'
        return min(actions,key=lambda a:(visits[(state,a)],a))
