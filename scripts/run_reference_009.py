"""G11 driver: run experiments/v070_reference.run over the sealed study-009 RESULTS files (all blocks), with the
mutation test (20 traces, >= 4 P7 planned actions). Writes results/study-009/SECOND_IMPLEMENTATION_009.json."""
from __future__ import annotations
import argparse,hashlib,json,time
from pathlib import Path
from experiments import v070_reference as R
from experiments.brute_common import load
ROOT=Path(__file__).resolve().parents[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--results',nargs='+',required=True);ap.add_argument('--output',required=True)
    ap.add_argument('--workers',type=int,default=2);ap.add_argument('--mutate',type=int,default=20);a=ap.parse_args()
    out=Path(a.output)
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    plan=load(R.PLAN);cases=[];srcs={}
    for f in a.results:
        d=json.loads(Path(f).read_text());cases+=d['cases'];srcs[f]=hashlib.sha256(Path(f).read_bytes()).hexdigest()
    t0=time.time();src=hashlib.sha256((ROOT/'experiments/v070_reference.py').read_bytes()).hexdigest()
    rep=R.run(cases,plan,workers=a.workers,mutate_k=a.mutate,source_sha=src)
    rep['results_files_sha256']=srcs;rep['cases']=len(cases);rep['wall_informational']=round(time.time()-t0,1)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({k:rep[k] for k in ('arm_traces_checked','mismatching_arm_traces','planning','cases')}|{'mutation':rep.get('mutation_test')}))
if __name__=='__main__':main()
