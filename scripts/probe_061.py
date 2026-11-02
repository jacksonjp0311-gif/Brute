"""Budget probe for plan 061 (v0.58.0; BRUTE_PLAN_061 budget_probe_rule; NOT a study, never gated). New file.
Question: does the frozen brute.certify/32b (v0.57.0) decide the 24-state worlds that were IDU at B 8M in study 060 when the
conflict budget is raised to 16M or 24M, and what do two 32-state worlds do at those budgets?
Seeds are NON-FRESH: sealed study-060 main seeds. n 24: 12600101, 12600102, 12600103, 12600109 (the four S24 IDU records);
n 32: 12600201, 12600202. Worlds exactly worlds_060 (scale24r4 / scale32r4), passive prefix worlds_060.actions(s, 0, 3).
Grid: {16M, 24M} x 6 seeds = 12 jobs; C 50000, K 400, read_bits 4, bound = n; one 8-worker pool, max_tasks_per_child=1.
Order: n32 jobs and n24 at 24M first, then n24 at 16M. Probe wall cap: a 2100 s per-case wall guard (probe only; disclosed),
so the whole probe stays under 60 min. A guard firing is reported as such. No global is patched; no file is edited.
B61 rule (plan): the smallest probed B that decides >= 3 of the 4 n24 seeds; if neither, B61 = 24M.
Output: results/diag-061/BUDGET_PROBE_061.json. Labels against the true machine. Labels: Observed.
  PYTHONPATH=. python scripts/probe_061.py"""
from __future__ import annotations
import json,sys,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import worlds_060 as W60
from experiments.brute_study_060 import truth_label,_Step
from brute.api import certify32b as C32B
from brute.scalesearch4 import SOLVER4
from experiments.brute_common import dumps

S24=(12600101,12600102,12600103,12600109);S32=(12600201,12600202);BS=(16000000,24000000);C=50000;K=400
GUARD_CASE_S=2100.0;GUARD_CALL_S=30.0
FAM={24:'scale24r4',32:'scale32r4'}
OUT=ROOT/'results/diag-061/BUDGET_PROBE_061.json'


def job(seed,n,B):
    w=W60.world(seed,FAM[n]);sw=_Step(w);acts=list(W60.actions(seed,0.0,w.k));t0=time.perf_counter()
    c=C32B.Certifier32B(sw.read(),w.k,n,'a16d',read_bits=4,max_chunks=None,K=K,conflict_cap=C,budget_conflicts=B,
                        wall_guard_case_s=GUARD_CASE_S,wall_guard_call_s=GUARD_CALL_S,solver=SOLVER4,hook=None,factory=C32B.counted16d)
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
            'extra_actions':len(R['acts'])-len(acts),'wall_s_informational':round(time.perf_counter()-t0,1)}


def main():
    if OUT.exists():raise SystemExit('refusing overwrite '+str(OUT))
    t0=time.time()
    jobs=[(s,32,B) for B in BS[::-1] for s in S32]+[(s,24,BS[1]) for s in S24]+[(s,24,BS[0]) for s in S24];out=[]
    with ProcessPoolExecutor(8,max_tasks_per_child=1) as ex:
        fs={ex.submit(job,*j):j for j in jobs}
        for f in as_completed(fs):
            r=f.result();out.append(r);print(dumps(r),flush=True)
    out.sort(key=lambda r:(r['n'],r['B'],r['seed']))
    summ={}
    for n in (24,32):
        for B in BS:
            rs=[r for r in out if r['n']==n and r['B']==B]
            summ[f'n{n}_B{B//1000000}M']={'decided':sum(r['label'] in ('ID','IDF') for r in rs),'of':len(rs),'wrong':sum(r['label']=='WRONG' for r in rs),
                'labels':[r['label'] for r in rs],'conflicts':[r['conflicts_spent'] for r in rs],'guard':sum(bool(r['wall_guard']) for r in rs),
                'max_wall_s':max(r['wall_s_informational'] for r in rs)}
    dec={B:summ[f'n24_B{B//1000000}M']['decided'] for B in BS}
    ok=[B for B in BS if dec[B]>=3];B61=min(ok) if ok else BS[1]
    d={'schema':'brute.probe.v58_0','label':'Observed','purpose':'budget probe for BRUTE_PLAN_061 (budget_probe_rule); not evidence for any gate',
       'seeds_non_fresh':{'n24':list(S24),'n32':list(S32)},'seed_note':'sealed study-060 main seeds; spent, never fresh evidence','api':C32B.API,'C':C,'K':K,
       'guard_case_s':GUARD_CASE_S,'records':out,'summary':summ,'B61':B61,'B61_rule':'smallest probed B deciding >= 3 of 4 n24 seeds; else 24M',
       'B61_rule_met':bool(ok),'elapsed_informational':round(time.time()-t0,1)}
    OUT.write_text(json.dumps(d,indent=1,sort_keys=True)+'\n');print(json.dumps(summ,indent=1),'B61',B61)


if __name__=='__main__':main()
