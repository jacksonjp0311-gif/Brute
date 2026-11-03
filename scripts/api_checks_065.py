"""GHOST65 and GFID65 inputs for study-065 (BRUTE_PLAN_065 design.fidelity; the pre-run deviation #204 fixes every definition). New
file; built from scripts/api_checks_064.py (frozen); api_checks_063 ast_scan/_rm_walls, api_checks_047 compat() and the
api_checks_046 closure are imported unchanged.
  compat:     api_checks_047.compat(), reported;
  ghost:      GHOST65: (1) static: the import closure of brute.api.certify20s has no bad imports or calls and an AST scan of
              brute/api/certify20s.py finds no os, io, threading, subprocess, socket or multiprocessing import and no open; (2) every
              brute/api file hashed in BRUTE_SOURCE_FREEZE_064 keeps its sha256; (3) a subprocess with socket disabled runs one full
              certify/20s loop (smoke seed 12650303, eps 0.30, eps_bar 0.35, delta 0.001, worlds_065, bound 20, C 50000, B 2000000,
              K 400, node cap 200000) to any final label with 0 socket attempts;
  equiv:      certify/20s at eps_bar 0 (m = 1: one clean reading per observation) on smoke worlds 12650301 and 12650302 (B 2000000)
              is byte-identical to certify/20p: record minus walls and the read fields, result and current minus api names,
              soundness and the read fields;
  threshold:  certify20s.threshold(t, eps_bar, 0.001, 2) == the exact-fraction rule of scripts/recount_065.m_exact for t 1..500 at
              eps_bar 0.15, 0.25 and 0.35 (1500 checks);
  montecarlo: reported only: for each arm (eps, eps_bar) and t in (1, 100, 500) the per-bit wrong-barrier rate of 100000 simulated
              walks at m_t (random.Random(652)) against the bound r^m/(1+r^m);
  fidelity:   GFID65 (only with --study): every DECIDED noisy record of block main is driven again in a fresh process through the
              public certify/20s interface: the raw readings are regenerated from worlds_065.Noise on the true world along the recorded
              actions, drawn one at a time until more() is False; every proposed word must equal the recorded extra actions; api result,
              masks, reads_per_obs, thresholds, settle_at, pins and every round minus wall fields must equal the record, and the
              regenerated raw-reading sha must equal readings_sha256.
Writes <out> (default results/study-065/API_CHECKS_065.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_065.py [--study results/study-065/main] [--output PATH]"""
from __future__ import annotations
import argparse,hashlib,json,random,subprocess,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,dumps
from scripts import api_checks_047 as A47
from scripts import api_checks_046 as A46
from scripts.api_checks_063 import ast_scan,_rm_walls
OUT=ROOT/'results/study-065/API_CHECKS_065.json'
FZ64='experiments/BRUTE_SOURCE_FREEZE_064.json'
READ_FIELDS=('reads_per_obs','thresholds','settle_at','eps_bar','delta','inner_api','observations','reads_total','reads_max','soundness','api')
NONET='''
import socket,json
hits=[]
def _no(*a,**k):hits.append(1);raise OSError('network disabled by api_checks_065')
socket.socket=_no;socket.create_connection=_no
from brute.api import certify20s as X
from brute.api.certify20b import counted16d
from experiments import worlds_065 as W
s=12650303;w=W.world(s);acts=list(W.actions(s,0.0,w.k));q=w.start;nz=W.Noise(s,0.30)
def reads(more):
    rs=[]
    while True:
        rs.append(nz.read(W.clean(w,q)))
        if not more(rs):return rs
m1=X.threshold(1,0.35,0.001,2)
c=X.Certifier20S(reads(lambda rs:X.settle(rs,m1,2)[0] is None),w.k,20,read_bits=2,eps_bar=0.35,delta=0.001,K=400,max_chunks=None,conflict_cap=50000,
                 budget_conflicts=2000000,node_cap=200000,wall_guard_case_s=3600.0,hook=None,factory=counted16d)
def ob(a):
    global q
    q=w.transitions[q][a];c.observe(a,reads(c.more))
for a in acts:ob(a)
while True:
    x=c.propose()
    if x is None:break
    for a in x:ob(a)
r=c.result();c.close()
print(json.dumps({'loop':[r['api'],r['inner_api'],r['label'],r['n_min'],r['used'],r['conflicts'],r['reads_total'],r['family_bound']],'socket_attempts':len(hits)}))
'''


def ghost():
    cv=A46.closure('brute.api.certify20s');static_ok=all(not v['bad_imports'] and not v['bad_calls'] for v in cv.values())
    sc=ast_scan(ROOT/'brute/api/certify20s.py');fz=load(ROOT/FZ64)['sha256_files']
    shas={f:{'now':sha(ROOT/f),'frozen':d,'freeze':FZ64} for f,d in fz.items() if f.startswith('brute/api/')}
    sha_ok=bool(shas) and all(v['now']==v['frozen'] for v in shas.values())
    p=subprocess.run([sys.executable,'-c',NONET],cwd=ROOT,capture_output=True,text=True,timeout=1800,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:net=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):net={'error':p.stderr.strip()[-400:]}
    lp=net.get('loop',[None,None,None])
    net_ok=p.returncode==0 and net.get('socket_attempts')==0 and lp[0]=='brute.certify/20s' and lp[2] in ('ID','IDF','IDU','AMB')
    out={'certify20s_closure':cv,'static_ok':static_ok,'ast_scan':sc,'frozen_api_sha256':shas,'frozen_api_unchanged':sha_ok,'no_network_run':net,
         'no_network_returncode':p.returncode,'socket_attempts':net.get('socket_attempts'),'network_pass':net_ok}
    out['PASS']=bool(static_ok and sc['PASS'] and net_ok and sha_ok);return out


def _clean_run(arg):
    """Full smoke-world record of certify/20p, or certify/20s at eps_bar 0 (one clean reading per observation), minus walls / read fields."""
    seed,which=arg
    from brute.api import certify20p as P,certify20s as S
    from brute.api.certify20b import counted16d
    from brute.scalesearch4 import SOLVER4
    from brute.evaluation import no_time
    from experiments import worlds_065 as W
    w=W.world(seed);acts=list(W.actions(seed,0.0,w.k));q=w.start
    kw=dict(K=400,max_chunks=None,conflict_cap=50000,budget_conflicts=2000000,node_cap=200000,wall_guard_case_s=3600.0,
            wall_guard_call_s=30.0,hook=None,factory=counted16d,solver=SOLVER4)
    if which=='20p':c=P.Certifier20P(W.clean(w,q),w.k,20,'a16d',read_bits=2,**kw);ob=lambda a,x:c.observe(a,x)
    else:c=S.Certifier20S([W.clean(w,q)],w.k,20,read_bits=2,eps_bar=0,delta=0.001,**kw);ob=lambda a,x:c.observe(a,[x])
    try:
        for a in acts:q=w.transitions[q][a];ob(a,W.clean(w,q))
        while True:
            x=c.propose()
            if x is None:break
            for a in x:q=w.transitions[q][a];ob(a,W.clean(w,q))
        R=dict(c.record());res=dict(c.result());cur=dict(c.current())
    finally:c.close()
    for d in (R,res,cur):
        for f in READ_FIELDS:d.pop(f,None)
    return seed,which,dumps(no_time(_rm_walls({'res':res,'cur':cur,'rec':R}))),res.get('label')


def equiv(seeds=(12650301,12650302)):
    jobs=[(s,w) for s in seeds for w in ('20p','20s')]
    with ProcessPoolExecutor(4,max_tasks_per_child=1) as ex:out=list(ex.map(_clean_run,jobs))
    d={(s,w):(t,l) for s,w,t,l in out};rows=[]
    for s in seeds:
        rows.append({'seed':s,'identical':d[(s,'20p')][0]==d[(s,'20s')][0],'label_20p':d[(s,'20p')][1],'label_20s':d[(s,'20s')][1],
                     'sha256':hashlib.sha256(d[(s,'20p')][0] if isinstance(d[(s,'20p')][0],bytes) else d[(s,'20p')][0].encode()).hexdigest()})
    return {'cases':rows,'identical':sum(r['identical'] for r in rows),'PASS':all(r['identical'] for r in rows)}


def threshold_check():
    from brute.api.certify20s import threshold
    from scripts.recount_065 import m_exact
    bad=[];n=0
    for eb in (0.15,0.25,0.35):
        for t in range(1,501):
            n+=1;a=threshold(t,eb,0.001,2);b=m_exact(t,eb)
            if a!=b:bad.append([eb,t,a,b])
    return {'checked':n,'disagreements':bad,'PASS':n==1500 and not bad}


def montecarlo(trials=100000):
    from brute.api.certify20s import threshold
    rng=random.Random(652);rows=[]
    for eps,eb in ((0.10,0.15),(0.20,0.25),(0.30,0.35)):
        for t in (1,100,500):
            m=threshold(t,eb,0.001,2);wrong=0;steps=0
            for _ in range(trials):
                L=0
                while abs(L)<m:L+=-1 if rng.random()<eps else 1;steps+=1
                wrong+=L<0
            r=eb/(1-eb);re_=eps/(1-eps)
            rows.append({'eps':eps,'eps_bar':eb,'t':t,'m':m,'trials':trials,'wrong':wrong,'rate':wrong/trials,'bound_eps_bar':r**m/(1+r**m),
                         'exact_at_eps':re_**m/(1+re_**m),'mean_reads':steps/trials})
    return {'rows':rows,'note':'reported only; per-bit wrong-barrier rate of the +-1 walk at threshold m_t'}


def drive(arg):
    cid,c,arm,a=arg
    from brute.api.certify20b import counted16d
    from brute.api.certify20s import Certifier20S,threshold,settle
    from experiments import worlds_065 as W
    from brute.scalesearch4 import SOLVER4
    w=W.world(c['seed']);q=w.start;nz=W.Noise(c['seed'],a['eps']);raw=[];ea=list(a['extra_acts']);diffs=[]
    acts=list(W.actions(c['seed'],0.0,c['k']))
    def reads(more):
        rs=[]
        while True:
            rs.append(nz.read(W.clean(w,q)))
            if not more(rs):raw.append([list(r) for r in rs]);return rs
    kw=dict(max_chunks=a['max_chunks'],K=a['K'],conflict_cap=a['conflict_cap'],budget_conflicts=a['budget_conflicts'],hook=None,
            factory=counted16d,wall_guard_case_s=a['hard_kill_s'],wall_guard_call_s=30.0,solver=SOLVER4)
    m1=threshold(1,a['eps_bar'],a['delta'],2)
    x=Certifier20S(reads(lambda rs:settle(rs,m1,2)[0] is None),c['k'],c['N'],read_bits=2,eps_bar=a['eps_bar'],delta=a['delta'],node_cap=a['node_cap'],**kw)
    i=0
    try:
        for s in acts:q=w.transitions[q][s];x.observe(s,reads(x.more))
        while True:
            wd=x.propose()
            if wd is None:break
            for s in wd:
                if i>=len(ea) or ea[i]!=s:diffs.append(['word_differs',i]);raise StopIteration
                q=w.transitions[q][s];x.observe(s,reads(x.more));i+=1
        rec=x.record();res=x.result()
    except StopIteration:return cid,False,diffs
    finally:x.close()
    if i!=len(ea):diffs.append(['trace_not_consumed',i,len(ea)])
    if list(rec['masks'])!=list(a['prefix_masks'])+list(a['extra_masks']):diffs.append('masks')
    if dumps(res)!=dumps(a['api']):diffs.append('api_result')
    for f in ('reads_per_obs','thresholds','settle_at'):
        if dumps(rec[f])!=dumps(a[f]):diffs.append(f)
    if hashlib.sha256(json.dumps(raw,separators=(',',':')).encode()).hexdigest()!=a['readings_sha256']:diffs.append('readings_sha256')
    if dumps([list(y) for y in rec.get('repins') or []])!=dumps(a['repins']):diffs.append('repins')
    if len(rec['rounds'])!=len(a['rounds']):diffs.append(['rounds',len(rec['rounds']),len(a['rounds'])])
    for j,(r1,r2) in enumerate(zip(rec['rounds'],a['rounds'])):
        for f in ('T','n_min','M1','s1','call_conflicts','call_capped','capped','check','word','probe','pred1','pred2','obs','call_chunks','chunk_conflicts'):
            if dumps(r1.get(f))!=dumps(r2.get(f)):diffs.append([j,f])
    return cid,not diffs,diffs


def fidelity(study,workers=6,block='main'):
    res=load(Path(study)/'RESULTS.json')
    todo=[(f"{c['key']}/{c['seed']}/{g}",c,g,a) for c in res['cases'] if c['block']==block for g,a in c['arms'].items()
          if a['label'] in ('ID','IDF') and a.get('eps_bar') is not None]
    rows=[]
    if todo:
        with ProcessPoolExecutor(workers,max_tasks_per_child=1) as ex:rows=list(ex.map(drive,todo))
    return {'study_results_sha256':sha(Path(study)/'RESULTS.json'),'decided_records':len(todo),'exact':sum(r[1] for r in rows),'workers':workers,
            'per_case':{r[0]:{'exact':r[1],'diffs':r[2]} for r in rows},'vacuous':not todo,'PASS':all(r[1] for r in rows)}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));ap.add_argument('--study')
    ap.add_argument('--block',default='main');ap.add_argument('--mc-trials',type=int,default=100000);a=ap.parse_args(argv)
    out={'schema':'brute.api-checks.v62','certify20s_sha256':sha(ROOT/'brute/api/certify20s.py'),'compat':A47.compat(),'ghost':ghost(),
         'equiv':equiv(),'threshold':threshold_check(),'montecarlo':montecarlo(a.mc_trials)}
    if a.study:out['fidelity']=fidelity(a.study,block=a.block)
    out['PASS']=bool(out['compat']['PASS'] and out['ghost']['PASS'] and out['equiv']['PASS'] and out['threshold']['PASS']
                     and (out['fidelity']['PASS'] if a.study else True))
    write_new(Path(a.output),out);g=out['ghost']
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':g['PASS'],'static':g['static_ok'],'ast':g['ast_scan']['PASS'],'frozen_api_unchanged':g['frozen_api_unchanged'],
                      'net':g['no_network_run'],'equiv':{k:v for k,v in out['equiv'].items() if k!='cases'},'equiv_labels':[[r['label_20p'],r['label_20s']] for r in out['equiv']['cases']],
                      'threshold':out['threshold']['PASS'],'mc':[[r['eps'],r['t'],r['m'],r['rate'],round(r['bound_eps_bar'],6)] for r in out['montecarlo']['rows']],
                      'fidelity':{k:v for k,v in out.get('fidelity',{}).items() if k!='per_case'}}))
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
