"""GHOST50, GFID50 and compat inputs for study-050 (BRUTE_PLAN_050; pre-run deviation #173). New file; the frozen
scripts/api_checks_047.py compat() and _reading(), scripts/api_checks_046.py closure() are imported unchanged.
  compat:   api_checks_047.compat() (certify/16 and certify/14 test modules, 046 compat sample byte for byte), reported;
  ghost:    GHOST50: (1) brute.api.certify14 / 16 / 16d / 16e files have the sha256 frozen in BRUTE_SOURCE_FREEZE_047 (14, 16,
            16d) and BRUTE_SOURCE_FREEZE_049 (16e), and the certify16e closure equals the one recorded in
            results/study-049/API_CHECKS_049.json; (2) newly imported modules (certify16n's closure minus certify16e's, plus
            certify16n itself) import none of os, subprocess, threading, multiprocessing, socket, signal, asyncio, io, shutil,
            tempfile, pathlib, urllib, _thread, concurrent and call no open / exec / eval / __import__; (3) a subprocess with socket
            disabled runs a full Certifier16N loop (family_bound 12, noise12 smoke seed 11810005, eps 0.05, anytime k) to ID or IDF,
            0 socket attempts;
  fidelity: (GFID50, only with --study) every API16E record of block main (scale20 24 + control 6) and every API16N record
            (noise12 12) is driven again, observation by observation, over its own recorded trace in a fresh process per case
            (8 workers), with the record's C, B and max_chunks. API16E: prefix readings, then each proposed word answered from
            the recorded masks. API16N: each observation is fed k readings rebuilt from its recorded vote vector (bit j is 1 in
            the first ones_j readings), never from the world. The api result (canonical JSON) and every round's T, n_min, check,
            M1, s1, word, M2, s2, capped, call_conflicts, call_capped, call_chunks and chunk_conflicts (and for API16N
            reads_per_obs and votes) must equal the record byte for byte.
Writes <out> (default results/study-050/API_CHECKS_050.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_050.py [--study results/study-050/main] [--output PATH]"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,dumps
from scripts import api_checks_047 as A47
from scripts import api_checks_046 as A46
OUT=ROOT/'results/study-050/API_CHECKS_050.json'
CLOSURE_049=ROOT/'results/study-049/API_CHECKS_049.json'
FROZEN={'brute/api/certify14.py':'experiments/BRUTE_SOURCE_FREEZE_047.json','brute/api/certify16.py':'experiments/BRUTE_SOURCE_FREEZE_047.json',
        'brute/api/certify16d.py':'experiments/BRUTE_SOURCE_FREEZE_047.json','brute/api/certify16e.py':'experiments/BRUTE_SOURCE_FREEZE_049.json'}
ROUND_FIELDS=A47.ROUND_FIELDS+('call_chunks','chunk_conflicts')
NONET='''
import socket,json
hits=[]
def _no(*a,**k):hits.append(1);raise OSError('network disabled by api_checks_050')
socket.socket=_no;socket.create_connection=_no
from brute.api.certify16n import Certifier16N,reads_for
from experiments import worlds_050 as W
from experiments.brute_study_033 import StepWorld,passive
s=11810005;w=W.world(s,'scale12');sw=StepWorld(w);_,acts,rd=passive(sw,s);nw=W.NoisyStepWorld(w,s,0.05);nw.reset()
c=Certifier16N([nw.read() for _ in range(reads_for(1,0.10,0.001))],w.k,12,eps_bar=0.10,delta=0.001,conflict_cap=50000,budget_conflicts=1500000)
for a in acts:nw.step(a);c.observe(a,[nw.read() for _ in range(c.reads_needed())])
while True:
    x=c.propose()
    if x is None:break
    for a in x:nw.step(a);c.observe(a,[nw.read() for _ in range(c.reads_needed())])
r=c.result();c.close()
print(json.dumps({'loop':[r['api'],r['label'],r['n_min'],r['used'],r['reads_total']],'socket_attempts':len(hits)}))
'''


def ghost():
    C={m:A46.closure(m) for m in ('brute.api.certify14','brute.api.certify16','brute.api.certify16d','brute.api.certify16e','brute.api.certify16n')}
    old=load(CLOSURE_049)['ghost']['closures']['brute.api.certify16e']
    shas={f:{'now':sha(ROOT/f),'frozen':load(ROOT/fz)['sha256_files'].get(f),'freeze':fz} for f,fz in FROZEN.items()}
    sha_ok=all(v['now']==v['frozen'] for v in shas.values())
    new=sorted(set(C['brute.api.certify16n'])-set(C['brute.api.certify16e']));cn=C['brute.api.certify16n']
    flag={m:cn[m] for m in new if cn[m]['bad_imports'] or cn[m]['bad_calls']}
    p=subprocess.run([sys.executable,'-c',NONET],cwd=ROOT,capture_output=True,text=True,timeout=600,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:net=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):net={'error':p.stderr.strip()[-400:]}
    lp=net.get('loop',[None,None])
    net_ok=p.returncode==0 and net.get('socket_attempts')==0 and lp[0]=='brute.certify/16n' and lp[1] in ('ID','IDF')
    out={'closures':{m:sorted(v) for m,v in C.items()},'certify16e_closure_049':old,'certify16e_closure_unchanged':sorted(C['brute.api.certify16e'])==old,
         'frozen_api_sha256':shas,'frozen_api_unchanged':sha_ok,'newly_imported':new,'new_flagged':flag,
         'static_pass':'brute.api.certify16n' in new and not flag,'no_network_run':net,'no_network_returncode':p.returncode,
         'socket_attempts':net.get('socket_attempts'),'network_pass':net_ok}
    out['PASS50']=bool(out['static_pass'] and net_ok and sha_ok and out['certify16e_closure_unchanged']);return out


def _rebuild(k,ones):return [tuple(1 if i<o else 0 for o in ones) for i in range(k)]


def drive(arg):
    """Replay one API16E / API16N record over its own trace; returns (id, ok, diffs)."""
    cid,c,arm,a=arg
    from brute.api.certify16e import Certifier16E,counted16d
    from brute.api.certify16n import Certifier16N
    from experiments.host_hook_047 import TimerHook
    from experiments import worlds_050 as W
    from experiments.brute_study_033 import StepWorld,passive
    w=W.world(c['seed'],c['family']);_,acts,rd=passive(StepWorld(w),c['seed'])
    ex_a=list(a['extra_acts']);ex_m=list(a['extra_masks']);i=0;diffs=[]
    kw=dict(max_chunks=a['max_chunks'],K=a['K'],conflict_cap=a['conflict_cap'],budget_conflicts=a['budget_conflicts'],hook=TimerHook(),factory=counted16d)
    if arm=='API16E':
        x=Certifier16E(rd[0],c['k'],c['N'],'a16d',**kw);feed=lambda j,s:x.observe(s,rd[j] if j<len(rd) else A47._reading(ex_m[j-len(rd)]))
    else:
        ks=a['reads_per_obs'];V=a['votes']
        x=Certifier16N(_rebuild(ks[0],V[0]),c['k'],c['N'],eps_bar=a['eps_bar'],delta=a['noise_delta'],reads=a['reads'],**kw)
        feed=lambda j,s:x.observe(s,_rebuild(ks[j],V[j]))
    try:
        for j,s in enumerate(acts):feed(j+1,s)
        while True:
            wd=x.propose()
            if wd is None:break
            for s in wd:
                if i>=len(ex_a) or ex_a[i]!=s:diffs.append(('word_beyond_or_differs_from_trace',i));raise StopIteration
                feed(len(rd)+i,s);i+=1
        rec=x.record();res=x.result()
    except (StopIteration,IndexError):return cid,False,diffs or ['trace_exhausted']
    finally:x.close()
    if i!=len(ex_a):diffs.append(('trace_not_consumed',i,len(ex_a)))
    if dumps(res)!=dumps(a['api']):diffs.append('api_result')
    if len(rec['rounds'])!=len(a['rounds']):diffs.append(('rounds',len(rec['rounds']),len(a['rounds'])))
    for j,(r1,r2) in enumerate(zip(rec['rounds'],a['rounds'])):
        for f in ROUND_FIELDS:
            if dumps(r1.get(f))!=dumps(r2.get(f)):diffs.append((j,f))
    if arm=='API16N':
        for f in ('reads_per_obs','votes'):
            if dumps(rec[f])!=dumps(a[f]):diffs.append(f)
    return cid,not diffs,diffs


def fidelity(study,expected,workers=8):
    res=load(Path(study)/'RESULTS.json')
    todo=[(f"{c['key']}/{c['seed']}/{g}",c,g,c['arms'][g]) for c in res['cases'] if c['block']=='main' for g in ('API16E','API16N') if g in c['arms']]
    with ProcessPoolExecutor(workers,max_tasks_per_child=1) as ex:rows=list(ex.map(drive,todo))
    return {'study_results_sha256':sha(Path(study)/'RESULTS.json'),'cases':len(rows),'expected':expected,'exact':sum(r[1] for r in rows),
            'per_key':{k:sum(1 for r in rows if r[0].startswith(k+'/')) for k in ('scale20','control','noise12')},
            'exact_per_arm':{g:sum(r[1] for r in rows if r[0].endswith('/'+g)) for g in ('API16E','API16N')},
            'per_case':{r[0]:{'exact':r[1],'diffs':r[2]} for r in rows},'PASS':len(rows)==expected and all(r[1] for r in rows)}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));ap.add_argument('--study');ap.add_argument('--workers',type=int,default=8)
    ap.add_argument('--expected',type=int,default=24+6+12);a=ap.parse_args(argv)
    out={'schema':'brute.api-checks.v47','certify16n_sha256':sha(ROOT/'brute/api/certify16n.py'),'compat':A47.compat(),'ghost':ghost()}
    if a.study:out['fidelity']=fidelity(a.study,a.expected,a.workers)
    out['PASS']=out['compat']['PASS'] and out['ghost']['PASS50'] and (out['fidelity']['PASS'] if a.study else True);write_new(Path(a.output),out)
    g=out['ghost']
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':g['PASS50'],'new':g['newly_imported'],'flag':g['new_flagged'],
                      'frozen_api_unchanged':g['frozen_api_unchanged'],'c16e_closure':g['certify16e_closure_unchanged'],'net':g['no_network_run'],
                      'fidelity':{k:v for k,v in out.get('fidelity',{}).items() if k!='per_case'}}));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
