"""World dispatch for study BRUTE-0400-A16-LOWOBS-043 (experiments/BRUTE_PLAN_043.json design.worlds). New file; the generators
are imported unchanged: lowobs12 from the frozen experiments/worlds_040.py (one-bit emissions over codes {0, 1}), scale16 from the
frozen experiments/worlds_039.py (= worlds_026.scale_world, the 042 generator), control_cycle3 from worlds_026. Passive actions and
readings: worlds_026.actions / trajectory (eps 0). Hidden truth never reaches a learner."""
from __future__ import annotations
from experiments import worlds_026 as W26
from experiments import worlds_039 as W39
from experiments import worlds_040 as W40
from experiments.worlds_026 import actions,trajectory,bits,HORIZON,S_BITS

__all__=['SIZES','FAMILIES','world','actions','trajectory','bits','HORIZON','S_BITS']
SIZES={'lowobs12':12,'scale16':16,'control_cycle3':3}
FAMILIES=tuple(SIZES)


def world(seed,family):
    if family=='lowobs12':return W40.world(seed,family)
    if family=='scale16':return W39.world(seed,family)
    if family=='control_cycle3':return W26.world(seed,family)
    raise ValueError(f'unknown family {family!r}')
