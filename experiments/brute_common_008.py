"""Shared helpers for study BRUTE-060-DRIFTSOUND-008 (paths, plan view, freeze chain, checkpoints)."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_007 import Checkpoint,check_freeze as check_freeze_007

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_008.json'
PLAN007=ROOT/'experiments/BRUTE_PLAN_007.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_008.json'
RELEASE_FREEZE_050=ROOT/'experiments/BRUTE_RELEASE_FREEZE_050.json'
STUDY_DIR=ROOT/'results/study-008'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','PLAN007','FREEZE','STUDY_DIR',
         'check_freeze','plan_view','plan006_keys','Checkpoint']


def plan_view(plan):
    """Plan 008 does not restate the learner configuration of the frozen v0.5.0 learners it subclasses (state caps,
    row budget, smoothing, epsilon, breadth learner bounds); those keys are read from the frozen BRUTE_PLAN_007 and
    every key plan 008 defines overrides them (disclosed in docs/research/BRUTE_DEVIATIONS_008.md). Same reading as
    experiments/v060_reference.plan_view."""
    v=dict(load(PLAN007));v.update(plan);v.update(plan['rule_constants_frozen'])
    check(v['row_budget_enumeration']==160000,'row budget');return v


def plan006_keys(v):
    return {'family_state_cap':v['family_state_cap_2x2'],'margin_state_cap':v['margin_state_cap_2x2'],
            'row_budget_family':v['row_budget_enumeration'],'row_budget_margin':v['row_budget_enumeration'],
            'prediction_smoothing':v['prediction_smoothing'],'open_world_reserve_epsilon':v['open_world_reserve_epsilon'],
            'residual_surprise':{'window_W':v['window_W'],'tau_v030':v['tau_v030']},
            'in_family':v['in_family_2x2'],'actions_per_case':v['actions_per_case_2x2'],'burn_in':v['burn_in'],
            'declared_family':'deterministic-moore<=4/stationary'}


def check_freeze():
    """Study-002..007 source freezes, the v0.5.0 release freeze (G13) and the study-008 source freeze must all hold."""
    check_freeze_007()
    for f in (RELEASE_FREEZE_050,FREEZE):
        frozen=load(f)
        if f==FREEZE:check(frozen['plan_sha256']==sha(PLAN),'study-008 plan changed after source freeze')
        for rel,digest in frozen['sha256_files'].items():
            check(sha(ROOT/rel)==digest,f'{f.name} invalid: '+rel)
    return load(FREEZE)
