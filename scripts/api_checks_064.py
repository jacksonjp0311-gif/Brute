"""GHOST64, GFID64 and GXREF64 inputs for study-064 (BRUTE_PLAN_064; the pre-run deviation fixes every definition). New file; built
from scripts/api_checks_063.py (frozen), whose _run_small(), beq(), _sound() and ast_scan() are imported; the frozen api_checks_047
compat() and api_checks_046 closure are imported unchanged.
  compat:   api_checks_047.compat(), reported;
  ghost:    GHOST64: (1) static: the import closure of brute.api.certify32p has no bad imports or calls (api_checks_046), and an AST
            scan of brute/api/certify32p.py finds no import of os, io, threading, subprocess, socket or multiprocessing and no open;
            (2) every brute/api file hashed in BRUTE_SOURCE_FREEZE_063 keeps its sha256, and certify16d.A16D_MAX_BOUND is still 20
            after importing certify32p (no global patch); (3) a subprocess with socket disabled runs one full certify/32p loop
            (smoke seed 12640303, worlds_064 scale24, read_bits 2, bound 24, C 50000, B 2000000, K 400, node cap 200000) to any final
            label, 0 socket attempts;
  equiv:    (a) certify/32p at bound <= 20 is certify/20p exactly: on 18 small worlds (read_bits 2, 3, 4; bound n+1) and on the smoke
            world 12640302 (worlds_064 scale20, bound 20, C 50000, B 2000000, K 400) the full record and result minus wall fields and
            the api name are byte-identical; (b) at bound n+5 > n on the small worlds no ID/IDF is wrong against the true machine;
            (c) bounds 0 and 33 are refused, 21..32 accepted;
  xref:     GXREF64: the clique-pinned reference (experiments/v0610_reference.py) against the frozen plain reference
            (v0300_reference.solve, v0310_reference.exists_different): n_min and every exists_different verdict (n = n_min..N,
            future and start, L = N + n_min - 1) on 150 seeded random small 2-bit traces (random.Random(641); n 3..6, k 2, N n+1),
            and the pinned audit of the 2 study-063 records the frozen reference audited must equal REFERENCE_063's per-record
            label, mismatches, verdict count and future_match_ref;
  fidelity: (GFID64, only with --study) every DECIDED record of block main is driven again in a fresh process through its own
            arm's API (P24: certify/32p; B24: certify/32b; P20, P20b: certify/20p) fed the recorded prefix and its own proposed words
            with readings from the recorded masks; api result, pins and every round minus wall fields must equal the record.
Writes <out> (default results/study-064/API_CHECKS_064.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_064.py [--study results/study-064/main] [--output PATH]"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,dumps
from scripts import api_checks_047 as A47
from scripts import api_checks_046 as A46
from scripts.api_checks_059 import _small,_bits
from scripts.api_checks_063 import _run_small,_sound,ast_scan,_rm_walls
OUT=ROOT/'results/study-064/API_CHECKS_064.json'
FZ63='experiments/BRUTE_SOURCE_FREEZE_063.json'
NONET='''
import socket,json
hits=[]
def _no(*a,**k):hits.append(1);raise OSError('network disabled by api_checks_064')
socket.socket=_no;socket.create_connection=_no
from brute.api import certify32p as X
from brute.api.certify20b import counted16d
from experiments import worlds_064 as W
from experiments.worlds_058 import bits
s=12640303;w=W.world(s,'scale24');acts=list(W.actions(s,0.0,w.k));q=w.start
c=X.Certifier32P(bits(w.emissions[q],2),w.k,24,'a16d',read_bits=2,K=400,max_chunks=None,conflict_cap=50000,budget_conflicts=2000000,
                 node_cap=200000,wall_guard_case_s=3600.0,hook=None,factory=counted16d)
def ob(a):
    global q
    q=w.transitions[q][a];c.observe(a,bits(w.emissions[q],2))
for a in acts:ob(a)
while True:
    x=c.propose()
    if x is None:break
    for a in x:ob(a)
r=c.result();c.close()
print(json.dumps({'loop':[r['api'],r['label'],r['n_min'],r['used'],r['conflicts'],r['read_bits'],r['family_bound'],r['clique_size'],r['repins']],'socket_attempts':len(hits)}))
'''
XREF063='''
import json,sys
from experiments import v0610_reference as PIN
from experiments.brute_common import load
from scripts import run_reference_063 as R63
from scripts import run_reference_041 as R41
cur={}
def cl(a,c):
    if cur.get('C') is None:cur['C'],cur['src']=PIN.verified_clique(a,c,cur.get('hint'))
    return cur['C']
R41._nmin=lambda a,c,k,N:PIN.nmin(a,c,k,R41.M,N,cl(a,c))
R41.exists_different=lambda a,c,n,k,m,M1,s1,mode,L:PIN.exists_different(a,c,n,k,m,M1,s1,mode,L,cl(a,c))
res=load('results/study-063/main/RESULTS.json');ref=load('results/study-063/main/REFERENCE_063.json')
want={x['id']:x for x in ref['per_record'] if x.get('audited')};out={}
for c in res['cases']:
    for g in c['arms']:
        r=R63.view(c,g)
        if r['id'] not in want:continue
        cur.clear();cur['hint']=list(c['arms'][g].get('final_clique') or []) or None
        x,_,_=R63._audit(r);o=want[r['id']]
        out[r['id']]={f:[x.get(f),o.get(f)] for f in ('label','mismatches','verdicts_checked','future_match_ref','N_audited')}
print(json.dumps(out))
'''


def ghost():
    cv=A46.closure('brute.api.certify32p');static_ok=all(not v['bad_imports'] and not v['bad_calls'] for v in cv.values())
    sc=ast_scan(ROOT/'brute/api/certify32p.py');fz=load(ROOT/FZ63)['sha256_files']
    shas={f:{'now':sha(ROOT/f),'frozen':d,'freeze':FZ63} for f,d in fz.items() if f.startswith('brute/api/')}
    sha_ok=bool(shas) and all(v['now']==v['frozen'] for v in shas.values())
    from brute.api import certify32p as _X  # noqa: F401
    from brute.api import certify16d as D;glob_ok=D.A16D_MAX_BOUND==20
    p=subprocess.run([sys.executable,'-c',NONET],cwd=ROOT,capture_output=True,text=True,timeout=1800,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:net=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):net={'error':p.stderr.strip()[-400:]}
    lp=net.get('loop',[None,None])
    net_ok=p.returncode==0 and net.get('socket_attempts')==0 and lp[0]=='brute.certify/32p' and lp[1] in ('ID','IDF','IDU','AMB')
    out={'certify32p_closure':cv,'certify32p_static_ok':static_ok,'certify32p_ast_scan':sc,'frozen_api_sha256':shas,'frozen_api_unchanged':sha_ok,
         'a16d_max_bound_unpatched':glob_ok,'no_network_run':net,'no_network_returncode':p.returncode,'socket_attempts':net.get('socket_attempts'),
         'network_pass':net_ok}
    out['PASS64']=bool(static_ok and sc['PASS'] and net_ok and sha_ok and glob_ok);return out


def _strip(d):
    d=json.loads(dumps(d))
    if isinstance(d.get('res'),dict):d['res'].pop('api',None)
    return dumps(d)


def _smoke_pair(which):
    """Full smoke-world record of certify/20p or certify/32p at bound 20, minus walls and api names."""
    from brute.api import certify20p as P,certify32p as X
    from brute.api.certify20b import counted16d
    from brute.scalesearch4 import SOLVER4
    from brute.evaluation import no_time
    from experiments import worlds_064 as W
    from experiments.worlds_058 import bits
    s=12640302;w=W.world(s,'scale20');acts=list(W.actions(s,0.0,w.k));q=w.start
    kw=dict(K=400,max_chunks=None,conflict_cap=50000,budget_conflicts=2000000,node_cap=200000,wall_guard_case_s=3600.0,
            wall_guard_call_s=30.0,hook=None,factory=counted16d,solver=SOLVER4)
    c=(P.Certifier20P if which=='20p' else X.Certifier32P)(bits(w.emissions[q],2),w.k,20,'a16d',read_bits=2,**kw)
    try:
        for a in acts:q=w.transitions[q][a];c.observe(a,bits(w.emissions[q],2))
        while True:
            x=c.propose()
            if x is None:break
            for a in x:q=w.transitions[q][a];c.observe(a,bits(w.emissions[q],2))
        R=c.record();res=dict(c.result());cur=dict(c.current())
    finally:c.close()
    res.pop('api',None);res.pop('soundness',None);cur.pop('api',None)
    return which,dumps(no_time(_rm_walls({'res':res,'cur':cur,'rec':R}))),res.get('label')


def equiv():
    from brute.api import certify20p as P,certify32p as X
    kw=dict(K=60,conflict_cap=5000,budget_conflicts=200000);rows=[]
    with ProcessPoolExecutor(2,max_tasks_per_child=1) as ex:sm=dict((w,(t,l)) for w,t,l in ex.map(_smoke_pair,('20p','32p')))
    for sb in (2,3,4):
        for s in range(6):
            sd=6400+10*sb+s;n=3+s%4;T,em=_small(sd,n,sb)
            a,wa,qa=_run_small(lambda ini:P.Certifier20P(ini,3,n+1,'a16d',read_bits=sb,**kw),T,em,sd,sb)
            d,wd,qd=_run_small(lambda ini:X.Certifier32P(ini,3,n+1,'a16d',read_bits=sb,**kw),T,em,sd,sb)
            e,we,qe=_run_small(lambda ini:X.Certifier32P(ini,3,n+5,'a16d',read_bits=sb,**kw),T,em,sd,sb)
            rows.append({'read_bits':sb,'seed':sd,'n':n,'stop_20p':a['stop'],'stop_32p':d['stop'],'stop_32p_n5':e['stop'],
                         'identical_at_n1':_strip(a)==_strip(d) and wa==wd,'sound_32p_n5':_sound(e['stop'],e['final'],T,em,qe),
                         'k_ok':e['used']==sum(len(w) for w in we)<=60})
    ref=[]
    for fb in (0,33,21,24,32):
        try:X.Certifier32P((0,1),3,fb,read_bits=2,conflict_cap=10,budget_conflicts=10).close();ref.append([fb,'ACCEPTED'])
        except (ValueError,TypeError):ref.append([fb,'refused'])
    ref_ok=ref==[[0,'refused'],[33,'refused'],[21,'ACCEPTED'],[24,'ACCEPTED'],[32,'ACCEPTED']]
    smoke_ok=sm['20p'][0]==sm['32p'][0]
    return {'cases':rows,'bounds':ref,'smoke_world_identical':smoke_ok,'smoke_labels':{k:v[1] for k,v in sm.items()},
            'smoke_sha256':{k:__import__('hashlib').sha256(v[0] if isinstance(v[0],bytes) else v[0].encode()).hexdigest() for k,v in sm.items()},
            'decided_32p_n5':sum(r['stop_32p_n5'] in ('ID','IDF') for r in rows),
            'PASS':all(r['identical_at_n1'] and r['sound_32p_n5'] and r['k_ok'] for r in rows) and ref_ok and smoke_ok
                   and sum(r['stop_20p'] in ('ID','IDF') for r in rows)>0,
            'note':'n+5 runs are a soundness check only (loose bounds rarely decide at K 60 / B 200000; the decided count is reported)'}


def xref():
    import random
    from experiments import v0610_reference as PIN
    from experiments.v0300_reference import solve
    from experiments.v0310_reference import exists_different as ED
    def nm(a,c,k,m,N):
        for n in range(1,N+1):
            if solve(a,c,n,k,m)[0] is not None:return n
    rng=random.Random(641);bad=[];tot=0
    for it in range(150):
        n=rng.randint(3,6);k=2;m=4
        D=[[rng.randrange(n) for _ in range(k)] for _ in range(n)];E=[rng.randrange(m) for _ in range(n)]
        T=rng.randint(8,30);acts=[rng.randrange(k) for _ in range(T)];q=0;codes=[E[0]]
        for a in acts:q=D[q][a];codes.append(E[q])
        N=n+1;C,_=PIN.verified_clique(acts,codes);a=nm(acts,codes,k,m,N);b=PIN.nmin(acts,codes,k,m,N,C);tot+=1
        if a!=b:bad.append([it,'nmin',a,b]);continue
        M1=solve(acts,codes,a,k,m)[0];s=0
        for x in acts:s=M1[0][s][x]
        L=N+a-1
        for nn in range(a,N+1):
            for mode in ('future','start'):
                u=ED(acts,codes,nn,k,m,M1,s,mode,L);v=PIN.exists_different(acts,codes,nn,k,m,M1,s,mode,L,C);tot+=1
                if u!=v:bad.append([it,'exd',nn,mode,u,v])
    p=subprocess.run([sys.executable,'-c',XREF063],cwd=ROOT,capture_output=True,text=True,timeout=3600,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:r63=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):r63={'error':p.stderr.strip()[-400:]}
    ok63=p.returncode==0 and len(r63)==2 and all(v[0]==v[1] for x in r63.values() if isinstance(x,dict) for v in x.values())
    return {'random_traces':150,'checks':tot,'disagreements':bad,'study063':r63,'study063_match':ok63,'PASS':not bad and tot>150 and ok63}


def drive(arg):
    cid,c,arm,a=arg
    from brute.api.certify20b import counted16d
    from brute.api.certify20p import Certifier20P
    from brute.api.certify32p import Certifier32P
    from brute.api.certify32b import Certifier32B
    from experiments import worlds_064 as W
    from experiments.worlds_058 import bits
    from brute.scalesearch4 import SOLVER4
    sb=a['read_bits'];pm=list(a['prefix_masks']);em=list(a['extra_masks']);ea=list(a['extra_acts']);diffs=[]
    acts=list(W.actions(c['seed'],0.0,c['k']));rd=lambda mk:bits(mk.bit_length()-1,sb)
    kw=dict(max_chunks=a['max_chunks'],K=a['K'],conflict_cap=a['conflict_cap'],budget_conflicts=a['budget_conflicts'],hook=None,
            factory=counted16d,wall_guard_case_s=a['hard_kill_s'],wall_guard_call_s=30.0,solver=SOLVER4)
    if arm=='P24':x=Certifier32P(rd(pm[0]),c['k'],c['N'],'a16d',read_bits=sb,node_cap=a['node_cap'],**kw)
    elif arm=='B24':x=Certifier32B(rd(pm[0]),c['k'],c['N'],'a16d',read_bits=sb,**kw)
    else:x=Certifier20P(rd(pm[0]),c['k'],c['N'],'a16d',read_bits=sb,node_cap=a['node_cap'],**kw)
    i=0
    try:
        for s,mk in zip(acts,pm[1:]):x.observe(s,rd(mk))
        while True:
            wd=x.propose()
            if wd is None:break
            for s in wd:
                if i>=len(ea) or ea[i]!=s:diffs.append(['word_differs',i]);raise StopIteration
                x.observe(s,rd(em[i]));i+=1
        rec=x.record();res=x.result()
    except StopIteration:return cid,False,diffs
    finally:x.close()
    if i!=len(ea):diffs.append(['trace_not_consumed',i,len(ea)])
    if list(rec['masks'])!=pm+em:diffs.append('masks')
    if dumps(res)!=dumps(a['api']):diffs.append('api_result')
    if a.get('node_cap') is not None and dumps([list(x) for x in rec.get('repins') or []])!=dumps(a['repins']):diffs.append('repins')
    if len(rec['rounds'])!=len(a['rounds']):diffs.append(['rounds',len(rec['rounds']),len(a['rounds'])])
    for j,(r1,r2) in enumerate(zip(rec['rounds'],a['rounds'])):
        for f in ('T','n_min','M1','s1','call_conflicts','call_capped','capped','check','word','probe','pred1','pred2','obs','call_chunks','chunk_conflicts'):
            if dumps(r1.get(f))!=dumps(r2.get(f)):diffs.append([j,f])
    return cid,not diffs,diffs


def fidelity(study,workers=6,block='main'):
    res=load(Path(study)/'RESULTS.json')
    todo=[(f"{c['key']}/{c['seed']}/{g}",c,g,a) for c in res['cases'] if c['block']==block for g,a in c['arms'].items() if a['label'] in ('ID','IDF')]
    rows=[]
    if todo:
        with ProcessPoolExecutor(workers,max_tasks_per_child=1) as ex:rows=list(ex.map(drive,todo))
    return {'study_results_sha256':sha(Path(study)/'RESULTS.json'),'decided_records':len(todo),'exact':sum(r[1] for r in rows),'workers':workers,
            'per_case':{r[0]:{'exact':r[1],'diffs':r[2]} for r in rows},'vacuous':not todo,'PASS':all(r[1] for r in rows)}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));ap.add_argument('--study')
    ap.add_argument('--block',default='main');ap.add_argument('--skip-xref',action='store_true');a=ap.parse_args(argv)
    out={'schema':'brute.api-checks.v61','certify32p_sha256':sha(ROOT/'brute/api/certify32p.py'),'compat':A47.compat(),'ghost':ghost(),'equiv':equiv()}
    out['xref']={'skipped':True,'PASS':None} if a.skip_xref else xref()
    if a.study:out['fidelity']=fidelity(a.study,block=a.block)
    out['PASS']=bool(out['compat']['PASS'] and out['ghost']['PASS64'] and out['equiv']['PASS'] and (a.skip_xref or out['xref']['PASS'])
                     and (out['fidelity']['PASS'] if a.study else True))
    write_new(Path(a.output),out);g=out['ghost']
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':g['PASS64'],'static':g['certify32p_static_ok'],'ast':g['certify32p_ast_scan']['PASS'],
                      'frozen_api_unchanged':g['frozen_api_unchanged'],'unpatched':g['a16d_max_bound_unpatched'],'net':g['no_network_run'],
                      'equiv':out['equiv']['PASS'],'smoke_identical':out['equiv']['smoke_world_identical'],
                      'xref':{k:v for k,v in out['xref'].items() if k in ('checks','disagreements','study063_match','PASS')},
                      'fidelity':{k:v for k,v in out.get('fidelity',{}).items() if k!='per_case'}}))
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
