"""brute.cover20/1: a truth-free, host-agnostic coverage-first explorer (BRUTE_PLAN_057 design.cover20_policy). New file.

The host feeds every (action, observation) pair of the walk so far with observe(); propose() returns the next action to take, or
None once STEPS actions have been proposed. Policy (fixed before data): the context of a step is the last H (action, observation)
pairs plus the current observation; propose the action with the fewest prior uses in the current context, ties to the lowest
action index. Counts include the walk observed before the first propose (the passive prefix). The explorer never sees a world,
a truth model or a state; it is deterministic in its inputs. Pure Python: no I/O, threads, subprocess, os or sockets.
Use (then hand the whole trace to certify/16e through its public interface):
    x=Cover20(first_observation,num_actions)
    for a,o in zip(prefix_actions,prefix_observations):x.observe(a,o)
    while (a:=x.propose()) is not None:x.observe(a,world.step(a))
"""
API='brute.cover20/1'
H=1
STEPS=120


def _key(o):
    if isinstance(o,(list,tuple)):return tuple(_key(x) for x in o)
    if isinstance(o,(bool,int,str)) or o is None:return o
    raise TypeError('observation must be nested lists/tuples of int, bool or str')


class Cover20:
    def __init__(self,initial,num_actions,h=H,steps=STEPS):
        if not isinstance(num_actions,int) or isinstance(num_actions,bool) or num_actions<1:raise ValueError('num_actions must be a positive int')
        if not isinstance(h,int) or h<0:raise ValueError('h must be a non-negative int')
        if not isinstance(steps,int) or steps<0:raise ValueError('steps must be a non-negative int')
        self.k=num_actions;self.h=h;self.steps=steps;self.hist=[(None,_key(initial))];self.counts={};self.proposed=[];self._pending=None

    def _ctx(self,i):return tuple(self.hist[max(0,i-self.h):i+1])

    def observe(self,action,observation):
        if not isinstance(action,int) or isinstance(action,bool) or not 0<=action<self.k:raise ValueError('bad action')
        if self._pending is not None and action!=self._pending:raise ValueError('observed action differs from the proposed one')
        c=(self._ctx(len(self.hist)-1),action);self.counts[c]=self.counts.get(c,0)+1
        self.hist.append((action,_key(observation)));self._pending=None

    def propose(self):
        if self._pending is not None:raise ValueError('observe the proposed action first')
        if len(self.proposed)>=self.steps:return None
        c=self._ctx(len(self.hist)-1);a=min(range(self.k),key=lambda x:(self.counts.get((c,x),0),x))
        self.proposed.append(a);self._pending=a;return a

    def result(self):
        return {'api':API,'h':self.h,'steps':self.steps,'proposed':list(self.proposed),'observed_steps':len(self.hist)-1,
                'contexts':len({c for c,_ in self.counts}),'done':len(self.proposed)>=self.steps and self._pending is None}


def cover20(initial,actions,observations,num_actions,world_step,h=H,steps=STEPS):
    """Run the explorer after a given prefix; world_step(a) returns the next observation. Returns the proposed actions and their
    observations."""
    if len(actions)!=len(observations):raise ValueError('need one observation per action')
    x=Cover20(initial,num_actions,h,steps)
    for a,o in zip(actions,observations):x.observe(a,o)
    acts=[];obs=[]
    while True:
        a=x.propose()
        if a is None:break
        o=world_step(a);x.observe(a,o);acts.append(a);obs.append(o)
    return acts,obs
