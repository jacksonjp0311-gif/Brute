"""Held-out run orchestrator for study BRUTE-0170-SEQUENTIAL-MARGIN-019 (same method as scripts/run_study_018.py; plan stop_rule, G_RT_study_runtime).

Run with:  nohup setsid $PY scripts/run_study_019.py > results/study-019/RUN_019.log 2>&1 &
together with the independent watchdog (scripts/watchdog_019.py). Before the first start the operator appends the
ledger run_start_019 entry and writes its epoch seconds to results/study-019/RUN_T0. The 2 h cap is measured from
RUN_T0 and is never extended; a restarted orchestrator resumes every stream from its checkpoint and charges each
stream budget with the time already spent (RUN_STATE_019.json).

Streams (plan stop_rule.streams_and_budgets: fixed by scripts/rate_math_019.py before the source freeze; STREAMS below;
at most 8 worker processes at once):
  MANDATORY at t0:     transfer (360 main + 120 stress + 96 alphabet3) | gti (scripts/run_tests_0170.py, parallel per-module runner)
  after transfer:      repro (block reproset = main[::3] + alphabet3[::3], 152 cases) | g11 (scripts/run_reference_019.py: audit
                       of all 576 transfer cases, then the mutation test on main + alphabet3 cases; PROGRESS_G11_019.json every 60 s)
Stops: at RUN_T0 + 7200 s the orchestrator stops every running stream (SIGTERM, SIGKILL after 10 s), seals each
checkpoint as it is (--seal-partial / --summarize-only; never a new case) and writes STOP_019_ORCHESTRATOR.json (the
watchdog writes STOP_019.json). Every stream completion is stamped (wall epoch) in RUN_STATE_019.json 'completed_at'.
PROGRESS_019.json (read-only projection) is written at t0 + 360 s.
Dry-run hooks (only with SMOKE=1 and a directory outside results/study-019): CAP_S, BUDGET_S, LIMIT, SKIP_GTI.
With SMOKE=1 the transfer and repro streams run block smoke-all (smoke-transfer + smoke-a3 smoke seeds; repro every 3rd); with
SMOKE=1 and BRUTE_SMOKE_DRILL=1 (the kill drill) they run block smoke-drill.
PROGRESS_019.json (all streams, read-only projection) is written at t0 + 360 s.
"""
from __future__ import annotations
import json,os,shlex,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_study_019 import _select
from experiments.brute_common_019 import load,PLAN
STUDY=ROOT/'results/study-019'
D=Path(os.environ.get('STUDY_DIR_019',STUDY))
PY=os.environ.get('PY','/workspace/bgr/venv/bin/python')
CAP=7200
MAX_WORKERS=8
GRACE=10
PROGRESS_AT=360
# name: (workers, budget_s). Fixed by scripts/rate_math_019.py (docs/research/v0.17.0/RATE_MATH_019.md) before the source freeze.
STREAMS={'transfer':(4,2400),'gti':(4,4800),'repro':(2,1800),'g11':(2,1800)}
SM=['--smoke'] if os.environ.get('SMOKE') else []
if SM and os.environ.get('CAP_S'):CAP=int(os.environ['CAP_S'])
DRY_BUDGET=int(os.environ['BUDGET_S']) if SM and os.environ.get('BUDGET_S') else None
LIM=['--limit',os.environ['LIMIT']] if SM and os.environ.get('LIMIT') else []


BLOCK=('smoke-drill' if os.environ.get('BRUTE_SMOKE_DRILL') else 'smoke-all') if SM else 'transfer'
RBLOCK=BLOCK if SM else 'reproset'
RDIR='repro/'+('smoke' if SM else 'reproset')


def study(block,workers,out,extra=()):
    return [PY,'-m','experiments.brute_study_019','--block',block,'--workers',str(workers),'--output',str(out),*extra,*LIM]


def g11(workers,budget):
    out=D/'SECOND_IMPLEMENTATION_019.json';ck=D/'SECOND_IMPLEMENTATION_019_CHECKPOINT.jsonl'
    base=[PY,'scripts/run_reference_019.py','--results',str(D/'transfer/RESULTS.json'),'--checkpoint',str(ck),'--output',str(out)]
    return base+['--workers',str(workers),'--progress',str(D/'PROGRESS_G11_019.json'),'--budget',str(budget)],out,('summary',out,base+['--summarize-only'])


def tasks():
    W={k:v[0] for k,v in STREAMS.items()};B={k:v[1] for k,v in STREAMS.items()}
    g,go,gf=g11(W['g11'],DRY_BUDGET or B['g11']);R=('--every','3','--offset','0') if SM else ()
    T=[('transfer',W['transfer'],B['transfer'],[],study(BLOCK,W['transfer'],D/'transfer'),D/'transfer/SEAL.json',('study',BLOCK,D/'transfer',()),True),
       ('gti',W['gti'],B['gti'],[],[PY,'scripts/run_tests_0170.py','--workers',str(W['gti']),'--output',str(D/'TEST_SUITE_019.json')],D/'TEST_SUITE_019.json',None,True),
       ('repro',W['repro'],B['repro'],['transfer'],study(RBLOCK,W['repro'],D/RDIR,R),D/RDIR/'SEAL.json',('study',RBLOCK,D/RDIR,R),True),
       ('g11',W['g11'],B['g11'],['transfer'],g,go,gf,True)]
    T=[dict(zip(('name','workers','budget','deps','cmd','done','finalize','mandatory'),t)) for t in T]
    if DRY_BUDGET:
        for t in T:t['budget']=DRY_BUDGET
    if os.environ.get('SKIP_GTI') and SM:T=[t for t in T if t['name']!='gti']
    return T


def now():return time.time()
def stamp(t=None):return time.strftime('%Y-%m-%dT%H:%M:%S%z',time.localtime(t))
def log(msg):print(f'[{stamp()}] {msg}',flush=True)


def load_state():
    p=D/'RUN_STATE_019.json'
    st=json.loads(p.read_text()) if p.exists() else {}
    for k in ('spent','stopped','finished','running','completed_at','started_at'):st.setdefault(k,{})
    return st


def save_state(st):
    p=D/'RUN_STATE_019.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(st,indent=1,sort_keys=True));tmp.replace(p)


def reap_orphans(st):
    for n,r in list(st['running'].items()):
        for sig in (signal.SIGTERM,signal.SIGKILL):
            try:os.killpg(r['pgid'],sig)
            except ProcessLookupError:pass
            time.sleep(3)
        st['spent'][n]=r['spent_before']+max(0.,st.get('heartbeat',r['since'])-r['since']);del st['running'][n]
        log(f'{n}: orphan from an interrupted orchestrator stopped; charged {st["spent"][n]:.0f} s; will resume')
    save_state(st)


def stop(proc,name):
    try:os.killpg(proc.pid,signal.SIGTERM)
    except ProcessLookupError:return
    t=now()
    while proc.poll() is None and now()-t<GRACE:time.sleep(0.5)
    if proc.poll() is None:
        log(f'{name}: SIGKILL after {GRACE} s')
        try:os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        proc.wait()


def finalize(t,reason):
    """Seal a stopped stream as it is (never runs a case)."""
    f=t['finalize']
    if f is None or t['done'].exists():return
    env=dict(os.environ,PYTHONPATH=str(ROOT))
    if f[0]=='study':
        _,block,out,extra=f;Path(out).mkdir(parents=True,exist_ok=True);Path(out,'CHECKPOINT.jsonl').touch()
        cmd=[PY,'-m','experiments.brute_study_019','--block',block,'--output',str(out),'--seal-partial',*extra,*LIM]
    else:
        cmd=f[2];ck=Path(cmd[cmd.index('--checkpoint')+1]);ck.touch()
        if '--results' in cmd and not Path(cmd[cmd.index('--results')+1]).exists():log(f"{t['name']}: no results file to summarise ({reason})");return
    r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True)
    log(f"{t['name']}: sealed as it is ({reason}) rc={r.returncode} {r.stdout.strip()[-300:]} {r.stderr.strip()[-300:]}")


def g11_events(st):
    """Copy the g11 checkpoint events (start, audit_done, mutation, done) into the run state."""
    ck=D/'SECOND_IMPLEMENTATION_019_CHECKPOINT.jsonl'
    if not ck.exists():return
    ev={}
    for l in open(ck):
        if '"event":' in l:
            try:r=json.loads(l)
            except ValueError:continue
            if 'event' in r:ev[r['event']]={k:v for k,v in r.items() if k!='details'}
    st.setdefault('events',{})['g11']=ev


def ck_lines(t):
    f=t['finalize']
    if f is None:return None
    ck=Path(f[2])/'CHECKPOINT.jsonl' if f[0]=='study' else Path(f[2][f[2].index('--checkpoint')+1])
    return sum(1 for _ in open(ck)) if ck.exists() else None


def expected(t):
    f=t['finalize']
    if not f or f[0]!='study':
        return len(_select(load(PLAN),BLOCK,1,0,int(LIM[1]) if LIM else None))+1 if t['name']=='g11' else None
    every=int(f[3][1]) if f[3] else 1
    return len(_select(load(PLAN),f[1],every,0,int(LIM[1]) if LIM else None))


def progress(T,st,t0):
    p=D/'PROGRESS_019.json'
    if p.exists():return
    rep={'written_at':stamp(),'elapsed_s':round(now()-t0),'note':'read-only projection (stop_rule); no design, budget or seed change follows','streams':{}}
    for t in T:
        n=t['name'];el=st['spent'].get(n,0)+(now()-st['running'][n]['since'] if n in st['running'] else 0);done=ck_lines(t);E=expected(t)
        proj=round(el*E/done) if done and E else None
        rep['streams'][n]={'mandatory':t['mandatory'],'done':t['done'].exists(),'checkpoint_lines':done,'expected_cases':E,'spent_s':round(el),'budget_s':t['budget'],
                           'projected_total_s':proj,'projected_over_budget':None if proj is None else proj>t['budget'],'stopped':st['stopped'].get(n)}
    p.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n');log('PROGRESS_019.json written: '+json.dumps({k:(v['checkpoint_lines'],v['expected_cases'],v['projected_total_s']) for k,v in rep['streams'].items()}))


def finalize_only():
    st=load_state();T=tasks()
    check_running=[n for n,r in st['running'].items()]
    for n in check_running:
        try:os.killpg(st['running'][n]['pgid'],0);raise SystemExit(f'{n} still running; refusing')
        except ProcessLookupError:pass
    for t in T:
        if t['done'].exists() and t['name'] not in st['finished'] and t['name'] not in st['stopped']:
            st['finished'][t['name']]=stamp(t['done'].stat().st_mtime);st['completed_at'][t['name']]=t['done'].stat().st_mtime
            st.setdefault('completed_at_basis',{})[t['name']]='output file mtime (finished as the stop fired; recorded by --finalize-only)'
        if not t['done'].exists():
            st['stopped'].setdefault(t['name'],'STUDY_BUDGET (2 h cap, watchdog)');finalize(t,'after stop')
    g11_events(st);st['running']={};save_state(st);return 0


def main():
    D.mkdir(parents=True,exist_ok=True)
    if not SM and (os.environ.get('CAP_S') or os.environ.get('BUDGET_S') or os.environ.get('LIMIT') or os.environ.get('SKIP_GTI')):
        raise SystemExit('dry-run hooks set without SMOKE')
    if SM and D.resolve().is_relative_to(STUDY.resolve()):raise SystemExit('smoke directory must be outside results/study-019')
    if not (D/'RUN_T0').exists():raise SystemExit('RUN_T0 missing: append the ledger run_start_019 entry and write its epoch to RUN_T0 first')
    if '--finalize-only' in sys.argv:return finalize_only()
    t0=float((D/'RUN_T0').read_text().split()[0]);deadline=t0+CAP
    st=load_state();st['orchestrator_pid']=os.getpid();reap_orphans(st);T=tasks();running={}
    st['mandatory']={t['name']:t['mandatory'] for t in T};save_state(st);env=dict(os.environ,PYTHONPATH=str(ROOT))
    (D/'logs').mkdir(exist_ok=True)
    log(f'orchestrator start pid {os.getpid()}; cap {CAP} s, deadline {stamp(deadline)}')
    def finished(n):
        t=next(x for x in T if x['name']==n);return t['done'].exists() or n in st['stopped']
    while True:
        if now()-t0>=PROGRESS_AT:progress(T,st,t0)
        st['heartbeat']=now()
        st['running']={n:{'pgid':p.pid,'since':ts,'spent_before':st['spent'].get(n,0)} for n,(p,t,ts) in running.items()};save_state(st)
        if now()>=deadline:
            log(f'{CAP} s CAP reached: stopping every running stream (no extension, no rerun)')
            for n,(p,t,ts) in list(running.items()):
                stop(p,n);st['spent'][n]=st['spent'].get(n,0)+now()-ts;st['stopped'][n]=f'STUDY_BUDGET ({CAP} s cap)';save_state(st);finalize(t,'cap')
            g11_events(st);running.clear();st['running']={};save_state(st)
            unfinished=[t['name'] for t in T if not t['done'].exists() or t['name'] in st['stopped']]
            (D/'STOP_019_ORCHESTRATOR.json').write_text(json.dumps({'stopped_at':stamp(),'cap_s':CAP,'t0':t0,'unfinished_or_stopped':unfinished,
                                                                   'stopped':st['stopped']},indent=1,sort_keys=True)+'\n')
            log(f'STOP_019_ORCHESTRATOR written: {unfinished}');return 2
        for n,(p,t,ts) in list(running.items()):
            el=st['spent'].get(n,0)+now()-ts
            if p.poll() is not None:
                st['spent'][n]=el;del running[n];st['running'].pop(n,None)
                if p.returncode==0 and t['done'].exists():
                    st['finished'][n]=stamp();st['completed_at'][n]=now();log(f'{n}: done in {el:.0f} s')
                else:st['stopped'][n]=f'exit code {p.returncode}';log(f'{n}: FAILED rc={p.returncode} (see logs/{n}.log)');finalize(t,'stream error')
                if n=='g11':g11_events(st)
                save_state(st)
            elif t['budget'] is not None and el>=t['budget']:
                log(f'{n}: stream budget {t["budget"]} s reached: stopping');stop(p,n)
                st['spent'][n]=st['spent'].get(n,0)+now()-ts;st['stopped'][n]=f'stream budget {t["budget"]} s';del running[n];st['running'].pop(n,None)
                save_state(st);finalize(t,'stream budget')
                if n=='g11':g11_events(st);save_state(st)
        free=MAX_WORKERS-sum(t['workers'] for _,t,_ in running.values())
        for t in T:
            n=t['name']
            if n in running or finished(n):continue
            if not all(next(x for x in T if x['name']==d)['done'].exists() or d in st['stopped'] for d in t['deps']) or t['workers']>free:continue
            dep_ok=all(next(x for x in T if x['name']==d)['done'].exists() for d in t['deps'])
            if not dep_ok:st['stopped'][n]='input stream stopped before sealing';save_state(st);continue
            if st['spent'].get(n,0)>=t['budget']:
                st['stopped'][n]=f'stream budget {t["budget"]} s (exhausted before resume)';save_state(st);finalize(t,'stream budget');continue
            lf=open(D/'logs'/f'{n}.log','a');log(f'{n}: start ({t["workers"]} workers, spent {st["spent"].get(n,0):.0f} s, budget {t["budget"]})')
            p=subprocess.Popen(t['cmd'],cwd=ROOT,env=env,stdout=lf,stderr=subprocess.STDOUT,start_new_session=True)
            running[n]=(p,t,now());st['started_at'].setdefault(n,now());free-=t['workers']
            st['running'][n]={'pgid':p.pid,'since':running[n][2],'spent_before':st['spent'].get(n,0)};save_state(st)   # visible to the watchdog at once
        if not running and all(finished(t['name']) for t in T):
            (D/'RUN_DONE_019.json').write_text(json.dumps({'finished_at':stamp(),'elapsed_s':round(now()-t0),'t0':t0,
                'spent':{k:round(v) for k,v in st['spent'].items()},'stopped':st['stopped'],'finished':st['finished'],
                'completed_at':st['completed_at'],'mandatory':st['mandatory'],'events':st.get('events',{})},indent=1,sort_keys=True)+'\n')
            log(f'RUN_DONE ({now()-t0:.0f} s since t0; stopped streams: {st["stopped"]})');return 0
        time.sleep(2)


if __name__=='__main__':sys.exit(main())
