"""Independent watchdog for study-010 (BRUTE_PLAN_010 process_controls.watchdog, stop_rule).

Started by the operator with nohup in its own session right after RUN_T0 is written:
    nohup setsid $PY scripts/watchdog_010.py > results/study-010/WATCHDOG_010.log 2>&1 &
Every 2 s it appends {wall, monotonic, gap_s} to HEARTBEAT_010.jsonl (a wall gap > 10 s is a suspected VM suspension,
reported, never excluded). It tracks the orchestrator pid and every stream process group listed in RUN_STATE_010.json
(the union of all pgids ever seen). At RUN_T0 + cap it sends SIGTERM to the orchestrator and to every tracked process
group, SIGKILL after 20 s to whatever survives, and writes STOP_010.json with the deadline, the kill wall time and the
kill latency (last tracked process gone - deadline). It exits early, without killing, once RUN_DONE_010.json exists.
--cap may differ from 7200 only for a smoke drill whose directory is outside results/study-010.
"""
from __future__ import annotations
import argparse,json,os,signal,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/'results/study-010'
CAP=7200
PERIOD=2.0
KILL_AFTER=20.0
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


def read_state(d):
    try:return json.loads((d/'RUN_STATE_010.json').read_text())
    except (OSError,ValueError):return {}


def run(d,cap=CAP,period=PERIOD,kill_after=KILL_AFTER):
    d=Path(d);d.mkdir(parents=True,exist_ok=True)
    t0=float((d/'RUN_T0').read_text().split()[0]);deadline=t0+cap
    hb=open(d/'HEARTBEAT_010.jsonl','a');pgids=set();orch=set();last=None;gaps=[]
    print(f'[{stamp()}] watchdog start pid {os.getpid()}; deadline {stamp(deadline)} (cap {cap} s)',flush=True)
    while True:
        w=time.time();m=time.monotonic();gap=None if last is None else round(w-last,3);last=w
        if gap is not None and gap>GAP:gaps.append({'at':stamp(w),'gap_s':gap})
        hb.write(json.dumps({'wall':round(w,3),'monotonic':round(m,3),'gap_s':gap})+'\n');hb.flush();os.fsync(hb.fileno())
        st=read_state(d)
        if st.get('orchestrator_pid'):orch.add(int(st['orchestrator_pid']))
        for r in st.get('running',{}).values():pgids.add(int(r['pgid']))
        if (d/'RUN_DONE_010.json').exists():
            print(f'[{stamp()}] RUN_DONE_010.json present: watchdog exits without killing; gaps>10s {gaps}',flush=True);hb.close();return 0
        if w>=deadline:break
        time.sleep(max(0.,min(period,deadline-time.time())))
    hb.close();fire=time.time();print(f'[{stamp(fire)}] DEADLINE: SIGTERM orchestrator {sorted(orch)} and process groups {sorted(pgids)}',flush=True)
    for p in orch:
        try:os.kill(p,signal.SIGTERM)
        except ProcessLookupError:pass
    for g in pgids:
        try:os.killpg(g,signal.SIGTERM)
        except ProcessLookupError:pass
    def survivors():return [p for p in orch if pid_alive(p)]+[p for g in pgids for p in alive_in_group(g)]
    killed=False
    while survivors() and time.time()-fire<kill_after:time.sleep(0.2)
    if survivors():
        killed=True;print(f'[{stamp()}] SIGKILL survivors {survivors()}',flush=True)
        for p in orch:
            try:os.kill(p,signal.SIGKILL)
            except ProcessLookupError:pass
        for g in pgids:
            try:os.killpg(g,signal.SIGKILL)
            except ProcessLookupError:pass
        while survivors() and time.time()-fire<kill_after+10:time.sleep(0.2)
    gone=time.time();left=survivors()
    rep={'deadline':stamp(deadline),'deadline_epoch':deadline,'cap_s':cap,'t0':t0,'fired_at':stamp(fire),'fire_delay_s':round(fire-deadline,3),
         'all_gone_at':stamp(gone),'kill_latency_s':round(gone-deadline,3),'sigkill_used':killed,'survivors':left,
         'orchestrator_pids':sorted(orch),'process_groups':sorted(pgids),'heartbeat_gaps_over_10s':gaps}
    p=d/'STOP_010.json'
    if p.exists():p=d/'STOP_010_WATCHDOG.json'
    p.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n');print(f'[{stamp()}] {p.name} written: latency {rep["kill_latency_s"]} s',flush=True)
    return 3


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dir',default=str(STUDY));ap.add_argument('--cap',type=int,default=CAP)
    a=ap.parse_args()
    if a.cap!=CAP and Path(a.dir).resolve().is_relative_to(STUDY.resolve()):raise SystemExit('--cap override only outside results/study-010')
    raise SystemExit(run(a.dir,a.cap))


if __name__=='__main__':main()
