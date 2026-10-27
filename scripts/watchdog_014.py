"""Independent watchdog for study-014 (BRUTE_PLAN_014 watchdog_definition, stop_rule.watchdog; watchdog_013 untouched).

Started by the operator with nohup in its own session right after RUN_T0 is written:
    nohup setsid $PY scripts/watchdog_014.py > results/study-014/WATCHDOG_014.log 2>&1 &
Changes against watchdog_013 (the heartbeat-gap fix):
 (1) every 2 s one line is appended to HEARTBEAT_014.jsonl with a plain buffered write + flush, no per-beat fsync;
     a background thread calls os.fsync on the heartbeat file every 30 s;
 (2) the deadline / kill logic runs in its own thread that does no disk I/O before the kill: it sleeps on
     CLOCK_MONOTONIC until RUN_T0 + cap (the wall deadline converted once at start), then SIGSTOPs the orchestrator,
     adds the process group of every orchestrator descendant (from /proc, procfs only), SIGTERMs the orchestrator and
     every process group of an in-memory copy of RUN_STATE_014 refreshed by the main thread, SIGKILLs survivors after
     20 s, and only then writes STOP_014.json (deadline, fire delay, kill latency = last tracked process gone - deadline);
 (3) every beat records wall, CLOCK_MONOTONIC, CLOCK_BOOTTIME, process CPU time and the /proc/pressure/io some/full
     total (microseconds), so a gap can be attributed (descheduled host: BOOTTIME and MONOTONIC advance, CPU and PSI
     flat; I/O stall: PSI full total advances).
It exits early, without killing, once RUN_DONE_014.json exists. --cap may differ from 7200 only for a smoke drill
whose directory is outside results/study-014.
"""
from __future__ import annotations
import argparse,json,os,signal,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/'results/study-014'
CAP=7200
PERIOD=2.0
KILL_AFTER=20.0
FSYNC_EVERY=30.0
GAP=10.0


def stamp(t=None):return time.strftime('%Y-%m-%dT%H:%M:%S%z',time.localtime(t))


def alive_in_group(pg):
    """pids (not zombies) whose process group is pg."""
    out=[]
    for d in os.listdir('/proc'):
        if not d.isdigit():continue
        try:
            s=Path(f'/proc/{d}/stat').read_text();r=s[s.rindex(')')+2:].split()
            if r[0]!='Z' and int(r[2])==pg:out.append(int(d))
        except (OSError,ValueError,IndexError):pass
    return out


def pid_alive(pid):
    try:
        s=Path(f'/proc/{pid}/stat').read_text();return s[s.rindex(')')+2:].split()[0]!='Z'
    except OSError:return False


def descendants(roots):
    """every live pid whose parent chain reaches one of roots (from /proc)."""
    par={}
    for d in os.listdir('/proc'):
        if not d.isdigit():continue
        try:s=Path(f'/proc/{d}/stat').read_text();par[int(d)]=int(s[s.rindex(')')+2:].split()[1])
        except (OSError,ValueError,IndexError):pass
    out=set();roots=set(roots)
    for p in par:
        q=p;seen=0
        while q in par and seen<64:
            q=par[q];seen+=1
            if q in roots:out.add(p);break
    return out


def read_state(d):
    try:return json.loads((d/'RUN_STATE_014.json').read_text())
    except (OSError,ValueError):return {}


def psi_io():
    """{'some': total_us, 'full': total_us} from /proc/pressure/io, or None if unavailable."""
    try:
        out={}
        for line in Path('/proc/pressure/io').read_text().split('\n'):
            if line:k,*f=line.split();out[k]=int(dict(x.split('=') for x in f)['total'])
        return out
    except (OSError,ValueError,KeyError):return None


def beat(last):
    w=time.time();m=time.monotonic()
    try:b=time.clock_gettime(time.CLOCK_BOOTTIME)
    except (AttributeError,OSError):b=None
    p=psi_io()
    rec={'wall':round(w,3),'monotonic':round(m,3),'boottime':None if b is None else round(b,3),'cpu_s':round(time.process_time(),4),
         'psi_io_some_us':p and p.get('some'),'psi_io_full_us':p and p.get('full'),'gap_s':None if last is None else round(w-last,3)}
    return w,rec


class Shared:
    def __init__(self):self.lock=threading.Lock();self.orch=set();self.pgids=set()
    def update(self,st):
        with self.lock:
            if st.get('orchestrator_pid'):self.orch.add(int(st['orchestrator_pid']))
            for r in st.get('running',{}).values():self.pgids.add(int(r['pgid']))
    def copy(self):
        with self.lock:return set(self.orch),set(self.pgids)


def _sig(pids,groups,s):
    for p in pids:
        try:os.kill(p,s)
        except ProcessLookupError:pass
    for g in groups:
        try:os.killpg(g,s)
        except ProcessLookupError:pass


def killer(d,t0,cap,deadline_mono,shared,done,stop_evt,kill_after,result):
    """Kill thread: no disk I/O before the kill."""
    while not stop_evt.is_set():
        left=deadline_mono-time.monotonic()
        if left<=0:break
        stop_evt.wait(min(left,1.0))
    if stop_evt.is_set():return
    fire_m=time.monotonic();fire=time.time();orch,pgids=shared.copy()
    _sig(orch,(),signal.SIGSTOP)                       # freeze the orchestrator so it cannot start a stream while we collect
    for p in descendants(orch):
        try:pgids.add(os.getpgid(p))
        except ProcessLookupError:pass
    pgids-={os.getpgid(0)}
    _sig(orch,pgids,signal.SIGTERM);_sig(orch,(),signal.SIGCONT)
    def survivors():return [p for p in orch if pid_alive(p)]+[p for g in pgids for p in alive_in_group(g)]
    killed=False
    while survivors() and time.monotonic()-fire_m<kill_after:time.sleep(0.2)
    if survivors():
        killed=True;_sig(orch,pgids,signal.SIGKILL)
        while survivors() and time.monotonic()-fire_m<kill_after+10:time.sleep(0.2)
    gone_m=time.monotonic();gone=time.time();left=survivors();deadline=t0+cap
    rep={'deadline':stamp(deadline),'deadline_epoch':deadline,'cap_s':cap,'t0':t0,'fired_at':stamp(fire),
         'fire_delay_s':round(fire-deadline,3),'fire_delay_monotonic_s':round(fire_m-deadline_mono,3),
         'all_gone_at':stamp(gone),'kill_latency_s':round(gone-deadline,3),'kill_latency_monotonic_s':round(gone_m-deadline_mono,3),
         'sigkill_used':killed,'survivors':left,'orchestrator_pids':sorted(orch),'process_groups':sorted(pgids),
         'kill_thread_disk_io_before_kill':False}
    p=d/'STOP_014.json'
    if p.exists():p=d/'STOP_014_WATCHDOG.json'
    p.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n');result.update(rep);done.set()
    print(f'[{stamp()}] {p.name} written: latency {rep["kill_latency_s"]} s, survivors {left}',flush=True)


def fsyncer(hb,lock,stop_evt,every):
    while not stop_evt.wait(every):
        with lock:
            try:hb.flush();os.fsync(hb.fileno())
            except (OSError,ValueError):return


def run(d,cap=CAP,period=PERIOD,kill_after=KILL_AFTER,fsync_every=FSYNC_EVERY):
    d=Path(d);d.mkdir(parents=True,exist_ok=True)
    t0=float((d/'RUN_T0').read_text().split()[0]);deadline=t0+cap
    deadline_mono=time.monotonic()+(deadline-time.time())
    hb=open(d/'HEARTBEAT_014.jsonl','a');hlock=threading.Lock();shared=Shared();shared.update(read_state(d))
    stop_evt=threading.Event();done=threading.Event();result={};last=None;gaps=[]
    kt=threading.Thread(target=killer,args=(d,t0,cap,deadline_mono,shared,done,stop_evt,kill_after,result),daemon=True)
    ft=threading.Thread(target=fsyncer,args=(hb,hlock,stop_evt,fsync_every),daemon=True)
    print(f'[{stamp()}] watchdog_014 start pid {os.getpid()}; deadline {stamp(deadline)} (cap {cap} s)',flush=True)
    kt.start();ft.start();nxt=time.monotonic()
    while True:
        last,rec=beat(last)
        if rec['gap_s'] is not None and rec['gap_s']>GAP:gaps.append({'at':stamp(rec['wall']),'gap_s':rec['gap_s']})
        with hlock:hb.write(json.dumps(rec)+'\n');hb.flush()
        shared.update(read_state(d))
        if (d/'RUN_DONE_014.json').exists() and not done.is_set() and time.monotonic()<deadline_mono:
            stop_evt.set();kt.join();ft.join()
            with hlock:hb.flush();os.fsync(hb.fileno());hb.close()
            print(f'[{stamp()}] RUN_DONE_014.json present: watchdog exits without killing; gaps>10s {gaps}',flush=True);return 0
        if done.is_set():
            stop_evt.set();ft.join()
            with hlock:hb.flush();os.fsync(hb.fileno());hb.close()
            print(f'[{stamp()}] kill done; gaps>10s {gaps}',flush=True);return 3
        nxt+=period;time.sleep(max(0.,nxt-time.monotonic()))
        if time.monotonic()-nxt>period:nxt=time.monotonic()   # do not burst after a stall


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dir',default=str(STUDY));ap.add_argument('--cap',type=int,default=CAP)
    a=ap.parse_args()
    if a.cap!=CAP and Path(a.dir).resolve().is_relative_to(STUDY.resolve()):raise SystemExit('--cap override only outside results/study-014')
    raise SystemExit(run(a.dir,a.cap))


if __name__=='__main__':main()
