"""Held-out run orchestrator for study-015, revision R1 (deviation #72, RATE_MATH_015).

Run with:  nohup setsid $PY scripts/run_study_015_R1.py > results/study-015/RUN_015.log 2>&1 &

scripts/run_study_015.py is ledger-hashed (process_scripts_015, re-receipted as process_scripts_015b: deviation #73)
and is not edited. This file loads it, refuses unless its sha256 equals the re-receipted digest, and changes ONE value:
the g11 reference stream runs with 4 workers instead of 2 (budget unchanged at 2400 s). Every other stream, the cap,
the dry-run hooks, the stops and the state files are the base module's. Worker ceiling: after transfer,
2 (gti) + 2 (repro) + 4 (g11) = 8 = MAX_WORKERS.
"""
from __future__ import annotations
import hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
BASE=ROOT/'scripts/run_study_015.py'
BASE_SHA256='9fa73b8ce591b18fc13ba3f9588f52fed465c3d6461592299b4eb26db000c469'
G11_WORKERS=4
if hashlib.sha256(BASE.read_bytes()).hexdigest()!=BASE_SHA256:
    raise SystemExit('run_study_015.py bytes differ from the process_scripts_015b receipt; refusing to run')
from scripts import run_study_015 as _B

_base_tasks=_B.tasks


def tasks():
    T=_base_tasks()
    for t in T:
        if t['name']=='g11':
            g,_o,_f=_B.g11(G11_WORKERS);t['cmd']=g;t['workers']=G11_WORKERS
    assert max(t['workers'] for t in T if t['name']!='transfer')<=_B.MAX_WORKERS
    return T


CAP=_B.CAP;MAX_WORKERS=_B.MAX_WORKERS


def main():
    _B.tasks=tasks  # patched only when this file runs as the orchestrator
    return _B.main()

if __name__=='__main__':sys.exit(main())
