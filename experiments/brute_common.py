"""Shared helpers for study BRUTE-010-ABSTENTION-002 (hashing, freeze, no-overwrite writes)."""
from pathlib import Path
import hashlib,json,os
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_002.json'
FREEZE=ROOT/'experiments/BRUTE_SOURCE_FREEZE_002.json'
STUDY_DIR=ROOT/'results/study-002'


class VerificationError(RuntimeError):
    """Raised instead of assert so checks survive python -O (F11)."""


def check(cond,msg):
    if not cond:raise VerificationError(msg)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def dumps(obj):return (json.dumps(obj,sort_keys=True,indent=2)+'\n').encode()


def write_new(path,obj):
    path=Path(path)
    if path.exists():raise RuntimeError('refusing overwrite '+str(path))
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(dumps(obj));f.flush();os.fsync(f.fileno())


def check_freeze():
    frozen=load(FREEZE)
    for rel,digest in frozen['sha256_files'].items():
        check(sha(ROOT/rel)==digest,'study-002 source freeze invalid: '+rel)
    return frozen
