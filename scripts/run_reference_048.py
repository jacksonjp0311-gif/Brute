"""GS_ref / GS20_sound audit for study-048 (BRUTE_PLAN_048 GS_ref: 0 mismatches, 20 mutations caught, total budget 2400 s on
8 workers; pre-run deviation #169). New file: a thin wrapper over the frozen scripts/run_reference_047.py main (independent
CaDiCaL reference, worlds_047 dispatch, audit at bound N = 16 / 3 / 20, mutation seed 470), called with --budget 2400 and
--output-name REFERENCE_048.json. The 047 arm order (API16D, A16_N, API16D_b) is kept; study 048 has no A16_N records, so the
audit order is API16D then API16D_b, control, scale16, scale20 by seed. The output schema string stays the 047 one
(brute.reference.v44_0) because the frozen main writes it.
  PYTHONPATH=. python scripts/run_reference_048.py results/study-048/main [--workers 8] [--block main]"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import run_reference_047 as R47
BUDGET_S=2400.0;OUTPUT_NAME='REFERENCE_048.json'


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if '--budget' not in argv:argv+=['--budget',str(BUDGET_S)]
    if '--output-name' not in argv:argv+=['--output-name',OUTPUT_NAME]
    return R47.main(argv)


if __name__=='__main__':sys.exit(main())
