"""Shared helpers for study BRUTE-050-REGION-007 (paths, freeze chain, checkpoints)."""
import json,os
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_006 import check_freeze as check_freeze_006

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_007.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_007.json'
STUDY_DIR=ROOT/'results/study-007'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'plan006_keys','Checkpoint']


def check_freeze():
    """Study-002..006 source freezes AND the study-007 source freeze must all hold."""
    check_freeze_006()
    frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-007 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():
        check(sha(ROOT/rel)==digest,'study-007 source freeze invalid: '+rel)
    return frozen


def plan006_keys(plan):
    """The BRUTE_PLAN_006 keys the frozen study-006 learner factory reads, filled from plan 007 (2x2 block)."""
    return {'family_state_cap':plan['family_state_cap_2x2'],'margin_state_cap':plan['margin_state_cap_2x2'],
            'row_budget_family':plan['row_budget_enumeration'],'row_budget_margin':plan['row_budget_enumeration'],
            'prediction_smoothing':plan['prediction_smoothing'],'open_world_reserve_epsilon':plan['open_world_reserve_epsilon'],
            'residual_surprise':{'window_W':plan['window_W'],'tau_v030':plan['tau_v030']},
            'in_family':plan['in_family_2x2'],'actions_per_case':plan['actions_per_case_2x2'],'burn_in':plan['burn_in'],
            'declared_family':'deterministic-moore<=4/stationary'}


class Checkpoint:
    """Append-only JSON-lines checkpoint: one line per finished job key; resumable after an interruption."""
    def __init__(self,path):
        self.path=Path(path);self.done={}
        if self.path.exists():
            lines=self.path.read_text().split('\n')
            for i,line in enumerate(lines):
                if not line.strip():continue
                try:rec=json.loads(line)
                except json.JSONDecodeError:
                    if i==len(lines)-1:continue  # torn final line from an interruption: that job is simply redone
                    raise
                self.done[rec['key']]=rec['case']

    def add(self,key,case):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with open(self.path,'a') as f:
            f.write(json.dumps({'key':key,'case':case},sort_keys=True)+'\n');f.flush();os.fsync(f.fileno())
        self.done[key]=case
