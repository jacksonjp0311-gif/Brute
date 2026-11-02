"""GHOST59 and GFID59 inputs for study-059 (BRUTE_PLAN_059; pre-run deviation #192). New file; built from scripts/api_checks_058.py
(frozen), with the frozen api_checks_047 compat() and api_checks_046 closure/scan imported unchanged.
  compat:   api_checks_047.compat(), reported;
  ghost:    GHOST59: (1) static: every module in the import closure of brute.api.certify20n has no bad imports and no bad calls
            (api_checks_046.scan); (2) the frozen certify14 / 16 / 16d / 16e / 16n / 20b files keep the sha256 of their freezes;
            (3) a subprocess with socket disabled runs one full certify/20n loop (smoke seed 12590053, scale20r4, read_bits 4, eps 0.10,
            eps_bar 0.15, delta 0.001, bound 20, C 50000, B 2000000, K 400) to any final label, 0 socket attempts;
  equiv:    (a) certify/20n reads=1 vs certify/20b on noise-free readings, 6 seeded small worlds per read_bits 2, 3, 4 (3-6 states,
            40-step prefix, K 60, C 5000, B 200000): api result minus the 20n-only fields, masks, acts and every round minus wall fields
            equal; (b) certify/20n read_bits 2 vs certify/16n (anytime k, eps_bar 0.10, delta 0.001) fed the same noisy reads
            (eps 0.05) on 6 small worlds: as (a) plus reads_per_obs and votes; (c) malformed inputs that must be refused;
  fidelity: (GFID59, only with --study) every DECIDED (ID or IDF) record of block main is driven again in a fresh process through the
            public interface: C4 by certify/20b fed the recorded prefix and its own proposed words with readings from the recorded masks;
            noisy arms by certify/20n with the reads regenerated from the true world and worlds_059.Noise (seeded) for the record's
            eps and eps_bar. The api result (canonical JSON, minus 'reads_total' type-equal) and every round minus wall fields must equal
            the record, the extra actions must match and, for noisy arms, the majority masks must equal the recorded masks.
Writes <out> (default results/study-059/API_CHECKS_059.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_059.py [--study results/study-059/main] [--output PATH]"""
from __future__ import annotations
import argparse,json,random,subprocess,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,dumps
from scripts import api_checks_047 as A47
from scripts import api_checks_046 as A46
OUT=ROOT/'results/study-059/API_CHECKS_059.json'
FZ58='experiments/BRUTE_SOURCE_FREEZE_058.json'
FROZEN={f:FZ58 for f in ('brute/api/certify14.py','brute/api/certify16.py','brute/api/certify16d.py','brute/api/certify16e.py',
                         'brute/api/certify16n.py','brute/api/certify20b.py')}
WALL=('query_walls','chunk_walls')
ONLY20N=('api','inner_api','soundness','read_bits','eps_bar','delta','reads','observations','reads_total','reads_max')
NONET='''
import socket,json
hits=[]
def _no(*a,**k):hits.append(1);raise OSError('network disabled by api_checks_059')
socket.socket=_no;socket.create_connection=_no
from brute.api import certify20n as N,certify20b as B
from experiments import worlds_059 as W
s=12590053;w=W.world(s);acts=list(W.actions(s,0.0,w.k));q=w.start;nz=W.Noise(s,0.10)
c=N.Certifier20N(nz.reads(W.bits(w.emissions[q]),N.reads_for(1,0.15,0.001,4)),w.k,20,read_bits=4,eps_bar=0.15,delta=0.001,K=400,max_chunks=None,
                 conflict_cap=50000,budget_conflicts=2000000,wall_guard_case_s=900.0,hook=None,factory=B.counted16d)
def ob(a):
    global q
    q=w.transitions[q][a];c.observe(a,nz.reads(W.bits(w.emissions[q]),c.reads_needed()))
for a in acts:ob(a)
while True:
    x=c.propose()
    if x is None:break
    for a in x:ob(a)
r=c.result();c.close()
print(json.dumps({'loop':[r['api'],r['label'],r['n_min'],r['used'],r['conflicts'],r['read_bits'],r['reads_total']],'socket_attempts':len(hits)}))
'''


def ghost():
    cv=A46.closure('brute.api.certify20n');static_ok=all(not v['bad_imports'] and not v['bad_calls'] for v in cv.values())
    shas={f:{'now':sha(ROOT/f),'frozen':load(ROOT/fz)['sha256_files'].get(f),'freeze':fz} for f,fz in FROZEN.items()}
    sha_ok=all(v['now']==v['frozen'] for v in shas.values())
    p=subprocess.run([sys.executable,'-c',NONET],cwd=ROOT,capture_output=True,text=True,timeout=1200,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:net=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):net={'error':p.stderr.strip()[-400:]}
    lp=net.get('loop',[None,None])
    net_ok=p.returncode==0 and net.get('socket_attempts')==0 and lp[0]=='brute.certify/20n' and lp[1] in ('ID','IDF','IDU','AMB')
    out={'certify20n_closure':cv,'certify20n_static_ok':static_ok,'frozen_api_sha256':shas,'frozen_api_unchanged':sha_ok,
         'no_network_run':net,'no_network_returncode':p.returncode,'socket_attempts':net.get('socket_attempts'),'network_pass':net_ok}
    out['PASS59']=bool(static_ok and net_ok and sha_ok);return out


def _small(seed,n,sb):
    r=random.Random(seed);T=[[r.randrange(n) for _ in range(3)] for _ in range(n)];em=[r.randrange(1<<sb) for _ in range(n)];return T,em


def _bits(c,sb):return tuple((c>>(sb-1-j))&1 for j in range(sb))


def _run_small(make,T,em,seed,n,sb,feed):
    """make(first) -> certifier; feed(c, clean) -> what observe() gets; returns comparable parts."""
    r=random.Random(seed+1);acts=[r.randrange(3) for _ in range(40)];q=0
    c=make(_bits(em[q],sb))
    try:
        for a in acts:q=T[q][a];c.observe(a,feed(c,_bits(em[q],sb)))
        while True:
            x=c.propose()
            if x is None:break
            for a in x:q=T[q][a];c.observe(a,feed(c,_bits(em[q],sb)))
        R=c.record();res=dict(c.result())
    finally:c.close()
    for f in ONLY20N:res.pop(f,None)
    out={'res':res,'masks':R['masks'],'acts':R['acts'],'rounds':[{k:v for k,v in x.items() if k not in WALL} for x in R['rounds']]}
    for f in ('reads_per_obs','votes'):
        if f in R:out[f]=R[f]
    return out


def equiv():
    from brute.api import certify16n as N16,certify20b as B,certify20n as N
    from experiments.worlds_059 import Noise
    kw=dict(K=60,conflict_cap=5000,budget_conflicts=200000);rows=[]
    for sb in (2,3,4):
        for s in range(6):
            sd=5900+10*sb+s;n=3+s%4;T,em=_small(sd,n,sb)
            a=_run_small(lambda ini:B.Certifier20B(ini,3,n+1,'a16d',read_bits=sb,**kw),T,em,sd,n,sb,lambda c,x:x)
            b=_run_small(lambda ini:N.Certifier20N([ini],3,n+1,read_bits=sb,eps_bar=0.10,delta=0.001,reads=1,**kw),T,em,sd,n,sb,lambda c,x:[x])
            b.pop('reads_per_obs',None);b.pop('votes',None)
            rows.append({'part':'a','read_bits':sb,'seed':sd,'n':n,'label':a['res']['label'],'equal':dumps(a)==dumps(b)})
    for s in range(6):
        sd=5990+s;n=3+s%4;T,em=_small(sd,n,2);r=[]
        for cls in ('16n','20n'):
            nz=Noise(sd,0.05);feed=lambda c,x,nz=nz:nz.reads(x,c.reads_needed())
            if cls=='16n':mk=lambda ini,nz=nz:N16.Certifier16N(nz.reads(ini,N16.reads_for(1,0.10,0.001)),3,n+1,eps_bar=0.10,delta=0.001,**kw)
            else:mk=lambda ini,nz=nz:N.Certifier20N(nz.reads(ini,N.reads_for(1,0.10,0.001,2)),3,n+1,read_bits=2,eps_bar=0.10,delta=0.001,**kw)
            r.append(_run_small(mk,T,em,sd,n,2,feed))
        rows.append({'part':'b','read_bits':2,'seed':sd,'n':n,'label':r[0]['res']['label'],'equal':dumps(r[0])==dumps(r[1])})
    bad=[([(0,0,0,0)]*2,{}),([(0,0,0)]*37,{}),([(0,2,0,0)]*37,{}),([(True,0,0,0)]*37,{}),((0,0,0,0),{}),
         ([(0,0,0,0)],{'read_bits':5,'reads':1}),([(0,0,0,0)],{'read_bits':True,'reads':1}),([(0,0,0,0)],{'eps_bar':0.0,'reads':1}),
         ([(0,0,0,0)],{'eps_bar':0.5,'reads':1}),([(0,0,0,0)],{'eps_bar':True,'reads':1}),([(0,0,0,0)]*2,{'reads':2}),
         ([(0,0,0,0)],{'delta':0,'reads':1})]
    ref=[]
    for ini,k2 in bad:
        kk={'read_bits':4,'eps_bar':0.15,**k2}
        try:N.Certifier20N(ini,3,4,conflict_cap=10,budget_conflicts=10,**kk).close();ref.append([str(ini)[:40],str(k2),'ACCEPTED'])
        except ValueError:ref.append([str(ini)[:40],str(k2),'refused'])
    c=N.Certifier20N([(0,1,0,1)],3,4,read_bits=4,eps_bar=0.15,reads=1,conflict_cap=10,budget_conflicts=10)
    for o in ([(0,1)],[(0,1,0,2)],[(0,1,0,1)]*3,[(0,1,0,None)],(0,1,0,1)):
        try:c.observe(0,o);ref.append(['observe',str(o)[:40],'ACCEPTED'])
        except ValueError:ref.append(['observe',str(o)[:40],'refused'])
    c.close()
    return {'cases':rows,'refusals':ref,'PASS':all(r['equal'] for r in rows) and all(x[2]=='refused' for x in ref)}


def drive(arg):
    cid,c,arm,a=arg
    from brute.api.certify20b import Certifier20B,counted16d
    from brute.api import certify20n as N
    from experiments import worlds_059 as W
    from experiments.brute_common_059 import GUARD_CALL_S
    from brute.scalesearch4 import SOLVER4
    sb=a['read_bits'];pm=list(a['prefix_masks']);em=list(a['extra_masks']);ea=list(a['extra_acts']);diffs=[]
    acts=list(W.actions(c['seed'],0.0,c['k']));rd=lambda mk:W.bits(mk.bit_length()-1,sb)
    kw=dict(max_chunks=a['max_chunks'],K=a['K'],conflict_cap=a['conflict_cap'],budget_conflicts=a['budget_conflicts'],hook=None,
            factory=counted16d,wall_guard_case_s=a['hard_kill_s'],wall_guard_call_s=GUARD_CALL_S,solver=SOLVER4)
    noisy=a['eps_bar'] is not None;w=W.world(c['seed']);q=w.start
    if noisy:
        nz=W.Noise(c['seed'],a['eps']);x=N.Certifier20N(nz.reads(W.bits(w.emissions[q]),N.reads_for(1,a['eps_bar'],a['delta'],sb)),c['k'],c['N'],
                                                     read_bits=sb,eps_bar=a['eps_bar'],delta=a['delta'],**kw)
    else:x=Certifier20B(rd(pm[0]),c['k'],c['N'],'a16d',read_bits=sb,**kw)
    i=0;masks=[]
    def ob(s,mk):
        nonlocal q
        q=w.transitions[q][s]
        if noisy:x.observe(s,nz.reads(W.bits(w.emissions[q]),x.reads_needed()))
        else:x.observe(s,rd(mk))
    try:
        for s,mk in zip(acts,pm[1:]):ob(s,mk)
        while True:
            wd=x.propose()
            if wd is None:break
            for s in wd:
                if i>=len(ea) or ea[i]!=s:diffs.append(['word_differs',i]);raise StopIteration
                ob(s,em[i]);i+=1
        rec=x.record();res=x.result()
    except StopIteration:return cid,False,diffs
    finally:x.close()
    if i!=len(ea):diffs.append(['trace_not_consumed',i,len(ea)])
    if list(rec['masks'])!=pm+em:diffs.append('masks')
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
    ap.add_argument('--block',default='main');a=ap.parse_args(argv)
    out={'schema':'brute.api-checks.v56','certify20n_sha256':sha(ROOT/'brute/api/certify20n.py'),'compat':A47.compat(),'ghost':ghost(),'equiv':equiv()}
    if a.study:out['fidelity']=fidelity(a.study,block=a.block)
    out['PASS']=out['compat']['PASS'] and out['ghost']['PASS59'] and out['equiv']['PASS'] and (out['fidelity']['PASS'] if a.study else True)
    write_new(Path(a.output),out);g=out['ghost']
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':g['PASS59'],'static':g['certify20n_static_ok'],'frozen_api_unchanged':g['frozen_api_unchanged'],
                      'net':g['no_network_run'],'equiv':out['equiv']['PASS'],'fidelity':{k:v for k,v in out.get('fidelity',{}).items() if k!='per_case'}}))
    return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
