"""Host-pause probe for study-024 (BRUTE_PLAN_024 non_gated_reports.host_pause_probe). Before run_start, beats once a second
for --duration seconds (default 600) with no other work, and records every gap between consecutive wall-clock beats.
Reported next to G_HB; it is never used to excuse G_HB. Output: results/diag-024/HOST_PAUSE_PROBE_024.json (refuses overwrite).
  PYTHONPATH=. python scripts/host_pause_probe_024.py [--duration 600] [--output F]"""
from __future__ import annotations
import argparse,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import write_new


def probe(duration,period=1.0):
    t0=time.time();W=[t0]
    while W[-1]-t0<duration:
        time.sleep(period);W.append(time.time())
    G=[round(b-a,3) for a,b in zip(W,W[1:])]
    return {'schema':'brute.host-pause-probe.v1','start_epoch':round(t0,3),'duration_s':round(W[-1]-t0,3),'period_s':period,'beats':len(W),
            'max_gap_s':max(G),'gaps_over_2s':sum(g>2 for g in G),'gaps_over_10s':sum(g>10 for g in G),'largest_gaps':sorted(G)[-5:],
            'label':'Observed; reported next to G_HB, never used to excuse it'}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--duration',type=float,default=600.0)
    ap.add_argument('--output',default=str(ROOT/'results/diag-024/HOST_PAUSE_PROBE_024.json'));a=ap.parse_args()
    r=probe(a.duration);Path(a.output).parent.mkdir(parents=True,exist_ok=True);write_new(Path(a.output),r)
    print({k:r[k] for k in ('duration_s','beats','max_gap_s','gaps_over_10s')})
