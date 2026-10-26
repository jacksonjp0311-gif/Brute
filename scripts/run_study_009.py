"""Held-out run orchestrator for study BRUTE-070-SYNCPLAN-009 (plan process_controls (8), stop_rule).

Run with:  nohup $PY scripts/run_study_009.py > results/study-009/RUN_009.log 2>&1 &
Before the first start the operator appends the ledger run_start entry and writes its epoch seconds to
results/study-009/RUN_T0 (the 3 h cap is measured from that time and never extended). A restart after an interruption
reuses RUN_T0, skips every stream whose output exists, resumes the per-case checkpoints, and charges each stream budget
with the time already spent (results/study-009/RUN_STATE_009.json).

Streams (at most 8 worker processes at once; a stream starts when its inputs exist and its workers fit; order = priority):
  planning   P7 planning block, 6 workers, budget 60 min
  2x2        main 2x2 block, 2 workers, budget 45 min
  breadth    breadth block, 2 workers, budget 45 min
  gx2_sym    v070_xcheck symmetric, B5/BS7/BSC7, 4 workers, 30 min (after breadth)
  gx2_spot   v070_xcheck --no-symmetry on SPOT_SAMPLE_009 (B5), 2 workers, 30 min (after breadth)
  g11        second implementation (all blocks, mutation 20), 2 workers (after 2x2, breadth, planning)
  gp1_audit  GP1 (iv) replay + (v) count audit, 2 workers (after planning)
  repro_*    G12 every-3rd reruns per block to results/study-009/repro/<block> (2x2 2, breadth 2, planning 4 workers)
  gti        scripts/run_tests_070.py (GTI, in-cap run), counted as 2 workers
A study stream stopped by its budget is SIGTERMed (SIGKILL after 60 s) and sealed as it is (--seal-partial); an xcheck
stream stopped by its budget is summarised from its checkpoint (unreached steps = unchecked). At the 3 h cap every running
stream is stopped the same way, STOP_009.json lists the unfinished streams, and nothing is extended or rerun.
"""
from __future__ import annotations
import json,os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
D=Path(os.environ.get('STUDY_DIR_009',ROOT/'results/study-009'))
PY=os.environ.get('PY','/workspace/bgr/venv/bin/python')
CAP=3*3600
MAX_WORKERS=8
GRACE=60
SM=['--smoke'] if os.environ.get('SMOKE') else []
# Dry-run hooks, honoured ONLY together with SMOKE=1 (pre-freeze smoke of this runner): CAP_S overrides the cap,
# BUDGET_S overrides every stream budget. The held-out run sets none of SMOKE, CAP_S, BUDGET_S, LIMIT.
if SM and os.environ.get('CAP_S'):CAP=int(os.environ['CAP_S'])
DRY_BUDGET=int(os.environ['BUDGET_S']) if SM and os.environ.get('BUDGET_S') else None
LIM=['--limit',os.environ['LIMIT']] if os.environ.get('LIMIT') else []


def study(block,workers,out,extra=()):
    return [PY,'-m','experiments.brute_study_009','--block',block,'--workers',str(workers),'--output',str(out),*extra,*SM,*LIM]


def S(block):return D/block


def tasks():
    sp=ROOT/'results/study-009/SPOT_SAMPLE_009.json'
    T=[('planning',6,3600,[],study('planning',6,S('planning')),S('planning')/'SEAL.json',('study','planning',S('planning'),())),
       ('2x2',2,2700,[],study('2x2',2,S('2x2')),S('2x2')/'SEAL.json',('study','2x2',S('2x2'),())),
       ('breadth',2,2700,['2x2'],study('breadth',2,S('breadth')),S('breadth')/'SEAL.json',('study','breadth',S('breadth'),())),
       ('gx2_sym',4,1800,['breadth'],[PY,'-m','experiments.v070_xcheck','--results',str(S('breadth')/'RESULTS.json'),'--checkpoint',
            str(D/'XCHECK_009_CHECKPOINT.jsonl'),'--output',str(D/'XCHECK_009.json'),'--workers','4'],D/'XCHECK_009.json',
        ('xcheck',D/'XCHECK_009.json',[PY,'-m','experiments.v070_xcheck','--results',str(S('breadth')/'RESULTS.json'),'--checkpoint',
            str(D/'XCHECK_009_CHECKPOINT.jsonl'),'--output',str(D/'XCHECK_009.json'),'--summarize-only'])),
       ('gx2_spot',2,1800,['breadth'],[PY,'-m','experiments.v070_xcheck','--results',str(S('breadth')/'RESULTS.json'),'--checkpoint',
            str(D/'XCHECK_SPOT_009_CHECKPOINT.jsonl'),'--output',str(D/'XCHECK_SPOT_009.json'),'--workers','2','--no-symmetry',
            '--arms','B5','--spot',str(sp)],D/'XCHECK_SPOT_009.json',
        ('xcheck',D/'XCHECK_SPOT_009.json',[PY,'-m','experiments.v070_xcheck','--results',str(S('breadth')/'RESULTS.json'),'--checkpoint',
            str(D/'XCHECK_SPOT_009_CHECKPOINT.jsonl'),'--output',str(D/'XCHECK_SPOT_009.json'),'--no-symmetry','--arms','B5',
            '--spot',str(sp),'--summarize-only'])),
       ('gp1_audit',2,None,['planning'],[PY,'scripts/check_planning_009.py','--results',str(S('planning')/'RESULTS.json'),
            '--output',str(D/'PLANNING_AUDIT_009.json'),'--workers','2'],D/'PLANNING_AUDIT_009.json',None),
       ('g11',2,None,['2x2','breadth','planning'],[PY,'scripts/run_reference_009.py','--results',str(S('2x2')/'RESULTS.json'),
            str(S('breadth')/'RESULTS.json'),str(S('planning')/'RESULTS.json'),'--output',str(D/'SECOND_IMPLEMENTATION_009.json'),
            '--workers','2'],D/'SECOND_IMPLEMENTATION_009.json',None),
       ('repro_2x2',2,None,['2x2'],study('2x2',2,D/'repro/2x2',('--every','3','--offset','0')),D/'repro/2x2/SEAL.json',
        ('study','2x2',D/'repro/2x2',('--every','3','--offset','0'))),
       ('repro_breadth',2,None,['breadth'],study('breadth',2,D/'repro/breadth',('--every','3','--offset','0')),D/'repro/breadth/SEAL.json',
        ('study','breadth',D/'repro/breadth',('--every','3','--offset','0'))),
       ('repro_planning',4,None,['planning'],study('planning',4,D/'repro/planning',('--every','3','--offset','0')),
        D/'repro/planning/SEAL.json',('study','planning',D/'repro/planning',('--every','3','--offset','0'))),
       ('gti',2,None,['g11','gp1_audit'],[PY,'scripts/run_tests_070.py','--output',str(D/'TEST_SUITE_009.json')],D/'TEST_SUITE_009.json',None)]
    T=[dict(zip(('name','workers','budget','deps','cmd','done','finalize'),t)) for t in T]
    if DRY_BUDGET:
        for t in T:t['budget']=DRY_BUDGET if t['budget'] is not None else None
    return T


def now():return time.time()
def stamp():return time.strftime('%Y-%m-%dT%H:%M:%S%z')
def log(msg):print(f'[{stamp()}] {msg}',flush=True)


def load_state():
    p=D/'RUN_STATE_009.json'
    st=json.loads(p.read_text()) if p.exists() else {}
    for k in ('spent','stopped','finished','running'):st.setdefault(k,{})
    return st


def reap_orphans(st):
    """After an orchestrator interruption: stop any stream process group it left running and charge its budget with
    the time up to the last heartbeat (the stream resumes from its checkpoint)."""
    for n,r in list(st['running'].items()):
        try:
            os.killpg(r['pgid'],signal.SIGTERM);time.sleep(5);os.killpg(r['pgid'],signal.SIGKILL)
        except ProcessLookupError:pass
        st['spent'][n]=r['spent_before']+max(0.,st.get('heartbeat',r['since'])-r['since']);del st['running'][n]
        log(f'{n}: orphan from an interrupted orchestrator stopped; charged {st["spent"][n]:.0f} s; will resume')
    save_state(st)


def save_state(st):
    p=D/'RUN_STATE_009.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(st,indent=1,sort_keys=True));tmp.replace(p)


def stop(proc,name):
    try:os.killpg(proc.pid,signal.SIGTERM)
    except ProcessLookupError:return
    t=now()
    while proc.poll() is None and now()-t<GRACE:time.sleep(1)
    if proc.poll() is None:
        log(f'{name}: SIGKILL after {GRACE} s')
        try:os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        proc.wait()


def finalize(t,reason):
    """Seal a stopped stream as it is."""
    f=t['finalize']
    if f is None or t['done'].exists():return
    env=dict(os.environ,PYTHONPATH=str(ROOT))
    if f[0]=='study':
        _,block,out,extra=f
        if not (Path(out)/'CHECKPOINT.jsonl').exists():Path(out).mkdir(parents=True,exist_ok=True);Path(out,'CHECKPOINT.jsonl').touch()
        cmd=[PY,'-m','experiments.brute_study_009','--block',block,'--output',str(out),'--seal-partial',*extra,*SM,*LIM]
    else:
        cmd=f[2]
        if not Path(cmd[cmd.index('--checkpoint')+1]).exists():Path(cmd[cmd.index('--checkpoint')+1]).touch()
    r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True)
    log(f"{t['name']}: sealed as it is ({reason}) rc={r.returncode} {r.stdout.strip()[-200:]} {r.stderr.strip()[-300:]}")


def progress(T,st,t0):
    p=D/'PROGRESS_009.json'
    if p.exists():return
    rep={'written_at':stamp(),'elapsed_s':round(now()-t0),'note':'read-only projection (stop_rule.projection); no design, budget or seed change follows','streams':{}}
    for t in T:
        ck=None
        if t['finalize'] and t['finalize'][0]=='study':ck=Path(t['finalize'][2])/'CHECKPOINT.jsonl'
        elif t['finalize']:c=t['finalize'][2];ck=Path(c[c.index('--checkpoint')+1])
        n=sum(1 for _ in open(ck)) if ck and ck.exists() else None
        rep['streams'][t['name']]={'done':t['done'].exists(),'checkpoint_lines':n,'spent_s':round(st['spent'].get(t['name'],0)),
                                   'budget_s':t['budget'],'stopped':st['stopped'].get(t['name'])}
    p.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n');log('PROGRESS_009.json written')


def main():
    D.mkdir(parents=True,exist_ok=True)
    if not SM and (os.environ.get('CAP_S') or os.environ.get('BUDGET_S') or LIM):raise SystemExit('dry-run hooks set without SMOKE')
    if not (D/'RUN_T0').exists():raise SystemExit('RUN_T0 missing: append the ledger run_start entry and write its epoch to RUN_T0 first')
    t0=float((D/'RUN_T0').read_text().split()[0]);deadline=t0+CAP
    st=load_state();reap_orphans(st);T=tasks();running={};env=dict(os.environ,PYTHONPATH=str(ROOT))
    if os.environ.get('SKIP_GTI'):T=[t for t in T if t['name']!='gti']      # orchestrator dry run only
    (D/'logs').mkdir(exist_ok=True)
    log(f'orchestrator start; cap at {time.strftime("%Y-%m-%dT%H:%M:%S%z",time.localtime(deadline))}')
    def finished(n):
        t=next(x for x in T if x['name']==n);return t['done'].exists() or n in st['stopped']
    while True:
        if now()-t0>=1800:progress(T,st,t0)
        st['heartbeat']=now()
        st['running']={n:{'pgid':p.pid,'since':ts,'spent_before':st['spent'].get(n,0)} for n,(p,t,ts) in running.items()};save_state(st)
        if now()>=deadline:
            log('3 h CAP reached: stopping every running stream (no extension, no rerun)')
            for n,(p,t,ts) in list(running.items()):
                stop(p,n);st['spent'][n]=st['spent'].get(n,0)+now()-ts;st['stopped'][n]='STUDY_BUDGET (3 h cap)';save_state(st);finalize(t,'3 h cap')
            running.clear();st['running']={};save_state(st)
            unfinished=[t['name'] for t in T if not t['done'].exists() or t['name'] in st['stopped']]
            (D/'STOP_009.json').write_text(json.dumps({'stopped_at':stamp(),'cap_s':CAP,'t0':t0,'unfinished_or_stopped':unfinished,
                                                       'stopped':st['stopped']},indent=1,sort_keys=True)+'\n')
            log(f'STOP_009 written: {unfinished}');return 2
        for n,(p,t,ts) in list(running.items()):
            el=st['spent'].get(n,0)+now()-ts
            if p.poll() is not None:
                st['spent'][n]=el;del running[n];st['running'].pop(n,None)
                if p.returncode==0 and t['done'].exists():st['finished'][n]=stamp();log(f'{n}: done in {el:.0f} s')
                else:st['stopped'][n]=f'exit code {p.returncode}';log(f'{n}: FAILED rc={p.returncode} (see logs/{n}.log)');finalize(t,'stream error')
                save_state(st)
            elif t['budget'] is not None and el>=t['budget']:
                log(f'{n}: stream budget {t["budget"]} s reached: stopping');stop(p,n)
                st['spent'][n]=st['spent'].get(n,0)+now()-ts;st['stopped'][n]=f'stream budget {t["budget"]} s';del running[n];st['running'].pop(n,None)
                save_state(st);finalize(t,'stream budget')
        free=MAX_WORKERS-sum(t['workers'] for _,t,_ in running.values())
        for t in T:
            n=t['name']
            if n in running or finished(n):continue
            if not all(finished(d) for d in t['deps']) or t['workers']>free:continue
            if t['budget'] is not None and st['spent'].get(n,0)>=t['budget']:
                st['stopped'][n]=f'stream budget {t["budget"]} s (exhausted before resume)';save_state(st);finalize(t,'stream budget');continue
            lf=open(D/'logs'/f'{n}.log','a');log(f'{n}: start ({t["workers"]} workers, spent {st["spent"].get(n,0):.0f} s, budget {t["budget"]})')
            p=subprocess.Popen(t['cmd'],cwd=ROOT,env=env,stdout=lf,stderr=subprocess.STDOUT,start_new_session=True)
            running[n]=(p,t,now());free-=t['workers']
        if not running and all(finished(t['name']) for t in T):
            (D/'RUN_DONE_009.json').write_text(json.dumps({'finished_at':stamp(),'elapsed_s':round(now()-t0),'t0':t0,
                'spent':{k:round(v) for k,v in st['spent'].items()},'stopped':st['stopped'],'finished':st['finished']},indent=1,sort_keys=True)+'\n')
            log(f'RUN_DONE ({now()-t0:.0f} s since t0; stopped streams: {st["stopped"]})');return 0
        time.sleep(2)


if __name__=='__main__':sys.exit(main())
