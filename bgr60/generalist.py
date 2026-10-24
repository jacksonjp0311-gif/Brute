"""A single typed local-function learner, with evidence-gated predictions.

The UNKNOWN function table is never filled by a pretrained template. All
hypotheses consistent with actual observations are retained, so speculative
transfer hints influence *query selection only*, not certification or safety.
"""
from __future__ import annotations
from dataclasses import dataclass,field
from itertools import combinations,product
from collections import defaultdict
import random,json,hashlib

class Contradiction(Exception): pass
class Underspecified(Exception): pass

@dataclass(frozen=True)
class StateSchema:
    names:tuple[str,...]
    domains:tuple[tuple[int,...],...]
    def __post_init__(self):
        if not self.names or len(self.names)!=len(self.domains) or len(set(self.names))!=len(self.names):raise ValueError('schema names')
        if any(len(v)<2 or len(set(v))!=len(v) for v in self.domains):raise ValueError('finite domains')
    def validate(self,s):
        if len(s)!=len(self.names) or any(x not in dom for x,dom in zip(s,self.domains)):
            raise ValueError('out-of-schema state')
    def all_states(self):return tuple(product(*self.domains))
    def data(self):return {'names':list(self.names),'domains':[list(x) for x in self.domains]}
    def fingerprint(self):return hashlib.sha256(json.dumps(self.data(),sort_keys=True).encode()).hexdigest()

@dataclass
class Hypothesis:
    target:int
    parents:tuple[int,...]
    table:dict[tuple[int,...],int]=field(default_factory=dict)
    def key(self,s):return (s[self.target],)+(tuple(s[p] for p in self.parents))
    def predict_values(self,s,schema):
        key=self.key(s)
        return (self.table[key],) if key in self.table else schema.domains[self.target]
    def predict(self,s):return self.table.get(self.key(s))
    def data(self):return {'target':self.target,'parents':list(self.parents),'table':[{'input':list(k),'value':v} for k,v in sorted(self.table.items())]}

@dataclass(frozen=True)
class Template:
    domain_profile:tuple[int,...]
    values:tuple[int,...]
    def data(self):return {'domain_profile':list(self.domain_profile),'values':list(self.values)}
    @staticmethod
    def read(d):return Template(tuple(d['domain_profile']),tuple(d['values']))

class GeneralLearner:
    def __init__(self,schema:StateSchema,actions:tuple[str,...],max_parents=2,templates=()):
        if not actions or len(set(actions))!=len(actions):raise ValueError('actions invalid')
        if max_parents<0 or max_parents>2:raise ValueError('bounded research grammar')
        self.schema=schema;self.actions=actions;self.max_parents=max_parents
        self._states=schema.all_states()
        if len(self._states)>120:raise ValueError('finite-state research cap')
        self.banks=[]
        for _ in actions:
            bank=[]
            for target in range(len(schema.names)):
                others=[i for i in range(len(schema.names)) if i!=target]
                for k in range(min(max_parents,len(others))+1):
                    for pp in combinations(others,k):bank.append(Hypothesis(target,pp))
            self.banks.append(bank)
        self.templates=tuple(templates)
        self.history=[];self.candidate_checks=0;self.query_count=0
        self.first_identified=None
    def observe(self,action:int,before:tuple[int,...],after:tuple[int,...]):
        self.schema.validate(before);self.schema.validate(after)
        if not 0<=action<len(self.actions):raise ValueError('invalid action')
        prior=self.banks[action];retained=[]
        for hyp in prior:
            self.candidate_checks+=1
            if any(before[j]!=after[j] for j in range(len(before)) if j!=hyp.target):continue
            inp=hyp.key(before)
            if inp in hyp.table and hyp.table[inp]!=after[hyp.target]:continue
            new=Hypothesis(hyp.target,hyp.parents,dict(hyp.table));new.table[inp]=after[hyp.target]
            retained.append(new)
        self.history.append({'action':action,'before':list(before),'after':list(after),
                             'remaining_before':len(prior),'remaining_after':len(retained),
                             'status':'accepted' if retained else 'contradiction'})
        if not retained:raise Contradiction('no consistent local function; prior model remains intact')
        self.banks[action]=retained;self.query_count+=1
        if self.first_identified is None and self.identified():self.first_identified=self.query_count
    def possible_outcomes(self,action,s):
        self.schema.validate(s)
        poss=set()
        for h in self.banks[action]:
            for y in h.predict_values(s,self.schema):
                t=list(s);t[h.target]=y;poss.add(tuple(t))
                if len(poss)>40:return poss
        return poss
    def certified(self,action,s):
        outcomes=self.possible_outcomes(action,s)
        return next(iter(outcomes)) if len(outcomes)==1 else None
    def identified(self):return all(len(self.possible_outcomes(a,s))==1 for a in range(len(self.actions)) for s in self._states)
    def remaining(self):return tuple(len(b) for b in self.banks)
    def _template_match(self,h:Hypothesis):
        if not self.templates:return False
        profile=tuple(len(self.schema.domains[i]) for i in (h.target,*h.parents))
        compatible=[t for t in self.templates if t.domain_profile==profile]
        if not compatible:return False
        options=tuple(product(*(self.schema.domains[i] for i in (h.target,*h.parents))))
        for template in compatible:
            if len(template.values)!=len(options):continue
            if all(h.table.get(k,template.values[idx])==template.values[idx] for idx,k in enumerate(options)):
                return True
        return False
    def choose(self,policy:str,rng:random.Random,step:int):
        if policy=='random':return rng.randrange(len(self.actions)),rng.choice(self._states)
        if policy=='cyclic':return step%len(self.actions),self._states[(step//len(self.actions))%len(self._states)]
        if policy not in ('active','transfer'):raise ValueError('policy')
        candidates=[]
        for ai,bank in enumerate(self.banks):
            for state in self._states:
                outcome_weight=defaultdict(float)
                for h in bank:
                    outcomes=h.predict_values(state,self.schema)
                    for y in outcomes:
                        s=list(state);s[h.target]=y
                        outcome_weight[tuple(s)]+=1/(len(bank)*len(outcomes))
                disagreement=1-sum(v*v for v in outcome_weight.values())
                unknown=sum(h.key(state) not in h.table for h in bank)/max(len(bank),1)
                hint=0.0
                if policy=='transfer' and self.templates:
                    relevant=[h for h in bank if self._template_match(h)]
                    if relevant:
                        hint=max(0.0,len(bank)-len(relevant))/len(bank)*0.2
                        # Focus on experiments that can distinguish prior candidates
                        # from non-prior ones; never restrict the full evidence bank.
                score=disagreement + 0.12*unknown + hint
                candidates.append((score,-ai,state,ai,state))
        _,_,_,a,s=max(candidates)
        return a,s
    def extracted_templates(self):
        if not self.identified():raise Underspecified('exhaustive finite model identification required')
        found={}
        for a in range(len(self.actions)):
            # Pick smallest parent-set candidate with a complete local table
            # equivalent to the globally certified full-state transition.
            full={s:self.certified(a,s) for s in self._states}
            compatible=[]
            for h in self.banks[a]:
                coords=(h.target,*h.parents)
                inputs=tuple(product(*(self.schema.domains[i] for i in coords)))
                inferred={}
                for s,out in full.items():
                    k=h.key(s);value=out[h.target]
                    if k in inferred and inferred[k]!=value:break
                    inferred[k]=value
                else:
                    if len(inferred)==len(inputs):
                        profile=tuple(len(self.schema.domains[i]) for i in coords)
                        compatible.append((len(h.parents),Template(profile,tuple(inferred[key] for key in inputs))))
            if compatible:
                best=min(k for k,v in compatible)
                for k,v in compatible:
                    if k==best:found[(v.domain_profile,v.values)]=v
        return tuple(sorted(found.values(),key=lambda t:(t.domain_profile,t.values)))
    def plan(self,start,goal):
        from collections import deque
        self.schema.validate(start);self.schema.validate(goal)
        if start==goal:return {'status':'solved','actions':[],'shortest_claim':self.identified()}
        visited={start:None};frontier=deque([start])
        while frontier:
            s=frontier.popleft()
            for a in range(len(self.actions)):
                t=self.certified(a,s)
                if t is None or t in visited:continue
                visited[t]=(s,a)
                if t==goal:
                    path=[];x=t
                    while visited[x] is not None:
                        prev,i=visited[x];path.append(i);x=prev
                    return {'status':'solved','actions':path[::-1],'shortest_claim':self.identified()}
                frontier.append(t)
        return {'status':'abstain_uncertified_or_unreachable','actions':None,'shortest_claim':False}
