"""Reference-cost probe for plan 060 (v0.57.0 planning; NOT a study, never gated). New file. Question: does the plain-CNF
reference audit (frozen scripts/run_reference_041.audit, CaDiCaL, M = 16) finish on a decided 24-state, 4-bit record in a time
that fits the GS_ref budget? One NON-FRESH seed (12530001, a sealed study-058 main seed, also used by scripts/probe_060.py):
the probe_060 world at n = 24 is driven by the frozen certify/20b at B 8M (same in-process A16D_MAX_BOUND patch as probe_060,
disclosed), then the decided record is audited once. Output: results/diag-060/REFERENCE_PROBE_060.json. Labels: Observed.
  PYTHONPATH=. python scripts/probe_060_ref.py"""
from __future__ import annotations
import json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import worlds_026 as W26
from experiments.brute_study_059 import truth_label,_Step,_verd,GUARD_CALL_S
from brute.api import certify20b as C20B
from brute.api import certify16d as C16D
from brute.scalesearch4 import SOLVER4
from scripts import run_reference_041 as R41
from scripts.probe_060 import W
SEED=12530001;N=24;B=8000000;C=50000;K=400
OUT=ROOT/'results/diag-060/REFERENCE_PROBE_060.json'


def main():
    if OUT.exists():raise SystemExit('refusing overwrite '+str(OUT))
    C16D.A16D_MAX_BOUND=32;R41.M=16
    w=W(SEED,N);sw=_Step(w);acts=list(W26.actions(SEED,0.0,w.k));t0=time.perf_counter()
    c=C20B.Certifier20B(sw.read(),w.k,N,'a16d',read_bits=4,max_chunks=None,K=K,conflict_cap=C,budget_conflicts=B,
                        wall_guard_case_s=8000.0,wall_guard_call_s=GUARD_CALL_S,solver=SOLVER4,hook=None,factory=C20B.counted16d)
    try:
        for a in acts:c.observe(a,sw.step(a))
        while True:
            x=c.propose()
            if x is None:break
            for a in x:c.observe(a,sw.step(a))
        R=c.record()
    finally:c.close()
    f=R['final'];t1=time.perf_counter()
    lab=truth_label(R['stop'],f['model'],f['s1'],w,sw.q)
    r={'id':'probe/24/'+str(SEED),'stop':'AMB' if R['stop']=='K_spent' else R['stop'],'N':N,'n_min':f['n_min'],'model':f['model'],
       's1':f['s1'],'future':_verd(f['future']),'start':_verd(f['start'])}
    allacts=list(R['acts']);codes=[m.bit_length()-1 for m in R['masks']]
    x=R41.audit(r,w,allacts,codes,{}) if r['stop']!='unknown' else {'decided':False,'mismatches':[]};t2=time.perf_counter()
    d={'schema':'brute.probe.v57_0','label':'Observed','purpose':'reference-audit cost probe for BRUTE_PLAN_060 GS_ref; not evidence for any gate',
       'seed_non_fresh':SEED,'n':N,'B':B,'C':C,'K':K,'M':16,'patch':'certify16d.A16D_MAX_BOUND 20 -> 32 in-process (probe only)',
       'label_truth':lab,'stop':R['stop'],'conflicts_spent':R['conflicts_spent'],'steps':len(allacts),'audit':x,
       'certify_wall_s_informational':round(t1-t0,1),'audit_wall_s_informational':round(t2-t1,1)}
    OUT.write_text(json.dumps(d,indent=1,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in d.items() if k!='audit'}),x.get('mismatches'))


if __name__=='__main__':main()
