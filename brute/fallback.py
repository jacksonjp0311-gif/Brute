"""Brute v0.1.1 learner: F1 open-world fallback forecast and F3 retraction bookkeeping.

Pre-registered in experiments/BRUTE_PLAN_003.json (probability_rule, G8). Kept outside
brute/core/ (amendment A1) so the v0.1.0 API source hash and API_REPLAY stay valid.

Before the declared family is contradicted, every output equals frozen v0.1.0
(brute.core.learner.BruteLearner). After contradiction only the published
probabilities change:
  margin (<=5 states) still supported -> (1-eps)*uniform(margin support) + eps/4   [margin_n5]
  else                                -> (1-eps)*suffix-1 frequency + eps/4         [suffix1]
The plan's last tier, uniform, is never reached here: suffix-1 with alpha 0.7 is always
defined (it is uniform itself on an unseen context). 'uniform' stays a valid source name.
The fallback never certifies: the gate order is unchanged, so the status stays
OUT_OF_FAMILY/FAMILY_CONTRADICTED for the rest of the case.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from bgr89.baselines import SuffixFrequency
from bgr90.symbolic import mask_for_observation
from brute.core.learner import BruteLearner,BruteForecast

FORECAST_SOURCES=('v090','margin_n5','suffix1','uniform')
RETRACTION_REASONS=('falsified_by_observation','scope_withdrawn','unverifiable_masked')
SUFFIX_CONTEXT=1
SUFFIX_ALPHA=0.7


@dataclass(frozen=True)
class FallbackForecast(BruteForecast):
    forecast_source:str='v090'
    ablation_probabilities:Optional[tuple[float,float,float,float]]=None  # margin -> uniform only (no suffix1 tier)


def retraction_reason(certificate:int,observed)->str:
    """G8 / amendment A4: classify a retracted certificate by the bits seen at its own step."""
    mask_for_observation(observed)
    bits=((certificate>>1)&1,certificate&1)
    if any(o is not None and o!=b for o,b in zip(observed,bits)):return 'falsified_by_observation'
    if all(o is not None for o in observed):return 'scope_withdrawn'
    return 'unverifiable_masked'


class FallbackBruteLearner(BruteLearner):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.suffix=SuffixFrequency(SUFFIX_CONTEXT,SUFFIX_ALPHA)
        self.issued_observations={}   # step -> observation at that step, for issued certificates

    def initialize(self,obs):
        super().initialize(obs)
        self.suffix.initialize(obs)

    def _fallback(self,action,margin_support):
        e=self.epsilon
        if self.margin.status=='supported' and margin_support:
            q=tuple((1-e)*(1/len(margin_support) if c in margin_support else 0.)+e/4 for c in range(4))
            return q,'margin_n5',q
        uniform=(.25,)*4
        s=self.suffix.predict(action)
        return tuple((1-e)*p+e/4 for p in s),'suffix1',uniform

    def predict(self,action:int)->FallbackForecast:
        f=super().predict(action)
        fields={k:getattr(f,k) for k in f.__dataclass_fields__}
        if self.support.status!='grammar_contradicted':
            return FallbackForecast(**fields,forecast_source='v090',ablation_probabilities=f.probabilities)
        probs,source,ablation=self._fallback(action,f.margin_support)
        fields['probabilities']=probs
        return FallbackForecast(**fields,forecast_source=source,ablation_probabilities=ablation)

    def observe(self,action:int,obs):
        s=super().observe(action,obs)   # surprise uses the published (fallback) probabilities via self.predict
        self.suffix.observe(action,obs)
        if self.issued and self.issued[-1][0]==self.steps:
            self.issued_observations[self.steps]=tuple(obs)
        return s

    def retractions(self):
        """Certificates withdrawn at contradiction, each with its G8 reason."""
        out=[]
        for step,cert in self.issued[:self.retracted]:
            obs=self.issued_observations.get(step)
            out.append({'step':step,'certificate':cert,'observed':None if obs is None else list(obs),
                        'reason':'unverifiable_masked' if obs is None else retraction_reason(cert,obs)})
        return out

    def retry(self,family_states=None,max_prefixes=None):
        """Replay all evidence under a new bound with the v0.1.1 learner. Attestation never carries over."""
        new=FallbackBruteLearner(family_states or self.family_states,
                                 max(self.margin_states,(family_states or self.family_states)+1),
                                 max_prefixes or self.support.max_prefixes,self.margin.max_prefixes,
                                 self.smoothing,self.epsilon,self.window,self.tau,None)
        ev=self.support.evidence
        new.initialize(ev[0][1])
        for a,obs in ev[1:]:new.observe(a,obs)
        return new

    def diagnostics(self):
        d=super().diagnostics()
        d['retraction_reasons']={r:sum(x['reason']==r for x in self.retractions()) for r in RETRACTION_REASONS}
        return d
