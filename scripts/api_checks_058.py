"""GHOST58 and GFID58 inputs for study-058 (BRUTE_PLAN_058; pre-run deviation #190). New file; built from scripts/api_checks_057.py
(frozen), with the frozen api_checks_047 compat() and api_checks_046 closure/scan imported unchanged.
  compat:   api_checks_047.compat() (certify/16 and certify/14 test modules, 046 compat sample byte for byte), reported;
  ghost:    GHOST58: (1) static: every module in the import closure of brute.api.certify20b has no bad imports and no bad calls
            (api_checks_046.scan: no I/O, threads, subprocess, os or socket); (2) the frozen certify14 / 16 / 16d / 16e files keep the
            sha256 of their freezes; (3) a subprocess with socket disabled runs one full certify/20b loop (smoke seed 12550003,
            scale20r4, read_bits 4, bound 20, C 50000, B 2000000, K 400, conflict-only stop) to any final label, 0 socket attempts;
  equiv:    certify/20b read_bits 2 vs certify/16e on 6 seeded small worlds (3-6 states, 40-step prefix, K 60, C 5000, B 200000):
            api result, masks, acts and every round minus wall fields must be equal; plus 8 malformed inputs that must be refused;
  fidelity: (GFID58, only with --study) every DECIDED (ID or IDF) record of block main is driven again in a fresh process: certify/20b
            fed the recorded prefix and then its own proposed words, readings taken from the recorded masks; the api result
            (canonical JSON) and every round minus wall fields must equal the record byte for byte, and the trace must be consumed.
Writes <out> (default results/study-058/API_CHECKS_058.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_058.py [--study results/study-058/main] [--output PATH]"""
from __future__ import annotations
import argparse,json,random,subprocess,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,dumps
from scripts import api_checks_047 as A47
from scripts import api_checks_046 as A46
OUT=ROOT/'results/study-058/API_CHECKS_058.json'
FROZEN={'brute/api/certify14.py':'experiments/BRUTE_SOURCE_FREEZE_047.json','brute/api/certify16.py':'experiments/BRUTE_SOURCE_FREEZE_047.json',
        'brute/api/certify16d.py':'experiments/BRUTE_SOURCE_FREEZE_047.json','brute/api/certify16e.py':'experiments/BRUTE_SOURCE_FREEZE_049.json'}
WALL=('query_walls','chunk_walls')
NONET='''
import socket,json
hits=[]
def _no(*a,**k):hits.append(1);raise OSError('network disabled by api_checks_058')
socket.socket=_no;socket.create_connection=_no
from brute.api import certify20b as B
from experiments import worlds_058 as W
s=12550003;w=W.world(s,'scale20r4');acts=list(W.actions(s,0.0,w.k));q=w.start;rd=[W.bits(w.emissions[q],4)]
for a in acts:q=w.transitions[q][a];rd.append(W.bits(w.emissions[q],4))
c=B.Certifier20B(rd[0],w.k,20,'a16d',read_bits=4,K=400,max_chunks=None,conflict_cap=50000,budget_conflicts=2000000,wall_guard_case_s=900.0,hook=None,factory=B.counted16d)
for a,o in zip(acts,rd[1:]):c.observe(a,o)
while True:
    x=c.propose()
    if x is None:break
    for a in x:q=w.transitions[q][a];c.observe(a,W.bits(w.emissions[q],4))
r=c.result();c.close()
print(json.dumps({'loop':[r['api'],r['label'],r['n_min'],r['used'],r['conflicts'],r['read_bits']],'socket_attempts':len(hits)}))
'''


def ghost():
    cv=A46.closure('brute.api.certify20b');static_ok=all(not v['bad_imports'] and not v['bad_calls'] for v in cv.values())
    shas={f:{'now':sha(ROOT/f),'frozen':load(ROOT/fz)['sha256_files'].get(f),'freeze':fz} for f,fz in FROZEN.items()}
    sha_ok=all(v['now']==v['frozen'] for v in shas.values())
    p=subprocess.run([sys.executable,'-c',NONET],cwd=ROOT,capture_output=True,text=True,timeout=1200,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:net=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):net={'error':p.stderr.strip()[-400:]}
    lp=net.get('loop',[None,None])
    net_ok=p.returncode==0 and net.get('socket_attempts')==0 and lp[0]=='brute.certify/20b' and lp[1] in ('ID','IDF','IDU','AMB')
    out={'certify20b_closure':cv,'certify20b_static_ok':static_ok,'frozen_api_sha256':shas,'frozen_api_unchanged':sha_ok,
         'no_network_run':net,'no_network_returncode':p.returncode,'socket_attempts':net.get('socket_attempts'),'network_pass':net_ok}
    out['PASS58']=bool(static_ok and net_ok and sha_ok);return out


def _small(seed,n,sb):
    r=random.Random(seed);T=[[r.randrange(n) for _ in range(3)] for _ in range(n)];em=[r.randrange(1<<sb) for _ in range(n)];return T,em


def _run_small(cls,T,em,seed,n,sb,extra):
    from experiments.worlds_058 import bits
    r=random.Random(seed+1);acts=[r.randrange(3) for _ in range(40)];q=0;rd=[bits(em[q],sb)]
    for a in acts:q=T[q][a];rd.append(bits(em[q],sb))
    c=cls(rd[0],3,n+1,'a16d',K=60,conflict_cap=5000,budget_conflicts=200000,**extra)
    try:
        for a,o in zip(acts,rd[1:]):c.observe(a,o)
        while True:
            x=c.propose()
            if x is None:break
            for a in x:q=T[q][a];c.observe(a,bits(em[q],sb))
        R=c.record();res=dict(c.result())
    finally:c.close()
    res.pop('api',None);res.pop('soundness',None);res.pop('read_bits',None)
    return {'res':res,'masks':R['masks'],'acts':R['acts'],'rounds':[{k:v for k,v in x.items() if k not in WALL} for x in R['rounds']]}


def equiv():
    from brute.api import certify16e as E,certify20b as B
    rows=[]
    for s in range(6):
        n=3+s%4;T,em=_small(5800+s,n,2)
        a=_run_small(E.Certifier16E,T,em,5800+s,n,2,{});b=_run_small(B.Certifier20B,T,em,5800+s,n,2,{'read_bits':2})
        rows.append({'seed':5800+s,'n':n,'label':a['res']['label'],'equal':dumps(a)==dumps(b)})
    bad=[((0,0,0),{'read_bits':2}),((0,1),{'read_bits':3}),((0,2,0),{'read_bits':3}),((True,0),{'read_bits':2}),
         ((0,0),{'read_bits':5}),((0,0),{'read_bits':1}),((0,0),{'read_bits':True}),([0,0,0,0,0],{'read_bits':4})]
    ref=[]
    for ini,kw in bad:
        try:B.Certifier20B(ini,3,4,'a16d',conflict_cap=10,budget_conflicts=10,**kw);ref.append([str(ini),str(kw),'ACCEPTED'])
        except ValueError:ref.append([str(ini),str(kw),'refused'])
    c=B.Certifier20B((0,1,0),3,4,'a16d',read_bits=3,conflict_cap=10,budget_conflicts=10)
    for o in ((0,1),(0,1,2),(0,1,0,1)):
        try:c.observe(0,o);ref.append(['observe',str(o),'ACCEPTED'])
        except ValueError:ref.append(['observe',str(o),'refused'])
    c.close()
    return {'cases':rows,'refusals':ref,'PASS':all(r['equal'] for r in rows) and all(x[2]=='refused' for x in ref)}


def drive(arg):
    cid,c,arm,a=arg
    from brute.api.certify20b import Certifier20B,counted16d
    from experiments.worlds_058 import bits
    from experiments.brute_common_058 import GUARD_CALL_S
    from brute.scalesearch4 import SOLVER4
    sb=a['read_bits'];pm=list(a['prefix_masks']);em=list(a['extra_masks']);ea=list(a['extra_acts']);diffs=[]
    from experiments import worlds_058 as W
    acts=list(W.actions(c['seed'],0.0,c['k']));rd=lambda mk:bits(mk.bit_length()-1,sb)
    kw=dict(max_chunks=a['max_chunks'],K=a['K'],conflict_cap=a['conflict_cap'],budget_conflicts=a['budget_conflicts'],hook=None,
            factory=counted16d,wall_guard_case_s=a['hard_kill_s'],wall_guard_call_s=GUARD_CALL_S,solver=SOLVER4)
    x=Certifier20B(rd(pm[0]),c['k'],c['N'],'a16d',read_bits=sb,**kw);i=0
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
    if dumps(res)!=dumps(a['api']):diffs.append('api_result')
    if len(rec['rounds'])!=len(a['rounds']):diffs.append(['rounds',len(rec['rounds']),len(a['rounds'])])
    for j,(r1,r2) in enumerate(zip(rec['rounds'],a['rounds'])):
        for f in ('T','n_min','M1','s1','call_conflicts','call_capped','capped','check','word','pred1','pred2','obs','call_chunks','chunk_conflicts'):
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
    ap.add_argument('--block',default='main');ap.add_argument('--ghost-only',action='store_true');a=ap.parse_args(argv)
    out={'schema':'brute.api-checks.v55','certify20b_sha256':sha(ROOT/'brute/api/certify20b.py'),'compat':A47.compat(),'ghost':ghost(),'equiv':equiv()}
    if a.study:out['fidelity']=fidelity(a.study,block=a.block)
    out['PASS']=out['compat']['PASS'] and out['ghost']['PASS58'] and out['equiv']['PASS'] and (out['fidelity']['PASS'] if a.study else True)
    write_new(Path(a.output),out);g=out['ghost']
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':g['PASS58'],'static':g['certify20b_static_ok'],'frozen_api_unchanged':g['frozen_api_unchanged'],
                      'net':g['no_network_run'],'equiv':out['equiv']['PASS'],'fidelity':{k:v for k,v in out.get('fidelity',{}).items() if k!='per_case'}}))
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
