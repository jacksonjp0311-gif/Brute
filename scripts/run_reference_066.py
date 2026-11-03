"""GS_ref66 audit for study-066 (BRUTE_PLAN_066 GS_ref66 and design.reference; new file, built from scripts/run_reference_065.py
(frozen): identical machinery with each record's own declared bound (20 for C20/S30/S30b on scale20, 24 for C24/S24 on scale24),
the 066 arms and mutations from random.Random(660). Noisy-arm records are audited against the TRUE (clean) trace of the world, so
any settled-bit error that changed the answer is caught here too. The frozen scripts/run_reference_047.py machinery (pool, budget,
mutation test, report) and the frozen scripts/run_reference_041.py audit() are imported unchanged; in this process and its forked
workers only:
  R47.W43 -> worlds_064 (world(seed, family), actions; = worlds_066); R47.view -> this view (family per arm, N = the record's bound,
  the record's final_clique carried as a hint; a KILL record (runner SIGKILL, no trace) is viewed as 'unknown', i.e. not decided and
  not audited); R47.ORDER = ('C24','S24','C20','S30','S30b'), KEYS = ('scale20','scale24'), DELTA all None;
  run_reference_041.M = 4 (read_bits 2) before each audit;
  run_reference_041._nmin and exists_different -> the clique-pinned experiments/v0610_reference.py versions (own apartness, own
  pairwise clique verification of the hint, else its own greedy clique through position 0; own CNF; CaDiCaL; no brute/ code).
Per decided record: n_min, consistency, s1, every stored future / start verdict, completeness at the declared N and the stop label;
K_spent is audited as AMB. 1800 s total budget, 6 workers; 20 seeded mutations (random.Random(660)). PASS iff 0 mismatches, every
decided record audited and 20/20 mutations detected (vacuous pass stated if 0 decided).
  PYTHONPATH=. python scripts/run_reference_066.py results/study-066/main --workers 6 --budget 1800"""
import sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import run_reference_065 as R65   # installs the frozen 065 shims (clique-pinned _nmin / exists_different, _audit, audit)
from experiments import worlds_064 as W64
from scripts import run_reference_047 as R47
ORDER=('C24','S24','C20','S30','S30b');KEYS=('scale20','scale24');SEED=660;BUDGET_S=1800.0;WORKERS=6


def view(c,arm):
    a=c['arms'][arm];stop='AMB' if a['stop']=='K_spent' else ('unknown' if a['stop']=='KILL' else a['stop'])
    return {'id':f"{c['block']}/{c['key']}/{c['seed']}/{arm}",'arm':arm,'key':c['key'],'seed':c['seed'],'family':a['family'],
            'extra_acts':list(a.get('extra_acts') or []),'stop':stop,'stop_recorded':a['stop'],'n_min':a['n_min'],'model':a['model'],'s1':a['s1'],
            'future':a.get('future'),'start':a.get('start'),'N':a['bound'],'final_clique':list(a.get('final_clique') or [])}


R47.W43=types.SimpleNamespace(world=W64.world,actions=W64.actions,SIZES=W64.SIZES)
R47.view=view;R47.ORDER=ORDER;R47.KEYS=KEYS;R47.DELTA={a:None for a in ORDER};R47.SEED=SEED;R47.BUDGET_S=BUDGET_S;R47.WORKERS=WORKERS


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if '--output-name' not in argv:argv+=['--output-name','REFERENCE_066.json']
    if '--workers' not in argv:argv+=['--workers',str(WORKERS)]
    if '--budget' not in argv:argv+=['--budget',str(BUDGET_S)]
    return R47.main(argv)


if __name__=='__main__':sys.exit(main())
