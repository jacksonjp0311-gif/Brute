"""Heartbeat-gap attribution for study-020 (deviation #90). REPORTED, UNGATED: G_HB stays max watchdog gap <= 30 s.

Reads HEARTBEAT_020.jsonl (frozen watchdog_014 format via watchdog_020) and HB_SENTINEL_020.jsonl (scripts/
hbsentinel_020.py). For every consecutive watchdog beat pair with a wall gap > 10 s it reports d_wall, d_mono, d_boot,
the sentinel's largest tick gap overlapping the window (monotonic), worker CPU accrued in the window, the steal /
iowait / idle jiffy deltas, checkpoint bytes written, and one class (first match; every class is an Inferred reading):
  suspend         d_boot - d_mono > 1 s (MONOTONIC stops in suspend, BOOTTIME does not)
  clock_step      |d_wall - d_boot| > 1 s (d_mono when BOOTTIME is unavailable)
  box_pause       sentinel stalled >= 50 % of d_mono and worker CPU < 10 % of d_mono x max(n_desc, 1)
  watchdog_stall  the sentinel did not stall (largest tick gap < 50 % of d_mono)
  unattributed    none of the above (e.g. sentinel stalled but the workers kept computing)
    $PY scripts/hb_attribution_020.py [--dir results/study-020]  -> HEARTBEAT_ATTRIBUTION_020.json
"""
from __future__ import annotations
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GAP=10.0


def _jl(p):
    out=[]
    if not p.exists():return out
    for l in open(p):
        try:out.append(json.loads(l))
        except ValueError:pass
    return out


def classify(dw,dm,db,sg,cpu,n):
    if db is not None and db-dm>1:return 'suspend'
    if abs(dw-(db if db is not None else dm))>1:return 'clock_step'
    stalled=sg is not None and sg>=0.5*dm
    if stalled and cpu is not None and cpu<0.1*dm*max(n,1):return 'box_pause'
    if sg is not None and not stalled:return 'watchdog_stall'
    return 'unattributed'


def attribute(d):
    d=Path(d);H=_jl(d/'HEARTBEAT_020.jsonl');S=_jl(d/'HB_SENTINEL_020.jsonl');gaps=[]
    for a,b in zip(H,H[1:]):
        dw=b['wall']-a['wall']
        if dw<=GAP:continue
        dm=b['monotonic']-a['monotonic'];db=None if a.get('boottime') is None or b.get('boottime') is None else b['boottime']-a['boottime']
        lo,hi=a['monotonic'],b['monotonic']
        inside=[s for s in S if lo<=s['monotonic']<=hi+2.5]
        before=[s for s in S if s['monotonic']<lo];prev=before[-1] if before else None
        # largest sentinel stall overlapping the window: record-to-record monotonic gaps and in-record tick gaps
        seq=([prev] if prev else [])+inside;sg=None
        if seq:
            sg=max([s['max_tick_gap_mono'] for s in inside]+[y['monotonic']-x['monotonic']-2.0 for x,y in zip(seq,seq[1:])]+[0.0])
        cpu=None;n=0;jd=None;wb=None
        if prev and inside:
            last=inside[-1]
            if prev.get('workers_cpu_s') is not None and last.get('workers_cpu_s') is not None:cpu=round(last['workers_cpu_s']-prev['workers_cpu_s'],2)
            n=max([s['n_desc'] for s in [prev]+inside]);wb=last['ckpt_bytes']-prev['ckpt_bytes']
            if prev.get('cpu_jiffies') and last.get('cpu_jiffies'):jd={k:last['cpu_jiffies'][k]-prev['cpu_jiffies'][k] for k in ('steal','iowait','idle','user','system')}
        gaps.append({'from_wall':a['wall'],'gap_wall_s':round(dw,3),'d_mono_s':round(dm,3),'d_boot_s':None if db is None else round(db,3),
                     'sentinel_stall_s':None if sg is None else round(sg,3),'workers_cpu_s':cpu,'n_desc':n,'jiffies_delta':jd,
                     'ckpt_bytes_written':wb,'class':classify(dw,dm,db,sg,cpu,n),'label':'Inferred'})
    mx=max([b['wall']-a['wall'] for a,b in zip(H,H[1:])],default=None)
    rep={'schema':'brute.heartbeat-attribution.v1','gated':False,'label':'Inferred (classes are readings of clock / CPU evidence)',
         'G_HB_unchanged':'max watchdog heartbeat gap <= 30 s (gated separately in GATES_020)',
         'heartbeats':len(H),'sentinel_records':len(S),'max_watchdog_gap_s':None if mx is None else round(mx,3),
         'max_sentinel_tick_gap_s':max([s['max_tick_gap_mono'] for s in S],default=None),
         'gaps_over_10s':gaps,'class_counts':{c:sum(g['class']==c for g in gaps) for c in ('clock_step','suspend','box_pause','watchdog_stall','unattributed')}}
    return rep


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--dir',default=str(ROOT/'results/study-020'));ap.add_argument('--output')
    a=ap.parse_args();rep=attribute(a.dir);out=Path(a.output or Path(a.dir)/'HEARTBEAT_ATTRIBUTION_020.json')
    if out.exists():raise SystemExit('refusing overwrite '+str(out))
    out.write_text(json.dumps(rep,indent=1,sort_keys=True)+'\n');print(json.dumps(rep['class_counts']),rep['max_watchdog_gap_s'])
