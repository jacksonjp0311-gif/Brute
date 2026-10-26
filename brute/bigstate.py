"""Brute v0.10.0 big-state wrapper (BRUTE_PLAN_012 J10_definition.big78). New file; frozen learners untouched.

big(cls) returns a subclass of `cls` constructed exactly as `cls` with the frozen symbolic caps (family 5, margin 6;
the frozen SymbolicLearner refuses larger bounds) and then re-bound to the declared <= 8 family: family / margin
RegionSpace replaced by RegionSpace(8) / RegionSpace(9) (same max_prefixes, same conf_budget), family_states /
margin_states 8 / 9 and family string 'deterministic-moore<=8/stationary' (the attestation must name that family).
The recency-window tier keeps its frozen <= 4 bound (disclosed; it is used only after a contradiction).
Must be applied before initialize().
"""
from __future__ import annotations
from brute.region import RegionSpace

BIG_FAMILY=8;BIG_MARGIN=9;CONSTRUCT_CAPS=(5,6)
_cache={}


def big(cls,family_states=BIG_FAMILY,margin_states=BIG_MARGIN):
    k=(cls,family_states,margin_states)
    if k in _cache:return _cache[k]

    class Big(cls):
        def __init__(self,*args,**kwargs):
            args=list(args)
            if len(args)<2:raise ValueError('big(): family_states and margin_states must be positional')
            args[0],args[1]=CONSTRUCT_CAPS
            super().__init__(*args,**kwargs)
            if getattr(self,'initialized',False):raise ValueError('big(): already initialized')
            for name in ('support','margin'):
                old=getattr(self,name);n=family_states if name=='support' else margin_states
                new=RegionSpace(n,old.max_prefixes,conf_budget=self.conf_budget)
                if hasattr(old,'close'):old.close()
                setattr(self,name,new)
            self.family_states=family_states;self.margin_states=margin_states
            self.family=f'deterministic-moore<={family_states}/stationary'

        def diagnostics(self):
            d=super().diagnostics();d['big_state']={'family_states':self.family_states,'margin_states':self.margin_states,
                                                   'window_tier':'frozen <= 4'};return d

    Big.__name__=Big.__qualname__=f'Big{family_states}{cls.__name__}';_cache[k]=Big
    return Big
