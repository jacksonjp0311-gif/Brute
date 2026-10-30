"""ADDENDUM to the frozen scripts/make_gates_028.py (deviation #129, written after the run). New file; the frozen
script is not edited.
Defect (Exact): make_gates_028 reads case records from SCIENTIFIC.json, which no_time() strips of every *_informational
key, so GQB (query_max_informational / observe_max_informational) raises KeyError before any gate is computed. This
is the same input defect #127 item 3 recorded for v0.24.0's diagnosis.
Fix: identical gate code and thresholds (the frozen module is imported and called unchanged). The only change is that
case records are taken from the sealed RESULTS.json, after checking that (1) sha256(RESULTS.json) equals
main/SEAL.json results_sha256 and (2) no_time(RESULTS.json) equals the sealed SCIENTIFIC.json exactly. RESULTS.json
is therefore SCIENTIFIC.json plus the wall-clock fields. The completeness check still hashes SCIENTIFIC.json against
its seal. Output: results/study-028/GATES_028.json (never written by the frozen script), with 'scored_by' recorded.
  PYTHONPATH=. python scripts/make_gates_028b.py [--study-dir D] [--check]"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_028 import STUDY_DIR,load,dumps,write_new,check,sha
from brute.evaluation import no_time
from scripts import make_gates_028 as MG


def build(study=STUDY_DIR):
    study=Path(study);D=study/'main';orig=MG.opt;src='SCIENTIFIC.json (no RESULTS.json)'
    if (D/'RESULTS.json').exists() and (D/'SEAL.json').exists() and (D/'SCIENTIFIC.json').exists():
        seal=load(D/'SEAL.json');res=load(D/'RESULTS.json')
        check(sha(D/'RESULTS.json')==seal.get('results_sha256'),'RESULTS.json does not match its seal')
        check(no_time(res)==load(D/'SCIENTIFIC.json'),'no_time(RESULTS.json) differs from SCIENTIFIC.json')
        src='RESULTS.json (sealed; no_time equals SCIENTIFIC.json)'
        MG.opt=lambda p:res if Path(p).name=='SCIENTIFIC.json' else orig(p)
    try:obj=MG.build(study)
    finally:MG.opt=orig
    obj['scored_by']={'script':'scripts/make_gates_028b.py','frozen_gate_code':'scripts/make_gates_028.py','deviation':129,'case_records_from':src}
    return obj


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true');a=ap.parse_args()
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'GATES_028.json'
    if a.check:check(out.read_bytes()==dumps(obj),'GATES_028.json does not reproduce');print('GATES_028 reproduces (028b)')
    else:write_new(out,obj);print(json.dumps({k:v['pass'] for k,v in obj['gates'].items()}),obj['failed'])
