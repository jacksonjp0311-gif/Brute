"""GHOST63 and GFID63 inputs for study-063 (BRUTE_PLAN_063; pre-run deviation #200). New file; built from scripts/api_checks_062.py
(frozen), whose _run_small(), ghost() and drive() logic is kept; the frozen api_checks_047 compat() and api_checks_046 closure/scan
are imported unchanged.
  compat:   api_checks_047.compat(), reported;
  ghost:    GHOST63: (1) static: every module in the import closure of brute.api.certify20p has no bad imports and no bad calls
            (api_checks_046.scan), and an AST scan of brute/api/certify20p.py finds no import of os, io, threading, subprocess,
            socket or multiprocessing and no call of open; (2) every brute/api file hashed in BRUTE_SOURCE_FREEZE_062 keeps its sha256,
            and certify16d.A16D_MAX_BOUND is still 20 after importing certify20p (no global patch); (3) a subprocess with socket
            disabled runs one full certify/20p loop (smoke seed 12630303, worlds_058 scale20, read_bits 2, bound 20, C 50000,
            B 2000000, K 400, node cap 200000) to any final label, 0 socket attempts;
  equiv:    certify/20p changes the pool, not the policy, so it is NOT expected to equal certify/20b record-for-record. On 18 small
            worlds (read_bits 2, 3, 4) it must (a) never give a wrong ID/IDF against the true machine (sound_vs_truth), (b) give the
            same n_min as the frozen certify/20b whenever both decide (agree_with_20b), (c) keep K accounting, (d) pin a first clique
            containing state 0; the one-shot certify20p is sound too; malformed node caps, read_bits and bounds are refused;
  fidelity: (GFID63, only with --study) every DECIDED (ID or IDF) record of block main is driven again in a fresh process through
            its own arm's API (B2: certify/20b; P2, P2b: certify/20p, node cap from the record) fed the recorded prefix and its own
            proposed words with readings from the recorded masks; api result, pins and every round minus wall fields must equal the
            record.
Writes <out> (default results/study-063/API_CHECKS_063.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_063.py [--study results/study-063/main] [--output PATH]"""
from __future__ import annotations
import argparse,ast,json,subprocess,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,dumps
from scripts import api_checks_047 as A47
from scripts import api_checks_046 as A46
from scripts.api_checks_059 import _small,_bits,WALL
OUT=ROOT/'results/study-063/API_CHECKS_063.json'
FZ62='experiments/BRUTE_SOURCE_FREEZE_062.json'
BAD_MODS=('os','io','threading','subprocess','socket','multiprocessing');BAD_CALLS=('open',)
DROP=('api','soundness')
NONET='''
import socket,json
hits=[]
def _no(*a,**k):hits.append(1);raise OSError('network disabled by api_checks_063')
socket.socket=_no;socket.create_connection=_no
from brute.api import certify20p as X
from experiments import worlds_058 as W
s=12630303;w=W.world(s,'scale20');acts=list(W.actions(s,0.0,w.k));q=w.start
c=X.Certifier20P(W.bits(w.emissions[q],2),w.k,20,'a16d',read_bits=2,K=400,max_chunks=None,conflict_cap=50000,budget_conflicts=2000000,
                 node_cap=200000,wall_guard_case_s=3600.0,hook=None,factory=X.counted16d)
def ob(a):
    global q
    q=w.transitions[q][a];c.observe(a,W.bits(w.emissions[q],2))
for a in acts:ob(a)
while True:
    x=c.propose()
    if x is None:break
    for a in x:ob(a)
r=c.result();c.close()
print(json.dumps({'loop':[r['api'],r['label'],r['n_min'],r['used'],r['conflicts'],r['read_bits'],r['family_bound'],r['clique_size'],r['repins']],'socket_attempts':len(hits)}))
'''


def ast_scan(path=ROOT/'brute/api/certify20p.py'):
    tree=ast.parse(Path(path).read_text());imps=set();calls=set()
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):imps|={a.name.split('.')[0] for a in n.names}
        elif isinstance(n,ast.ImportFrom):imps.add((n.module or '').split('.')[0])
        elif isinstance(n,ast.Call) and isinstance(n.func,ast.Name):calls.add(n.func.id)
    bad=sorted(imps&set(BAD_MODS));badc=sorted(calls&set(BAD_CALLS))
    return {'imports':sorted(imps),'bad_imports':bad,'bad_calls':badc,'PASS':not bad and not badc}


def ghost():
    cv=A46.closure('brute.api.certify20p');static_ok=all(not v['bad_imports'] and not v['bad_calls'] for v in cv.values())
    sc=ast_scan();fz=load(ROOT/FZ62)['sha256_files']
    shas={f:{'now':sha(ROOT/f),'frozen':d,'freeze':FZ62} for f,d in fz.items() if f.startswith('brute/api/')}
    sha_ok=bool(shas) and all(v['now']==v['frozen'] for v in shas.values())
    from brute.api import certify20p as _X  # noqa: F401
    from brute.api import certify16d as D;glob_ok=D.A16D_MAX_BOUND==20
    p=subprocess.run([sys.executable,'-c',NONET],cwd=ROOT,capture_output=True,text=True,timeout=1800,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:net=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):net={'error':p.stderr.strip()[-400:]}
    lp=net.get('loop',[None,None])
    net_ok=p.returncode==0 and net.get('socket_attempts')==0 and lp[0]=='brute.certify/20p' and lp[1] in ('ID','IDF','IDU','AMB')
    out={'certify20p_closure':cv,'certify20p_static_ok':static_ok,'certify20p_ast_scan':sc,'frozen_api_sha256':shas,'frozen_api_unchanged':sha_ok,
         'a16d_max_bound_unpatched':glob_ok,'no_network_run':net,'no_network_returncode':p.returncode,'socket_attempts':net.get('socket_attempts'),
         'network_pass':net_ok}
    out['PASS63']=bool(static_ok and sc['PASS'] and net_ok and sha_ok and glob_ok);return out


def _rm_walls(x):
    if isinstance(x,dict):return {k:_rm_walls(v) for k,v in x.items() if k not in WALL and k not in ('wall','case_wall','chunk_wall_max')}
    if isinstance(x,list):return [_rm_walls(v) for v in x]
    return x


def _run_small(make,T,em,seed,sb):
    import random
    r=random.Random(seed+1);acts=[r.randrange(3) for _ in range(40)];q=0;words=[]
    c=make(_bits(em[q],sb))
    try:
        for a in acts:q=T[q][a];c.observe(a,_bits(em[q],sb))
        while True:
            x=c.propose()
            if x is None:break
            words.append(list(x))
            for a in x:q=T[q][a];c.observe(a,_bits(em[q],sb))
        R=c.record();res=dict(c.result())
    finally:c.close()
    from brute.evaluation import no_time
    for f in DROP:res.pop(f,None)
    return no_time(_rm_walls({'res':res,'masks':R['masks'],'acts':R['acts'],'used':R['used'],'stop':R['stop'],'rounds':R['rounds'],
                              'final':R['final'],'repins':R.get('repins'),'final_clique':R.get('final_clique')})),words,q


def beq(d1,e1,s1,d2,e2,s2):
    """Bisimulation from (s1, s2): same emission codes along every pair reachable by the 3 actions."""
    seen={(s1,s2)};st=[(s1,s2)]
    while st:
        p,q=st.pop()
        if e1[p]!=e2[q]:return False
        for a in range(3):
            x=(d1[p][a],d2[q][a])
            if x not in seen:seen.add(x);st.append(x)
    return True


def _sound(stop,final,T,em,q):
    if stop=='ID':return beq(final['model'][0],final['model'][1],0,T,em,0)
    if stop=='IDF':return beq(final['model'][0],final['model'][1],final['s1'],T,em,q)
    return True


def equiv():
    import random
    from brute.api import certify20b as B,certify20p as X
    from brute.evaluation import no_time
    kw=dict(K=60,conflict_cap=5000,budget_conflicts=200000);rows=[]
    for sb in (2,3,4):
        for s in range(6):
            sd=6300+10*sb+s;n=3+s%4;T,em=_small(sd,n,sb)
            a,wa,qa=_run_small(lambda ini:B.Certifier20B(ini,3,n+1,'a16d',read_bits=sb,**kw),T,em,sd,sb)
            d,wd,qd=_run_small(lambda ini:X.Certifier20P(ini,3,n+1,'a16d',read_bits=sb,**kw),T,em,sd,sb)
            both=a['stop'] in ('ID','IDF') and d['stop'] in ('ID','IDF')
            r=random.Random(sd+2);acts=[r.randrange(3) for _ in range(30)];q=0;obs=[]
            for x in acts:q=T[q][x];obs.append(_bits(em[q],sb))
            o2=X.certify20p(_bits(em[0],sb),acts,obs,3,n+1,read_bits=sb,conflict_cap=5000,budget_conflicts=200000)
            o2f={'model':o2.get('model'),'s1':o2.get('s1')}
            rows.append({'read_bits':sb,'seed':sd,'n':n,'label_20b':a['res']['label'],'label_20p':d['res']['label'],'stop_20b':a['stop'],'stop_20p':d['stop'],
                         'sound_20p':_sound(d['stop'],d['final'],T,em,qd),'sound_20b':_sound(a['stop'],a['final'],T,em,qa),
                         'both_decided':both,'n_min_equal':(a['res']['n_min']==d['res']['n_min']) if both else None,
                         'k_ok':d['used']==sum(len(w) for w in wd)<=60,'first_pin_ok':bool(d['repins']) and d['repins'][0][1] is None and d['final_clique'][:1]==[0],
                         'pins':len(d['repins'] or []),'oneshot_api':o2['api']==X.API,
                         'oneshot_sound':_sound(o2.get('stop') or o2.get('label'),o2f,T,em,q) if o2f['model'] is not None else True})
    ref=[]
    for nc,k2 in ((0,{}),(-1,{}),(True,{}),(1.5,{}),('5',{}),(None,{}),(200000,{'read_bits':5}),(200000,{'family_bound':21}),(200000,{'family_bound':0})):
        kk={'read_bits':2,'family_bound':20,**k2}
        try:X.Certifier20P((0,1),3,kk.pop('family_bound'),conflict_cap=10,budget_conflicts=10,node_cap=nc,**kk).close();ref.append([repr(nc),str(k2),'ACCEPTED'])
        except (ValueError,TypeError):ref.append([repr(nc),str(k2),'refused'])
    dec=sum(r['stop_20p'] in ('ID','IDF') for r in rows);both=[r for r in rows if r['both_decided']]
    return {'cases':rows,'refusals':ref,'decided_20p':dec,'agree_with_20b':[sum(r['n_min_equal'] for r in both),len(both)],
            'sound_vs_truth':[sum(r['sound_20p'] for r in rows),len(rows)],
            'PASS':all(r['sound_20p'] and r['sound_20b'] and r['k_ok'] and r['first_pin_ok'] and r['oneshot_api'] and r['oneshot_sound'] for r in rows)
                   and all(r['n_min_equal'] for r in both) and dec>0 and all(x[2]=='refused' for x in ref)}


def drive(arg):
    cid,c,arm,a=arg
    from brute.api.certify20b import Certifier20B,counted16d
    from brute.api.certify20p import Certifier20P
    from experiments import worlds_058 as W
    from brute.scalesearch4 import SOLVER4
    sb=a['read_bits'];pm=list(a['prefix_masks']);em=list(a['extra_masks']);ea=list(a['extra_acts']);diffs=[]
    acts=list(W.actions(c['seed'],0.0,c['k']));rd=lambda mk:W.bits(mk.bit_length()-1,sb)
    kw=dict(max_chunks=a['max_chunks'],K=a['K'],conflict_cap=a['conflict_cap'],budget_conflicts=a['budget_conflicts'],hook=None,
            factory=counted16d,wall_guard_case_s=a['hard_kill_s'],wall_guard_call_s=30.0,solver=SOLVER4)
    if a.get('node_cap') is not None:x=Certifier20P(rd(pm[0]),c['k'],c['N'],'a16d',read_bits=sb,node_cap=a['node_cap'],**kw)
    else:x=Certifier20B(rd(pm[0]),c['k'],c['N'],'a16d',read_bits=sb,**kw)
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
    out={'schema':'brute.api-checks.v60','certify20p_sha256':sha(ROOT/'brute/api/certify20p.py'),'compat':A47.compat(),'ghost':ghost(),'equiv':equiv()}
    if a.study:out['fidelity']=fidelity(a.study,block=a.block)
    out['PASS']=out['compat']['PASS'] and out['ghost']['PASS63'] and out['equiv']['PASS'] and (out['fidelity']['PASS'] if a.study else True)
    write_new(Path(a.output),out);g=out['ghost']
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':g['PASS63'],'static':g['certify20p_static_ok'],'ast':g['certify20p_ast_scan']['PASS'],
                      'frozen_api_unchanged':g['frozen_api_unchanged'],'unpatched':g['a16d_max_bound_unpatched'],'net':g['no_network_run'],
                      'equiv':out['equiv']['PASS'],'fidelity':{k:v for k,v in out.get('fidelity',{}).items() if k!='per_case'}}))
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
