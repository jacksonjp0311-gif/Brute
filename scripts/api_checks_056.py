"""GHOST56, GFID56 and compat inputs for study-056 (BRUTE_PLAN_056; pre-run deviation #185). New file; built
from scripts/api_checks_055.py (frozen), whose replay logic is followed, with the frozen api_checks_050 ROUND_FIELDS and
api_checks_047 / 046 helpers imported unchanged.
  compat:   api_checks_047.compat() (certify/16 and certify/14 test modules, 046 compat sample byte for byte), reported;
  ghost:    GHOST56: (1) brute.api.certify14 / 16 / 16d / 16e / 16n / 16s / 20t / 20c files have the sha256 frozen in BRUTE_SOURCE_FREEZE_047
            (14, 16, 16d), _049 (16e), _050 (16n), _051 (16s), _054 (20t) and _055 (20c), and the certify16e, certify16n, certify16s,
            certify20t and certify20c closures equal the ones recorded in results/study-056/API_CHECKS_056.json; the certify20l closure is
            recorded; (2) a subprocess with socket disabled runs a full Certifier20L loop (smoke seed 12370003, scale16, family_bound 16,
            C 50000, B 3000000, conflict-only stop) to any final label (#185: a completed loop with no network), 0 socket attempts;
  fidelity: (GFID56, only with --study) every record of block main is driven again, observation by observation, over its own
            recorded trace in a fresh process per record on 8 workers, with the record's C, B, max_chunks and stop rule (hook
            None, the 900 s case guard). The api result (canonical JSON) and every round's ROUND_FIELDS must equal the record
            byte for byte, and for API20L records the record's table (#185) must equal the recorded one too. Gated: the API20L / API20L_b records (12 scale20t + 6 compat20t = 18 at full size); the API16E20 and
            API16E records are replayed and reported.
Writes <out> (default results/study-056/API_CHECKS_056.json; refuses overwrite).
  PYTHONPATH=. python scripts/api_checks_056.py [--study results/study-056/main] [--output PATH] [--expected 18]"""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import load,write_new,sha,dumps
from scripts import api_checks_047 as A47
from scripts import api_checks_046 as A46
from scripts.api_checks_050 import ROUND_FIELDS
OUT=ROOT/'results/study-056/API_CHECKS_056.json'
CLOSURE_054=ROOT/'results/study-054/API_CHECKS_054.json'
FROZEN={'brute/api/certify14.py':'experiments/BRUTE_SOURCE_FREEZE_047.json','brute/api/certify16.py':'experiments/BRUTE_SOURCE_FREEZE_047.json',
        'brute/api/certify16d.py':'experiments/BRUTE_SOURCE_FREEZE_047.json','brute/api/certify16e.py':'experiments/BRUTE_SOURCE_FREEZE_049.json',
        'brute/api/certify16n.py':'experiments/BRUTE_SOURCE_FREEZE_050.json','brute/api/certify16s.py':'experiments/BRUTE_SOURCE_FREEZE_051.json',
        'brute/api/certify20t.py':'experiments/BRUTE_SOURCE_FREEZE_054.json','brute/api/certify20c.py':'experiments/BRUTE_SOURCE_FREEZE_055.json'}
MODS=('brute.api.certify14','brute.api.certify16','brute.api.certify16d','brute.api.certify16e','brute.api.certify16n','brute.api.certify16s','brute.api.certify20t','brute.api.certify20c','brute.api.certify20l')
NONET='''
import socket,json
hits=[]
def _no(*a,**k):hits.append(1);raise OSError('network disabled by api_checks_056')
socket.socket=_no;socket.create_connection=_no
from brute.api import certify20l as T
from experiments import worlds_050 as W
from experiments.brute_study_033 import StepWorld,passive
s=12370003;w=W.world(s,'scale16');sw=StepWorld(w);_,acts,rd=passive(sw,s)
c=T.Certifier20L(rd[0],w.k,16,conflict_cap=50000,budget_conflicts=3000000,wall_guard_case_s=900.0,hook=None)
for a,o in zip(acts,rd[1:]):c.observe(a,o)
while True:
    x=c.propose()
    if x is None:break
    for a in x:c.observe(a,sw.step(a))
r=c.result();c.close()
print(json.dumps({'loop':[r['api'],r['label'],r['n_min'],r['used'],r['conflicts']],'socket_attempts':len(hits)}))
'''
T_ARMS=('API20L','API20L_b');E_ARMS=('API16E20','API16E');ARMS=T_ARMS+E_ARMS;KEYS=('scale20t','compat20t')


def ghost():
    C={m:A46.closure(m) for m in MODS};prev=load(CLOSURE_055)['ghost']['closures']
    shas={f:{'now':sha(ROOT/f),'frozen':load(ROOT/fz)['sha256_files'].get(f),'freeze':fz} for f,fz in FROZEN.items()}
    sha_ok=all(v['now']==v['frozen'] for v in shas.values())
    p=subprocess.run([sys.executable,'-c',NONET],cwd=ROOT,capture_output=True,text=True,timeout=900,env={'PYTHONPATH':str(ROOT),'PATH':'/usr/bin:/bin'})
    try:net=json.loads(p.stdout.strip().splitlines()[-1])
    except (ValueError,IndexError):net={'error':p.stderr.strip()[-400:]}
    lp=net.get('loop',[None,None])
    net_ok=p.returncode==0 and net.get('socket_attempts')==0 and lp[0]=='brute.certify/20l' and lp[1] in ('ID','IDF','IDU','AMB')  # #185: a completed loop with no network; the plan does not require a decision
    cl_ok={m:sorted(C[m])==prev[m] for m in ('brute.api.certify16e','brute.api.certify16n','brute.api.certify16s','brute.api.certify20t','brute.api.certify20c')}
    out={'closures':{m:sorted(v) for m,v in C.items()},'closures_055':{m:prev[m] for m in cl_ok},'closures_unchanged':cl_ok,
         'frozen_api_sha256':shas,'frozen_api_unchanged':sha_ok,'no_network_run':net,'no_network_returncode':p.returncode,
         'socket_attempts':net.get('socket_attempts'),'network_pass':net_ok}
    out['PASS56']=bool(net_ok and sha_ok and all(cl_ok.values()));return out


def drive(arg):
    """Replay one API20L / API16E record over its own trace; returns (id, ok, diffs)."""
    cid,c,arm,a=arg
    from brute.api.certify16e import Certifier16E,counted16d
    from brute.api.certify20l import Certifier20L
    from experiments import worlds_050 as W
    from experiments.brute_study_033 import StepWorld,passive
    w=W.world(c['seed'],c['family']);_,acts,rd=passive(StepWorld(w),c['seed'])
    ex_a=list(a['extra_acts']);ex_m=list(a['extra_masks']);i=0;diffs=[]
    kw=dict(max_chunks=a['max_chunks'],K=a['K'],conflict_cap=a['conflict_cap'],budget_conflicts=a['budget_conflicts'],hook=None,
            factory=counted16d,wall_guard_case_s=a['hard_kill_s'])
    x=Certifier20L(rd[0],c['k'],c['N'],'a20l',**kw) if arm in T_ARMS else Certifier16E(rd[0],c['k'],c['N'],'a16d',**kw)
    feed=lambda j,s:x.observe(s,rd[j] if j<len(rd) else A47._reading(ex_m[j-len(rd)]))
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
    if arm in T_ARMS and dumps(rec.get('table'))!=dumps(a.get('table')):diffs.append('table')
    if len(rec['rounds'])!=len(a['rounds']):diffs.append(('rounds',len(rec['rounds']),len(a['rounds'])))
    for j,(r1,r2) in enumerate(zip(rec['rounds'],a['rounds'])):
        for f in ROUND_FIELDS:
            if dumps(r1.get(f))!=dumps(r2.get(f)):diffs.append((j,f))
    return cid,not diffs,diffs


def fidelity(study,expected,workers=8,block='main'):
    res=load(Path(study)/'RESULTS.json')
    todo=[(f"{c['key']}/{c['seed']}/{g}",c,g,c['arms'][g]) for c in res['cases'] if c['block']==block for g in ARMS if g in c['arms']]
    with ProcessPoolExecutor(workers,max_tasks_per_child=1) as ex:rows=list(ex.map(drive,todo))
    gated=[r for r in rows if r[0].split('/')[-1] in T_ARMS]
    return {'study_results_sha256':sha(Path(study)/'RESULTS.json'),'cases':len(rows),'expected':expected,'exact':sum(r[1] for r in rows),
            'workers':workers,'per_key':{k:sum(1 for r in rows if r[0].startswith(k+'/')) for k in KEYS},
            'gated':{'cases':len(gated),'exact':sum(r[1] for r in gated)},
            'reported':{'cases':len(rows)-len(gated),'exact':sum(r[1] for r in rows)-sum(r[1] for r in gated)},
            'exact_per_arm':{g:sum(r[1] for r in rows if r[0].endswith('/'+g)) for g in ARMS},
            'records_per_arm':{g:sum(1 for r in rows if r[0].endswith('/'+g)) for g in ARMS},
            'per_case':{r[0]:{'exact':r[1],'diffs':r[2]} for r in rows},
            'PASS':len(gated)==expected and all(r[1] for r in gated)}


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(OUT));ap.add_argument('--study')
    ap.add_argument('--expected',type=int,default=18);ap.add_argument('--block',default='main');a=ap.parse_args(argv)
    out={'schema':'brute.api-checks.v53','certify20l_sha256':sha(ROOT/'brute/api/certify20l.py'),'compat':A47.compat(),'ghost':ghost()}
    if a.study:out['fidelity']=fidelity(a.study,a.expected,block=a.block)
    out['PASS']=out['compat']['PASS'] and out['ghost']['PASS56'] and (out['fidelity']['PASS'] if a.study else True);write_new(Path(a.output),out)
    g=out['ghost']
    print(json.dumps({'compat':out['compat']['PASS'],'ghost':g['PASS56'],'frozen_api_unchanged':g['frozen_api_unchanged'],
                      'closures':g['closures_unchanged'],'net':g['no_network_run'],
                      'fidelity':{k:v for k,v in out.get('fidelity',{}).items() if k!='per_case'}}));return 0 if out['PASS'] else 1


if __name__=='__main__':sys.exit(main())
