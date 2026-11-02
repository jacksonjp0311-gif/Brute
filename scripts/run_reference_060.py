"""GS_ref audit for study-060 (BRUTE_PLAN_060 GS_ref; pre-run deviation #194; new file). The frozen scripts/run_reference_047.py
machinery (pool, budget, mutation test, report) and the frozen scripts/run_reference_041.py audit() (experiments/v0300_reference.py
and v0310_reference.py: plain CNF, CaDiCaL, no shared code with brute/) are imported unchanged; in this process and its forked
workers only:
  R47.W43 -> a shim over experiments/worlds_060 (world(seed, family), actions, SIZES); R47.view -> this view (bound N = the record's
            declared bound, 24 or 32);
  R47.trace -> as frozen (true codes of the noise-free world; recount_060 checks the recorded masks equal them independently);
  R47.ORDER = ('S24','S24b','S32'), KEYS = ('scale24w','scale32w'), DELTA all None, M = 16.
Records with stop 'none' are reported as not decided; K_spent is audited as AMB. Budget 3600 s total, 8 workers, fixed from
results/diag-060/REFERENCE_PROBE_060.json (one decided 24-state record audited in 62.5 s, Observed); 20 seeded mutations
(random.Random(600)). PASS iff 0 mismatches, every decided record audited and 20/20 mutations detected (vacuous pass stated if 0
decided).
  PYTHONPATH=. python scripts/run_reference_060.py results/study-060/main [--workers 8] [--budget 3600]"""
import sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import worlds_060 as W60
from scripts import run_reference_047 as R47
from scripts import run_reference_041 as R41
ORDER=('S24','S24b','S32');KEYS=('scale24w','scale32w');SEED=600;BUDGET_S=3600.0


def view(c,arm):
    a=c['arms'][arm];stop={'K_spent':'AMB','none':'unknown'}.get(a['stop'],a['stop'])
    return {'id':f"{c['block']}/{c['key']}/{c['seed']}/{arm}",'arm':arm,'key':c['key'],'seed':c['seed'],'family':a['family'],
            'extra_acts':list(a['extra_acts']),'stop':stop,'stop_recorded':a['stop'],'n_min':a['n_min'],'model':a['model'],'s1':a['s1'],
            'future':a['future'],'start':a['start'],'N':c['N']}


R41.M=16
R47.W43=types.SimpleNamespace(world=W60.world,actions=W60.actions,SIZES=W60.SIZES)
R47.view=view;R47.ORDER=ORDER;R47.KEYS=KEYS;R47.DELTA={a:None for a in ORDER};R47.SEED=SEED;R47.BUDGET_S=BUDGET_S


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if '--output-name' not in argv:argv+=['--output-name','REFERENCE_060.json']
    return R47.main(argv)


if __name__=='__main__':sys.exit(main())
