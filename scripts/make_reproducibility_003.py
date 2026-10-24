"""G11: rerun the calibration check and study-003 from scratch into a NEW path; compare bytes."""
from __future__ import annotations
import argparse,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_003 import STUDY_DIR,write_new,dumps,check,sha
from experiments.brute_calibrate_003 import calibrate_check
from experiments.brute_study_003 import run

OUT=STUDY_DIR/'REPRODUCIBILITY.json'


def build():
    with tempfile.TemporaryDirectory(prefix='brute-study-003-rerun-') as tmp:
        tmp=Path(tmp);write_new(tmp/'CALIBRATION_CHECK.json',calibrate_check());run(tmp,tmp/'CALIBRATION_CHECK.json')
        rows={}
        for name in ('CALIBRATION_CHECK.json','SCIENTIFIC.json'):
            rows[name]={'committed_sha256':sha(STUDY_DIR/name),'rerun_sha256':sha(tmp/name),
                        'byte_identical':(STUDY_DIR/name).read_bytes()==(tmp/name).read_bytes()}
    return {'schema':'brute.reproducibility.v1','study':'BRUTE-011-FALLBACK-003','files':rows,
            'all_byte_identical':all(r['byte_identical'] for r in rows.values()),
            'note':'RESULTS.json carries timing fields and is not expected to be byte-identical; SCIENTIFIC.json is RESULTS minus *_informational keys.'}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');a=ap.parse_args();obj=build()
    if a.check:check(obj['all_byte_identical'],'study-003 does not reproduce');print('study-003 reproduces byte-for-byte')
    else:write_new(OUT,obj);print(dumps(obj).decode())
