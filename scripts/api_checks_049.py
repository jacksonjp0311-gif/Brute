"""GHOST49, GFID49 and compat inputs for study-049 (BRUTE_PLAN_049; pre-run deviation #171). New file; the frozen
scripts/api_checks_047.py compat() and scripts/api_checks_046.py closure() are imported unchanged.
  compat:   api_checks_047.compat() (certify/16 and certify/14 test modules, 046 compat sample byte for byte), reported;
  ghost:    GHOST49: (1) the brute.* import closures of brute.api.certify14, certify16 and certify16d equal their closures today
            computed from the frozen files, and certify14.py / certify16.py / certify16d.py have the sha256 frozen in
            experiments/BRUTE_SOURCE_FREEZE_047.json, and the certify16d closure equals the one recorded in
            results/study-047/API_CHECKS_047.json; (2) newly imported modules (certify16e's closure minus certify16d's, plus
            certify16e itself) import none of os, subprocess, threading, multiprocessing, socket, signal, asyncio, io, shutil,
            tempfile, pathlib, urllib, _thread, concurrent and call no open / exec / eval / __import__; (3) a subprocess with socket
            disabled runs certify16e one-shot and a full Certifier16E loop (family_bound 3, control 10050003) to ID, 0 socket
            attempts;
  fidelity: (GFID49, only with --study) every API16E record of the main block (parts a and d: 18 + N20) is driven again,
            observation by observation, over its own recorded trace (prefix readings, then each proposed word answered from the
            recorded masks, never from the world), in a fresh process per case (8 workers), with the record's C, B and
            max_chunks; the api result (canonical JSON) and every round's T, n_min, check, M1, s1, word, M2, s2, capped,
            call_conflicts, call_capped, call_chunks and chunk_conflicts must equal the record byte for byte.
Writes <out> (default results/study-049/API_CHECKS_049.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_049.py [--study results/study-049/main] [--output PATH]"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,dumps
from scripts import api_checks_047 as A47
from scripts import api_checks_046 as A46
OUT=ROOT/'results/study-049/API_CHECKS_049.json'
CLOSURE_047=ROOT/'results/study-047/API_CHECKS_047.json';FREEZE_047=ROOT/'experiments/BRUTE_SOURCE_FREEZE_047.json'
FROZEN_API=('brute/api/certify14.py','brute/api/certify16.py','brute/api/certify16d.py')
ROUND_FIELDS=A47.ROUND_FIELDS+('call_chunks','chunk_conflicts')
NONET='''
import socket,json
hits=[]
def _no(*a,**k):hits.append(1);raise OSError('network disabled by api_checks_049')
socket.socket=_no;socket.create_connection=_no
from brute.api.certify16e import Certifier16E,certify16e
from experiments import worlds_047 as W
from experiments.brute_study_033 import StepWorld,passive
w=W.world(10050003,'control_cycle3');sw=StepWorld(w);_,acts,rd=passive(sw,10050003)
r1=certify16e(rd[0],acts,rd[1:],w.k,3,conflict_cap=50000,budget_conflicts=1500000)
c=Certifier16E(rd[0],w.k,3,conflict_cap=50000,budget_conflicts=1500000)
for a,o in zip(acts,rd[1:]):c.observe(a,o)
while True:
    x=c.propose()
    if x is None:break
    for a in x:c.observe(a,sw.step(a))
r2=c.result()
print(json.dumps({'one_shot':[r1['api'],r1['label'],r1['n_min']],'loop':[r2['api'],r2['label'],r2['n_min'],r2['used']],'socket_attempts':len(hits)}))
'''


def ghost():
    C={m:A46.closure(m) for m in ('brute.api.certify14','brute.api.certify16','brute.api.certify16d','brute.api.certify16e')}
    fz=load(FREEZE_047)['sha256_files'];old=load(CLOSURE_047)['ghost']['closure']
    shas={f:{'now':sha(ROOT/f),'frozen_047':fz.get(f)} for f in FROZEN_API};sha_ok=all(v['now']==v['frozen_047'] for v in shas.values())
    new=sorted(set(C['brute.api.certify16e'])-set(C['brute.api.certify16d']));ce=C['brute.api.certify16e']
    flag={m:ce[m] for m in new if ce[m]['bad_imports'] or ce[m]['bad_calls']}
    p=subprocess.run([sys.executable,'-c',NONET],cwd=ROOT,capture_output=True,text=True,timeout=600,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:net=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):net={'error':p.stderr.strip()[-400:]}
    net_ok=(p.returncode==0 and net.get('socket_attempts')==0 and net.get('one_shot',[None,None])[1]=='ID' and net.get('loop',[None,None])[1]=='ID'
            and net.get('loop',[None])[0]=='brute.certify/16e')
    out={'closures':{m:sorted(v) for m,v in C.items()},'certify16d_closure_047':old,'certify16d_closure_unchanged':sorted(C['brute.api.certify16d'])==old,
         'frozen_api_sha256':shas,'frozen_api_unchanged':sha_ok,'newly_imported':new,'new_flagged':flag,
         'static_pass':'brute.api.certify16e' in new and not flag,'no_network_run':net,'no_network_returncode':p.returncode,
         'socket_attempts':net.get('socket_attempts'),'network_pass':net_ok}
    out['PASS49']=bool(out['static_pass'] and net_ok and sha_ok and out['certify16d_closure_unchanged']);return out


def drive(arg):
    """Replay one API16E record over its own trace; returns (id, ok, diffs)."""
    cid,c,a=arg
    from brute.api.certify16e import Certifier16E,counted16d
    from experiments.host_hook_047 import TimerHook
    from experiments import worlds_047 as W
    from experiments.brute_study_033 import StepWorld,passive
    w=W.world(c['seed'],c['family']);_,acts,rd=passive(StepWorld(w),c['seed'])
    ex_a=list(a['extra_acts']);ex_m=list(a['extra_masks']);i=0
    x=Certifier16E(rd[0],c['k'],c['N'],'a16d',max_chunks=a['max_chunks'],K=a['K'],conflict_cap=a['conflict_cap'],
                   budget_conflicts=a['budget_conflicts'],hook=TimerHook(),factory=counted16d)
    diffs=[]
    try:
        for s,o in zip(acts,rd[1:]):x.observe(s,o)
        while True:
            wd=x.propose()
            if wd is None:break
            for s in wd:
                if i>=len(ex_a) or ex_a[i]!=s:diffs.append(('word_beyond_or_differs_from_trace',i));raise StopIteration
                x.observe(s,A47._reading(ex_m[i]));i+=1
        rec=x.record();res=x.result()
    except StopIteration:return cid,False,diffs
    finally:x.close()
    if i!=len(ex_a):diffs.append(('trace_not_consumed',i,len(ex_a)))
    if dumps(res)!=dumps(a['api']):diffs.append('api_result')
    if len(rec['rounds'])!=len(a['rounds']):diffs.append(('rounds',len(rec['rounds']),len(a['rounds'])))
    for j,(r1,r2) in enumerate(zip(rec['rounds'],a['rounds'])):
        for f in ROUND_FIELDS:
            if dumps(r1.get(f))!=dumps(r2.get(f)):diffs.append((j,f))
    return cid,not diffs,diffs


def fidelity(study,expected,workers=8):
    res=load(Path(study)/'RESULTS.json')
    todo=[(f"{c['key']}/{c['seed']}",c,c['arms']['API16E']) for c in res['cases'] if c['block']=='main' and 'API16E' in c['arms']]
    with ProcessPoolExecutor(workers,max_tasks_per_child=1) as ex:rows=list(ex.map(drive,todo))
    return {'study_results_sha256':sha(Path(study)/'RESULTS.json'),'cases':len(rows),'expected':expected,'exact':sum(r[1] for r in rows),
            'per_key':{k:sum(1 for r in rows if r[0].startswith(k+'/')) for k in ('scale16','control','scale20')},
            'per_case':{r[0]:{'exact':r[1],'diffs':r[2]} for r in rows},'PASS':len(rows)==expected and all(r[1] for r in rows)}


def main(argv=None):
    from experiments.brute_study_049 import N20
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));ap.add_argument('--study');ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--expected',type=int,default=18+N20);a=ap.parse_args(argv)
    out={'schema':'brute.api-checks.v46','certify16e_sha256':sha(ROOT/'brute/api/certify16e.py'),'compat':A47.compat(),'ghost':ghost()}
    if a.study:out['fidelity']=fidelity(a.study,a.expected,a.workers)
    out['PASS']=out['compat']['PASS'] and out['ghost']['PASS49'] and (out['fidelity']['PASS'] if a.study else True);write_new(Path(a.output),out)
    g=out['ghost']
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':g['PASS49'],'new':g['newly_imported'],'flag':g['new_flagged'],
                      'frozen_api_unchanged':g['frozen_api_unchanged'],'c16d_closure':g['certify16d_closure_unchanged'],'net':g['no_network_run'],
                      'fidelity':{k:v for k,v in out.get('fidelity',{}).items() if k!='per_case'}}));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
