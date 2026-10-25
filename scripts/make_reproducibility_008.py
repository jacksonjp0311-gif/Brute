"""G12 input for study-008: (a) the repro re-run (results/study-008/repro = jobs_for(plan)[0::3], 2x2 and breadth) must be
byte-identical case by case to the sealed main run (canonical JSON of each SCIENTIFIC case; timing keys already stripped
by no_time); (b) GMC: results/study-008/repro/GMC_COUNT_008.json (make_count_008 on the repro RESULTS) is compared step by
step with the main GMC_COUNT_008.json on every common case key. Compared count fields: R, blocking, blocking_censored,
pairs, fibre. A difference is ALLOWED only when one side is UNKNOWN (None) and that side's reason is a timeout/budget
reason (R_reason / unknown_fibre_reasons); every allowed difference is reported. Any other difference fails G12.
Committed before the held-out run_start."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common_008 import STUDY_DIR,PLAN,load,dumps,write_new,check,sha

def _key(c):return f"{c['block']}/{c['family']}/{c['seed']}/{c['mask_rate']}"
def _canon(c):return json.dumps(c,sort_keys=True,separators=(',',':')).encode()
def _timeoutish(reason):return reason is not None and any(w in str(reason).lower() for w in ('timeout','budget','cap'))


def gmc_compare(main,rep):
    M={c['key']:c for c in main['cases']};R={c['key']:c for c in rep['cases']}
    common=sorted(set(M)&set(R));same=0;allowed=[];bad=[]
    for k in common:
        sm={s['step']:s for s in M[k]['steps']};sr={s['step']:s for s in R[k]['steps']}
        if set(sm)!=set(sr):bad.append({'key':k,'why':'sampled steps differ'});continue
        for st in sorted(sm):
            a,b=sm[st],sr[st];diffs=[]
            for f in ('R','blocking','blocking_censored'):
                if a.get(f)!=b.get(f):diffs.append(f)
            for f in ('pairs','fibre'):
                for sub in sorted(set(a.get(f,{}))|set(b.get(f,{}))):
                    if a.get(f,{}).get(sub)!=b.get(f,{}).get(sub):diffs.append(f'{f}.{sub}')
            if not diffs:same+=1;continue
            ok=True
            for f in diffs:
                x=a.get(f) if '.' not in f else a.get(f.split('.')[0],{}).get(f.split('.',1)[1])
                y=b.get(f) if '.' not in f else b.get(f.split('.')[0],{}).get(f.split('.',1)[1])
                if f in ('blocking','blocking_censored'):ok=False;break   # the blocking count has no wall-clock timeout
                side=a if x is None else (b if y is None else None)
                if side is None:ok=False;break
                why=side['R_reason'] if f=='R' else ' '.join(r for r,_ in side.get('unknown_fibre_reasons',[]))
                if not _timeoutish(why):ok=False;break
            (allowed if ok else bad).append({'key':k,'step':st,'fields':diffs})
    return {'common_cases':len(common),'repro_cases':len(R),'identical_steps':same,
            'differences_only_by_timeout':len(allowed),'timeout_differences':allowed[:100],
            'other_differences':len(bad),'other_difference_list':bad[:100],'identical':not bad and len(common)==len(R)}


def build(study=STUDY_DIR):
    study=Path(study)
    if study==STUDY_DIR:
        from scripts.study008_storage import ensure_raw;ensure_raw()
    from experiments.brute_study_008 import jobs_for,key
    main=load(study/'SCIENTIFIC.json');rep=load(study/'repro/SCIENTIFIC.json');plan=load(PLAN)
    seal=load(study/'SEAL.json');rseal=load(study/'repro/SEAL.json')
    check(sha(study/'SCIENTIFIC.json')==seal['scientific_sha256'] and sha(study/'repro/SCIENTIFIC.json')==rseal['scientific_sha256'],'seal mismatch')
    want=[key(j) for j in jobs_for(plan)[0::3]]
    M={_key(c):c for c in main['cases']};Rc={_key(c):c for c in rep['cases']}
    diff=[k for k in want if k not in Rc or k not in M or _canon(Rc[k])!=_canon(M[k])]
    blocks={}
    for k in want:
        b=k.split('/')[0];blocks.setdefault(b,{'cases':0,'identical':0});blocks[b]['cases']+=1;blocks[b]['identical']+=k not in diff
    files={'cases_index_divisible_by_3':{'expected':len(want),'rerun':len(Rc),'byte_identical':not diff and len(Rc)==len(want),
                                         'differing':diff[:50],'per_block':blocks}}
    gm=load(study/'GMC_COUNT_008.json');gr=load(study/'repro/GMC_COUNT_008.json')
    check(gm['results_sha256']==seal['results_sha256'] and gr['results_sha256']==rseal['results_sha256'],'GMC inputs are not the sealed RESULTS')
    g=gmc_compare(gm,gr)
    return {'schema':'brute.reproducibility.v8','study':plan['study'],'scientific_sha256':seal['scientific_sha256'],
            'repro_scientific_sha256':rseal['scientific_sha256'],'files':files,'gmc_recount':g,
            'all_byte_identical':files['cases_index_divisible_by_3']['byte_identical'],
            'G12_pass':files['cases_index_divisible_by_3']['byte_identical'] and g['identical']}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--study-dir',default=str(STUDY_DIR));ap.add_argument('--check',action='store_true')
    a=ap.parse_args();obj=build(Path(a.study_dir));out=Path(a.study_dir)/'REPRODUCIBILITY.json'
    if a.check:check(out.read_bytes()==dumps(obj),'REPRODUCIBILITY.json does not reproduce');print('REPRODUCIBILITY reproduces')
    else:write_new(out,obj);print(json.dumps({k:obj[k] for k in ('all_byte_identical','G12_pass')}),json.dumps({k:v for k,v in obj['gmc_recount'].items() if k not in ('timeout_differences','other_difference_list')}))
