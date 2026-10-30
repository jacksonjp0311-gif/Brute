"""Shared helpers for study BRUTE-0330-REPEATED-READS-036 (experiments/BRUTE_PLAN_036.json; deviation #144 fixes every
definition added here). New file.
The study-036 freeze hashes BRUTE_PLAN_036.json and the v0.33.0 sources; the 025-035 freezes are checked unchanged via the
frozen 035 check. The host-side solver interrupt hook is experiments.brute_common_035.TimerHook (a fresh instance here)."""
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_035 import TimerHook,check_freeze as check_freeze_035

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_036.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_036.json'
STUDY_DIR=ROOT/'results/study-036'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson','TimerHook','HOOK']

HOOK=TimerHook()


def check_freeze():
    """The study-025 to 035 source freezes (unchanged files, via the frozen 035 check) and the study-036 source freeze."""
    check_freeze_035()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-036 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
