"""Storage for the sealed study-023 outputs (same scheme as scripts/study009_storage.py / study014_storage.py / study018_storage.py / study019_storage.py, which stay frozen).

Large raw files (each block's RESULTS.json / SCIENTIFIC.json, incl. repro/reproset) are git-ignored; the committed form is a
deterministic gzip (level 9, mtime 0, no file name) of the exact sealed bytes. Restored bytes are checked against the
block SEAL.json, so the seals bind the raw bytes. Per-case CHECKPOINT*.jsonl files are not committed (they are
reproduced by RESULTS.json; the study SEAL.json records their sha256).

  python scripts/study023_storage.py pack      # write *.json.gz for every sealed raw file (refuses overwrite)
  python scripts/study023_storage.py restore   # restore missing raw files from *.json.gz and check them against the seals
"""
from __future__ import annotations
import gzip,io,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import check,sha,load

STUDY=ROOT/'results/study-023'
BLOCKS=('transfer','repro/reproset')
RAW=(('RESULTS.json','results_sha256'),('SCIENTIFIC.json','scientific_sha256'))


def _gz(data):
    buf=io.BytesIO()
    with gzip.GzipFile(filename='',mode='wb',compresslevel=9,fileobj=buf,mtime=0) as f:f.write(data)
    return buf.getvalue()


def _items(study):
    for b in BLOCKS:
        sd=Path(study)/b
        if (sd/'SEAL.json').exists():
            S=load(sd/'SEAL.json')
            for name,key in RAW:yield sd/name,S[key]


def pack(study=STUDY):
    n=0
    for p,digest in _items(study):
        check(sha(p)==digest,str(p)+' does not match its seal');out=p.with_name(p.name+'.gz')
        check(not out.exists(),'refusing overwrite '+str(out));z=_gz(p.read_bytes())
        check(gzip.decompress(z)==p.read_bytes(),'gzip round trip');out.write_bytes(z);n+=1
    return n


def ensure_raw(study=STUDY):
    for p,digest in _items(study):
        if not p.exists():
            z=p.with_name(p.name+'.gz');check(z.exists(),'missing '+str(z))
            tmp=p.with_suffix('.json.partial');tmp.write_bytes(gzip.decompress(z.read_bytes()));tmp.replace(p)
        check(sha(p)==digest,f'study-023 {p.relative_to(Path(study))} does not match its seal')
    return True


if __name__=='__main__':
    print({'pack':pack,'restore':ensure_raw}[sys.argv[1]]())
