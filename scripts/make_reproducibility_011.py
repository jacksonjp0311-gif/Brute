"""G12 input for study-011 (BRUTE_PLAN_011 criteria.G12_reproducibility). For the 2x2 block the
reproducibility re-run D/repro/<block> (--every 3 --offset 0, i.e. jobs_for(plan, block)[0::3]) is compared case by case
with the sealed main block D/<block>: the canonical JSON (sort_keys, compact) of each case of SCIENTIFIC.json (timing keys
already stripped by no_time) must be byte-identical. A missing case, an unexpected case, any difference or an incomplete
repro block fails G12. No allowed-difference class (study-011 has no planner). Committed before the held-out run_start."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_011 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha

BLOCKS=('2x2',)
def _key(c):return f"{c['block']}/{c['family']}/{c['seed']}/{c['mask_rate']}"
def _canon(c):return json.dumps(c,sort_keys=True,separators=(',',':')).encode()


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
    from experiments.brute_study_011 import jobs_for,smoke_jobs,key
    out={'schema':'brute.reproducibility.v11','study':plan['study'],'smoke_dry_run':smoke,'blocks':{}};ok_all=True
    for b in BLOCKS:
        m=load(study/b/'SCIENTIFIC.json');r=load(study/'repro'/b/'SCIENTIFIC.json')
        ms=load(study/b/'SEAL.json');rs=load(study/'repro'/b/'SEAL.json')
        check(sha(study/b/'SCIENTIFIC.json')==ms['scientific_sha256'] and sha(study/'repro'/b/'SCIENTIFIC.json')==rs['scientific_sha256'],f'{b}: seal mismatch')
        want=[key(j) for j in (smoke_jobs(plan,b) if smoke else jobs_for(plan,b))[0::3]]
        M={_key(c):c for c in m['cases']};R={_key(c):c for c in r['cases']}
        missing=[k for k in want if k not in R or k not in M];ident=0;diff=[]
        for k in want:
            if k in missing:continue
            if _canon(M[k])==_canon(R[k]):ident+=1
            else:diff.append({'key':k,'why':'not byte-identical','first_difference':first_diff(M[k],R[k])})
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
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'REPRODUCIBILITY_011.json'
    if a.check:check(out.read_bytes()==dumps(obj),'REPRODUCIBILITY_011.json does not reproduce');print('REPRODUCIBILITY_011 reproduces')
    else:write_new(out,obj);print(json.dumps({b:{k:v for k,v in x.items() if k in ('expected','byte_identical','passed')} for b,x in obj['blocks'].items()}),'G12',obj['G12_pass'])
