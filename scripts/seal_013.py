"""Study-level seal for BRUTE-0110-SOUND-TRANSFER-013 (plan process_controls): results/study-013/SEAL.json lists the sha256 of
every artifact under the study directory, the block seals (2x2, big78, transfer, repro/2x2, repro/transfer) with their complete
flags, STOP_013 (watchdog) / STOP_013_ORCHESTRATOR / RUN_DONE_013 status and heartbeat gaps > 10 s.
Written once (refuses to overwrite). The ledger seal_013 entry records this file's digest."""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()


def _j(p):return json.loads(p.read_text()) if p.exists() else None


def heartbeat(d):
    p=d/'HEARTBEAT_013.jsonl'
    if not p.exists():return None
    R=[json.loads(l) for l in p.read_text().splitlines() if l.strip()]
    gaps=[r for r in R if r.get('gap_s') is not None and r['gap_s']>10]
    return {'beats':len(R),'first_wall':R[0]['wall'] if R else None,'last_wall':R[-1]['wall'] if R else None,
            'max_gap_s':max((r['gap_s'] for r in R if r.get('gap_s') is not None),default=None),'gaps_over_10s':gaps}


def build(d):
    d=Path(d);files={p.relative_to(d).as_posix():sha(p) for p in sorted(d.rglob('*')) if p.is_file() and p!=d/'SEAL.json'}
    blocks={}
    for b in ('2x2','big78','transfer'):
        for k,sub in ((b,d/b),)+(((f'repro/{b}',d/'repro'/b),) if b!='big78' else ()):
            s=sub/'SEAL.json'
            if s.exists():
                S=json.loads(s.read_text());blocks[k]={'seal_sha256':sha(s),'complete':S.get('complete'),'case_count':S.get('case_count'),
                    'expected_case_count':S.get('expected_case_count'),'missing_job_keys':len(S.get('missing_job_keys',[]) or [])}
            else:blocks[k]={'seal_sha256':None,'complete':False,'note':'no block seal (stream never started or produced nothing)'}
    stop=d/'STOP_013.json'
    return {'study':'BRUTE-0110-SOUND-TRANSFER-013','sealed_at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'blocks':blocks,
            'stop_rule_fired':stop.exists() or (d/'STOP_013_ORCHESTRATOR.json').exists(),'stop_watchdog':_j(stop),
            'stop_orchestrator':_j(d/'STOP_013_ORCHESTRATOR.json'),'run_done':_j(d/'RUN_DONE_013.json'),
            'heartbeat':heartbeat(d),'files_sha256':files}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dir',default=str(ROOT/'results/study-013'));a=ap.parse_args()
    out=Path(a.dir)/'SEAL.json'
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    S=build(a.dir);out.write_text(json.dumps(S,indent=1,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in S.items() if k not in ('files_sha256',)},indent=1)[:3000]);print(len(S['files_sha256']),'files sealed; sha256',sha(out))


if __name__=='__main__':main()
