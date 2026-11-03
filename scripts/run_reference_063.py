"""GS_ref63 audit for study-063 (BRUTE_PLAN_063 GS_ref63; new file, built from scripts/run_reference_062.py, frozen). The frozen scripts/run_reference_047.py machinery (pool, budget,
mutation test, report) and the frozen scripts/run_reference_041.py audit() (experiments/v0300_reference.py and v0310_reference.py:
plain CNF, CaDiCaL, no shared code with brute/) are imported unchanged; in this process and its forked workers only:
  R47.W43 -> a shim over experiments/worlds_058 (world(seed, family), actions); R47.view -> this view (family per arm);
  R47.ORDER = ('B2','P2','P2b'), KEYS = ('scale20p2',), DELTA all None (bound N = 20 in every arm);
  R47._audit and R47.audit -> wrappers that set run_reference_041.M = 4 (2**read_bits, read_bits 2) before auditing.
certify/20p changes only the pool, so the audit needs nothing new. Per decided record: n_min, consistency, s1,
every stored future / start verdict, completeness at N 20 and the stop label; K_spent is audited as AMB. 1800 s total budget,
8 workers; 20 seeded mutations (random.Random(630)). PASS iff 0 mismatches, every decided record audited and 20/20 mutations
detected (vacuous pass stated if 0 decided).
  PYTHONPATH=. python scripts/run_reference_063.py results/study-063/main [--workers 8] [--budget 1800]"""
import sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import worlds_058 as W58
from scripts import run_reference_047 as R47
from scripts import run_reference_041 as R41
ORDER=('B2','P2','P2b');KEYS=('scale20p2',);SEED=630;BUDGET_S=1800.0
_audit47=R47._audit;_auditR41=R41.audit


def view(c,arm):
    a=c['arms'][arm];stop='AMB' if a['stop']=='K_spent' else a['stop']
    return {'id':f"{c['block']}/{c['key']}/{c['seed']}/{arm}",'arm':arm,'key':c['key'],'seed':c['seed'],'family':a['family'],
            'extra_acts':list(a['extra_acts']),'stop':stop,'stop_recorded':a['stop'],'n_min':a['n_min'],'model':a['model'],'s1':a['s1'],
            'future':a['future'],'start':a['start'],'N':c['N']}


def _setm(r):R41.M=1<<W58.BITS[r['family']]


def _audit(r):_setm(r);return _audit47(r)


def audit(r,w,acts,codes,cache):_setm(r);return _auditR41(r,w,acts,codes,cache)


R47.W43=types.SimpleNamespace(world=W58.world,actions=W58.actions,SIZES=W58.SIZES)
R47.view=view;R47.ORDER=ORDER;R47.KEYS=KEYS;R47.DELTA={a:None for a in ORDER};R47.SEED=SEED;R47.BUDGET_S=BUDGET_S
R47._audit=_audit;R47.audit=audit


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if '--output-name' not in argv:argv+=['--output-name','REFERENCE_063.json']
    return R47.main(argv)


if __name__=='__main__':sys.exit(main())
