"""GHOST62 and GFID62 inputs for study-062 (BRUTE_PLAN_062; pre-run deviation #198). New file; built from scripts/api_checks_060.py
and api_checks_061.py (frozen), whose _run_small() and drive() logic is kept; the frozen api_checks_047 compat() and api_checks_046
closure/scan are imported unchanged.
  compat:   api_checks_047.compat(), reported;
  ghost:    GHOST62: (1) static: every module in the import closure of brute.api.certify20w has no bad imports and no bad calls
            (api_checks_046.scan), and an AST scan of brute/api/certify20w.py finds no import of os, io, threading, subprocess,
            socket or multiprocessing and no call of open; (2) every brute/api file hashed in BRUTE_SOURCE_FREEZE_061 keeps its sha256,
            and certify16d.A16D_MAX_BOUND is still 20 after importing certify20w (no global patch); (3) a subprocess with socket
            disabled runs one full certify/20w loop (smoke seed 12620303, worlds_058 scale20, read_bits 2, bound 20, C 50000,
            B 2000000, K 400) to any final label, 0 socket attempts;
  equiv:    certify/20w with probe_word=() equals the frozen certify/20b record-for-record (masks, actions, every round minus wall
            fields, result minus api / probe_word / soundness / walls) on 18 small worlds (read_bits 2, 3, 4), one-shot equal;
            the default probe word is appended after every proposed word on those worlds; malformed probe words, read_bits and
            bounds are refused;
  fidelity: (GFID62, only with --study) every DECIDED (ID or IDF) record of block main is driven again in a fresh process through
            its own arm's API (B2: certify/20b; W2, W2b: certify/20w, probe (0, 1)) fed the recorded prefix and its own proposed
            words with readings from the recorded masks; api result and every round minus wall fields must equal the record.
Writes <out> (default results/study-062/API_CHECKS_062.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_062.py [--study results/study-062/main] [--output PATH]"""
from __future__ import annotations
import argparse,ast,json,subprocess,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,dumps
from scripts import api_checks_047 as A47
from scripts import api_checks_046 as A46
from scripts.api_checks_059 import _small,_bits,WALL
OUT=ROOT/'results/study-062/API_CHECKS_062.json'
FZ61='experiments/BRUTE_SOURCE_FREEZE_061.json'
BAD_MODS=('os','io','threading','subprocess','socket','multiprocessing');BAD_CALLS=('open',)
DROP=('api','soundness','probe_word')
NONET='''
import socket,json
hits=[]
def _no(*a,**k):hits.append(1);raise OSError('network disabled by api_checks_062')
socket.socket=_no;socket.create_connection=_no
from brute.api import certify20w as X
from experiments import worlds_058 as W
s=12620303;w=W.world(s,'scale20');acts=list(W.actions(s,0.0,w.k));q=w.start
c=X.Certifier20W(W.bits(w.emissions[q],2),w.k,20,'a16d',read_bits=2,K=400,max_chunks=None,conflict_cap=50000,budget_conflicts=2000000,
                 wall_guard_case_s=3600.0,hook=None,factory=X.counted16d)
def ob(a):
    global q
    q=w.transitions[q][a];c.observe(a,W.bits(w.emissions[q],2))
for a in acts:ob(a)
while True:
    x=c.propose()
    if x is None:break
    for a in x:ob(a)
r=c.result();c.close()
print(json.dumps({'loop':[r['api'],r['label'],r['n_min'],r['used'],r['conflicts'],r['read_bits'],r['family_bound'],r['probe_word']],'socket_attempts':len(hits)}))
'''


def ast_scan(path=ROOT/'brute/api/certify20w.py'):
    tree=ast.parse(Path(path).read_text());imps=set();calls=set()
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):imps|={a.name.split('.')[0] for a in n.names}
        elif isinstance(n,ast.ImportFrom):imps.add((n.module or '').split('.')[0])
        elif isinstance(n,ast.Call) and isinstance(n.func,ast.Name):calls.add(n.func.id)
    bad=sorted(imps&set(BAD_MODS));badc=sorted(calls&set(BAD_CALLS))
    return {'imports':sorted(imps),'bad_imports':bad,'bad_calls':badc,'PASS':not bad and not badc}


def ghost():
    cv=A46.closure('brute.api.certify20w');static_ok=all(not v['bad_imports'] and not v['bad_calls'] for v in cv.values())
    sc=ast_scan();fz=load(ROOT/FZ61)['sha256_files']
    shas={f:{'now':sha(ROOT/f),'frozen':d,'freeze':FZ61} for f,d in fz.items() if f.startswith('brute/api/')}
    sha_ok=bool(shas) and all(v['now']==v['frozen'] for v in shas.values())
    from brute.api import certify20w as _X  # noqa: F401
    from brute.api import certify16d as D;glob_ok=D.A16D_MAX_BOUND==20
    p=subprocess.run([sys.executable,'-c',NONET],cwd=ROOT,capture_output=True,text=True,timeout=1800,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:net=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):net={'error':p.stderr.strip()[-400:]}
    lp=net.get('loop',[None,None])
    net_ok=p.returncode==0 and net.get('socket_attempts')==0 and lp[0]=='brute.certify/20w' and lp[1] in ('ID','IDF','IDU','AMB')
    out={'certify20w_closure':cv,'certify20w_static_ok':static_ok,'certify20w_ast_scan':sc,'frozen_api_sha256':shas,'frozen_api_unchanged':sha_ok,
         'a16d_max_bound_unpatched':glob_ok,'no_network_run':net,'no_network_returncode':p.returncode,'socket_attempts':net.get('socket_attempts'),
         'network_pass':net_ok}
    out['PASS62']=bool(static_ok and sc['PASS'] and net_ok and sha_ok and glob_ok);return out


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
    return no_time(_rm_walls({'res':res,'masks':R['masks'],'acts':R['acts'],'used':R['used'],'stop':R['stop'],'rounds':R['rounds']})),words


def equiv():
    import random
    from brute.api import certify20b as B,certify20w as X
    from brute.evaluation import no_time
    kw=dict(K=60,conflict_cap=5000,budget_conflicts=200000);rows=[];win=[]
    for sb in (2,3,4):
        for s in range(6):
            sd=6200+10*sb+s;n=3+s%4;T,em=_small(sd,n,sb)
            a,wa=_run_small(lambda ini:B.Certifier20B(ini,3,n+1,'a16d',read_bits=sb,**kw),T,em,sd,sb)
            b,wb=_run_small(lambda ini:X.Certifier20W(ini,3,n+1,'a16d',read_bits=sb,probe_word=(),**kw),T,em,sd,sb)
            d,wd=_run_small(lambda ini:X.Certifier20W(ini,3,n+1,'a16d',read_bits=sb,**kw),T,em,sd,sb)
            rr=[x for x in d['rounds'] if x.get('obs') is not None]
            wok=len(rr)==len(wd) and all(w==list(x['word'])+list(x.get('probe',[])) and list(x.get('probe',[]))==[0,1][:len(x.get('probe',[]))] for x,w in zip(rr,wd)) and d['used']<=60
            r=random.Random(sd+2);acts=[r.randrange(3) for _ in range(30)];q=0;obs=[]
            for x in acts:q=T[q][x];obs.append(_bits(em[q],sb))
            o1=B.certify20b(_bits(em[0],sb),acts,obs,3,n+1,read_bits=sb,conflict_cap=5000,budget_conflicts=200000)
            o2=X.certify20w(_bits(em[0],sb),acts,obs,3,n+1,read_bits=sb,conflict_cap=5000,budget_conflicts=200000)
            s1={k:v for k,v in no_time(_rm_walls(o1)).items() if k not in DROP};s2={k:v for k,v in no_time(_rm_walls(o2)).items() if k not in DROP}
            rows.append({'read_bits':sb,'seed':sd,'n':n,'label_20b':a['res']['label'],'label_20w':d['res']['label'],'empty_probe_equal':dumps(a)==dumps(b) and wa==wb,
                         'window_rule_ok':wok,'windows_appended':sum(bool(x.get('probe')) for x in rr),
                         'oneshot_equal':dumps(s1)==dumps(s2) and o2['api']==X.API})
    ref=[]
    for p,k2 in (((3,),{}),((0,-1),{}),(('0',),{}),((True,),{}),('01',{}),(None,{}),(0,{}),((0.0,),{}),((0,1),{'read_bits':5}),((0,1),{'family_bound':21}),((0,1),{'family_bound':0})):
        kk={'read_bits':2,'family_bound':20,**k2}
        try:X.Certifier20W((0,1),3,kk.pop('family_bound'),conflict_cap=10,budget_conflicts=10,probe_word=p,**kk).close();ref.append([repr(p),str(k2),'ACCEPTED'])
        except (ValueError,TypeError):ref.append([repr(p),str(k2),'refused'])
    return {'cases':rows,'refusals':ref,'windows_appended_total':sum(r['windows_appended'] for r in rows),
            'PASS':all(r['empty_probe_equal'] and r['oneshot_equal'] and r['window_rule_ok'] for r in rows) and all(x[2]=='refused' for x in ref)
                   and sum(r['windows_appended'] for r in rows)>0}


def drive(arg):
    cid,c,arm,a=arg
    from brute.api.certify20b import Certifier20B,counted16d
    from brute.api.certify20w import Certifier20W
    from experiments import worlds_058 as W
    from brute.scalesearch4 import SOLVER4
    sb=a['read_bits'];pm=list(a['prefix_masks']);em=list(a['extra_masks']);ea=list(a['extra_acts']);diffs=[]
    acts=list(W.actions(c['seed'],0.0,c['k']));rd=lambda mk:W.bits(mk.bit_length()-1,sb)
    kw=dict(max_chunks=a['max_chunks'],K=a['K'],conflict_cap=a['conflict_cap'],budget_conflicts=a['budget_conflicts'],hook=None,
            factory=counted16d,wall_guard_case_s=a['hard_kill_s'],wall_guard_call_s=30.0,solver=SOLVER4)
    if a['probe_word']:x=Certifier20W(rd(pm[0]),c['k'],c['N'],'a16d',read_bits=sb,probe_word=tuple(a['probe_word']),**kw)
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
    out={'schema':'brute.api-checks.v59','certify20w_sha256':sha(ROOT/'brute/api/certify20w.py'),'compat':A47.compat(),'ghost':ghost(),'equiv':equiv()}
    if a.study:out['fidelity']=fidelity(a.study,block=a.block)
    out['PASS']=out['compat']['PASS'] and out['ghost']['PASS62'] and out['equiv']['PASS'] and (out['fidelity']['PASS'] if a.study else True)
    write_new(Path(a.output),out);g=out['ghost']
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':g['PASS62'],'static':g['certify20w_static_ok'],'ast':g['certify20w_ast_scan']['PASS'],
                      'frozen_api_unchanged':g['frozen_api_unchanged'],'unpatched':g['a16d_max_bound_unpatched'],'net':g['no_network_run'],
                      'equiv':out['equiv']['PASS'],'fidelity':{k:v for k,v in out.get('fidelity',{}).items() if k!='per_case'}}))
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
