"""Frozen 7-family, 3-mask controlled study. No overwrites, SHA-256 evidence."""
from pathlib import Path
import argparse,hashlib,json,os,time
from bgr90.evaluation import run_case,aggregate
ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()
def no_time(obj):
    if isinstance(obj,dict):return {k:no_time(v) for k,v in obj.items() if k not in ('elapsed_informational','time_informational_seconds')}
    if isinstance(obj,list):return [no_time(v) for v in obj]
    return obj


def write(path,obj):
    if path.exists():raise RuntimeError('output already exists: '+str(path))
    with path.open('xb') as f:f.write((json.dumps(obj,sort_keys=True,indent=2)+'\n').encode());f.flush();os.fsync(f.fileno())


def run(output):
    output=Path(output).resolve()
    if output.exists():raise RuntimeError('refusing overwrite '+str(output))
    plan=json.loads((ROOT/'experiments/PLAN.json').read_text())
    frozen=json.loads((ROOT/'experiments/SOURCE_FREEZE.json').read_text())
    for rel,hashval in frozen['sha256_files'].items():
        if sha(ROOT/rel)!=hashval:raise RuntimeError('source freeze invalid: '+rel)
    output.mkdir(parents=True)
    cases=[];started=time.perf_counter()
    for family,(low,high) in plan['heldout_ranges'].items():
        for seed in range(low,high+1):
            for rate in plan['mask_rates']:
                cases.append(run_case(seed,family,rate,plan['actions_per_case'],plan['burn_in'],plan['symbolic_partial_row_cap']))
        print('frozen study completed',family,len(cases),'cases',flush=True)
    result={'schema':'bgr90.study.v1','plan':plan,'cases':cases,'summary':aggregate(cases),
            'total_elapsed_informational':time.perf_counter()-started}
    stripped=no_time(result)
    write(output/'RESULTS.json',result)
    write(output/'SCIENTIFIC.json',stripped)
    write(output/'SEAL.json',{'study':plan['study'],
        'results_sha256':sha(output/'RESULTS.json'),
        'scientific_sha256':sha(output/'SCIENTIFIC.json'),
        'plan_sha256':sha(ROOT/'experiments/PLAN.json'),
        'freeze_sha256':sha(ROOT/'experiments/SOURCE_FREEZE.json'),
        'case_count':len(cases)})
    print(json.dumps(result['summary'],indent=2))
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(ROOT/'results/study-001'))
    run(ap.parse_args().output)
