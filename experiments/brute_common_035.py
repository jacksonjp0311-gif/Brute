"""Shared helpers for study BRUTE-0320-NOISY-ACTIVE-ID-035 (experiments/BRUTE_PLAN_035.json; deviation #142 fixes every
definition added here). New file.
The study-035 freeze hashes BRUTE_PLAN_035.json and the v0.32.0 sources; the 025-034 freezes are checked unchanged.
Host-side solver interrupt hook (experiments/ only; brute/ stays host-agnostic): TimerHook.arm(fn, s) starts a daemon
threading.Timer that calls fn (the solver's interrupt) after s seconds; disarm cancels and joins it, so no interrupt can
land after the caller clears the solver's interrupt flag."""
import threading
from pathlib import Path
from experiments.brute_common import VerificationError,check,sha,load,dumps,write_new
from experiments.brute_common_009 import Checkpoint,repair_torn_tail
from experiments.brute_common_026 import wilson
from experiments.brute_common_034 import check_freeze as check_freeze_034

ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_035.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_035.json'
STUDY_DIR=ROOT/'results/study-035'

__all__=['VerificationError','check','sha','load','dumps','write_new','ROOT','PLAN','FREEZE','STUDY_DIR','check_freeze',
         'Checkpoint','repair_torn_tail','wilson','TimerHook','HOOK']


class TimerHook:
    def __init__(self):self.armed=0;self.fired=0

    def arm(self,fn,s):
        def fire():self.fired+=1;fn()
        t=threading.Timer(max(0.0,s),fire);t.daemon=True;t.start();self.armed+=1;return t

    def disarm(self,t):t.cancel();t.join()


HOOK=TimerHook()


def check_freeze():
    """The study-025 to 034 source freezes (unchanged files, via the frozen 034 check) and the study-035 source freeze."""
    check_freeze_034()
    check(FREEZE.exists(),FREEZE.name+' missing');frozen=load(FREEZE)
    check(frozen['plan_sha256']==sha(PLAN),'study-035 plan changed after source freeze')
    for rel,digest in frozen['sha256_files'].items():check(sha(ROOT/rel)==digest,f'{FREEZE.name} invalid: '+rel)
    return frozen
