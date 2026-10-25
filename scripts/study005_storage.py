"""Storage for the sealed study-005 traces (deviation D1 in docs/research/BRUTE_DEVIATIONS_005.md).

RESULTS.json and SCIENTIFIC.json exceed, above GitHub's 100 MB per-file limit. The committed form is a
deterministic gzip (level 9, mtime 0, no file name) of the exact sealed bytes; the raw files are git-ignored and are
restored on demand. Restored bytes are checked against SEAL.json, so the seal is unchanged and still binds the raw bytes.

  python scripts/study005_storage.py pack      # write *.json.gz from the raw sealed files (refuses overwrite)
  python scripts/study005_storage.py restore   # write missing raw files from *.json.gz and check them against SEAL.json
"""
from __future__ import annotations
import gzip,io,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import check,sha,load

STUDY=ROOT/'results/study-005'
NAMES={'RESULTS.json':'results_sha256','SCIENTIFIC.json':'scientific_sha256'}


def _gz(data):
    buf=io.BytesIO()
    with gzip.GzipFile(filename='',mode='wb',compresslevel=9,fileobj=buf,mtime=0) as f:f.write(data)
    return buf.getvalue()


def pack(study=STUDY):
    seal=load(study/'SEAL.json')
    for name,key in NAMES.items():
        raw=(study/name).read_bytes();check(__import__('hashlib').sha256(raw).hexdigest()==seal[key],name+' does not match SEAL')
        out=study/(name+'.gz');check(not out.exists(),'refusing overwrite '+str(out))
        z=_gz(raw);check(gzip.decompress(z)==raw,'gzip round trip');out.write_bytes(z)


def ensure_raw(study=STUDY):
    """Restore any missing raw file from its .gz; always check raw bytes against SEAL.json."""
    study=Path(study);seal=load(study/'SEAL.json')
    for name,key in NAMES.items():
        p=study/name
        if not p.exists():
            z=study/(name+'.gz');check(z.exists(),'missing '+str(z))
            tmp=p.with_suffix('.json.partial');tmp.write_bytes(gzip.decompress(z.read_bytes()));tmp.replace(p)
        check(sha(p)==seal[key],f'study-005 {name} does not match SEAL')
        z=study/(name+'.gz')
        if z.exists():check(gzip.decompress(z.read_bytes())==p.read_bytes(),f'study-005 {name}.gz does not hold the sealed bytes')
    return True


if __name__=='__main__':
    {'pack':pack,'restore':ensure_raw}[sys.argv[1]]();print('ok')
