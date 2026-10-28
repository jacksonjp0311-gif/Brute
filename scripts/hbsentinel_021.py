"""Heartbeat sentinel for study-021 (deviation #90, as study-018). REPORTED, UNGATED diagnostic:
it never kills, never touches the watchdog (scripts/watchdog_021.py -> frozen watchdog_014, byte-identical) and does not
change G_HB (max watchdog heartbeat gap <= 30 s).

A tight loop ticks every 0.25 s on CLOCK_MONOTONIC. Every 2 s (monotonic) one JSON line is appended to
HB_SENTINEL_021.jsonl (buffered write + flush; fsync every 30 s):
  wall, monotonic, boottime          - the three clocks at the record
  max_tick_gap_mono / _wall          - the largest gap between consecutive 0.25 s ticks since the last record
  workers_cpu_s                      - utime + stime of every live orchestrator descendant + the orchestrator's own
                                       utime + stime + cutime + cstime (seconds; /proc; reaped children are counted via
                                       cutime / cstime, so the sum is approximately monotone)
  n_desc                             - live orchestrator descendants
  cpu_jiffies                        - /proc/stat aggregate user, nice, system, idle, iowait, irq, softirq, steal
  ckpt_bytes                         - total size of every *CHECKPOINT*.jsonl under the study directory (files written)
How to read a gap (scripts/hb_attribution_021.py): a box-wide pause (the VM / container descheduled) stalls the sentinel
too (its tick gap ~ the watchdog gap) and the workers accrue little CPU; a stall of the watchdog process alone leaves the
sentinel ticking; a suspend shows d_boot - d_mono > 1 s; a wall-clock step shows |d_wall - d_boot| > 1 s.
    nohup setsid $PY scripts/hbsentinel_021.py > results/study-021/HB_SENTINEL_021.log 2>&1 &
Exits once RUN_DONE_021.json or STOP_021.json exists (after one last record), or 600 s after RUN_T0 + cap.
"""
from __future__ import annotations
import argparse,json,os,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/'results/study-021'
CAP=7200
TICK=0.25
PERIOD=2.0
FSYNC_EVERY=30.0
HZ=os.sysconf('SC_CLK_TCK')


def _stat(pid):
    s=Path(f'/proc/{pid}/stat').read_text();return s[s.rindex(')')+2:].split()


def proc_table():
    """{pid: (ppid, utime + stime, cutime + cstime) in jiffies}."""
    out={}
    for d in os.listdir('/proc'):
        if not d.isdigit():continue
        try:r=_stat(d);out[int(d)]=(int(r[1]),int(r[11])+int(r[12]),int(r[13])+int(r[14]))
        except (OSError,ValueError,IndexError):pass
    return out


def workers_cpu(orch):
    """(seconds, n_desc) for the orchestrator tree, or (None, 0) if unknown."""
    if not orch:return None,0
    T=proc_table()
    if orch not in T:return None,0
    tot=T[orch][1]+T[orch][2];n=0
    for p,(pp,u,_) in T.items():
        q=p;k=0
        while q in T and k<64:
            q=T[q][0];k+=1
            if q==orch:tot+=u;n+=1;break
    return round(tot/HZ,2),n


def cpu_jiffies():
    try:
        f=Path('/proc/stat').read_text().split('\n')[0].split()[1:9];return dict(zip(('user','nice','system','idle','iowait','irq','softirq','steal'),map(int,f)))
    except (OSError,ValueError):return None


def ckpt_bytes(d):
    n=0
    for p in d.rglob('*CHECKPOINT*.jsonl'):
        try:n+=p.stat().st_size
        except OSError:pass
    return n


def orch_pid(d):
    try:return int(json.loads((d/'RUN_STATE_021.json').read_text()).get('orchestrator_pid') or 0) or None
    except (OSError,ValueError):return None


def record(d,gm,gw):
    w=time.time();m=time.monotonic()
    try:b=time.clock_gettime(time.CLOCK_BOOTTIME)
    except (AttributeError,OSError):b=None
    cpu,n=workers_cpu(orch_pid(d))
    return {'wall':round(w,3),'monotonic':round(m,3),'boottime':None if b is None else round(b,3),'max_tick_gap_mono':round(gm,3),
            'max_tick_gap_wall':round(gw,3),'workers_cpu_s':cpu,'n_desc':n,'cpu_jiffies':cpu_jiffies(),'ckpt_bytes':ckpt_bytes(d)}


def run(d,cap):
    d=Path(d);t0=float((d/'RUN_T0').read_text().split()[0]);end=t0+cap+600
    f=open(d/'HB_SENTINEL_021.jsonl','a');lm=time.monotonic();lw=time.time();nxt=lm+PERIOD;fs=lm+FSYNC_EVERY;gm=gw=0.0
    print(f'sentinel start pid {os.getpid()} tick {TICK} s period {PERIOD} s',flush=True)
    while True:
        time.sleep(TICK);m=time.monotonic();w=time.time();gm=max(gm,m-lm);gw=max(gw,w-lw);lm,lw=m,w
        if m>=nxt:
            f.write(json.dumps(record(d,gm,gw),sort_keys=True)+'\n');f.flush();gm=gw=0.0;nxt=m+PERIOD
            if m>=fs:os.fsync(f.fileno());fs=m+FSYNC_EVERY
            if (d/'RUN_DONE_021.json').exists() or (d/'STOP_021.json').exists() or w>end:
                os.fsync(f.fileno());f.close();print('sentinel exit',flush=True);return 0


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--dir',default=str(STUDY));ap.add_argument('--cap',type=int,default=CAP)
    a=ap.parse_args()
    if a.cap!=CAP and Path(a.dir).resolve().is_relative_to(STUDY.resolve()):raise SystemExit('--cap differs from 7200 only outside results/study-021')
    raise SystemExit(run(a.dir,a.cap))
