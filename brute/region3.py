"""Brute v0.17.0 three-action layer (BRUTE_PLAN_019 alphabet3_block; #101 item 6). Thin: the frozen RegionSpace /
RegionK (general in k) and brute.noisyregion.NoisyRegionSpace (k argument) are used unchanged.

  rg3_supports   RG4_3   frozen RegionSpace(n, k=3) on the readings (hard mask clauses, m = 0)
  rgn3_supports  RGN4_3  NoisyRegionSpace(n, m_rule(B), k=3)
  rgnb3_supports RGNB4_3 SeqMarginRegionSpace(n, boundary(B), k=3)
Certificates: rg3_decide = the RGN rule (singleton after burn-in, no SP8 passthrough: no 3-action SP8 exists).
"""
from __future__ import annotations
from brute.region import RegionSpace,PRODUCTION_CONF_BUDGET
from brute.noisyregion import NoisyRegionSpace,rgn_decide
from brute.seqmargin import SeqMarginRegionSpace,trajectory_supports

K3=3
__all__=['K3','rg3_supports','rgn3_supports','rgnb3_supports','rg3_decide']
rg3_decide=rgn_decide


class _RS(RegionSpace):
    m_bound=0


def rg3_supports(initial,actions,observations,n=4,conf_budget=PRODUCTION_CONF_BUDGET):
    return trajectory_supports(_RS(n,k=K3,conf_budget=conf_budget),initial,actions,observations,K3)


def rgn3_supports(initial,actions,observations,m,n=4,conf_budget=PRODUCTION_CONF_BUDGET):
    return trajectory_supports(NoisyRegionSpace(n,m,k=K3,conf_budget=conf_budget),initial,actions,observations,K3)


def rgnb3_supports(initial,actions,observations,bd,n=4,conf_budget=PRODUCTION_CONF_BUDGET):
    return trajectory_supports(SeqMarginRegionSpace(n,bd,k=K3,conf_budget=conf_budget),initial,actions,observations,K3)
