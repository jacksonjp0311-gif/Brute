"""Rate math for study-019 (plan stop_rule.g11_rate_projection; check: exits non-zero if any stream's projection > 0.8 of
its budget, or the critical path does not fit the 7200 s cap).

Inputs are measured on smoke seeds WITH the held-out concurrency (an orchestrator dry run, SMOKE=1, streams as in
scripts/run_study_019.STREAMS: transfer + gti from t0, then repro + g11):
  --transfer DIR    smoke-all RESULTS.json: case_wall_informational per case (16 main family x eps cells + the rand4a3 x eps cells)
  --g11 PATH        the smoke g11 checkpoint: wall_informational per audited case
  --gti PATH        the smoke TEST_SUITE json from scripts/run_tests_0170.py: wall per module + plain discovery
A held-out cell with no smoke measurement is an error.
Projection per stream (rule (2)): sum over cells of (held-out cases in the cell x the cell's SLOWEST smoke case) / workers
x 1.75; gti (rule (6)): max(sum of module walls / workers, slowest single module) x 1.75. A stream fits if the
projection <= 0.8 x budget. Repro projects block reproset (main[::3] + alphabet3[::3]). The critical path is
max(transfer, -) + max(repro, g11) next to gti, all from t0; it must be <= 0.8 x 7200 s.
"""
from __future__ import annotations
import argparse,json,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_019 import load,PLAN
from experiments.brute_study_019 import jobs_for
from scripts.run_study_019 import STREAMS,CAP
FACTOR=1.75
FILL=0.8


def cell_of(fam,eps):return f'{fam}/{eps}'


def per_cell(costs):
    """{cell: slowest smoke cost}; costs is [(family, eps, seconds)]."""
    out=defaultdict(float);n=defaultdict(int)
    for f,e,s in costs:out[cell_of(f,e)]=max(out[cell_of(f,e)],s);n[cell_of(f,e)]+=1
    return dict(out),dict(n)


def project(jobs,slow,workers):
    cnt=defaultdict(int)
    for j in jobs:cnt[cell_of(j[1],j[3])]+=1
    missing=sorted(c for c in cnt if c not in slow)
    if missing:raise SystemExit(f'no smoke measurement for cells {missing}')
    raw=sum(cnt[c]*slow[c] for c in cnt)/workers
    return {'cells':{c:{'heldout_cases':cnt[c],'slowest_smoke_s':round(slow[c],3)} for c in sorted(cnt)},
            'raw_s':round(raw,1),'projected_s':round(raw*FACTOR,1)}


def build(transfer,g11,gti):
    plan=load(PLAN);T=load(Path(transfer)/'RESULTS.json')['cases']
    tc=[(c['family'],c['eps'],c['case_wall_informational']) for c in T]
    G=[json.loads(l) for l in open(g11) if l.strip()];by={f"{c['family']}/{c['seed']}/{c['eps']}":c for c in T}
    gc=[(by[r['case']]['family'],by[r['case']]['eps'],r['wall_informational']) for r in G if 'case' in r]
    ts,tn=per_cell(tc);gs,gn=per_cell(gc)
    S=load(gti);mods={m:r['wall_informational'] for m,r in S['per_module'].items()};mods['<plain discovery>']=S['plain_discover']['wall_informational']
    mods.update({f'<clean {v}>':r['wall_informational'] for v,r in (S.get('clean_tag_runs') or {}).items() if r})
    W={k:v[0] for k,v in STREAMS.items()};B={k:v[1] for k,v in STREAMS.items()}
    st={'transfer':project(jobs_for(plan,'transfer'),ts,W['transfer']),'repro':project(jobs_for(plan,'reproset'),ts,W['repro']),
        'g11':project(jobs_for(plan,'transfer'),gs,W['g11'])}
    raw=max(sum(mods.values())/W['gti'],max(mods.values()))
    st['gti']={'modules':len(mods),'sum_module_wall_s':round(sum(mods.values()),1),'slowest_module':max(mods,key=mods.get),
               'slowest_module_s':round(max(mods.values()),1),'raw_s':round(raw,1),'projected_s':round(raw*FACTOR,1)}
    for k,v in st.items():v.update(workers=W[k],budget_s=B[k],fill=round(v['projected_s']/B[k],3),fits=v['projected_s']<=FILL*B[k])
    crit=max(st['gti']['projected_s'],st['transfer']['projected_s']+max(st['repro']['projected_s'],st['g11']['projected_s']))
    budget_path=max(B['gti'],B['transfer']+max(B['repro'],B['g11']))
    return {'schema':'brute.rate-math-019.v1','factor':FACTOR,'fill_limit':FILL,'cap_s':CAP,
            'measured_under':'orchestrator dry run with the held-out stream layout (SMOKE=1)',
            'smoke_cells_transfer':tn,'smoke_cells_g11':gn,'streams':st,'max_workers_at_once':max(W['transfer']+W['gti'],W['gti']+W['repro']+W['g11']),
            'critical_path_projected_s':round(crit,1),'budget_path_s':budget_path,
            'fits':all(v['fits'] for v in st.values()) and crit<=FILL*CAP and budget_path<=CAP and max(W['transfer']+W['gti'],W['gti']+W['repro']+W['g11'])<=8}


def table(R):
    L=['| stream | workers | budget (s) | raw (s) | x1.75 (s) | fill | fits (<= 0.8) |','|---|---|---|---|---|---|---|']
    for k,v in R['streams'].items():L.append(f"| {k} | {v['workers']} | {v['budget_s']} | {v['raw_s']} | {v['projected_s']} | {v['fill']} | {v['fits']} |")
    return '\n'.join(L)


def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--transfer',required=True);ap.add_argument('--g11',required=True);ap.add_argument('--gti',required=True)
    ap.add_argument('--json');a=ap.parse_args(argv);R=build(a.transfer,a.g11,a.gti)
    if a.json:Path(a.json).write_text(json.dumps(R,indent=1,sort_keys=True)+'\n')
    print(table(R));print('critical path projected',R['critical_path_projected_s'],'s; budget path',R['budget_path_s'],'s; fits',R['fits'])
    return 0 if R['fits'] else 1


if __name__=='__main__':sys.exit(main())
