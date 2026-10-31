"""GHOST51, GFID51 and compat inputs for study-051 (BRUTE_PLAN_051; pre-run deviation #175). New file; built from
scripts/api_checks_050.py (frozen), whose compat(), _rebuild() and the frozen api_checks_047 / 046 helpers are imported unchanged.
  compat:   api_checks_047.compat() (certify/16 and certify/14 test modules, 046 compat sample byte for byte), reported;
  ghost:    GHOST51: (1) brute.api.certify14 / 16 / 16d / 16e / 16n files have the sha256 frozen in BRUTE_SOURCE_FREEZE_047 (14, 16,
            16d), BRUTE_SOURCE_FREEZE_049 (16e) and BRUTE_SOURCE_FREEZE_050 (16n), and the certify16e and certify16n closures equal
            the ones recorded in results/study-050/API_CHECKS_050.json; (2) newly imported modules (certify16s's closure minus
            certify16e's, plus certify16s itself) import none of os, subprocess, threading, multiprocessing, socket, signal,
            asyncio, io, shutil, tempfile, pathlib, urllib, _thread, concurrent and call no open / exec / eval / __import__; (3) a
            subprocess with socket disabled runs a full Certifier16S loop (family_bound 12, control smoke seed 11890003, C 50000,
            B 3000000) to ID or IDF, 0 socket attempts;
  fidelity: (GFID51, only with --study) every API16S record of block main (scale20, 12; phase A, 4 workers), every API16E
            record (control, 6) and every API16N record (noise12, 12) (8 workers) is driven again, observation by observation,
            over its own recorded trace in a fresh process per case, with the record's C, B and max_chunks; API16N observations
            are rebuilt from the recorded vote vectors, never from the world. The api result (canonical JSON) and every round's
            T, n_min, check, M1, s1, word, M2, s2, capped, call_conflicts, call_capped, call_chunks and chunk_conflicts (API16N:
            also reads_per_obs and votes; API16S: also encoding and sym_clauses) must equal the record byte for byte.
Writes <out> (default results/study-051/API_CHECKS_051.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_051.py [--study results/study-051/main] [--output PATH]"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,dumps
from scripts import api_checks_047 as A47
from scripts import api_checks_046 as A46
from scripts.api_checks_050 import _rebuild,ROUND_FIELDS
OUT=ROOT/'results/study-051/API_CHECKS_051.json'
CLOSURE_050=ROOT/'results/study-050/API_CHECKS_050.json'
FROZEN={'brute/api/certify14.py':'experiments/BRUTE_SOURCE_FREEZE_047.json','brute/api/certify16.py':'experiments/BRUTE_SOURCE_FREEZE_047.json',
        'brute/api/certify16d.py':'experiments/BRUTE_SOURCE_FREEZE_047.json','brute/api/certify16e.py':'experiments/BRUTE_SOURCE_FREEZE_049.json',
        'brute/api/certify16n.py':'experiments/BRUTE_SOURCE_FREEZE_050.json'}
MODS=('brute.api.certify14','brute.api.certify16','brute.api.certify16d','brute.api.certify16e','brute.api.certify16n','brute.api.certify16s')
NONET='''
import socket,json
hits=[]
def _no(*a,**k):hits.append(1);raise OSError('network disabled by api_checks_051')
socket.socket=_no;socket.create_connection=_no
from brute.api.certify16s import Certifier16S
from experiments import worlds_050 as W
from experiments.brute_study_033 import StepWorld,passive
s=11890003;w=W.world(s,'scale12');sw=StepWorld(w);_,acts,rd=passive(sw,s)
c=Certifier16S(rd[0],w.k,12,conflict_cap=50000,budget_conflicts=3000000)
for a,o in zip(acts,rd[1:]):c.observe(a,o)
while True:
    x=c.propose()
    if x is None:break
    for a in x:c.observe(a,sw.step(a))
r=c.result();c.close()
print(json.dumps({'loop':[r['api'],r['label'],r['n_min'],r['used'],r['conflicts']],'socket_attempts':len(hits)}))
'''


def ghost():
    C={m:A46.closure(m) for m in MODS};prev=load(CLOSURE_050)['ghost']['closures']
    shas={f:{'now':sha(ROOT/f),'frozen':load(ROOT/fz)['sha256_files'].get(f),'freeze':fz} for f,fz in FROZEN.items()}
    sha_ok=all(v['now']==v['frozen'] for v in shas.values())
    new=sorted(set(C['brute.api.certify16s'])-set(C['brute.api.certify16e']));cs=C['brute.api.certify16s']
    flag={m:cs[m] for m in new if cs[m]['bad_imports'] or cs[m]['bad_calls']}
    p=subprocess.run([sys.executable,'-c',NONET],cwd=ROOT,capture_output=True,text=True,timeout=900,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:net=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):net={'error':p.stderr.strip()[-400:]}
    lp=net.get('loop',[None,None])
    net_ok=p.returncode==0 and net.get('socket_attempts')==0 and lp[0]=='brute.certify/16s' and lp[1] in ('ID','IDF')
    cl_ok={m:sorted(C[m])==prev[m] for m in ('brute.api.certify16e','brute.api.certify16n')}
    out={'closures':{m:sorted(v) for m,v in C.items()},'closures_050':{m:prev[m] for m in cl_ok},'closures_unchanged':cl_ok,
         'frozen_api_sha256':shas,'frozen_api_unchanged':sha_ok,'newly_imported':new,'new_flagged':flag,
         'static_pass':'brute.api.certify16s' in new and not flag,'no_network_run':net,'no_network_returncode':p.returncode,
         'socket_attempts':net.get('socket_attempts'),'network_pass':net_ok}
    out['PASS51']=bool(out['static_pass'] and net_ok and sha_ok and all(cl_ok.values()));return out


def drive(arg):
    """Replay one API16S / API16E / API16N record over its own trace; returns (id, ok, diffs)."""
    cid,c,arm,a=arg
    from brute.api.certify16e import Certifier16E,counted16d
    from brute.api.certify16n import Certifier16N
    from brute.api.certify16s import Certifier16S
    from experiments.host_hook_047 import TimerHook
    from experiments import worlds_050 as W
    from experiments.brute_study_033 import StepWorld,passive
    w=W.world(c['seed'],c['family']);_,acts,rd=passive(StepWorld(w),c['seed'])
    ex_a=list(a['extra_acts']);ex_m=list(a['extra_masks']);i=0;diffs=[]
    kw=dict(max_chunks=a['max_chunks'],K=a['K'],conflict_cap=a['conflict_cap'],budget_conflicts=a['budget_conflicts'],hook=TimerHook(),factory=counted16d)
    if arm in ('API16E','API16S'):
        cls=Certifier16E if arm=='API16E' else Certifier16S
        x=cls(rd[0],c['k'],c['N'],'a16d',**kw);feed=lambda j,s:x.observe(s,rd[j] if j<len(rd) else A47._reading(ex_m[j-len(rd)]))
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
    if arm=='API16S':
        for f in ('encoding','sym_clauses'):
            if dumps(rec.get(f))!=dumps(a.get(f)):diffs.append(f)
    return cid,not diffs,diffs


ARMS=('API16S','API16E','API16N')


def fidelity(study,expected,workers_a=4,workers_b=8):
    res=load(Path(study)/'RESULTS.json')
    todo=[(f"{c['key']}/{c['seed']}/{g}",c,g,c['arms'][g]) for c in res['cases'] if c['block']=='main' for g in ARMS if g in c['arms']]
    A=[t for t in todo if t[2]=='API16S'];B=[t for t in todo if t[2]!='API16S'];rows=[]
    for part,wk in ((A,workers_a),(B,workers_b)):
        if part:
            with ProcessPoolExecutor(wk,max_tasks_per_child=1) as ex:rows+=list(ex.map(drive,part))
    return {'study_results_sha256':sha(Path(study)/'RESULTS.json'),'cases':len(rows),'expected':expected,'exact':sum(r[1] for r in rows),
            'workers':{'A':workers_a,'B':workers_b},
            'per_key':{k:sum(1 for r in rows if r[0].startswith(k+'/')) for k in ('scale20','control','noise12')},
            'exact_per_arm':{g:sum(r[1] for r in rows if r[0].endswith('/'+g)) for g in ARMS},
            'per_case':{r[0]:{'exact':r[1],'diffs':r[2]} for r in rows},'PASS':len(rows)==expected and all(r[1] for r in rows)}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));ap.add_argument('--study')
    ap.add_argument('--expected',type=int,default=12+6+12);a=ap.parse_args(argv)
    out={'schema':'brute.api-checks.v48','certify16s_sha256':sha(ROOT/'brute/api/certify16s.py'),'compat':A47.compat(),'ghost':ghost()}
    if a.study:out['fidelity']=fidelity(a.study,a.expected)
    out['PASS']=out['compat']['PASS'] and out['ghost']['PASS51'] and (out['fidelity']['PASS'] if a.study else True);write_new(Path(a.output),out)
    g=out['ghost']
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':g['PASS51'],'new':g['newly_imported'],'flag':g['new_flagged'],
                      'frozen_api_unchanged':g['frozen_api_unchanged'],'closures':g['closures_unchanged'],'net':g['no_network_run'],
                      'fidelity':{k:v for k,v in out.get('fidelity',{}).items() if k!='per_case'}}));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
