"""Early-window diagnostic for study-024 (BRUTE_PLAN_024 non_gated_reports.early_window_diagnostic; Open, never gated).

For every eps-0.02 main case, step t <= 28 and bit b, compare
  needed(arm) = m_arm(t) + 1   consistent observations of bit b: with a flip budget m an adversary can explain away up to m
                               contradicting readings, so fewer than m + 1 readings of b can never pin b (Inferred; a necessary
                               condition only, it ignores the action dynamics, which can only raise the need);
  supplied    = readings of bit b observed (not masked) in readings 0..t (Observed, from the SP8 trace).
Reports, per arm (RGL5, RGL4, RGNB4, RGN4_or): the share of (case, step, bit) slots with supplied < needed, mean needed, mean
supplied, and recorded certificates on steps 1..28. Output: results/diag-024/EARLY_WINDOW_024.json (refuses overwrite).
  PYTHONPATH=. python scripts/early_window_024.py [--study-dir D] [--output F] [--print]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import write_new
from experiments.v0170_reference import readings_main

PREFIX=28;ARMS=('RGL5','RGL4','RGNB4','RGN4_or')


def case_rows(c):
    R=readings_main(c);out={}
    for a in ARMS:
        m=c['noisy'][a]['m'];m=m if isinstance(m,list) else [m]*c['steps'];tr=c['certifiers'][a]['trace'];rows=[]
        for t in range(1,PREFIX+1):
            for b in (0,1):
                sup=sum(R[j][0][b] is not None for j in range(t+1));need=m[t-1]+1
                rows.append((need,sup,tr[t-1]['certificate'][b] is not None))
        out[a]=rows
    return out


def run(study):
    raw=study/'transfer/SCIENTIFIC.json'
    if not raw.exists():raw=study/'transfer/RESULTS.json'
    cases=[c for c in json.loads(raw.read_text())['cases'] if c['eps']==0.02 and c['block']!='stress']
    agg={a:[] for a in ARMS}
    for c in cases:
        for a,rows in case_rows(c).items():agg[a]+=rows
    summ={}
    for a,rows in agg.items():
        n=len(rows) or 1
        summ[a]={'slots':len(rows),'short_share':round(sum(s<d for d,s,_ in rows)/n,6),'mean_needed':round(sum(d for d,_,_ in rows)/n,6),
                 'mean_supplied':round(sum(s for _,s,_ in rows)/n,6),'certificates_steps_1_28':sum(x for *_,x in rows),
                 'certificates_when_short':sum(x and s<d for d,s,x in rows)}
    return {'schema':'brute.early-window.v1','cases':len(cases),'prefix':PREFIX,'source':raw.name,'summary':summ,
            'label':'Open (diagnostic); needed is an Inferred necessary condition, supplied is Observed'}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(ROOT/'results/study-024'))
    ap.add_argument('--output',default=str(ROOT/'results/diag-024/EARLY_WINDOW_024.json'));ap.add_argument('--print',action='store_true');a=ap.parse_args()
    r=run(Path(a.study_dir))
    if a.print:print(json.dumps(r['summary'],indent=1));raise SystemExit(0)
    Path(a.output).parent.mkdir(parents=True,exist_ok=True);write_new(Path(a.output),r);print(r['summary'])
