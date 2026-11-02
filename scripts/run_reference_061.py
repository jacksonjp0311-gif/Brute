"""GS_ref audit for study-061 (BRUTE_PLAN_061 GS_ref; pre-run deviation #196; new file). Exactly the study-060 setup: the frozen
scripts/run_reference_060.py is imported (it binds the frozen run_reference_047 machinery and run_reference_041 audit() over
experiments/worlds_060 with ORDER ('S24','S24b','S32'), KEYS ('scale24w','scale32w'), DELTA None, M 16, its view()); this file only
changes the mutation seed (random.Random(610)) and the output name REFERENCE_061.json. Budget 3600 s total, 8 workers. PASS iff 0
mismatches, every decided record audited and 20/20 mutations detected (vacuous pass stated if 0 decided).
  PYTHONPATH=. python scripts/run_reference_061.py results/study-061/main [--workers 8] [--budget 3600]"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import run_reference_060 as R60
from scripts import run_reference_047 as R47
SEED=610;BUDGET_S=R60.BUDGET_S
R47.SEED=SEED


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if '--output-name' not in argv:argv+=['--output-name','REFERENCE_061.json']
    return R47.main(argv)


if __name__=='__main__':sys.exit(main())
