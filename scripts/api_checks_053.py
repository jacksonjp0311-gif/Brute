"""GHOST53, GFID53 and compat inputs for study-053 (BRUTE_PLAN_053; pre-run deviation #179). New file; built from
scripts/api_checks_052.py (frozen), whose replay logic is followed, with the frozen api_checks_050 _rebuild / ROUND_FIELDS and
api_checks_047 / 046 helpers imported unchanged.
  compat:   api_checks_047.compat() (certify/16 and certify/14 test modules, 046 compat sample byte for byte), reported;
  ghost:    GHOST53: (1) brute.api.certify14 / 16 / 16d / 16e / 16n / 16s files have the sha256 frozen in BRUTE_SOURCE_FREEZE_047
            (14, 16, 16d), _049 (16e), _050 (16n) and _051 (16s), and the certify16e, certify16n and certify16s closures equal the
            ones recorded in results/study-052/API_CHECKS_052.json (no new API in 053); (2) a subprocess with socket disabled runs a
            full Certifier16N loop through worlds_050.NoisyStepWorld (smoke seed 12130002, scale16, eps 0.05, eps_bar 0.10, delta
            0.001, anytime k rule, family_bound 16, C 50000, B 1500000) to ID or IDF, 0 socket attempts;
  fidelity: (GFID53, only with --study) every record of block main is driven again, observation by observation, over its own
            recorded trace in a fresh process per record on 8 workers, with the record's C, B and max_chunks, and the record's
            stop rule (part A: TimerHook and the 600 s case guard; part B: hook None and the 900 s case guard); certify/16n
            observations are rebuilt from the recorded vote vectors, never from the world. The api result (canonical JSON) and
            every round's ROUND_FIELDS (certify/16n: also reads_per_obs and votes) must equal the record byte for byte. The plan
            names 24 records (18 API16N16-family noisy records and 6 eps-0 compat records); #179 widens the gated replay to every
            part A record (24 + N16BAR + 12) and replays the part B records for the record (reported, not gated).
Writes <out> (default results/study-053/API_CHECKS_053.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_053.py [--study results/study-053/main] [--output PATH] [--expected 42]"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,dumps
from scripts import api_checks_047 as A47
from scripts import api_checks_046 as A46
from scripts.api_checks_050 import _rebuild,ROUND_FIELDS
OUT=ROOT/'results/study-053/API_CHECKS_053.json'
CLOSURE_052=ROOT/'results/study-052/API_CHECKS_052.json'
FROZEN={'brute/api/certify14.py':'experiments/BRUTE_SOURCE_FREEZE_047.json','brute/api/certify16.py':'experiments/BRUTE_SOURCE_FREEZE_047.json',
        'brute/api/certify16d.py':'experiments/BRUTE_SOURCE_FREEZE_047.json','brute/api/certify16e.py':'experiments/BRUTE_SOURCE_FREEZE_049.json',
        'brute/api/certify16n.py':'experiments/BRUTE_SOURCE_FREEZE_050.json','brute/api/certify16s.py':'experiments/BRUTE_SOURCE_FREEZE_051.json'}
MODS=('brute.api.certify14','brute.api.certify16','brute.api.certify16d','brute.api.certify16e','brute.api.certify16n','brute.api.certify16s')
NONET='''
import socket,json
hits=[]
def _no(*a,**k):hits.append(1);raise OSError('network disabled by api_checks_053')
socket.socket=_no;socket.create_connection=_no
from brute.api import certify16n as C16N
from experiments import worlds_050 as W
from experiments.brute_study_033 import StepWorld,passive
s=12130002;w=W.world(s,'scale16');sw=StepWorld(w);_,acts,rd=passive(sw,s)
nw=W.NoisyStepWorld(sw._w,s,0.05);nw.reset()
c=C16N.Certifier16N([nw.read() for _ in range(C16N.reads_for(1,0.10,0.001))],w.k,16,eps_bar=0.10,delta=0.001,conflict_cap=50000,budget_conflicts=1500000)
for a in acts:nw.step(a);c.observe(a,[nw.read() for _ in range(c.reads_needed())])
while True:
    x=c.propose()
    if x is None:break
    for a in x:sw.step(a);nw.step(a);c.observe(a,[nw.read() for _ in range(c.reads_needed())])
r=c.result();c.close()
print(json.dumps({'loop':[r['api'],r['label'],r['n_min'],r['used'],r['conflicts']],'socket_attempts':len(hits)}))
'''
N_ARMS=('API16N16','API16N16_b','API16N16_bar','API16N16_c');B_ARMS=('API16E20','API16E20_b');ARMS=N_ARMS+('API16E',)+B_ARMS
A_KEYS=('noise16','noise16_bar','compat16');KEYS=A_KEYS+('scale20c',)


def ghost():
    C={m:A46.closure(m) for m in MODS};prev=load(CLOSURE_052)['ghost']['closures']
    shas={f:{'now':sha(ROOT/f),'frozen':load(ROOT/fz)['sha256_files'].get(f),'freeze':fz} for f,fz in FROZEN.items()}
    sha_ok=all(v['now']==v['frozen'] for v in shas.values())
    p=subprocess.run([sys.executable,'-c',NONET],cwd=ROOT,capture_output=True,text=True,timeout=900,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:net=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):net={'error':p.stderr.strip()[-400:]}
    lp=net.get('loop',[None,None])
    net_ok=p.returncode==0 and net.get('socket_attempts')==0 and lp[0]=='brute.certify/16n' and lp[1] in ('ID','IDF')
    cl_ok={m:sorted(C[m])==prev[m] for m in ('brute.api.certify16e','brute.api.certify16n','brute.api.certify16s')}
    out={'closures':{m:sorted(v) for m,v in C.items()},'closures_052':{m:prev[m] for m in cl_ok},'closures_unchanged':cl_ok,
         'frozen_api_sha256':shas,'frozen_api_unchanged':sha_ok,'no_network_run':net,'no_network_returncode':p.returncode,
         'socket_attempts':net.get('socket_attempts'),'network_pass':net_ok}
    out['PASS53']=bool(net_ok and sha_ok and all(cl_ok.values()));return out


def drive(arg):
    """Replay one API16N16-family / API16E / API16E20 record over its own trace; returns (id, ok, diffs)."""
    cid,c,arm,a=arg
    from brute.api.certify16e import Certifier16E,counted16d
    from brute.api.certify16n import Certifier16N
    from experiments.host_hook_047 import TimerHook
    from experiments import worlds_050 as W
    from experiments.brute_study_033 import StepWorld,passive
    w=W.world(c['seed'],c['family']);_,acts,rd=passive(StepWorld(w),c['seed'])
    ex_a=list(a['extra_acts']);ex_m=list(a['extra_masks']);i=0;diffs=[]
    pb=arm in B_ARMS
    kw=dict(max_chunks=a['max_chunks'],K=a['K'],conflict_cap=a['conflict_cap'],budget_conflicts=a['budget_conflicts'],hook=None if pb else TimerHook(),factory=counted16d)
    if pb:kw['wall_guard_case_s']=a['hard_kill_s']
    if arm in ('API16E',)+B_ARMS:
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
    if arm in N_ARMS:
        for f in ('reads_per_obs','votes'):
            if dumps(rec[f])!=dumps(a[f]):diffs.append(f)
    return cid,not diffs,diffs


def fidelity(study,expected,workers=8,block='main'):
    res=load(Path(study)/'RESULTS.json')
    todo=[(f"{c['key']}/{c['seed']}/{g}",c,g,c['arms'][g]) for c in res['cases'] if c['block']==block for g in ARMS if g in c['arms']
          and c['arms'][g].get('stop')!='majority_error']
    with ProcessPoolExecutor(workers,max_tasks_per_child=1) as ex:rows=list(ex.map(drive,todo))
    return {'study_results_sha256':sha(Path(study)/'RESULTS.json'),'cases':len(rows),'expected':expected,'exact':sum(r[1] for r in rows),
            'workers':workers,'per_key':{k:sum(1 for r in rows if r[0].startswith(k+'/')) for k in KEYS},
            'part_a':{'cases':sum(1 for r in rows if r[0].split('/')[0] in A_KEYS),'exact':sum(r[1] for r in rows if r[0].split('/')[0] in A_KEYS)},
            'part_b':{'cases':sum(1 for r in rows if r[0].split('/')[0]=='scale20c'),'exact':sum(r[1] for r in rows if r[0].split('/')[0]=='scale20c')},
            'exact_per_arm':{g:sum(r[1] for r in rows if r[0].endswith('/'+g)) for g in ARMS},
            'records_per_arm':{g:sum(1 for r in rows if r[0].endswith('/'+g)) for g in ARMS},
            'per_case':{r[0]:{'exact':r[1],'diffs':r[2]} for r in rows},
            'PASS':sum(1 for r in rows if r[0].split('/')[0] in A_KEYS)==expected and all(r[1] for r in rows if r[0].split('/')[0] in A_KEYS)}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));ap.add_argument('--study')
    ap.add_argument('--expected',type=int,default=42);ap.add_argument('--block',default='main');a=ap.parse_args(argv)
    out={'schema':'brute.api-checks.v50','certify16n_sha256':sha(ROOT/'brute/api/certify16n.py'),'compat':A47.compat(),'ghost':ghost()}
    if a.study:out['fidelity']=fidelity(a.study,a.expected,block=a.block)
    out['PASS']=out['compat']['PASS'] and out['ghost']['PASS53'] and (out['fidelity']['PASS'] if a.study else True);write_new(Path(a.output),out)
    g=out['ghost']
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':g['PASS53'],'frozen_api_unchanged':g['frozen_api_unchanged'],
                      'closures':g['closures_unchanged'],'net':g['no_network_run'],
                      'fidelity':{k:v for k,v in out.get('fidelity',{}).items() if k!='per_case'}}));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
