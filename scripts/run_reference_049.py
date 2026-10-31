"""GS_ref / GS20_sound49 audit for study-049 (BRUTE_PLAN_049 GS_ref: every decided record audited at its family_bound,
0 mismatches, 20 mutations caught, scope 2400 s on 8 workers; pre-run deviation #171). New file: a thin wrapper over the frozen
scripts/run_reference_047.py main (independent CaDiCaL reference, worlds_047 dispatch, audit at bound N = 16 / 3 / 20, mutation
seed 470), with its module ORDER / DELTA names bound in this process to the 049 fresh arms (API16E, API16E_b), called with
--budget 2400 and --output-name REFERENCE_049.json on the main block (parts a and d). Parts r and c (sealed 048 traces) are not
in the reference scope; their labels are recounted against the truth by recount_049. The output schema string stays the 047 one
(brute.reference.v44_0) because the frozen main writes it.
  PYTHONPATH=. python scripts/run_reference_049.py results/study-049/main [--workers 8] [--block main]"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import run_reference_047 as R47
BUDGET_S=2400.0;OUTPUT_NAME='REFERENCE_049.json'
R47.ORDER=('API16E','API16E_b');R47.DELTA={a:None for a in R47.ORDER}


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if '--budget' not in argv:argv+=['--budget',str(BUDGET_S)]
    if '--output-name' not in argv:argv+=['--output-name',OUTPUT_NAME]
    return R47.main(argv)


if __name__=='__main__':sys.exit(main())
