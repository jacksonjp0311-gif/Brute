"""GAPI12 evidence for study-026: brute.certify/12 search='s2' streamed one reading at a time (Certifier12) on the first 4
scale8 eps-0 main cases (method 'exact' vs arm S2) and the first 2 scale8 eps-0.02 main cases (method 'betting' vs arm
RGB6, over the steps that arm completed, at most 40). On every query where both answered exactly (unknown 0) the
supports and certificates must be equal; queries with an UNKNOWN on either side are counted, not compared. New file.
Writes <study>/API_CHECK_026.json (refuses overwrite).
  PYTHONPATH=. python scripts/api_check_026.py results/study-026/main [--block main]"""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_026 import load,write_new,sha
from experiments import worlds_026 as W
from brute.api.certify12 import Certifier12,API
BETTING_STEPS=40


def check_case(c,method):
    arm={'exact':'S2','betting':'RGB6'}[method];a=c['arms'][arm];w=W.world(c['seed'],c['family']);tr=W.trajectory(w,c['seed'],c['eps'])
    steps=len(a['sup']) if method=='exact' else min(a['steps_done'],BETTING_STEPS);cmp=exc=0;diff=[]
    with Certifier12(tr['readings'][0],w.k,0.02,0.01,16,8,method,'s2') as C:
        for i in range(steps):
            r=C.current()
            for b in range(w.k):
                if r['unknown'][b]==0 and a['unk'][i][b]==0:
                    cmp+=1;s=None if r['supports'][b] is None else list(r['supports'][b])
                    if s!=a['sup'][i][b] or r['certificates'][b]!=a['cert'][i][b]:diff.append((i,b))
                else:exc+=1
            C.observe(tr['actions'][i],tr['readings'][i+1])
    return {'case':f"{c['family']}/{c['seed']}/{c['eps']}",'method':method,'steps':steps,'compared':cmp,'excluded':exc,
            'equal':not diff and cmp>0,'first_differences':diff[:5]}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('study');ap.add_argument('--block',default='main');a=ap.parse_args(argv)
    d=Path(a.study);R=load(d/'RESULTS.json');t0=time.time()
    s8=[c for c in R['cases'] if c['family']=='scale8' and c['block']==a.block]
    sel=[(c,'exact') for c in s8 if c['eps']==0][:4]+[(c,'betting') for c in s8 if c['eps']==0.02][:2]
    per=[check_case(c,m) for c,m in sel]
    rep={'schema':'brute.api-check-026.v1','api':API,'results_sha256':sha(d/'RESULTS.json'),'cases':per,'cases_checked':len(per),
         'passed':len(per)==6 and all(p['equal'] for p in per),'wall_informational':round(time.time()-t0,1)}
    write_new(d/'API_CHECK_026.json',rep);print(json.dumps({k:v for k,v in rep.items() if k!='cases'}));return 0 if rep['passed'] else 1


if __name__=='__main__':sys.exit(main())
