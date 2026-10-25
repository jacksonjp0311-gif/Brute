"""Storage for the sealed study-008 outputs (same scheme as scripts/study007_storage.py, which stays frozen).

Large raw files are git-ignored; the committed form is a deterministic gzip (level 9, mtime 0, no file name) of the
exact sealed bytes. Restored bytes are checked against SEAL.json (and the repro SEAL), so seals bind the raw bytes.

  python scripts/study008_storage.py pack      # write *.json.gz for every sealed raw file (refuses overwrite)
  python scripts/study008_storage.py restore   # restore missing raw files from *.json.gz and check them against the seals
"""
from __future__ import annotations
import gzip,io,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import check,sha,load

STUDY=ROOT/'results/study-008'
# (directory relative to STUDY, raw name, seal file, seal key)
FILES=[('.', 'RESULTS.json','SEAL.json','results_sha256'),('.', 'SCIENTIFIC.json','SEAL.json','scientific_sha256'),
       ('repro','RESULTS.json','SEAL.json','results_sha256'),('repro','SCIENTIFIC.json','SEAL.json','scientific_sha256')]


def _gz(data):
    buf=io.BytesIO()
    with gzip.GzipFile(filename='',mode='wb',compresslevel=9,fileobj=buf,mtime=0) as f:f.write(data)
    return buf.getvalue()


def _items(study):
    for d,name,seal,key in FILES:
        sd=Path(study)/d
        if (sd/seal).exists():yield sd/name,load(sd/seal)[key]


def pack(study=STUDY):
    for p,digest in _items(study):
        check(sha(p)==digest,str(p)+' does not match its seal');out=p.with_name(p.name+'.gz')
        check(not out.exists(),'refusing overwrite '+str(out));z=_gz(p.read_bytes())
        check(gzip.decompress(z)==p.read_bytes(),'gzip round trip');out.write_bytes(z)


def ensure_raw(study=STUDY):
    for p,digest in _items(study):
        if not p.exists():
            z=p.with_name(p.name+'.gz');check(z.exists(),'missing '+str(z))
            tmp=p.with_suffix('.json.partial');tmp.write_bytes(gzip.decompress(z.read_bytes()));tmp.replace(p)
        check(sha(p)==digest,f'study-008 {p.name} does not match its seal')
    return True


if __name__=='__main__':
    {'pack':pack,'restore':ensure_raw}[sys.argv[1]]();print('ok')
