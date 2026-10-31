"""Storage for the sealed study-048 outputs (same scheme as scripts/study047_storage.py, which stays frozen; new file).
RESULTS.json / SCIENTIFIC.json of results/study-048/main are git-ignored; the committed form is a deterministic gzip (level 9,
mtime 0, no file name) of the exact sealed bytes, checked against main/SEAL.json on restore.
  python scripts/study048_storage.py pack | restore"""
from __future__ import annotations
import gzip,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import check,sha
from scripts.study047_storage import _gz,_items

STUDY=ROOT/'results/study-048'


def pack(study=STUDY):
    n=0
    for p,digest in _items(study):
        check(sha(p)==digest,str(p)+' does not match its seal');out=p.with_name(p.name+'.gz')
        check(not out.exists(),'refusing overwrite '+str(out));z=_gz(p.read_bytes())
        check(gzip.decompress(z)==p.read_bytes(),'gzip round trip');out.write_bytes(z);n+=1
    return n


def ensure_raw(study=STUDY):
    n=0
    for p,digest in _items(study):
        if not p.exists():
            z=p.with_name(p.name+'.gz');check(z.exists(),'missing '+str(z))
            tmp=p.with_suffix('.json.partial');tmp.write_bytes(gzip.decompress(z.read_bytes()));tmp.replace(p)
        check(sha(p)==digest,f'study-048 {p.relative_to(Path(study))} does not match its seal');n+=1
    check(n==2,'study-048 main seal missing');return True


if __name__=='__main__':
    print({'pack':pack,'restore':ensure_raw}[sys.argv[1]]())
