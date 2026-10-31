"""GHOST48 and GFID48 inputs for study-048 (BRUTE_PLAN_048; pre-run deviation #169). New file; the frozen
scripts/api_checks_047.py compat(), ghost() and drive() are imported unchanged.
  compat:   api_checks_047.compat() (certify/16 and certify/14 test modules, 046 compat sample byte for byte), reported;
  ghost:    api_checks_047.ghost() (AST closure of brute.api.certify16d, flagged imports or calls, and the socket-disabled
            subprocess run); GHOST48 adds: the closure equals the closure recorded in results/study-047/API_CHECKS_047.json and
            brute/api/certify16d.py has the sha256 frozen in experiments/BRUTE_SOURCE_FREEZE_047.json (no new import, no edit since
            the 047 freeze), and 0 socket attempts;
  fidelity: (GFID48, only with --study) every API16D record of the main block (scale16, control and scale20: 18 + N20 records)
            driven again over its own recorded trace by api_checks_047.drive (fresh process per case, 8 workers, the record's cap
            and budget) and compared byte for byte (api result and every round's fields).
Writes <out> (default results/study-048/API_CHECKS_048.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_048.py [--study results/study-048/main] [--output PATH]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
from scripts import api_checks_047 as A47
OUT=ROOT/'results/study-048/API_CHECKS_048.json'
CLOSURE_047=ROOT/'results/study-047/API_CHECKS_047.json';FREEZE_047=ROOT/'experiments/BRUTE_SOURCE_FREEZE_047.json'


def ghost():
    g=A47.ghost();old=load(CLOSURE_047)['ghost']['closure'];fz=load(FREEZE_047)['sha256_files'].get('brute/api/certify16d.py')
    g['closure_047']=old;g['closure_unchanged']=g['closure']==old;g['certify16d_sha_frozen_047']=fz
    g['certify16d_unchanged']=sha(ROOT/'brute/api/certify16d.py')==fz
    g['socket_attempts']=g['no_network_run'].get('socket_attempts')
    g['PASS48']=bool(g['PASS'] and g['closure_unchanged'] and g['certify16d_unchanged'] and g['socket_attempts']==0);return g


def fidelity(study,expected,workers=8):
    res=load(Path(study)/'RESULTS.json')
    todo=[(f"{c['key']}/{c['seed']}",c,c['arms']['API16D']) for c in res['cases'] if c['block']=='main' and 'API16D' in c['arms']]
    with ProcessPoolExecutor(workers,max_tasks_per_child=1) as ex:rows=list(ex.map(A47.drive,todo))
    return {'study_results_sha256':sha(Path(study)/'RESULTS.json'),'cases':len(rows),'expected':expected,'exact':sum(r[1] for r in rows),
            'per_key':{k:sum(1 for r in rows if r[0].startswith(k+'/')) for k in ('scale16','control','scale20')},
            'per_case':{r[0]:{'exact':r[1],'diffs':r[2]} for r in rows},'PASS':len(rows)==expected and all(r[1] for r in rows)}


def main(argv=None):
    from experiments.brute_study_048 import N20
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));ap.add_argument('--study');ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--expected',type=int,default=18+N20);a=ap.parse_args(argv)
    out={'schema':'brute.api-checks.v45','certify16d_sha256':sha(ROOT/'brute/api/certify16d.py'),'compat':A47.compat(),'ghost':ghost()}
    if a.study:out['fidelity']=fidelity(a.study,a.expected,a.workers)
    out['PASS']=out['compat']['PASS'] and out['ghost']['PASS48'] and (out['fidelity']['PASS'] if a.study else True);write_new(Path(a.output),out)
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':out['ghost']['PASS48'],'closure_unchanged':out['ghost']['closure_unchanged'],
                      'certify16d_unchanged':out['ghost']['certify16d_unchanged'],'socket':out['ghost']['socket_attempts'],
                      'fidelity':{k:v for k,v in out.get('fidelity',{}).items() if k!='per_case'}}));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
