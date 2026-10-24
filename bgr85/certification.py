"""Finite reachable-competence certificate, requiring NO privileged world oracle.

The theorem: if from initial state s0, the subgraph of unanimously certified
transitions is closed under every permitted action (no uncertain boundary
edges), then this subgraph equals the reachable state set for *every* world
still consistent with learner's observations. All its action outcomes are
therefore known relative to the supplied model family.

If the closure is open, no correctness or learnability conclusion follows.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
import hashlib,json
from bgr60.generalist import GeneralLearner

State=tuple[int,...]

@dataclass(frozen=True)
class ReachableCertificate:
    initial:State
    states:tuple[State,...]
    edges:tuple[tuple[State,int,State],...]
    open_frontier:tuple[tuple[State,int],...]
    complete:bool
    sha256:str

    def data(self):
        return {'initial':list(self.initial), 'states':[list(s) for s in self.states],
                'edges':[[list(a),i,list(b)] for a,i,b in self.edges],
                'open_frontier':[[list(s),i] for s,i in self.open_frontier],
                'complete':self.complete,'sha256':self.sha256}


def certify_reachable(learner:GeneralLearner,initial:State):
    learner.schema.validate(initial)
    seen={initial};q=deque([initial]);edges=[];frontier=[]
    while q:
        s=q.popleft()
        for a in range(len(learner.actions)):
            out=learner.certified(a,s)
            if out is None:
                frontier.append((s,a));continue
            edges.append((s,a,out))
            if out not in seen:
                seen.add(out);q.append(out)
    sorted_states=tuple(sorted(seen))
    sorted_edges=tuple(sorted(edges))
    sorted_frontier=tuple(sorted(frontier))
    payload={'initial':initial,'states':sorted_states,'edges':sorted_edges,'open_frontier':sorted_frontier,
             'complete':not sorted_frontier}
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return ReachableCertificate(initial,sorted_states,sorted_edges,sorted_frontier,not sorted_frontier,digest)


def verify_certificate(learner:GeneralLearner,cert:ReachableCertificate):
    recomputed=certify_reachable(learner,cert.initial)
    if recomputed!=cert:return False
    if cert.complete:
        all_edges=len(cert.states)*len(learner.actions)
        if len(cert.edges)!=all_edges:return False
        if any(target not in cert.states for src,a,target in cert.edges):return False
    return True


def certified_goal_plan(learner:GeneralLearner,initial:State,goal:State):
    learner.schema.validate(goal)
    certificate=certify_reachable(learner,initial)
    if goal not in certificate.states:
        return {'status':'provably_unreachable_in_model_family' if certificate.complete else 'abstain_unknown_reachability',
                'plan':None,'reachable_certificate':certificate.complete}
    predecessor={initial:None};q=deque([initial])
    edges_by={}
    for u,a,v in certificate.edges:edges_by.setdefault(u,[]).append((a,v))
    while q:
        u=q.popleft()
        if u==goal:
            path=[];v=goal
            while predecessor[v] is not None:
                prior,a=predecessor[v];path.append(a);v=prior
            return {'status':'solved','plan':path[::-1],
                    'shortest_claim':certificate.complete, 'reachable_certificate':certificate.complete}
        for a,v in edges_by.get(u,[]):
            if v not in predecessor:predecessor[v]=(u,a);q.append(v)
    raise AssertionError('certified graph consistency broken')
