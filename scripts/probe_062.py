"""Budget probe for plan 062 (v0.59.0; BRUTE_PLAN_062 budget_probe_rule; NOT a study, never gated). New file.
Question: on 2-bit 20-state worlds (worlds_058 'scale20', original emissions), does the probe-word window policy (W2: the frozen
certify/20b proposal followed by the fixed probe word p = (0, 1)) decide any world that the usual policy (B2) does not, at
B 2M or 8M, and how long do the jobs take (to size the hard kill and the cut)?
Seeds are NON-FRESH: sealed study-058 main seeds 12530001-12530004 (all B2 IDU at 2M in study 058).
The window policy is defined HERE (class _W2Probe) as an exploratory stand-in, because brute/api/certify20w.py may only be built
after build_authorization_062 (plan status); the API module must implement the same rule. Rule: after each proposed word w, if the
action budget allows, the probe word p (truncated to the K actions left) is appended to the pending word; observe(), the solver,
the encoding and the labels are the frozen certify/20b ones. K counts every executed action.
Grid: {B2, W2} x {2M, 8M} x 4 seeds = 16 jobs; C 50000, K 400, read_bits 2, bound 20; one 8-worker pool, max_tasks_per_child=1.
Order: 8M first. Probe wall cap: a 2400 s per-case wall guard (probe only), so the probe stays near 60 min.
B62 rule (plan): the smallest probed B at which W2 decides >= 1 of 4; if none, B62 = 8M.
Output: results/diag-062/BUDGET_PROBE_062.json. Labels against the true machine (Observed).
  PYTHONPATH=. python scripts/probe_062.py"""
from __future__ import annotations
import json,sys,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import worlds_058 as W58
from experiments.brute_study_058 import truth_label,_Step
from brute.api import certify20b as C20B
from brute.scalesearch4 import SOLVER4
from experiments.brute_common import dumps

SEEDS=(12530001,12530002,12530003,12530004);BS=(2000000,8000000);C=50000;K=400;N=20;P=(0,1)
GUARD_CASE_S=2400.0;GUARD_CALL_S=30.0
OUT=ROOT/'results/diag-062/BUDGET_PROBE_062.json'


class _W2Probe(C20B.Certifier20B):
    """Exploratory window policy (same rule as the plan's certify/20w)."""
    def propose(self):
        w=super().propose()
        if w is None:return None
        tail=list(P[:max(0,self.K-self.used-len(w))])
        if tail:self._pending=list(w)+tail
        return list(self._pending)


def job(seed,arm,B):
    w=W58.world(seed,'scale20');sw=_Step(w);acts=list(W58.actions(seed,0.0,w.k));t0=time.perf_counter()
    cls=_W2Probe if arm=='W2' else C20B.Certifier20B
    c=cls(sw.read(),w.k,N,'a16d',read_bits=2,max_chunks=None,K=K,conflict_cap=C,budget_conflicts=B,
          wall_guard_case_s=GUARD_CASE_S,wall_guard_call_s=GUARD_CALL_S,solver=SOLVER4,hook=None,factory=C20B.counted16d)
    try:
        for a in acts:c.observe(a,sw.step(a))
        while True:
            x=c.propose()
            if x is None:break
            for a in x:c.observe(a,sw.step(a))
        R=c.record()
    finally:c.close()
    f=R['final']
    return {'seed':seed,'arm':arm,'B':B,'stop':R['stop'],'label':truth_label(R['stop'],f['model'],f['s1'],w,sw.q),'n_min':f['n_min'],
            'used':R['used'],'n_rounds':len(R['rounds']),'conflicts_spent':R['conflicts_spent'],'wall_guard':R['wall_guard'],
            'extra_actions':len(R['acts'])-len(acts),'wall_s_informational':round(time.perf_counter()-t0,1)}


def main():
    if OUT.exists():raise SystemExit('refusing overwrite '+str(OUT))
    t0=time.time()
    jobs=[(s,a,B) for B in BS[::-1] for s in SEEDS for a in ('W2','B2')];out=[]
    with ProcessPoolExecutor(8,max_tasks_per_child=1) as ex:
        fs={ex.submit(job,*j):j for j in jobs}
        for f in as_completed(fs):
            r=f.result();out.append(r);print(dumps(r),flush=True)
    out.sort(key=lambda r:(r['arm'],r['B'],r['seed']))
    summ={}
    for a in ('B2','W2'):
        for B in BS:
            rs=[r for r in out if r['arm']==a and r['B']==B]
            summ[f'{a}_B{B//1000000}M']={'decided':sum(r['label'] in ('ID','IDF') for r in rs),'of':len(rs),'wrong':sum(r['label']=='WRONG' for r in rs),
                'labels':[r['label'] for r in rs],'n_min':[r['n_min'] for r in rs],'used':[r['used'] for r in rs],
                'conflicts':[r['conflicts_spent'] for r in rs],'guard':sum(bool(r['wall_guard']) for r in rs),'max_wall_s':max(r['wall_s_informational'] for r in rs)}
    ok=[B for B in BS if summ[f'W2_B{B//1000000}M']['decided']>=1];B62=min(ok) if ok else BS[1]
    d={'schema':'brute.probe.v59_0','label':'Observed','purpose':'budget probe for BRUTE_PLAN_062 (budget_probe_rule); not evidence for any gate',
       'seeds_non_fresh':list(SEEDS),'seed_note':'sealed study-058 main seeds; spent, never fresh evidence','api':C20B.API,'probe_word':list(P),
       'C':C,'K':K,'N':N,'guard_case_s':GUARD_CASE_S,'records':out,'summary':summ,'B62':B62,
       'B62_rule':'smallest probed B at which W2 decides >= 1 of 4; else 8M','B62_rule_met':bool(ok),'elapsed_informational':round(time.time()-t0,1)}
    OUT.write_text(json.dumps(d,indent=1,sort_keys=True)+'\n');print(json.dumps(summ,indent=1),'B62',B62)


if __name__=='__main__':main()
