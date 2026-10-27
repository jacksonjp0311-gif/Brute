"""Independent watchdog for study-018: scripts/watchdog_014.py reused UNCHANGED via this thin wrapper (BRUTE_PLAN_018
watchdog_definition: study paths only; same method as scripts/watchdog_015.py).

watchdog_014 writes its file names as literals (RUN_STATE_014.json, HEARTBEAT_014.jsonl, STOP_014.json,
RUN_DONE_014.json, results/study-014). This wrapper reads the frozen watchdog_014 bytes, asserts their sha256 equals the
digest recorded below (= BRUTE_SOURCE_FREEZE_014), replaces only those study path tokens ('_014' -> '_018',
'study-014' -> 'study-018') and executes the result as module watchdog_018. No logic line changes.
    nohup setsid $PY scripts/watchdog_018.py > results/study-018/WATCHDOG_018.log 2>&1 &
"""
from __future__ import annotations
import hashlib,sys,types
from pathlib import Path
SRC=Path(__file__).resolve().parent/'watchdog_014.py'
SHA256_014='972a7fc61f6a2aa51371eba58b60eed23d9794b6938acd6e7b3bce8e91c9cf26'


def _build():
    b=SRC.read_bytes()
    if hashlib.sha256(b).hexdigest()!=SHA256_014:raise SystemExit('watchdog_014.py changed: refusing')
    s=b.decode().replace('_014','_018').replace('study-014','study-018')
    m=types.ModuleType('watchdog_018_impl');m.__file__=__file__;exec(compile(s,str(SRC)+' (paths -> 018)','exec'),m.__dict__);return m


_W=_build()
beat=_W.beat;run=_W.run;read_state=_W.read_state;descendants=_W.descendants;CAP=_W.CAP;STUDY=_W.STUDY

if __name__=='__main__':_W.main()
