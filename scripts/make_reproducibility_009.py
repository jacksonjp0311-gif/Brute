"""G12 input for study-009 (BRUTE_PLAN_009 criteria.G12_reproducibility). For each block (2x2, breadth, planning) the
reproducibility re-run D/repro/<block> (run with --every 3 --offset 0, i.e. jobs_for(plan, block)[0::3]) is compared case
by case with the sealed main block D/<block>: canonical JSON (sort_keys, compact) of each SCIENTIFIC case; timing keys are
already stripped by the study runner. 2x2 and breadth: byte-identical required. Planning (P7): the case is byte-identical
OR all of: (a) the case outside arms.P7 is identical; (b) let f = the first step at which EITHER run's P7 planner record has
a budget/timeout fallback (fallback_reason containing 'timeout', 'budget' or 'exhausted'); f exists and every trace record
before step f is identical in both runs (records from step f on, and the P7 diagnostics / issued / retractions /
experiment_calls, may differ). Every such allowed difference is reported with f and the first differing step. Any other
difference, a missing case or an incomplete repro block fails G12. Committed before the held-out run_start."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_009 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha

BLOCKS=('2x2','breadth','planning')
def _key(c):return f"{c['block']}/{c['family']}/{c['seed']}/{c['mask_rate']}"
def _canon(c):return json.dumps(c,sort_keys=True,separators=(',',':')).encode()
def _budgetish(r):return r is not None and any(w in str(r).lower() for w in ('timeout','budget','exhausted'))


def first_fallback(trace):
    for r in trace:
        P=r.get('planner')
        if P and _budgetish(P.get('fallback_reason')):return r['step']
    return None


def p7_compare(a,b):
    """None if identical; else dict with allowed flag."""
    if _canon(a)==_canon(b):return None
    ra={k:v for k,v in a.items() if k!='arms'}|{'arms':{x:y for x,y in a['arms'].items() if x!='P7'}}
    rb={k:v for k,v in b.items() if k!='arms'}|{'arms':{x:y for x,y in b['arms'].items() if x!='P7'}}
    if _canon(ra)!=_canon(rb):return {'allowed':False,'why':'difference outside arms.P7'}
    ta,tb=a['arms']['P7']['trace'],b['arms']['P7']['trace']
    fs=[s for s in (first_fallback(ta),first_fallback(tb)) if s is not None];f=min(fs) if fs else None
    first=next((x['step'] for x,y in zip(ta,tb) if _canon(x)!=_canon(y)),None)
    if first is None and len(ta)!=len(tb):first=min(len(ta),len(tb))+1
    if f is None:return {'allowed':False,'why':'P7 differs without a budget/timeout fallback','first_differing_step':first}
    ok=first is None or first>=f
    return {'allowed':ok,'first_budget_fallback_step':f,'first_differing_step':first,
            'why':'differs only from the first budget/timeout fallback' if ok else 'differs before the first budget/timeout fallback'}


def build(study=STUDY_DIR,smoke=False):
    study=Path(study);plan=load(PLAN)
    from experiments.brute_study_009 import jobs_for,smoke_jobs,key
    out={'schema':'brute.reproducibility.v9','study':plan['study'],'smoke_dry_run':smoke,'blocks':{}};ok_all=True
    for b in BLOCKS:
        m=load(study/b/'SCIENTIFIC.json');r=load(study/'repro'/b/'SCIENTIFIC.json')
        ms=load(study/b/'SEAL.json');rs=load(study/'repro'/b/'SEAL.json')
        check(sha(study/b/'SCIENTIFIC.json')==ms['scientific_sha256'] and sha(study/'repro'/b/'SCIENTIFIC.json')==rs['scientific_sha256'],f'{b}: seal mismatch')
        want=[key(j) for j in (smoke_jobs(plan,b) if smoke else jobs_for(plan,b))[0::3]]
        M={_key(c):c for c in m['cases']};R={_key(c):c for c in r['cases']}
        missing=[k for k in want if k not in R or k not in M];ident=0;diff=[];allowed=[]
        for k in want:
            if k in missing:continue
            if _canon(M[k])==_canon(R[k]):ident+=1;continue
            if b=='planning':
                v=p7_compare(M[k],R[k]);(allowed if v['allowed'] else diff).append({'key':k,**v})
            else:diff.append({'key':k,'why':'not byte-identical'})
        extra=sorted(set(R)-set(want))
        passed=not missing and not diff and not extra and bool(rs.get('complete')) and len(want)>0
        ok_all&=passed
        out['blocks'][b]={'expected':len(want),'rerun':len(R),'byte_identical':ident,'allowed_p7_fallback_differences':allowed,
                          'failing_differences':diff[:100],'missing':missing[:100],'unexpected':extra[:50],
                          'repro_complete':rs.get('complete'),'main_scientific_sha256':ms['scientific_sha256'],
                          'repro_scientific_sha256':rs['scientific_sha256'],'passed':passed}
    out['G12_pass']=ok_all;return out


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    ap.add_argument('--smoke',action='store_true',help='dry run on a smoke directory; prints, writes nothing')
    a=ap.parse_args()
    if a.smoke:obj=build(Path(a.study_dir),smoke=True);print(dumps(obj).decode()[:3000]);raise SystemExit
    obj=build(Path(a.study_dir));out=Path(a.study_dir)/'REPRODUCIBILITY_009.json'
    if a.check:check(out.read_bytes()==dumps(obj),'REPRODUCIBILITY_009.json does not reproduce');print('REPRODUCIBILITY_009 reproduces')
    else:write_new(out,obj);print(json.dumps({b:{k:v for k,v in x.items() if k in ('expected','byte_identical','passed')} for b,x in obj['blocks'].items()}),'G12',obj['G12_pass'])
