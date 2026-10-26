"""Study-level seal for BRUTE-070-SYNCPLAN-009 (plan process_controls (9)): results/study-009/SEAL.json lists the sha256 of
every artifact under the study directory, the block seals with their complete flags, and STOP_009 / RUN_DONE_009 status.
Written once (refuses to overwrite). The ledger seal_009 entry records this file's digest."""
from __future__ import annotations
import argparse,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def build(d):
    d=Path(d);files={p.relative_to(d).as_posix():sha(p) for p in sorted(d.rglob('*'))
                     if p.is_file() and p!=d/'SEAL.json'}
    blocks={}
    for b in ('2x2','breadth','planning'):
        for k,sub in ((b,d/b),(f'repro/{b}',d/'repro'/b)):
            s=sub/'SEAL.json'
            if s.exists():
                S=json.loads(s.read_text());blocks[k]={'seal_sha256':sha(s),'complete':S.get('complete'),
                    'case_count':S.get('case_count'),'expected_case_count':S.get('expected_case_count'),
                    'missing_job_keys':len(S.get('missing_job_keys',[]) or [])}
            else:blocks[k]={'seal_sha256':None,'complete':False,'note':'no block seal (stream never started or produced nothing)'}
    stop=d/'STOP_009.json';done=d/'RUN_DONE_009.json'
    return {'study':'BRUTE-070-SYNCPLAN-009','sealed_at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'blocks':blocks,
            'stop_rule_fired':stop.exists(),'stop':json.loads(stop.read_text()) if stop.exists() else None,
            'run_done':json.loads(done.read_text()) if done.exists() else None,'files_sha256':files}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dir',default=str(ROOT/'results/study-009'));a=ap.parse_args()
    out=Path(a.dir)/'SEAL.json'
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    S=build(a.dir);out.write_text(json.dumps(S,indent=1,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in S.items() if k!='files_sha256'},indent=1));print(len(S['files_sha256']),'files sealed; sha256',sha(out))


if __name__=='__main__':main()
