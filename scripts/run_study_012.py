"""Held-out run orchestrator for study BRUTE-0100-SUPPORT-TRANSFER-012 (plan stop_rule, G_RT_study_runtime).

Run with:  nohup $PY scripts/run_study_012.py > results/study-012/RUN_012.log 2>&1 &
together with the independent watchdog (scripts/watchdog_012.py). Before the first start the operator appends the
ledger run_start_012 entry and writes its epoch seconds to results/study-012/RUN_T0. The 2 h cap is measured from
RUN_T0 and is never extended; a restarted orchestrator resumes every stream from its checkpoint and
charges each stream budget with the time already spent (RUN_STATE_012.json).

Streams (plan stop_rule.streams_and_budgets; at most 8 worker processes at once):
  MANDATORY at t0: 2x2 3w 2400 s | big78 2w 1800 s | transfer 1w 1200 s | gti 2w 2400 s
  after 2x2: repro 2w 1200 s (2x2 then transfer, index % 3 == 0, one process group) |
             g11 2w 1500 s (after 2x2 AND transfer: mandatory sample, mutation, mandatory_done, GT_ref transfer audit,
             fixed optional list, stamp; the transfer dependency is the disclosed GT_ref-inside-g11 reading)
G_RT (plan 012): mandatory streams must complete inside the cap and not be stopped; g11 must have written
mandatory_done inside the cap and its own budget. The orchestrator copies the g11 events into RUN_STATE_012.json
'events' when that stream ends.
Stops: at RUN_T0 + 7200 s the orchestrator stops every running stream (SIGTERM, SIGKILL after 10 s), seals each
checkpoint as it is (--seal-partial / --summarize-only; never a new case) and writes STOP_012_ORCHESTRATOR.json (the
watchdog writes STOP_012.json). Every stream completion is stamped (wall epoch) in RUN_STATE_012.json
'completed_at'. PROGRESS_012.json (read-only projection) is written at t0 + 360 s.
Dry-run hooks (only with SMOKE=1 and a directory outside results/study-012): CAP_S, BUDGET_S, LIMIT, SKIP_GTI.
"""
from __future__ import annotations
import json,os,shlex,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/'results/study-012'
D=Path(os.environ.get('STUDY_DIR_012',STUDY))
PY=os.environ.get('PY','/workspace/bgr/venv/bin/python')
CAP=7200
MAX_WORKERS=8
GRACE=10
PROGRESS_AT=360
SM=['--smoke'] if os.environ.get('SMOKE') else []
if SM and os.environ.get('CAP_S'):CAP=int(os.environ['CAP_S'])
DRY_BUDGET=int(os.environ['BUDGET_S']) if SM and os.environ.get('BUDGET_S') else None
LIM=['--limit',os.environ['LIMIT']] if SM and os.environ.get('LIMIT') else []


def study(block,workers,out,extra=()):
    return [PY,'-m','experiments.brute_study_012','--block',block,'--workers',str(workers),'--output',str(out),*extra,*SM,*LIM]


def g11(block,workers):
    out=D/f'SECOND_IMPLEMENTATION_012_{block}.json';ck=D/f'SECOND_IMPLEMENTATION_012_{block}_CHECKPOINT.jsonl'
    extra=['--smoke-all-mandatory'] if SM else []
    base=[PY,'scripts/run_reference_012.py','--block',block,'--results',str(D/block/'RESULTS.json'),'--checkpoint',str(ck),'--output',str(out),
          '--transfer-results',str(D/'transfer/RESULTS.json'),*extra]
    return base+['--workers',str(workers)],out,('summary',out,base+['--summarize-only'])


def repro(workers):
    """One stream, one process group: repro/2x2 then repro/transfer (every run index % 3 == 0)."""
    R=('--every','3','--offset','0');parts=[('2x2',D/'repro/2x2',R),('transfer',D/'repro/transfer',R)]
    cmd=['bash','-c',' && '.join(shlex.join(study(b,workers,o,e)) for b,o,e in parts)]
    return cmd,D/'repro/transfer/SEAL.json',('studies',parts)


def tasks():
    g2,g2o,g2f=g11('2x2',2);rc,ro,rf=repro(2)
    T=[('2x2',3,2400,[],study('2x2',3,D/'2x2'),D/'2x2/SEAL.json',('study','2x2',D/'2x2',()),True),
       ('big78',2,2700,[],study('big78',2,D/'big78'),D/'big78/SEAL.json',('study','big78',D/'big78',()),True),
       ('transfer',1,1200,[],study('transfer',1,D/'transfer'),D/'transfer/SEAL.json',('study','transfer',D/'transfer',()),True),
       ('gti',2,2400,[],[PY,'scripts/run_tests_0100.py','--output',str(D/'TEST_SUITE_012.json')],D/'TEST_SUITE_012.json',None,True),
       ('repro',2,1200,['2x2'],rc,ro,rf,True),
       ('g11',2,1500,['2x2','transfer'],g2,g2o,g2f,True)]
    T=[dict(zip(('name','workers','budget','deps','cmd','done','finalize','mandatory'),t)) for t in T]
    if DRY_BUDGET:
        for t in T:t['budget']=DRY_BUDGET
    if os.environ.get('SKIP_GTI') and SM:T=[t for t in T if t['name']!='gti']
    return T


def now():return time.time()
def stamp(t=None):return time.strftime('%Y-%m-%dT%H:%M:%S%z',time.localtime(t))
def log(msg):print(f'[{stamp()}] {msg}',flush=True)


def load_state():
    p=D/'RUN_STATE_012.json'
    st=json.loads(p.read_text()) if p.exists() else {}
    for k in ('spent','stopped','finished','running','completed_at','started_at'):st.setdefault(k,{})
    return st


def save_state(st):
    p=D/'RUN_STATE_012.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(st,indent=1,sort_keys=True));tmp.replace(p)


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
    if f[0]=='studies':
        for block,out,extra in f[1]:
            if Path(out,'SEAL.json').exists():continue
            finalize({'name':f"{t['name']}:{block}",'finalize':('study',block,out,extra),'done':Path(out,'SEAL.json')},reason)
        return
    if f[0]=='study':
        _,block,out,extra=f;Path(out).mkdir(parents=True,exist_ok=True);Path(out,'CHECKPOINT.jsonl').touch()
        cmd=[PY,'-m','experiments.brute_study_012','--block',block,'--output',str(out),'--seal-partial',*extra,*SM,*LIM]
    else:
        cmd=f[2];ck=Path(cmd[cmd.index('--checkpoint')+1]);ck.touch()
        if '--results' in cmd and not Path(cmd[cmd.index('--results')+1]).exists():log(f"{t['name']}: no results file to summarise ({reason})");return
    r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True)
    log(f"{t['name']}: sealed as it is ({reason}) rc={r.returncode} {r.stdout.strip()[-300:]} {r.stderr.strip()[-300:]}")


def g11_events(st):
    """Copy the g11 checkpoint events (start, mutation, mandatory_done, transfer_done, optional_done) into the run state (G_RT (i))."""
    ck=D/'SECOND_IMPLEMENTATION_012_2x2_CHECKPOINT.jsonl'
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
    if f[0]=='studies':return sum(sum(1 for _ in open(Path(o)/'CHECKPOINT.jsonl')) for _,o,_ in f[1] if (Path(o)/'CHECKPOINT.jsonl').exists())
    ck=Path(f[2])/'CHECKPOINT.jsonl' if f[0]=='study' else Path(f[2][f[2].index('--checkpoint')+1])
    return sum(1 for _ in open(ck)) if ck.exists() else None


def expected(t):
    f=t['finalize']
    if not f or f[0] not in ('study','studies'):return None
    from experiments.brute_study_012 import _select
    from experiments.brute_common_012 import load,PLAN
    parts=[(f[1],f[2],f[3])] if f[0]=='study' else f[1];n=0
    for block,_,ex in parts:
        every=int(ex[1]) if ex else 1;n+=len(_select(load(PLAN),block,bool(SM),every,0,int(LIM[1]) if LIM else None))
    return n


def progress(T,st,t0):
    p=D/'PROGRESS_012.json'
    if p.exists():return
    rep={'written_at':stamp(),'elapsed_s':round(now()-t0),'note':'read-only projection (stop_rule); no design, budget or seed change follows','streams':{}}
    for t in T:
        n=t['name'];el=st['spent'].get(n,0)+(now()-st['running'][n]['since'] if n in st['running'] else 0);done=ck_lines(t);E=expected(t)
        proj=round(el*E/done) if done and E else None
        rep['streams'][n]={'mandatory':t['mandatory'],'done':t['done'].exists(),'checkpoint_lines':done,'expected_cases':E,'spent_s':round(el),'budget_s':t['budget'],
                           'projected_total_s':proj,'projected_over_budget':None if proj is None else proj>t['budget'],'stopped':st['stopped'].get(n)}
    p.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n');log('PROGRESS_012.json written: '+json.dumps({k:(v['checkpoint_lines'],v['expected_cases'],v['projected_total_s']) for k,v in rep['streams'].items()}))


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
    if SM and D.resolve().is_relative_to(STUDY.resolve()):raise SystemExit('smoke directory must be outside results/study-012')
    if not (D/'RUN_T0').exists():raise SystemExit('RUN_T0 missing: append the ledger run_start_012 entry and write its epoch to RUN_T0 first')
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
            (D/'STOP_012_ORCHESTRATOR.json').write_text(json.dumps({'stopped_at':stamp(),'cap_s':CAP,'t0':t0,'unfinished_or_stopped':unfinished,
                                                                   'stopped':st['stopped']},indent=1,sort_keys=True)+'\n')
            log(f'STOP_012_ORCHESTRATOR written: {unfinished}');return 2
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
            (D/'RUN_DONE_012.json').write_text(json.dumps({'finished_at':stamp(),'elapsed_s':round(now()-t0),'t0':t0,
                'spent':{k:round(v) for k,v in st['spent'].items()},'stopped':st['stopped'],'finished':st['finished'],
                'completed_at':st['completed_at'],'mandatory':st['mandatory'],'events':st.get('events',{})},indent=1,sort_keys=True)+'\n')
            log(f'RUN_DONE ({now()-t0:.0f} s since t0; stopped streams: {st["stopped"]})');return 0
        time.sleep(2)


if __name__=='__main__':sys.exit(main())
