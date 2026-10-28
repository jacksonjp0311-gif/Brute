"""Kill drill and resume drill for study-023 (BRUTE_PLAN_023 G_RT kill drill <= 15 s; G_RD resume drill). Both run on
block smoke-drill (SMOKE=1, SKIP_GTI=1, BRUTE_SMOKE_DRILL=1) in scratch directories OUTSIDE results/study-023, before
the source freeze; outputs (refuse overwrite) go to results/smoke-023/.

  kill    D=<scratch>/drill: RUN_T0 = now, orchestrator CAP_S=600 (so the watchdog, not the orchestrator, fires) and
          watchdog_023 --dir D --cap 15, both detached (setsid). Records STOP_023.json, heartbeat gaps, the partial
          checkpoint. PASS iff the watchdog fired, kill_latency_s <= 15, no survivors, every checkpoint line parses.
          -> KILL_DRILL_023.json
  resume  REF=<scratch>/rd_ref: one uninterrupted orchestrator run.  RD=<scratch>/rd: the same run, every process of
          the orchestrator session SIGKILLed at 45 s after launch (a crash, no cleanup), then relaunched ONCE.
          (i) every stream of RD finished (RUN_DONE_023.json, no stopped stream);
          (ii) each case of RD transfer/SCIENTIFIC.json is byte-identical (canonical JSON after removing every key
               ending in _informational, = make_reproducibility_023.strip_timing) to REF, same case set;
          (iii) RD spent['transfer'] >= the transfer time elapsed before the kill (from the last RUN_STATE heartbeat);
          (iv) no duplicate checkpoint key in any RD study checkpoint (transfer, repro).
          -> RESUME_DRILL_023.json
  PYTHONPATH=. python scripts/drill_023.py kill|resume [--scratch /tmp/s23]"""
from __future__ import annotations
import argparse,json,os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.make_reproducibility_023 import strip_timing
PY=os.environ.get('PY','/workspace/bgr/venv/bin/python');OUT=ROOT/'results/smoke-023'
KILL_AT=45


def stamp(t=None):return time.strftime('%Y-%m-%dT%H:%M:%S%z',time.localtime(t))


def env(d,cap):return dict(os.environ,PYTHONPATH=str(ROOT),SMOKE='1',SKIP_GTI='1',BRUTE_SMOKE_DRILL='1',CAP_S=str(cap),STUDY_DIR_023=str(d),PY=PY)


def launch(d,cap,log='RUN_023.log'):
    return subprocess.Popen([PY,'scripts/run_study_023.py'],cwd=ROOT,env=env(d,cap),stdout=open(d/log,'a'),stderr=subprocess.STDOUT,start_new_session=True)


def fresh(d):
    d=Path(d);d.mkdir(parents=True,exist_ok=False);(d/'RUN_T0').write_text(f'{time.time():.6f}\n');return d


def write(name,obj):
    p=OUT/name;OUT.mkdir(parents=True,exist_ok=True)
    if p.exists():raise SystemExit(f'{p} exists: refusing to overwrite')
    p.write_text(json.dumps(obj,indent=1,sort_keys=True)+'\n');print(json.dumps({k:obj[k] for k in ('passed','clauses') if k in obj}))


def lines(p):
    out=[];bad=0
    for l in (Path(p).read_text().splitlines() if Path(p).exists() else []):
        try:out.append(json.loads(l))
        except Exception:bad+=1
    return out,bad


def kill(scratch):
    d=fresh(Path(scratch)/'drill');o=launch(d,600);time.sleep(1)
    w=subprocess.run([PY,'scripts/watchdog_023.py','--dir',str(d),'--cap','15'],cwd=ROOT,env=dict(os.environ,PYTHONPATH=str(ROOT)),
                     capture_output=True,text=True,start_new_session=True,timeout=120)
    time.sleep(1);o.poll();stop=json.loads((d/'STOP_023.json').read_text()) if (d/'STOP_023.json').exists() else None
    hb,_=lines(d/'HEARTBEAT_023.jsonl');gaps=[r.get('gap_s') for r in hb if r.get('gap_s') is not None]
    ck,bad=lines(d/'transfer/CHECKPOINT.jsonl')
    rep={'schema':'brute.kill-drill.v2','setup':f'SMOKE=1 SKIP_GTI=1 BRUTE_SMOKE_DRILL=1, orchestrator CAP_S=600, watchdog_023 --dir {d} --cap 15',
         **(stop or {}),'heartbeat':{'beats':len(hb),'max_gap_s':max(gaps) if gaps else None,'gaps_over_10s':[g for g in gaps if g>10]},
         'partial_checkpoint':{'case_lines':len(ck),'all_lines_parse':bad==0},'orchestrator_returncode':o.returncode,
         'orchestrator_log':(d/'RUN_023.log').read_text().splitlines()[:6],'watchdog_stdout_tail':w.stdout.splitlines()[-3:]}
    rep['passed']=bool(stop) and stop.get('kill_latency_s',99)<=15 and not stop.get('survivors') and bad==0
    rep['label']='Observed (block smoke-drill; outside the cap; scratch directory).'
    write('KILL_DRILL_023.json',rep)


def wait(p,d,limit):
    t=time.time()
    while p.poll() is None and time.time()-t<limit:time.sleep(2)
    return p.poll()


def session_pids(sid):
    out=[]
    for x in os.listdir('/proc'):
        if not x.isdigit():continue
        try:
            s=Path(f'/proc/{x}/stat').read_text();r=s[s.rindex(')')+2:].split()
            if int(r[3])==sid and r[0]!='Z':out.append(int(x))
        except (FileNotFoundError,ProcessLookupError,ValueError,IndexError):pass
    return out


def resume(scratch):
    ref=fresh(Path(scratch)/'rd_ref');rd=fresh(Path(scratch)/'rd');t_launch=time.time()
    pr=launch(ref,3000);p1=launch(rd,3000);time.sleep(KILL_AT)
    st0=json.loads((rd/'RUN_STATE_023.json').read_text());kill_t=time.time()
    pg={p1.pid}|{v['pgid'] for v in st0.get('running',{}).values()};victims=sorted(set(session_pids(p1.pid)))
    for g in pg:
        try:os.killpg(g,signal.SIGKILL)
        except ProcessLookupError:pass
    t=time.time()
    while any(session_pids(g) for g in pg) and time.time()-t<20:time.sleep(0.2)
    p1.wait();left=[x for g in pg for x in session_pids(g)]
    run=st0.get('running',{}).get('transfer');pre=(st0.get('heartbeat',kill_t)-run['since'])+run.get('spent_before',0) if run else None
    p2=launch(rd,3000);rc2=wait(p2,rd,2400);rc1=wait(pr,ref,2400)
    st=json.loads((rd/'RUN_STATE_023.json').read_text());done=(rd/'RUN_DONE_023.json').exists()
    def cases(d):
        p=d/'transfer/SCIENTIFIC.json'
        return {} if not p.exists() else {f"{c['block']}/{c['family']}/{c['seed']}/{c['eps']}":json.dumps(strip_timing(c),sort_keys=True,separators=(',',':')) for c in json.loads(p.read_text())['cases']}
    A=cases(ref);B=cases(rd);diff=sorted(k for k in set(A)|set(B) if A.get(k)!=B.get(k))
    dup={}
    for s in ('transfer','repro/smoke'):
        ks=[r.get('key') for r in lines(rd/s/'CHECKPOINT.jsonl')[0] if 'key' in r];dup[s]={'lines':len(ks),'duplicates':len(ks)-len({json.dumps(k) for k in ks})}
    cl={'i_all_streams_complete':done and not st.get('stopped') and (ref/'RUN_DONE_023.json').exists(),
        'ii_scientific_identical_per_case':bool(A) and set(A)==set(B) and not diff,
        'iii_spent_includes_pre_kill_time':pre is not None and st['spent'].get('transfer',0)>=pre,
        'iv_no_duplicate_checkpoint_keys':all(v['duplicates']==0 and v['lines']>0 for v in dup.values())}
    log=(rd/'RUN_023.log').read_text().splitlines()
    rep={'schema':'brute.resume-drill.v1','setup':f'SMOKE=1 SKIP_GTI=1 BRUTE_SMOKE_DRILL=1 CAP_S=3000; REF {ref} uninterrupted; RD {rd} SIGKILL of the whole orchestrator session at {KILL_AT} s, relaunched once; REF and RD ran concurrently',
         'clauses':cl,'passed':all(cl.values()),'killed_at':stamp(kill_t),'kill_after_launch_s':round(kill_t-t_launch,3),'killed_process_groups':sorted(pg),
         'pids_before_kill':victims,'survivors':left,'state_at_kill':{k:st0.get(k) for k in ('running','spent','finished')},
         'transfer_elapsed_before_kill_s':None if pre is None else round(pre,3),'spent_final':st.get('spent'),'stopped_final':st.get('stopped'),
         'relaunch_returncode':rc2,'reference_returncode':rc1,'cases_ref':len(A),'cases_rd':len(B),'differing_cases':diff[:20],'checkpoints':dup,
         'orphan_log_lines':[l for l in log if 'orphan' in l],'label':'Observed (block smoke-drill; outside the cap; scratch directories).'}
    write('RESUME_DRILL_023.json',rep)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('drill',choices=('kill','resume'));ap.add_argument('--scratch',default='/tmp/s23')
    a=ap.parse_args();(kill if a.drill=='kill' else resume)(a.scratch)
