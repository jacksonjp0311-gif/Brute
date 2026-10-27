"""G12 input for study-018 (BRUTE_PLAN_018 criteria.G12_reproducibility; adapted from make_reproducibility_017, frozen). The
reproducibility re-run D/repro/main (block main, --every 3 --offset 0, i.e. jobs_for(plan, "main")[0::3] = 120 cases) is
compared case by case with the sealed transfer block D/transfer (which holds every main case): the canonical JSON (sort_keys, compact) of each case of SCIENTIFIC.json (timing keys
already stripped by no_time) must be byte-identical after removing, recursively, every key whose name ends in "_informational" (timing keys: no_time
only strips elapsed_informational and time_informational_seconds; the 017 records also carry bounded_wall_informational,
stress_wall_informational, wall_informational and the frozen 012/013 timing keys). A missing case, an unexpected case, any difference or an incomplete
repro block fails G12. No allowed-difference class. Committed before the held-out run_start."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_018 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha

BLOCKS=('transfer',)
REPRO='main'
def _key(c):return f"{c['block']}/{c['family']}/{c['seed']}/{c['eps']}"
def strip_timing(x):
    if isinstance(x,dict):return {k:strip_timing(v) for k,v in x.items() if not k.endswith('_informational')}
    if isinstance(x,list):return [strip_timing(v) for v in x]
    return x
def _canon(c):return json.dumps(strip_timing(c),sort_keys=True,separators=(',',':')).encode()


def first_diff(a,b,path=''):
    if type(a)!=type(b):return path or '/'
    if isinstance(a,dict):
        for k in sorted(set(a)|set(b)):
            if k not in a or k not in b:return f'{path}/{k}'
            d=first_diff(a[k],b[k],f'{path}/{k}')
            if d:return d
        return None
    if isinstance(a,list):
        if len(a)!=len(b):return f'{path}[len]'
        for i,(x,y) in enumerate(zip(a,b)):
            d=first_diff(x,y,f'{path}[{i}]')
            if d:return d
        return None
    return None if a==b else (path or '/')


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN)
    from experiments.brute_study_018 import jobs_for,key
    out={'schema':'brute.reproducibility.v17','timing_keys_stripped':'every key ending in _informational','study':plan['study'],'smoke_dry_run':smoke,'blocks':{}};ok_all=True
    for b in BLOCKS:
        m=load(study/b/'SCIENTIFIC.json');r=load(study/'repro'/REPRO/'SCIENTIFIC.json')
        ms=load(study/b/'SEAL.json');rs=load(study/'repro'/REPRO/'SEAL.json')
        check(sha(study/b/'SCIENTIFIC.json')==ms['scientific_sha256'] and sha(study/'repro'/REPRO/'SCIENTIFIC.json')==rs['scientific_sha256'],f'{b}: seal mismatch')
        want=[key(j) for j in jobs_for(plan,'smoke-transfer' if smoke else REPRO)[0::3]]
        M={_key(c):c for c in m['cases']};R={_key(c):c for c in r['cases']}
        missing=[k for k in want if k not in R or k not in M];ident=0;diff=[]
        for k in want:
            if k in missing:continue
            if _canon(M[k])==_canon(R[k]):ident+=1
            else:diff.append({'key':k,'why':'not byte-identical','first_difference':first_diff(strip_timing(M[k]),strip_timing(R[k]))})
        extra=sorted(set(R)-set(want))
        passed=not missing and not diff and not extra and bool(rs.get('complete')) and len(want)>0
        ok_all&=passed
        out['blocks'][b]={'expected':len(want),'rerun':len(R),'byte_identical':ident,'failing_differences':diff[:100],
                          'missing':missing[:100],'unexpected':extra[:50],'repro_complete':rs.get('complete'),
                          'main_scientific_sha256':ms['scientific_sha256'],'repro_scientific_sha256':rs['scientific_sha256'],'passed':passed}
    out['G12_pass']=ok_all;return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints, writes nothing')
    a=ap.parse_args()
    if a.smoke:obj=build(Path(a.study_dir),smoke=True);print(dumps(obj).decode()[:3000]);raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'REPRODUCIBILITY_018.json'
    if a.check:check(out.read_bytes()==dumps(obj),'REPRODUCIBILITY_018.json does not reproduce');print('REPRODUCIBILITY_018 reproduces')
    else:write_new(out,obj);print(json.dumps({b:{k:v for k,v in x.items() if k in ('expected','byte_identical','passed')} for b,x in obj['blocks'].items()}),'G12',obj['G12_pass'])
