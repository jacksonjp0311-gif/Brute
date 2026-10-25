"""Code assertion that every v0.5.0 smoke / dry-run seed is disjoint from every study-007 evaluation seed.

Added 2026-10-25 after the v0.4.0 review (H1) and the 06:17 EDT steering, i.e. AFTER study-007 run_start (06:11:52 EDT).
It is a retroactive check of what the smoke runs used, not a pre-registration (BRUTE_DEVIATIONS_007).
Smoke seed sets are copied verbatim from the smoke drivers (/tmp/w7/smoke_run.py, gx1smoke.py, bsmoke.py; not committed,
transcribed in docs/research/v0.5.0/PROCESS_NOTES.md). Exit code 0 iff disjoint. The 05:25 generator-table glance at
held-out seed 1710001 is reported separately (it is an overlap with the held-out set, but no learner was run).

  PYTHONPATH=. python scripts/check_smoke_seeds_007.py
"""
import json,sys
from experiments.brute_common_007 import load,PLAN
from experiments.brute_study_007 import jobs_for

SMOKE_RUNS={  # name -> (EDT window from /tmp/w7 file mtimes, seeds)
    'gx1smoke (A5 vs A4 2x2 equivalence, /tmp/w7/gx1smoke.log)':('2026-10-25 ~05:32-05:33:32',(901,902,903)),
    'bsmoke (breadth timing)':('2026-10-25 ~05:33',(901,)),
    'smoke_run (calibration + all arms, /tmp/w7/smoke/RESULTS.json)':('2026-10-25 05:36:37-05:38:36',(901,902,903)),
    'second-implementation count + mutation on smoke (COUNT.json, COUNT2.json)':('2026-10-25 ~05:45-05:56:16',(901,902,903)),
    'mkgt fake-sealed dir for scoring-script dry run (/tmp/w7/gt; stress seeds 901,902)':('2026-10-25 ~06:00',(901,902,903)),
}
GLANCE={'05:25 generator-table print, no learner run':(1710001,)}


def evaluation_seeds(plan):
    S={('heldout',b,f,s) for b,f,s,_ in jobs_for(plan)}
    for f,(lo,hi) in plan['calibration_ranges_tau7'].items():S|={('calibration','breadth',f,s) for s in range(lo,hi+1)}
    lo,hi=plan['scaling_block']['seeds'];S|={('scaling','scaling','*',s) for s in range(lo,hi+1)}
    return S


def main():
    plan=load(PLAN);E=evaluation_seeds(plan);nums={s for *_,s in E}
    out={'evaluation_seed_count':len(nums),'evaluation_seed_min':min(nums),'evaluation_seed_max':max(nums),'smoke':{},'glance':{}}
    ok=True
    for k,(t,seeds) in SMOKE_RUNS.items():
        hit=sorted(set(seeds)&nums);out['smoke'][k]={'start_edt':t,'seeds':list(seeds),'overlap':hit};ok&=not hit
    for k,seeds in GLANCE.items():out['glance'][k]={'seeds':list(seeds),'overlap':sorted(set(seeds)&nums)}
    out['smoke_disjoint']=ok
    print(json.dumps(out,indent=2))
    assert ok,'a smoke seed overlaps an evaluation seed'
    return 0


if __name__=='__main__':sys.exit(main())
