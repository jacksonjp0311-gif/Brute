"""Capability probe for plan 064 (v0.61.0; run BEFORE the plan is locked, so the plan can say whether the step decides anything;
NOT a study, never gated). New file.
Question (plan 063 next_if_pass): does clique anchoring (certify/20p's encoding) decide 2-bit readings at 24 STATES, and does the
frozen certify/32b (no anchoring) at the same budget? Worlds: worlds_026.scale_world(s, 24) with its ORIGINAL 2-bit emissions
(transitions, start, emissions as drawn; minimal and strongly connected under that draw), passive prefix worlds_026.actions(s, 0, 3).
Arms (declared N 24, read_bits 2, C 50000, K 400, conflict-only stop):
  P24  certify/20p's Certifier20P with the declared bound set to 24 after construction (the certify/32b method: construct at
       min(N, 20), then self.N = N; self.N is read only at query time; no global is changed);
  B24  frozen certify/32b at N 24, read_bits 2 (gated control candidate).
Seeds are NON-FRESH: sealed study-061 main 24-state seeds 12610101-12610104 (used there with 4-bit emissions; spent, never fresh).
Grid: P24 x 4 seeds + B24 x 2 seeds (12610101-02) at B 8M; WORKERS workers, max_tasks_per_child=1; probe-only wall guard 2400 s.
Output: results/diag-064/CAPABILITY_PROBE_064.json (refuses overwrite). Labels against the true machine (Observed).
  PYTHONPATH=. python scripts/probe_064.py"""
from __future__ import annotations
import hashlib,json,sys,time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import worlds_026 as W26
from experiments.brute_study_058 import truth_label,_Step
from brute.api import certify20b as C20B
from brute.api import certify20p as C20P
from brute.api import certify32b as C32B
from brute.scalesearch4 import SOLVER4
from experiments.brute_common import dumps

SEEDS=(12610101,12610102,12610103,12610104);B_SEEDS=SEEDS[:2];B=8000000;C=50000;K=400;N=24;WORKERS=6
GUARD_CASE_S=2400.0;GUARD_CALL_S=30.0
OUT=ROOT/'results/diag-064/CAPABILITY_PROBE_064.json'


class _P24(C20P.Certifier20P):
    def __init__(self,initial,k,fb,search,**kw):
        super().__init__(initial,k,min(fb,20),search,**kw);self.N=fb


def world(seed):
    w=W26.scale_world(seed,N);return w


def job(seed,arm):
    w=world(seed);assert w.n==N and w.s==2;sw=_Step(w);acts=list(W26.actions(seed,0.0,w.k));t0=time.perf_counter()
    kw=dict(read_bits=2,max_chunks=None,K=K,conflict_cap=C,budget_conflicts=B,wall_guard_case_s=GUARD_CASE_S,
            wall_guard_call_s=GUARD_CALL_S,solver=SOLVER4,hook=None,factory=C20B.counted16d)
    c=_P24(sw.read(),w.k,N,'a16d',**kw) if arm=='P24' else C32B.Certifier32B(sw.read(),w.k,N,'a16d',**kw)
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
            'repins':[list(x) for x in R.get('repins') or []],'final_clique':len(R.get('final_clique') or []),
            'wall_s_informational':round(time.perf_counter()-t0,1)}


def main():
    if OUT.exists():raise SystemExit('refusing overwrite '+str(OUT))
    t0=time.time();out=[]
    with ProcessPoolExecutor(WORKERS,max_tasks_per_child=1) as ex:
        fs={ex.submit(job,s,a):(s,a) for a,ss in (('P24',SEEDS),('B24',B_SEEDS)) for s in ss}
        for f in as_completed(fs):
            r=f.result();out.append(r);print(dumps(r),flush=True)
    out.sort(key=lambda r:(r['arm'],r['seed']))
    d={'schema':'brute.probe.v61_0','label':'Observed','purpose':'capability probe for plan 064 before locking; not evidence for any gate',
       'seeds_non_fresh':list(SEEDS),'seed_note':'sealed study-061 main 24-state seeds 12610101-04 (4-bit there; here original 2-bit emissions); spent, never fresh',
       'api':'probe-local _P24 around '+C20P.API+' and frozen '+C32B.API,'C':C,'K':K,'N':N,'B':B,'guard_case_s':GUARD_CASE_S,'records':out,
       'summary':{a:{'decided':sum(r['label'] in ('ID','IDF') for r in out if r['arm']==a),'of':sum(r['arm']==a for r in out),'labels':[r['label'] for r in out if r['arm']==a],'n_min':[r['n_min'] for r in out if r['arm']==a]} for a in ('P24','B24')},
       'decided':sum(r['label'] in ('ID','IDF') for r in out),'of':len(out),'wrong':sum(r['label']=='WRONG' for r in out),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'elapsed_informational':round(time.time()-t0,1)}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(d,indent=1,sort_keys=True)+'\n')
    print(json.dumps({k:d[k] for k in ('decided','of','wrong','elapsed_informational')}))


if __name__=='__main__':main()
