"""World generators for study BRUTE-080-ALIGN-010: re-exports of the frozen study-008/009 generators only
(BRUTE_PLAN_010 world_generators: no generator change). The new seed ranges live in BRUTE_PLAN_010.json and are
enforced by scripts/check_seeds_010.check_run_seeds."""
from experiments.worlds_009 import world,next_hidden,FAMILIES_2X2,FAMILIES_BREADTH,HiddenWorldK,breadth_world,passive_actions,minimal_states

__all__=['world','next_hidden','FAMILIES_2X2','FAMILIES_BREADTH','HiddenWorldK','breadth_world','passive_actions','minimal_states']
