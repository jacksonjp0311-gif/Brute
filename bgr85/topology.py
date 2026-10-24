"""BGR v0.85: bounded information-topology exploration on a certified graph.

All paths into an experiment are composed only of transitions that every
surviving causal model agrees on. An untested action may have unknown effects;
all such successor states are tracked, never silently certified. A separate
user/operator-provided allowed_state controls possible-outcome safety.

This is a heuristic. Information potential is not a calibrated Bayes posterior
and the policy does not yet solve arbitrary goal-conditioned POMDPs.
"""
from __future__ import annotations
from collections import Counter, deque
from dataclasses import dataclass
from typing import Callable
from bgr60.generalist import GeneralLearner

State=tuple[int,...]

@dataclass
class TopologyDiagnostics:
    certified_states_scanned:int=0
    frontier_candidates:int=0
    hypothetical_successors:int=0
    refused_safety:int=0
    selected_routes:int=0
    fallback_actions:int=0
    visited_states:int=0
    last_value:float=0.0


def certified_graph(learner:GeneralLearner,start:State,allowed_state=None,limit=120):
    """Reachable using only *certified*, scope-permitted edges. Teacher absent."""
    routes={start:()};queue=deque([start]);edges={}
    while queue and len(routes)<=limit:
        s=queue.popleft();edge_map={}
        for a in range(len(learner.actions)):
            t=learner.certified(a,s)
            if t is None:continue
            if allowed_state is not None and not allowed_state(t):continue
            edge_map[a]=t
            if t not in routes and len(routes)<limit:
                routes[t]=routes[s]+(a,);queue.append(t)
        edges[s]=edge_map
    return routes,edges


def back_reachable(edges,source,target):
    if source==target:return True
    q=deque([source]);seen={source}
    while q:
        s=q.popleft()
        for t in edges.get(s,{}).values():
            if t==target:return True
            if t not in seen:seen.add(t);q.append(t)
    return False


class TopologyExplorer:
    """Goal-aware, risk-budgeted explorer with no privileged state resets.

    In the absence of a goal, prioritizes observable coverage of reachable
    frontier experiments. With a goal, gives relevant unknown outcomes added
    priority; the goal must be explicitly supplied by the task, not the oracle.
    """
    def __init__(self,*,allowed_state:Callable[[State],bool]|None=None,
                 risk_penalty:float=0.0,travel_penalty:float=0.20,
                 novelty_bonus:float=1.0,goal:State|None=None,
                 graph_limit:int=120, compute_limit:int=1500):
        self.allowed_state=allowed_state
        self.risk_penalty=risk_penalty
        self.travel_penalty=travel_penalty
        self.novelty_bonus=novelty_bonus
        self.goal=goal
        self.graph_limit=graph_limit
        self.compute_limit=compute_limit
        self.stats=TopologyDiagnostics()

    def choose(self,learner:GeneralLearner,state:State,counts:Counter,step:int=0):
        learner.schema.validate(state)
        if self.goal is not None:learner.schema.validate(self.goal)
        routes,edges=certified_graph(learner,state,self.allowed_state,self.graph_limit)
        n=len(learner.actions);self.stats.certified_states_scanned+=len(routes)
        self.stats.visited_states=len({s for (s,a),num in counts.items() if num>0})
        visited={s for (s,a),num in counts.items() if num>0}
        scored=[];checks=0
        for target,route in routes.items():
            for a in range(n):
                checks+=1
                if checks>self.compute_limit:break
                possibilities=learner.possible_outcomes(a,target)
                if not possibilities:continue
                self.stats.hypothetical_successors+=len(possibilities)
                if self.allowed_state is not None and any(not self.allowed_state(p) for p in possibilities):
                    self.stats.refused_safety+=1
                    continue
                if len(possibilities)==1:continue  # no evidence available
                self.stats.frontier_candidates+=1
                novel=sum(p not in visited for p in possibilities)/len(possibilities)
                spread=(len(possibilities)-1)/max(1,len(learner.schema.all_states())-1)
                exposure=sum((1 / (1+sum(counts.get((p,j),0) for j in range(n)))) for p in possibilities)/len(possibilities)
                repeat=counts[(target,a)]
                # The route itself must be certified. Score is a heuristic
                # approximation of actionable information value per travel cost.
                value=(1.2*novel + 0.55*exposure + 0.35*spread
                       +self.novelty_bonus/(1+repeat)
                       -0.22*repeat-self.travel_penalty*len(route))
                if self.goal is not None:
                    if self.goal in possibilities:value+=0.8
                    # Distances here are Hamming on the public state code;
                    # they are NOT a certified route distance or physical map.
                    old=sum(x!=y for x,y in zip(target,self.goal))
                    avg_new=sum(sum(x!=y for x,y in zip(p,self.goal)) for p in possibilities)/len(possibilities)
                    value+=0.15*(old-avg_new)
                if self.risk_penalty and any(not back_reachable(edges,p,state) for p in possibilities):
                    value-=self.risk_penalty
                scored.append((value,-len(route),-repeat,-a,target,route,a))
            if checks>self.compute_limit:break
        if scored:
            score,*rest=max(scored)
            route=rest[-2];a=rest[-1]
            self.stats.selected_routes+=int(bool(route));self.stats.last_value=score
            result=route[0] if route else a
            outcomes=learner.possible_outcomes(result,state)
            if self.allowed_state is not None and any(not self.allowed_state(s) for s in outcomes):
                raise AssertionError('unsafe selected route')
            return result
        self.stats.fallback_actions+=1
        permitted=[]
        for a in range(n):
            possibles=learner.possible_outcomes(a,state)
            if self.allowed_state is None or all(self.allowed_state(s) for s in possibles):
                permitted.append(a)
        if not permitted:return None
        return min(permitted,key=lambda a:(counts[(state,a)],a))
