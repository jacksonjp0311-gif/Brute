"""World dispatch for study BRUTE-0440-CERTIFY16D-SCALE20-047 (experiments/BRUTE_PLAN_047.json design.scale20). New file.
scale16 and control_cycle3 come from the frozen experiments/worlds_043.world, unchanged. scale20 is the frozen
worlds_026.scale_world generator called with n = 20 and family 'scale20' (20-state reachable minimal strongly connected machines,
3 actions, 2 output bits; same draw rule as scale16 with n = 20). The frozen generator files are not edited. Passive actions and
readings: worlds_026.actions / trajectory (eps 0). Hidden truth never reaches a learner."""
from __future__ import annotations
from experiments import worlds_026 as W26
from experiments import worlds_043 as W43
from experiments.worlds_026 import actions,trajectory,bits,HORIZON,S_BITS

__all__=['SIZES','FAMILIES','world','actions','trajectory','bits','HORIZON','S_BITS']
SIZES={**W43.SIZES,'scale20':20}
FAMILIES=tuple(SIZES)


def world(seed,family):
    if family=='scale20':return W26.scale_world(seed,20,'scale20')
    if family in W43.SIZES:return W43.world(seed,family)
    raise ValueError(f'unknown family {family!r}')
