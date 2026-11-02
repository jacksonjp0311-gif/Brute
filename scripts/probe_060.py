"""Budget probe for plan 060 (v0.57.0 planning; NOT a study, never gated). New file. Question: what conflict budget does the frozen
certify/20b need at read_bits 4 for 24- and 32-state worlds? Seeds are NON-FRESH: sealed study-058 main seeds 12530001-12530004
(drawn here at n = 24 / 32, so these exact worlds are new, but the seeds are spent and can never be fresh evidence).
World(seed, n): worlds_026.scale_world(seed, n) transitions and start (minimal strongly connected, 3 actions), emissions replaced
by worlds_058.emissions(seed, 4, n) (random 4-bit); passive prefix worlds_026.actions(seed, 0, 3) (176 steps). Noise-free.
Grid: n in {24, 32} x B in {2M, 8M} x 4 seeds = 16 jobs, C 50000, K 400, bound = n, one 8-worker pool, max_tasks_per_child=1.
In-process patch (probe only, disclosed): brute.api.certify16d.A16D_MAX_BOUND is raised from 20 to 32 in each worker so the
frozen code accepts bound 24 / 32; no file is edited. The study for v0.57.0 needs a new module that owns this bound, with tests.
Output: results/diag-060/BUDGET_PROBE_060.json. Labels against the true machine (ID/IDF/AMB/IDU/WRONG). Labels: Observed.
  PYTHONPATH=. python scripts/probe_060.py"""
from __future__ import annotations
import json,sys,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import worlds_026 as W26
from experiments import worlds_058 as W58
from experiments.brute_study_059 import truth_label,_Step,HARD_KILL_S,GUARD_CALL_S
from brute.api import certify20b as C20B
from brute.api import certify16d as C16D
from brute.scalesearch4 import SOLVER4
from experiments.brute_common import dumps

SEEDS=(12530001,12530002,12530003,12530004);NS=(24,32);BS=(2000000,8000000);C=50000;K=400
OUT=ROOT/'results/diag-060/BUDGET_PROBE_060.json'


class W:
    def __init__(self,seed,n):
        b=W26.scale_world(seed,n);self.n=n;self.k=b.k;self.transitions=tuple(tuple(r) for r in b.transitions);self.start=b.start
        self.emissions=W58.emissions(seed,4,n)


def job(seed,n,B):
    C16D.A16D_MAX_BOUND=32
    w=W(seed,n);sw=_Step(w);acts=list(W26.actions(seed,0.0,w.k));t0=time.perf_counter()
    c=C20B.Certifier20B(sw.read(),w.k,n,'a16d',read_bits=4,max_chunks=None,K=K,conflict_cap=C,budget_conflicts=B,
                        wall_guard_case_s=max(HARD_KILL_S,B/1000),wall_guard_call_s=GUARD_CALL_S,solver=SOLVER4,hook=None,factory=C20B.counted16d)
    try:
        for a in acts:c.observe(a,sw.step(a))
        while True:
            x=c.propose()
            if x is None:break
            for a in x:c.observe(a,sw.step(a))
        R=c.record()
    finally:c.close()
    f=R['final']
    return {'seed':seed,'n':n,'B':B,'stop':R['stop'],'label':truth_label(R['stop'],f['model'],f['s1'],w,sw.q),'n_min':f['n_min'],
            'used':R['used'],'n_rounds':len(R['rounds']),'conflicts_spent':R['conflicts_spent'],'wall_guard':R['wall_guard'],
            'distinct_codes':len(set(w.emissions)),'extra_actions':len(R['acts'])-len(acts),'wall_s_informational':round(time.perf_counter()-t0,1)}


def main():
    if OUT.exists():raise SystemExit('refusing overwrite '+str(OUT))
    t0=time.time();jobs=[(s,n,B) for B in BS[::-1] for n in NS[::-1] for s in SEEDS];out=[]
    with ProcessPoolExecutor(8,max_tasks_per_child=1) as ex:
        fs={ex.submit(job,*j):j for j in jobs}
        for f in as_completed(fs):
            r=f.result();out.append(r);print(dumps(r),flush=True)
    out.sort(key=lambda r:(r['n'],r['B'],r['seed']))
    summ={}
    for n in NS:
        for B in BS:
            rs=[r for r in out if r['n']==n and r['B']==B]
            summ[f'n{n}_B{B//1000000}M']={'decided':sum(r['label'] in ('ID','IDF') for r in rs),'of':len(rs),'wrong':sum(r['label']=='WRONG' for r in rs),
                'labels':[r['label'] for r in rs],'conflicts':[r['conflicts_spent'] for r in rs],'max_wall_s':max(r['wall_s_informational'] for r in rs)}
    d={'schema':'brute.probe.v57_0','label':'Observed','purpose':'budget probe for BRUTE_PLAN_060 (24/32 states, 4-bit readings); not evidence for any gate',
       'seeds_non_fresh':list(SEEDS),'seed_note':'sealed study-058 main seeds; spent, never fresh evidence','api':C20B.API,'C':C,'K':K,
       'patch':'certify16d.A16D_MAX_BOUND 20 -> 32 in-process (probe only)','records':out,'summary':summ,'elapsed_informational':round(time.time()-t0,1)}
    OUT.write_text(json.dumps(d,indent=1,sort_keys=True)+'\n');print(json.dumps(summ,indent=1))


if __name__=='__main__':main()
