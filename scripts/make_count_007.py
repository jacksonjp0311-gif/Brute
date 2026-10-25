"""G11 / GX2 input: second-implementation COUNT on the sealed study-007 RESULTS.json (process step 5, committed before
any study-007 run). Wraps experiments/v050_reference.run with the registered mutation test: 20 injected single-field
errors in 20 distinct traces, random.Random(20261025). Writes results/study-007/SECOND_IMPLEMENTATION_COUNT.json.
Wording: second implementation by the same author, no brute import; not an independent audit."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_007 import STUDY_DIR,write_new,check


def build(study=STUDY_DIR,workers=6):
    from experiments import v050_reference as R
    if Path(study)==STUDY_DIR:
        from scripts.study007_storage import ensure_raw;ensure_raw()
    return R.run(study,workers=workers,mutate_k=20)


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--workers',type=int,default=6)
    a=ap.parse_args();rep=build(Path(a.study_dir),a.workers);out=Path(a.study_dir)/'SECOND_IMPLEMENTATION_COUNT.json'
    check(not out.exists(),'refusing overwrite '+str(out));out.write_text(json.dumps(rep,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:v for k,v in rep.items() if k!='mismatches'},indent=2))
