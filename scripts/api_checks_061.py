"""GHOST61 and GFID61 inputs for study-061 (BRUTE_PLAN_061; pre-run deviation #196). New file; built from scripts/api_checks_060.py
(frozen), whose equiv(), _run_small() and drive() logic is kept; the frozen api_checks_047 compat() and api_checks_046 closure/scan
are imported unchanged.
  compat:   api_checks_047.compat(), reported;
  ghost:    GHOST61: (1) static: every module in the import closure of brute.api.certify32b has no bad imports and no bad calls
            (api_checks_046.scan); (2) certify32b and the frozen certify14 / 16 / 16d / 16e / 16n / 20b / 20n files keep the sha256 of
            FREEZE_060, and certify16d.A16D_MAX_BOUND is still 20 after importing certify32b (no global patch); (3) a subprocess with
            socket disabled runs one full certify/32b loop (smoke seed 12610303, scale24r4, read_bits 4, bound 24, C 50000, B 2000000,
            K 400) to any final label, 0 socket attempts;
  equiv:    as api_checks_060 (certify/32b == certify/20b at bounds <= 20 on 18 small worlds, one-shot equal, bounds 21..32 accepted,
            bad bounds refused);
  fidelity: (GFID61, only with --study) every DECIDED (ID or IDF) record of block main is driven again in a fresh process through
            certify/32b fed the recorded prefix and its own proposed words with readings from the recorded masks; api result and
            every round minus wall fields must equal the record.
Writes <out> (default results/study-061/API_CHECKS_061.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_061.py [--study results/study-061/main] [--output PATH]"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,dumps
from scripts import api_checks_047 as A47
from scripts import api_checks_046 as A46
from scripts.api_checks_059 import _small,_bits,WALL
from scripts.api_checks_060 import equiv,drive
OUT=ROOT/'results/study-061/API_CHECKS_061.json'
FZ60='experiments/BRUTE_SOURCE_FREEZE_060.json'
FROZEN={f:FZ60 for f in ('brute/api/certify14.py','brute/api/certify16.py','brute/api/certify16d.py','brute/api/certify16e.py',
                         'brute/api/certify16n.py','brute/api/certify20b.py','brute/api/certify20n.py','brute/api/certify32b.py')}
ONLY32=('api','soundness')
NONET='''
import socket,json
hits=[]
def _no(*a,**k):hits.append(1);raise OSError('network disabled by api_checks_061')
socket.socket=_no;socket.create_connection=_no
from brute.api import certify32b as X
from experiments import worlds_060 as W
s=12610303;w=W.world(s,'scale24r4');acts=list(W.actions(s,0.0,w.k));q=w.start
c=X.Certifier32B(W.bits(w.emissions[q]),w.k,24,'a16d',read_bits=4,K=400,max_chunks=None,conflict_cap=50000,budget_conflicts=2000000,
                 wall_guard_case_s=3600.0,hook=None,factory=X.counted16d)
def ob(a):
    global q
    q=w.transitions[q][a];c.observe(a,W.bits(w.emissions[q]))
for a in acts:ob(a)
while True:
    x=c.propose()
    if x is None:break
    for a in x:ob(a)
r=c.result();c.close()
print(json.dumps({'loop':[r['api'],r['label'],r['n_min'],r['used'],r['conflicts'],r['read_bits'],r['family_bound']],'socket_attempts':len(hits)}))
'''


def ghost():
    cv=A46.closure('brute.api.certify32b');static_ok=all(not v['bad_imports'] and not v['bad_calls'] for v in cv.values())
    shas={f:{'now':sha(ROOT/f),'frozen':load(ROOT/fz)['sha256_files'].get(f),'freeze':fz} for f,fz in FROZEN.items()}
    sha_ok=all(v['now']==v['frozen'] for v in shas.values())
    from brute.api import certify32b as _X  # noqa: F401
    from brute.api import certify16d as D;glob_ok=D.A16D_MAX_BOUND==20
    p=subprocess.run([sys.executable,'-c',NONET],cwd=ROOT,capture_output=True,text=True,timeout=1800,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:net=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):net={'error':p.stderr.strip()[-400:]}
    lp=net.get('loop',[None,None])
    net_ok=p.returncode==0 and net.get('socket_attempts')==0 and lp[0]=='brute.certify/32b' and lp[1] in ('ID','IDF','IDU','AMB')
    out={'certify32b_closure':cv,'certify32b_static_ok':static_ok,'frozen_api_sha256':shas,'frozen_api_unchanged':sha_ok,
         'a16d_max_bound_unpatched':glob_ok,'no_network_run':net,'no_network_returncode':p.returncode,'socket_attempts':net.get('socket_attempts'),
         'network_pass':net_ok}
    out['PASS61']=bool(static_ok and net_ok and sha_ok and glob_ok);return out


def fidelity(study,workers=8,block='main'):
    res=load(Path(study)/'RESULTS.json')
    todo=[(f"{c['key']}/{c['seed']}/{g}",c,g,a) for c in res['cases'] if c['block']==block for g,a in c['arms'].items() if a['label'] in ('ID','IDF')]
    rows=[]
    if todo:
        with ProcessPoolExecutor(workers,max_tasks_per_child=1) as ex:rows=list(ex.map(drive,todo))
    return {'study_results_sha256':sha(Path(study)/'RESULTS.json'),'decided_records':len(todo),'exact':sum(r[1] for r in rows),'workers':workers,
            'per_case':{r[0]:{'exact':r[1],'diffs':r[2]} for r in rows},'vacuous':not todo,'PASS':all(r[1] for r in rows)}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));ap.add_argument('--study')
    ap.add_argument('--block',default='main');a=ap.parse_args(argv)
    out={'schema':'brute.api-checks.v58','certify32b_sha256':sha(ROOT/'brute/api/certify32b.py'),'compat':A47.compat(),'ghost':ghost(),'equiv':equiv()}
    if a.study:out['fidelity']=fidelity(a.study,block=a.block)
    out['PASS']=out['compat']['PASS'] and out['ghost']['PASS61'] and out['equiv']['PASS'] and (out['fidelity']['PASS'] if a.study else True)
    write_new(Path(a.output),out);g=out['ghost']
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':g['PASS61'],'static':g['certify32b_static_ok'],'frozen_api_unchanged':g['frozen_api_unchanged'],
                      'unpatched':g['a16d_max_bound_unpatched'],'net':g['no_network_run'],'equiv':out['equiv']['PASS'],
                      'fidelity':{k:v for k,v in out.get('fidelity',{}).items() if k!='per_case'}}))
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
