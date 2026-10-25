"""G12 / G13 input: compare the repro re-run (results/study-007/repro: every job whose run index is divisible by 3, i.e.
jobs_for(plan)[0::3]) and the second calibration (results/study-007/calibration-repro) with the sealed main run.
Committed before any study-007 run. Byte identity is on the canonical JSON of each case taken from SCIENTIFIC.json
(timing keys already stripped by no_time); calibration files are compared as raw bytes."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_007 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha


def _key(c):return f"{c['block']}/{c['family']}/{c['seed']}/{c['mask_rate']}"
def _canon(c):return json.dumps(c,sort_keys=True,separators=(',',':')).encode()


def build(study=STUDY_DIR):
    study=Path(study)
    if study==STUDY_DIR:
        from scripts.study007_storage import ensure_raw;ensure_raw()
    from experiments.brute_study_007 import jobs_for,key
    main=load(study/'SCIENTIFIC.json');rep=load(study/'repro/SCIENTIFIC.json');plan=load(PLAN)
    seal=load(study/'SEAL.json');rseal=load(study/'repro/SEAL.json')
    check(sha(study/'SCIENTIFIC.json')==seal['scientific_sha256'] and sha(study/'repro/SCIENTIFIC.json')==rseal['scientific_sha256'],'seal mismatch')
    want=[key(j) for j in jobs_for(plan)[0::3]]
    M={_key(c):c for c in main['cases']+main['stress_cases']};Rc={_key(c):c for c in rep['cases']+rep['stress_cases']}
    diff=[k for k in want if k not in Rc or k not in M or _canon(Rc[k])!=_canon(M[k])]
    blocks={}
    for k in want:
        b=k.split('/')[0];blocks.setdefault(b,{'cases':0,'identical':0});blocks[b]['cases']+=1;blocks[b]['identical']+=k not in diff
    files={'cases_index_divisible_by_3':{'expected':len(want),'rerun':len(Rc),'byte_identical':not diff and len(Rc)==len(want),
                                         'differing':diff[:50],'per_block':blocks}}
    for name in ('CALIBRATION_007.json','CALIBRATION_007_TRACES.json'):
        a,b=study/name,study/'calibration-repro'/name
        files[name]={'sha256_main':sha(a),'sha256_repro':sha(b),'byte_identical':a.read_bytes()==b.read_bytes()}
    return {'schema':'brute.reproducibility.v7','study':plan['study'],'scientific_sha256':seal['scientific_sha256'],
            'repro_scientific_sha256':rseal['scientific_sha256'],'files':files,
            'all_byte_identical':all(v['byte_identical'] for v in files.values())}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    a=ap.parse_args();obj=build(Path(a.study_dir));out=Path(a.study_dir)/'REPRODUCIBILITY.json'
    if a.check:check(out.read_bytes()==dumps(obj),'REPRODUCIBILITY.json does not reproduce');print('REPRODUCIBILITY reproduces')
    else:write_new(out,obj);print(json.dumps({k:obj[k] for k in ('all_byte_identical',)}),json.dumps({k:v['byte_identical'] for k,v in obj['files'].items()}))
