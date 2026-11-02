"""GHOST57 and GFID57 inputs for study-057 (BRUTE_PLAN_057; pre-run deviation #188). New file; built from scripts/api_checks_056.py
(frozen), whose replay logic is followed, with the frozen api_checks_050 ROUND_FIELDS and api_checks_047 / 046 helpers imported unchanged.
  compat:   api_checks_047.compat() (certify/16 and certify/14 test modules, 046 compat sample byte for byte), reported;
  ghost:    GHOST57: (1) static: every module in the import closure of brute.api.cover20 has no bad imports and no bad calls
            (api_checks_046.scan: no I/O, threads, subprocess, os or socket); (2) brute.api.certify14 / 16 / 16d / 16e / 16n / 16s / 20t /
            20c / 20l files have the sha256 frozen in their freezes, and the closures of those modules equal the ones recorded in
            results/study-056/API_CHECKS_056.json; (3) a subprocess with socket disabled runs one full cover20 + certify/16e loop (smoke
            seed 12430003, scale20, bound 20, C 50000, B 2000000, conflict-only stop) to any final label, 0 socket attempts;
  fidelity: (GFID57, only with --study) every COV_X record of block main is driven again in a fresh process per record on 8 workers:
            cover20 fed the prefix and the recorded extension observations must re-propose the recorded extension exactly; then
            certify/16e is fed prefix + extension and driven over its own recorded words with the record's C, B, max_chunks and stop rule
            (hook None, the 900 s case guard). The api result (canonical JSON) and every round's ROUND_FIELDS must equal the record byte
            for byte. Gated: the 12 COV_X records (plan GFID57: other arms not replayed).
Writes <out> (default results/study-057/API_CHECKS_057.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_057.py [--study results/study-057/main] [--output PATH] [--expected 12]"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,dumps
from scripts import api_checks_047 as A47
from scripts import api_checks_046 as A46
from scripts.api_checks_050 import ROUND_FIELDS
OUT=ROOT/'results/study-057/API_CHECKS_057.json'
CLOSURE_056=ROOT/'results/study-056/API_CHECKS_056.json'
FROZEN={'brute/api/certify14.py':'experiments/BRUTE_SOURCE_FREEZE_047.json','brute/api/certify16.py':'experiments/BRUTE_SOURCE_FREEZE_047.json',
        'brute/api/certify16d.py':'experiments/BRUTE_SOURCE_FREEZE_047.json','brute/api/certify16e.py':'experiments/BRUTE_SOURCE_FREEZE_049.json',
        'brute/api/certify16n.py':'experiments/BRUTE_SOURCE_FREEZE_050.json','brute/api/certify16s.py':'experiments/BRUTE_SOURCE_FREEZE_051.json',
        'brute/api/certify20t.py':'experiments/BRUTE_SOURCE_FREEZE_054.json','brute/api/certify20c.py':'experiments/BRUTE_SOURCE_FREEZE_055.json',
        'brute/api/certify20l.py':'experiments/BRUTE_SOURCE_FREEZE_056.json'}
MODS=('brute.api.certify14','brute.api.certify16','brute.api.certify16d','brute.api.certify16e','brute.api.certify16n','brute.api.certify16s','brute.api.certify20t','brute.api.certify20c','brute.api.certify20l')
NONET='''
import socket,json
hits=[]
def _no(*a,**k):hits.append(1);raise OSError('network disabled by api_checks_057')
socket.socket=_no;socket.create_connection=_no
from brute.api import certify16e as E
from brute.api import cover20 as CV
from experiments import worlds_050 as W
from experiments.brute_study_033 import StepWorld,passive
s=12430003;w=W.world(s,'scale20');sw=StepWorld(w);_,acts,rd=passive(sw,s)
ext,eo=CV.cover20(rd[0],acts,rd[1:],w.k,sw.step)
c=E.Certifier16E(rd[0],w.k,20,'a16d',max_chunks=None,conflict_cap=50000,budget_conflicts=2000000,wall_guard_case_s=900.0,hook=None,factory=E.counted16d)
for a,o in zip(list(acts)+list(ext),list(rd[1:])+list(eo)):c.observe(a,o)
while True:
    x=c.propose()
    if x is None:break
    for a in x:c.observe(a,sw.step(a))
r=c.result();c.close()
print(json.dumps({'loop':[r['api'],r['label'],r['n_min'],r['used'],r['conflicts'],len(ext)],'socket_attempts':len(hits)}))
'''
G_ARMS=('COV_X',);KEYS=('scale20v',)


def ghost():
    C={m:A46.closure(m) for m in MODS};prev=load(CLOSURE_056)['ghost']['closures']
    cv=A46.closure('brute.api.cover20');static_ok=all(not v['bad_imports'] and not v['bad_calls'] for v in cv.values())
    shas={f:{'now':sha(ROOT/f),'frozen':load(ROOT/fz)['sha256_files'].get(f),'freeze':fz} for f,fz in FROZEN.items()}
    sha_ok=all(v['now']==v['frozen'] for v in shas.values())
    p=subprocess.run([sys.executable,'-c',NONET],cwd=ROOT,capture_output=True,text=True,timeout=1200,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:net=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):net={'error':p.stderr.strip()[-400:]}
    lp=net.get('loop',[None,None])
    net_ok=p.returncode==0 and net.get('socket_attempts')==0 and lp[0]=='brute.certify/16e' and lp[1] in ('ID','IDF','IDU','AMB')
    cl_ok={m:sorted(C[m])==prev.get(m) for m in MODS}
    out={'cover20_closure':{m:v for m,v in cv.items()},'cover20_static_ok':static_ok,'closures':{m:sorted(v) for m,v in C.items()},
         'closures_unchanged':cl_ok,'frozen_api_sha256':shas,'frozen_api_unchanged':sha_ok,'no_network_run':net,
         'no_network_returncode':p.returncode,'socket_attempts':net.get('socket_attempts'),'network_pass':net_ok}
    out['PASS57']=bool(static_ok and net_ok and sha_ok and all(cl_ok.values()));return out


def drive(arg):
    """Replay one COV_X record: cover20 over the recorded observations, then certify/16e over its own trace."""
    cid,c,arm,a=arg
    from brute.api.certify16e import Certifier16E,counted16d
    from brute.api.cover20 import Cover20
    from experiments import worlds_050 as W
    from experiments.brute_study_033 import StepWorld,passive
    w=W.world(c['seed'],c['family']);_,acts,rd=passive(StepWorld(w),c['seed'])
    ex_a=list(a['extra_acts']);ex_m=list(a['extra_masks']);L=a['ext_len'];diffs=[]
    obs=lambda i:A47._reading(ex_m[i])
    cv=Cover20(rd[0],c['k'],a['explorer']['h'],a['explorer']['steps'])
    for s,o in zip(acts,rd[1:]):cv.observe(s,o)
    prop=[]
    while True:
        s=cv.propose()
        if s is None:break
        if len(prop)>=len(ex_a):diffs.append('cover_beyond_trace');break
        prop.append(s);cv.observe(s,obs(len(prop)-1))
    if prop!=list(a['ext_acts']) or prop!=ex_a[:L]:diffs.append('cover20_extension')
    if diffs:return cid,False,diffs
    kw=dict(max_chunks=a['max_chunks'],K=a['K'],conflict_cap=a['conflict_cap'],budget_conflicts=a['budget_conflicts'],hook=None,
            factory=counted16d,wall_guard_case_s=a['hard_kill_s'])
    x=Certifier16E(rd[0],c['k'],c['N'],'a16d',**kw);i=L
    try:
        for s,o in zip(acts,rd[1:]):x.observe(s,o)
        for j in range(L):x.observe(ex_a[j],obs(j))
        while True:
            wd=x.propose()
            if wd is None:break
            for s in wd:
                if i>=len(ex_a) or ex_a[i]!=s:diffs.append(('word_beyond_or_differs_from_trace',i));raise StopIteration
                x.observe(s,obs(i));i+=1
        rec=x.record();res=x.result()
    except (StopIteration,IndexError):return cid,False,diffs or ['trace_exhausted']
    finally:x.close()
    if i!=len(ex_a):diffs.append(('trace_not_consumed',i,len(ex_a)))
    if dumps(res)!=dumps(a['api']):diffs.append('api_result')
    if len(rec['rounds'])!=len(a['rounds']):diffs.append(('rounds',len(rec['rounds']),len(a['rounds'])))
    for j,(r1,r2) in enumerate(zip(rec['rounds'],a['rounds'])):
        for f in ROUND_FIELDS:
            if dumps(r1.get(f))!=dumps(r2.get(f)):diffs.append((j,f))
    return cid,not diffs,diffs


def fidelity(study,expected,workers=8,block='main'):
    res=load(Path(study)/'RESULTS.json')
    todo=[(f"{c['key']}/{c['seed']}/{g}",c,g,c['arms'][g]) for c in res['cases'] if c['block']==block for g in G_ARMS if g in c['arms']]
    with ProcessPoolExecutor(workers,max_tasks_per_child=1) as ex:rows=list(ex.map(drive,todo))
    return {'study_results_sha256':sha(Path(study)/'RESULTS.json'),'cases':len(rows),'expected':expected,'exact':sum(r[1] for r in rows),
            'workers':workers,'gated':{'cases':len(rows),'exact':sum(r[1] for r in rows)},
            'per_case':{r[0]:{'exact':r[1],'diffs':r[2]} for r in rows},
            'PASS':len(rows)==expected and all(r[1] for r in rows)}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));ap.add_argument('--study')
    ap.add_argument('--expected',type=int,default=12);ap.add_argument('--block',default='main');a=ap.parse_args(argv)
    out={'schema':'brute.api-checks.v54','cover20_sha256':sha(ROOT/'brute/api/cover20.py'),'compat':A47.compat(),'ghost':ghost()}
    if a.study:out['fidelity']=fidelity(a.study,a.expected,block=a.block)
    out['PASS']=out['compat']['PASS'] and out['ghost']['PASS57'] and (out['fidelity']['PASS'] if a.study else True);write_new(Path(a.output),out)
    g=out['ghost']
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':g['PASS57'],'static':g['cover20_static_ok'],'frozen_api_unchanged':g['frozen_api_unchanged'],
                      'closures':g['closures_unchanged'],'net':g['no_network_run'],
                      'fidelity':{k:v for k,v in out.get('fidelity',{}).items() if k!='per_case'}}));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
