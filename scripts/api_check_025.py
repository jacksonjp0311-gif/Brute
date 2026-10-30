"""GAPI11 smoke-api evidence (BRUTE_PLAN_025): brute.certify/11 method 'betting', streamed one reading at a time (Certifier11), on each smoke-api
case of a study-025 smoke RESULTS file; its supports, unknown sets, m and certificates must equal the RGB6 study arm
(noisy['RGB6'] and certifiers['RGB6']) case by case. Writes results/smoke-025/API_CHECK_025.json (refuses to overwrite).
    $PY scripts/api_check_025.py --results DIR/RESULTS.json --output results/smoke-025/API_CHECK_025.json
"""
from __future__ import annotations
import argparse,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load
from experiments.brute_study_014 import sp8_steps
from brute.api.certify11 import Certifier11,API


def check_case(c,eps_bar=0.02,delta=0.01):
    S=sp8_steps(c);acts=[s[1] for s in S];obs=[tuple(s[4]) for s in S];na=c['noisy']['RGB6'];tr=c['certifiers']['RGB6']['trace']
    rows=[]
    with Certifier11(tuple(c['initial_visible']),2,eps_bar,delta,4,c['burn_in'],'betting') as C:
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
    R=load(a.results);cases=[c for c in R['cases'] if c.get('block')=='smoke-api'] or [c for c in R['cases'] if c.get('block')=='main' and c['eps']==0.02][:4]   # A2: lean = first 4 eps-0.02 main cases;t0=time.time()
    per=[check_case(c) for c in cases]
    rep={'schema':'brute.api-check-025.v1','api':API,'gate':'GS_a11 / GAPI11 (A2: first 4 eps-0.02 lean main cases, or smoke-api)','results_file':a.results,
         'results_sha256':hashlib.sha256(Path(a.results).read_bytes()).hexdigest(),'cases':per,'cases_checked':len(per),
         'passed':len(per)==4 and all(p['equal'] for p in per),'wall_informational':round(time.time()-t0,1)}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in rep.items() if k!='cases'}));return 0 if rep['passed'] else 1


if __name__=='__main__':sys.exit(main())
