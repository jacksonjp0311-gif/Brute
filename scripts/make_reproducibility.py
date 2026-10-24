"""C11: rerun calibration and study-002 from scratch into a temp dir and compare bytes."""
from __future__ import annotations
import argparse,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import STUDY_DIR,write_new,dumps,check,sha
from experiments.brute_calibrate import calibrate
from experiments.brute_study import run

OUT=STUDY_DIR/'REPRODUCIBILITY.json'


def build():
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);write_new(tmp/'CALIBRATION.json',calibrate());run(tmp,tmp/'CALIBRATION.json')
        rows={}
        for name in ('CALIBRATION.json','SCIENTIFIC.json'):
            rows[name]={'committed_sha256':sha(STUDY_DIR/name),'rerun_sha256':sha(tmp/name),
                        'byte_identical':(STUDY_DIR/name).read_bytes()==(tmp/name).read_bytes()}
    return {'schema':'brute.reproducibility.v1','files':rows,'all_byte_identical':all(r['byte_identical'] for r in rows.values()),
            'note':'RESULTS.json carries timing fields and is not expected to be byte-identical; SCIENTIFIC.json is RESULTS minus *_informational keys.'}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build()
    if a.check:check(obj['all_byte_identical'],'study-002 does not reproduce');print('study-002 reproduces byte-for-byte')
    else:write_new(OUT,obj);print(dumps(obj).decode())
