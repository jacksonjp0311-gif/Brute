"""Append one receipt to results/RESEARCH_LEDGER.jsonl (local unsigned SHA chain). Append-only."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import sha
LEDGER=ROOT/'results/RESEARCH_LEDGER.jsonl'


def receipt_hash(obj):
    return hashlib.sha256(json.dumps({k:v for k,v in obj.items() if k!='receipt_sha256'},sort_keys=True,separators=(',',':')).encode()).hexdigest()


def append(event,source,note=None,commit=None):
    lines=LEDGER.read_text().splitlines();previous=json.loads(lines[-1])['receipt_sha256'] if lines else '0'*64
    r={'audit_scope':'local unsigned SHA chain (not independent signatures)','event':event,'previous':previous,
       'source':source,'source_sha256':sha(ROOT/source)}
    if note:r['note']=note
    if commit:r['commit']=commit
    r['receipt_sha256']=receipt_hash(r)
    with LEDGER.open('a') as f:f.write(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')
    return r


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('event');ap.add_argument('source');ap.add_argument('--note');ap.add_argument('--commit')
    a=ap.parse_args();print(json.dumps(append(a.event,a.source,a.note,a.commit)))
