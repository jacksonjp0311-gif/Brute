"""GAPI14 evidence for study-029: brute.certify/14 search='s4' streamed one reading at a time (Certifier14) on the first 4
scale8 eps-0 main cases against arm S4, capped at API_STEPS steps per case (deviations #128 and #130: capped and run in parallel,
4 processes). On every query where both answered exactly (unknown 0) the supports and certificates must be equal;
queries with an UNKNOWN on either side are counted, not compared. New file.
Writes <study>/API_CHECK_029.json (refuses overwrite).
  PYTHONPATH=. python scripts/api_check_029.py results/study-029/main [--block main]"""
import argparse,json,sys,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_029 import load,write_new,sha
from experiments import worlds_026 as W
from brute.api.certify14 import Certifier14,API
API_STEPS=60


def check_case(c):
    a=c['arms']['S4'];w=W.world(c['seed'],c['family']);tr=W.trajectory(w,c['seed'],c['eps'])
    steps=min(a['steps_done'],API_STEPS);cmp=exc=0;diff=[]
    with Certifier14(tr['readings'][0],w.k,0.02,0.01,16,8,'exact','s4') as C:
        for i in range(steps):
            r=C.current()
            for b in range(w.k):
                if r['unknown'][b]==0 and a['unk'][i][b]==0:
                    cmp+=1;s=None if r['supports'][b] is None else list(r['supports'][b])
                    if s!=a['sup'][i][b] or r['certificates'][b]!=a['cert'][i][b]:diff.append((i,b))
                else:exc+=1
            C.observe(tr['actions'][i],tr['readings'][i+1])
    return {'case':f"{c['family']}/{c['seed']}/{c['eps']}",'method':'exact','search':'s4','steps':steps,'compared':cmp,'excluded':exc,
            'equal':not diff and cmp>0,'first_differences':diff[:5]}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('study');ap.add_argument('--block',default='main');a=ap.parse_args(argv)
    d=Path(a.study);R=load(d/'RESULTS.json');t0=time.time()
    sel=[c for c in R['cases'] if c['family']=='scale8' and c['block']==a.block and c['eps']==0][:4]
    with ProcessPoolExecutor(4) as ex:per=list(ex.map(check_case,sel))
    rep={'schema':'brute.api-check-029.v1','api':API,'results_sha256':sha(d/'RESULTS.json'),'api_steps_cap':API_STEPS,'cases':per,
         'cases_checked':len(per),'passed':len(per)==4 and all(p['equal'] for p in per),'wall_informational':round(time.time()-t0,1)}
    write_new(d/'API_CHECK_029.json',rep);print(json.dumps({k:v for k,v in rep.items() if k!='cases'}));return 0 if rep['passed'] else 1


if __name__=='__main__':sys.exit(main())
