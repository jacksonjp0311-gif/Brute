"""GS_ref / GS20_sound50 / GN12_sound audit for study-050 (BRUTE_PLAN_050 GS_ref: every decided record audited at its family_bound,
0 mismatches, 20 mutations caught; pre-run deviation #173). New file: a thin wrapper over the frozen scripts/run_reference_047.py
main (independent CaDiCaL reference, audit at bound N = 20 / 12, mutation seed 470), with its module names ORDER / DELTA / KEYS /
W43 bound in this process to the 050 arms (API16E, API16E_b, API16N, API16N_b, API16N_c), keys and experiments/worlds_050. The
reference rebuilds the clean (noise-free) trace from the world and the recorded actions, so a noise record is audited against the
truth, not against its majority readings. Called with --budget 2400 and --output-name REFERENCE_050.json on block main (part c is
recounted against part k by recount_050 and is outside the reference scope). The output schema string stays the 047 one.
  PYTHONPATH=. python scripts/run_reference_050.py results/study-050/main [--workers 8] [--block main]"""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments import worlds_050 as W50
from scripts import run_reference_047 as R47
BUDGET_S=2400.0;OUTPUT_NAME='REFERENCE_050.json'
R47.ORDER=('API16E','API16E_b','API16N','API16N_b','API16N_c');R47.DELTA={a:None for a in R47.ORDER};R47.KEYS=('scale20','control','noise12');R47.W43=W50


def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if '--budget' not in argv:argv+=['--budget',str(BUDGET_S)]
    if '--output-name' not in argv:argv+=['--output-name',OUTPUT_NAME]
    return R47.main(argv)


if __name__=='__main__':sys.exit(main())
