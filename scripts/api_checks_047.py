"""GAPI16_compat, GHOST16D and GFID16D (i) inputs for study-047 (BRUTE_PLAN_047; pre-run deviation #167; new file).
  compat:   (a) the frozen certify/16 and certify/14 test modules (tests.test_certify16, tests.test_scalesearch4_0260) run in a
            subprocess and must pass; (b) the 046 compat sample (results/diag-046/CERTIFY14_SAMPLE_046.json) is reproduced byte for
            byte through certify16, by the frozen scripts/api_checks_046.compat() logic (its own test-module run is reported too);
  ghost:    static AST walk of brute/api/certify16d.py and its brute.* import closure; 'newly imported' = modules in certify16d's
            closure not in certify16's closure, plus certify16d itself; none may import os, subprocess, threading,
            multiprocessing, socket, signal, asyncio, io, shutil, tempfile, pathlib, urllib, _thread or concurrent, or call open /
            exec / eval / __import__ (scale20's generator is in experiments/, not brute/, so it is outside the scan); no network: a
            subprocess with socket disabled runs certify16d (one-shot and a full Certifier16D loop, family_bound 3, on control
            10050003) and must end ID with no socket attempt;
  fidelity: (GFID16D part i, only with --study) every API16D record of the main block's parts b (scale16, control) is driven
            again, observation by observation, over its own recorded trace (the passive prefix readings, then each proposed
            word answered from the recorded masks, never from the world), in a fresh process per case (8 workers), with the
            record's conflict cap and budget; the replayed api result (canonical JSON) and every round's T, n_min, check, M1, s1,
            word, M2, s2, capped, call_conflicts and call_capped must equal the record byte for byte.
Writes <out> (default results/study-047/API_CHECKS_047.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_047.py [--study results/study-047/main] [--output PATH]"""
from __future__ import annotations
import argparse,json,re,subprocess,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,dumps
from scripts import api_checks_046 as A46
OUT=ROOT/'results/study-047/API_CHECKS_047.json'
COMPAT_TESTS=('tests.test_certify16','tests.test_scalesearch4_0260')
ROUND_FIELDS=('T','n_min','check','M1','s1','word','M2','s2','capped','call_conflicts','call_capped')

NONET='''
import socket,json
hits=[]
def _no(*a,**k):hits.append(1);raise OSError('network disabled by api_checks_047')
socket.socket=_no;socket.create_connection=_no
from brute.api.certify16d import Certifier16D,certify16d
from experiments import worlds_047 as W
from experiments.brute_study_033 import StepWorld,passive
w=W.world(10050003,'control_cycle3');sw=StepWorld(w);_,acts,rd=passive(sw,10050003)
r1=certify16d(rd[0],acts,rd[1:],w.k,3,conflict_cap=294000,budget_conflicts=7840000)
c=Certifier16D(rd[0],w.k,3,conflict_cap=294000,budget_conflicts=7840000)
for a,o in zip(acts,rd[1:]):c.observe(a,o)
while True:
    x=c.propose()
    if x is None:break
    for a in x:c.observe(a,sw.step(a))
r2=c.result()
print(json.dumps({'one_shot':[r1['api'],r1['label'],r1['n_min']],'loop':[r2['api'],r2['label'],r2['n_min'],r2['used']],'socket_attempts':len(hits)}))
'''


def _tests(mods):
    out={}
    for m in mods:
        p=subprocess.run([sys.executable,'-m','unittest','-q',m],cwd=ROOT,capture_output=True,text=True,timeout=900)
        ran=re.findall(r'^Ran (\d+) tests?',p.stderr,re.M)
        out[m]={'returncode':p.returncode,'tests':int(ran[-1]) if ran else 0,'ok':p.stderr.strip().endswith('OK')}
    return out


def compat():
    t=_tests(COMPAT_TESTS);s=A46.compat()
    ok=all(v['returncode']==0 and v['tests']>0 for v in t.values())
    return {'tests':t,'tests_pass':ok,'sample_046':s,'PASS':ok and s['PASS']}


def ghost():
    cd=A46.closure('brute.api.certify16d');c16=A46.closure('brute.api.certify16');new=sorted(set(cd)-set(c16))
    flag=lambda ms,C:{m:C[m] for m in ms if C[m]['bad_imports'] or C[m]['bad_calls']}
    p=subprocess.run([sys.executable,'-c',NONET],cwd=ROOT,capture_output=True,text=True,timeout=600,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:net=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):net={'error':p.stderr.strip()[-400:]}
    net_ok=p.returncode==0 and net.get('socket_attempts')==0 and net.get('one_shot',[None,None])[1]=='ID' and net.get('loop',[None,None])[1]=='ID'
    return {'newly_imported':new,'new_flagged':flag(new,cd),'closure':sorted(cd),'closure_flagged_reported':flag(sorted(cd),cd),
            'no_network_run':net,'no_network_returncode':p.returncode,'static_pass':'brute.api.certify16d' in new and not flag(new,cd),
            'network_pass':net_ok,'PASS':'brute.api.certify16d' in new and not flag(new,cd) and net_ok}


def _reading(mask):
    from experiments.worlds_047 import bits
    if not mask or mask&(mask-1):raise ValueError('mask is not a single code')
    return tuple(bits(mask.bit_length()-1))


def drive(arg):
    """Replay one API16D record over its own trace; returns (id, ok, diffs)."""
    cid,c,a=arg
    from brute.api.certify16d import Certifier16D,counted16d
    from experiments.host_hook_047 import TimerHook
    from experiments import worlds_047 as W
    from experiments.brute_study_033 import StepWorld,passive
    w=W.world(c['seed'],c['family']);_,acts,rd=passive(StepWorld(w),c['seed'])  # the prefix only; the world is never stepped past it
    ex_a=list(a['extra_acts']);ex_m=list(a['extra_masks']);i=0
    x=Certifier16D(rd[0],c['k'],c['N'],'a16d',K=a['K'],conflict_cap=a['conflict_cap'],budget_conflicts=a['budget_conflicts'],hook=TimerHook(),factory=counted16d)
    diffs=[]
    try:
        for s,o in zip(acts,rd[1:]):x.observe(s,o)
        while True:
            wd=x.propose()
            if wd is None:break
            for s in wd:
                if i>=len(ex_a) or ex_a[i]!=s:diffs.append(('word_beyond_or_differs_from_trace',i));raise StopIteration
                x.observe(s,_reading(ex_m[i]));i+=1
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


def fidelity(study,workers=8):
    res=load(Path(study)/'RESULTS.json')
    todo=[(f"{c['key']}/{c['seed']}",c,c['arms']['API16D']) for c in res['cases'] if c['block']=='main' and c['key'] in ('scale16','control') and 'API16D' in c['arms']]
    with ProcessPoolExecutor(workers,max_tasks_per_child=1) as ex:rows=list(ex.map(drive,todo))
    return {'study_results_sha256':sha(Path(study)/'RESULTS.json'),'cases':len(rows),'exact':sum(r[1] for r in rows),
            'per_case':{r[0]:{'exact':r[1],'diffs':r[2]} for r in rows},'PASS':len(rows)==18 and all(r[1] for r in rows)}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));ap.add_argument('--study');ap.add_argument('--workers',type=int,default=8)
    a=ap.parse_args(argv)
    out={'schema':'brute.api-checks.v44','certify16d_sha256':sha(ROOT/'brute/api/certify16d.py'),'compat':compat(),'ghost':ghost()}
    if a.study:out['fidelity']=fidelity(a.study,a.workers)
    out['PASS']=out['compat']['PASS'] and out['ghost']['PASS'] and (out['fidelity']['PASS'] if a.study else True);write_new(Path(a.output),out)
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':out['ghost']['PASS'],'new':out['ghost']['newly_imported'],
                      'new_flagged':out['ghost']['new_flagged'],'net':out['ghost']['no_network_run'],
                      'fidelity':{k:v for k,v in out.get('fidelity',{}).items() if k!='per_case'}}));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
