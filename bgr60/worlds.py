"""Reference-only synthetic worlds (not imported by the learning core).

Known public interface = typed variables, finite value alphabets and opaque
legal actions. Hidden targets, parents and complete local functions withheld.
Research interventions permit choosing a full start state: a strong laboratory
privilege absent in open-world autonomy and explicitly reported as such.
"""
from dataclasses import dataclass
import random
from .generalist import StateSchema

@dataclass(frozen=True)
class TeacherOp:
    target:int
    parents:tuple[int,...]
    table:dict[tuple[int,...],int]
    def apply(self,s):
        key=(s[self.target],)+tuple(s[p] for p in self.parents)
        y=list(s);y[self.target]=self.table[key]
        return tuple(y)
    def data(self):
        return {'target':self.target,'parents':list(self.parents),
                'table':[{'input':list(k),'value':v} for k,v in sorted(self.table.items())]}

@dataclass
class World:
    family:str
    schema:StateSchema
    actions:tuple[str,...]
    operators:tuple[TeacherOp,...]
    seed:int
    def transition(self,a,s):
        self.schema.validate(s)
        return self.operators[a].apply(s)
    def public(self):return self.schema,self.actions
    def oracle(self):return {'family':self.family,'seed':self.seed,'schema':self.schema.data(),
                              'actions':list(self.actions),'operators':[x.data() for x in self.operators]}

def factory(seed:int,family:str):
    rng=random.Random(seed*7727+173)
    if family not in ('logic','switching','navigation','mixed','incompatible'):
        raise ValueError('unknown research family')
    if family=='navigation':domains=((0,1,2,3,4,5),);n_actions=5
    elif family=='mixed':domains=((0,1),(0,1),(0,1),(0,1,2));n_actions=4
    else:domains=((0,1),)*4;n_actions=4
    names=tuple('wire_'+format(rng.getrandbits(40),'010x')+'_'+str(i) for i in range(len(domains)))
    names=tuple(names[i] for i in rng.sample(range(len(names)),len(names)))
    schema=StateSchema(names,domains)
    acts=tuple('operation_'+format(rng.getrandbits(35),'09x')+'_'+str(i) for i in range(n_actions))
    ops=[]
    for ai in range(n_actions):
        if family=='navigation':
            target=0;parents=()
            dest=rng.randrange(6);sources=set(rng.sample(range(6),2));sources.discard(dest)
            def fun(vv,other,dest=dest,sources=sources):return dest if vv in sources else vv
        else:
            target=rng.randrange(len(domains))
            if family=='mixed' and ai==0:target=3
            available=[i for i in range(len(domains)) if i!=target]
            rng.shuffle(available)
            if family=='logic':
                # Two-source parity, gated target flip or Boolean AND.
                mode=('parity','guard','and','copy')[ai%4]
                count=2 if mode in ('parity','guard','and') else 1
                parents=tuple(sorted(available[:count]))
                def fun(vv,other,mode=mode):
                    if mode=='parity':return vv ^ (sum(other)%2)
                    if mode=='guard':return vv ^ int(all(other))
                    if mode=='and':return int(all(other))
                    return other[0]
            elif family=='switching':
                mode=('majority','nand','or','not')[ai%4]
                count=2 if mode in ('majority','nand') else 1 if mode=='or' else 0
                parents=tuple(sorted(available[:count]))
                def fun(vv,other,mode=mode):
                    if mode=='majority':return int(vv+sum(other)>=2)
                    if mode=='nand':return 1-int(all(other))
                    if mode=='or':return vv | other[0]
                    return 1-vv
            elif family=='incompatible':
                # Outside the source logic motifs but still in the broad learner.
                mode=('majority','nand','not','or')[ai%4]
                count=2 if mode in ('majority','nand') else 1 if mode=='or' else 0
                parents=tuple(sorted(available[:count]))
                def fun(vv,other,mode=mode):
                    if mode=='majority':return int(vv+sum(other)>=2)
                    if mode=='nand':return 1-int(all(other))
                    if mode=='not':return 1-vv
                    return vv | other[0]
            elif family=='mixed':
                # One categorical variable and three bits, action families differ.
                if target==3:
                    parents=tuple(available[:1]);base=rng.randrange(3)
                    def fun(vv,other,base=base):return base if other[0]==1 else vv
                else:
                    parents=(3,)
                    threshold=rng.randrange(3)
                    def fun(vv,other,threshold=threshold):return vv ^ int(other[0]==threshold)
        from itertools import product
        table={}
        for x in product(domains[target],*(domains[j] for j in parents)):
            y=fun(x[0],x[1:])
            if y not in domains[target]:raise AssertionError('world rule outside domain')
            table[tuple(x)]=y
        ops.append(TeacherOp(target,parents,table))
    return World(family,schema,acts,tuple(ops),seed)
