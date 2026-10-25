"""G12/G13 for study-006: rerun the tau6 calibration and the full study from scratch into a NEW path; compare bytes.
Committed (process step 5) before any study-006 run."""
from __future__ import annotations
import argparse,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_006 import STUDY_DIR,write_new,dumps,check,sha
from experiments.brute_calibrate_006 import calibrate
from experiments.brute_study_006 import run

OUT=STUDY_DIR/'REPRODUCIBILITY.json'


def build(workers=6):
    from scripts.study006_storage import ensure_raw;ensure_raw()
    with tempfile.TemporaryDirectory(prefix='brute-study-006-rerun-') as tmp:
        tmp=Path(tmp);write_new(tmp/'CALIBRATION_006.json',calibrate(workers));run(tmp,tmp/'CALIBRATION_006.json',workers)
        rows={}
        for name in ('CALIBRATION_006.json','SCIENTIFIC.json'):
            rows[name]={'committed_sha256':sha(STUDY_DIR/name),'rerun_sha256':sha(tmp/name),
                        'byte_identical':(STUDY_DIR/name).read_bytes()==(tmp/name).read_bytes()}
    return {'schema':'brute.reproducibility.v1','study':'BRUTE-040-GEOMETRY-006','files':rows,
            'all_byte_identical':all(r['byte_identical'] for r in rows.values()),
            'note':'RESULTS.json carries timing fields and is not expected to be byte-identical; SCIENTIFIC.json is RESULTS minus *_informational keys.'}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');ap.add_argument('--workers',type=int,default=6)
    a=ap.parse_args();obj=build(a.workers)
    if a.check:check(obj['all_byte_identical'],'study-006 does not reproduce');print('study-006 reproduces byte-for-byte')
    else:write_new(OUT,obj);print(dumps(obj).decode())
