"""GAPI10 smoke-api evidence (BRUTE_PLAN_024): brute.certify/10 method 'stitched', streamed one reading at a time (Certifier10), on each smoke-api
case of a study-024 smoke RESULTS file; its supports, unknown sets, m and certificates must equal the RGL5 study arm
(noisy['RGL5'] and certifiers['RGL5']) case by case. Writes results/smoke-024/API_CHECK_024.json (refuses to overwrite).
    $PY scripts/api_check_024.py --results DIR/RESULTS.json --output results/smoke-024/API_CHECK_024.json
"""
from __future__ import annotations
import argparse,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load
from experiments.brute_study_014 import sp8_steps
from brute.api.certify10 import Certifier10,API


def check_case(c,eps_bar=0.02,delta=0.01):
    S=sp8_steps(c);acts=[s[1] for s in S];obs=[tuple(s[4]) for s in S];na=c['noisy']['RGL5'];tr=c['certifiers']['RGL5']['trace']
    rows=[]
    with Certifier10(tuple(c['initial_visible']),2,eps_bar,delta,4,c['burn_in'],'stitched') as C:
        for a,o in zip(acts,obs):rows.append(C.current());C.observe(a,o)
    diff=[]
    for i,r in enumerate(rows):
        if r['supports']!=na['support'][i]:diff.append((i+1,'support'))
        if r['unknown']!=na['unknown'][i]:diff.append((i+1,'unknown'))
        if r['m']!=na['m'][i]:diff.append((i+1,'m'))
        if r['certificates']!=tr[i]['certificate']:diff.append((i+1,'certificate'))
    return {'case':f"{c['family']}/{c['seed']}/{c['eps']}",'steps':len(rows),'equal':not diff,'first_differences':diff[:5],
            'certificates':sum(x is not None for r in rows for x in r['certificates'])}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--results',required=True);ap.add_argument('--output',required=True);a=ap.parse_args(argv)
    out=Path(a.output)
    if out.exists():raise SystemExit(f'refusing to overwrite {out}')
    R=load(a.results);cases=[c for c in R['cases'] if c.get('block')=='smoke-api'];t0=time.time()
    per=[check_case(c) for c in cases]
    rep={'schema':'brute.api-check-024.v1','api':API,'gate':'GAPI10 (smoke-api part)','results_file':a.results,
         'results_sha256':hashlib.sha256(Path(a.results).read_bytes()).hexdigest(),'cases':per,'cases_checked':len(per),
         'passed':len(per)==4 and all(p['equal'] for p in per),'wall_informational':round(time.time()-t0,1)}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in rep.items() if k!='cases'}));return 0 if rep['passed'] else 1


if __name__=='__main__':sys.exit(main())
