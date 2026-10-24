"""Symbol <-> code mapping. v0.1.0 ships one alphabet: 2 actions, 2 binary channels.

Code c in 0..3 encodes channel x as bit 1 and channel y as bit 0: c = 2*x + y.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class ChannelSpec:
    name:str
    values:tuple[int,...]=(0,1)


@dataclass(frozen=True)
class Alphabet:
    actions:tuple[str,...]
    channels:tuple[ChannelSpec,...]

    def action_code(self,symbol):
        if symbol not in self.actions:raise ValueError(f'unknown action symbol {symbol!r}')
        return self.actions.index(symbol)

    def observation_tuple(self,obs:dict):
        names=[c.name for c in self.channels]
        if not isinstance(obs,dict) or set(obs)!=set(names):raise ValueError('observation must name exactly the channels '+','.join(names))
        out=[]
        for c in self.channels:
            v=obs[c.name]
            if v is not None and (isinstance(v,bool) or v not in c.values):raise ValueError(f'channel {c.name} value must be 0, 1 or null')
            out.append(v)
        return tuple(out)

    def decode(self,code:int)->dict:
        if code not in range(4):raise ValueError('code must be 0..3')
        return {self.channels[0].name:(code>>1)&1,self.channels[1].name:code&1}


DEFAULT_ALPHABET=Alphabet(('a','b'),(ChannelSpec('x'),ChannelSpec('y')))
