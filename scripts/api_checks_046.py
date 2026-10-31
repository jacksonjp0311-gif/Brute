"""GAPI14_compat and GHOST16 inputs for study-046 (BRUTE_PLAN_046; pre-run deviation #165 item 4; new file). Host-side checks of
brute/api/certify16.py, no solver timing involved, deterministic output:
  compat: (a) the frozen certify/14 test module tests/test_scalesearch4_0260.py (the only test module that imports
          brute.api.certify14) runs in a subprocess and must pass; (b) every case of the committed certify14 sample
          results/diag-046/CERTIFY14_SAMPLE_046.json (recorded before certify16 existed, commit 20a1afa) is reproduced byte for
          byte (canonical JSON) through certify16 with the same arguments and the case's search named explicitly ('region' when
          the sample used certify14's default);
  ghost:  (a) static: an AST walk of brute/api/certify16.py and the transitive closure of the brute.* modules it imports;
          'newly imported' = modules in certify16's closure that are not in certify14's closure; no module in the new set (gated)
          may import os, subprocess, threading, multiprocessing, socket, signal, asyncio, io, shutil, tempfile, pathlib or
          urllib, or call open / exec / eval / __import__; the same scan of the full closure is reported; (b) no network: a
          subprocess replaces socket.socket and socket.create_connection with functions that raise, then runs certify16 (one-shot,
          and a full Certifier16 propose / observe loop on a 3-state control world, family_bound 3) and must finish with the
          expected ID label and no socket attempt.
Writes <out> (default results/study-046/API_CHECKS_046.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_046.py [--output PATH]"""
from __future__ import annotations
import argparse,ast,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha
OUT=ROOT/'results/study-046/API_CHECKS_046.json';SAMPLE=ROOT/'results/diag-046/CERTIFY14_SAMPLE_046.json'
COMPAT_TESTS=('tests.test_scalesearch4_0260',)
BAD_MODULES=('os','subprocess','threading','multiprocessing','socket','signal','asyncio','io','shutil','tempfile','pathlib','urllib','_thread','concurrent')
BAD_CALLS=('open','exec','eval','__import__')


def _path(mod):
    p=ROOT/(mod.replace('.','/')+'.py')
    if p.exists():return p
    p=ROOT/mod.replace('.','/')/'__init__.py';return p if p.exists() else None


def scan(mod):
    """(brute imports, bad imports, bad calls) of one module."""
    tree=ast.parse(_path(mod).read_text());deps=set();bad=set();calls=set()
    for n in ast.walk(tree):
        names=[]
        if isinstance(n,ast.Import):names=[a.name for a in n.names]
        elif isinstance(n,ast.ImportFrom) and n.level==0 and n.module:
            names=[n.module]+[n.module+'.'+a.name for a in n.names]
        for x in names:
            top=x.split('.')[0]
            if top=='brute' and _path(x):deps.add(x)
            if top in BAD_MODULES:bad.add(x)
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in BAD_CALLS:calls.add(n.func.id)
    return deps,sorted(bad),sorted(calls)


def closure(mod):
    seen={};todo=[mod]
    while todo:
        m=todo.pop()
        if m in seen:continue
        d,b,c=scan(m);seen[m]={'bad_imports':b,'bad_calls':c};todo+=sorted(d)
    return seen


NONET='''
import socket,json
hits=[]
def _no(*a,**k):hits.append(1);raise OSError('network disabled by api_checks_046')
socket.socket=_no;socket.create_connection=_no
from brute.api.certify16 import Certifier16,certify16
from experiments import worlds_043 as W
from experiments.brute_study_033 import StepWorld,passive
w=W.world(10050003,'control_cycle3');sw=StepWorld(w);_,acts,rd=passive(sw,10050003)
r1=certify16(rd[0],acts,rd[1:],w.k,3)
c=Certifier16(rd[0],w.k,3,budget_s=60.0)
for a,o in zip(acts,rd[1:]):c.observe(a,o)
while True:
    x=c.propose()
    if x is None:break
    for a in x:c.observe(a,sw.step(a))
r2=c.result()
print(json.dumps({'one_shot':[r1['api'],r1['label'],r1['n_min']],'loop':[r2['api'],r2['label'],r2['n_min'],r2['used']],'socket_attempts':len(hits)}))
'''


def compat():
    from brute.api.certify16 import certify16
    from scripts.make_certify14_sample_046 import canon
    S=load(SAMPLE);cases=[]
    for c in S['cases']:
        a=c['args'];kw=dict(c['kwargs']);kw.setdefault('search','region')
        out=canon(certify16(tuple(a[0]),a[1],[tuple(o) for o in a[2]],**kw));cases.append({'name':c['name'],'search':kw['search'],'byte_equal':out==c['output']})
    tests={}
    for m in COMPAT_TESTS:
        p=subprocess.run([sys.executable,'-m','unittest','-q',m],cwd=ROOT,capture_output=True,text=True,timeout=600)
        import re;ran=re.findall(r'^Ran (\d+) tests?',p.stderr,re.M)
        tests[m]={'returncode':p.returncode,'tests':int(ran[-1]) if ran else 0,'ok':p.stderr.strip().endswith('OK')}
    return {'sample_sha256':sha(SAMPLE),'cases':cases,'s4_cases':sum(c['search']=='s4' for c in cases),
            'all_byte_equal':all(c['byte_equal'] for c in cases),'tests':tests,'tests_pass':all(v['returncode']==0 and v['tests']>0 for v in tests.values()),
            'PASS':all(c['byte_equal'] for c in cases) and any(c['search']=='s4' for c in cases) and all(v['returncode']==0 and v['tests']>0 for v in tests.values())}


def ghost():
    c16=closure('brute.api.certify16');c14=closure('brute.api.certify14');new=sorted(set(c16)-set(c14))
    flag=lambda ms,C:{m:C[m] for m in ms if C[m]['bad_imports'] or C[m]['bad_calls']}
    p=subprocess.run([sys.executable,'-c',NONET],cwd=ROOT,capture_output=True,text=True,timeout=600,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:net=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):net={'error':p.stderr.strip()[-400:]}
    net_ok=p.returncode==0 and net.get('socket_attempts')==0 and net.get('one_shot',[None,None])[1]=='ID' and net.get('loop',[None,None])[1]=='ID'
    return {'newly_imported':new,'new_flagged':flag(new,c16),'closure':sorted(c16),'closure_flagged_reported':flag(sorted(c16),c16),
            'no_network_run':net,'no_network_returncode':p.returncode,'static_pass':not flag(new,c16),'network_pass':net_ok,
            'PASS':not flag(new,c16) and net_ok}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));a=ap.parse_args(argv)
    out={'schema':'brute.api-checks.v43','certify16_sha256':sha(ROOT/'brute/api/certify16.py'),'compat':compat(),'ghost':ghost()}
    out['PASS']=out['compat']['PASS'] and out['ghost']['PASS'];write_new(Path(a.output),out)
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':out['ghost']['PASS'],'new':out['ghost']['newly_imported'],
                      'new_flagged':out['ghost']['new_flagged'],'net':out['ghost']['no_network_run']}));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
