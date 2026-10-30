"""Seed assertion for study-036 (BRUTE_PLAN_036 heldout_ranges: noisy_scale8, noisy_scale12, clean_scale12, noisy_scale12_extra,
control and smoke, each an explicit list of consecutive seeds). Run and ledgered (seedcheck_036) BEFORE any v0.33.0 run
code touches a target seed. New file (check_seeds_035 logic with the 036 ranges; noisy keys at eps 0.05, the rest eps 0).

Asserts (exit 0 iff all hold):
  1. every 036 list is consecutive and the 036 ranges (5 targets + smoke) are pairwise disjoint;
  2. disjoint from every [lo, hi] pair in experiments/PLAN.json and every experiments/BRUTE_PLAN_0*.json except
     BRUTE_PLAN_036* (parsed), plus the extra ranges of check_seeds_035 (034 extras, 034 smoke and lists), the 035 smoke range and the 035 list ranges;
  3. token scan: no git-tracked file under results/ or experiments/ (BRUTE_PLAN_036* and this check's output excluded)
     contains a standalone integer token in any 036 range;
  4. check_run_seeds(block, seeds, key) refuses any seed outside its declared range (negative controls);
  5. 12 + 12 + 12 + 6 + 6 = 48 target seeds -> 48 cases; eps 0.05 on the three noisy keys, 0 elsewhere.
  PYTHONPATH=. python scripts/check_seeds_036.py [--write results/diag-036/SEEDCHECK_036.json]
"""
import gzip,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
from scripts import check_seeds_033 as c33
from scripts import check_seeds_035 as c35
PLAN=ROOT/'experiments/BRUTE_PLAN_036.json'
EXTRA_PRIOR={**c35.EXTRA_PRIOR,'smoke_035':c35.SMOKE,**{'plan035/'+k:v for k,v in c35.ranges_035().items()}}
SMOKE=(10290001,10290030)
FAMILY_OF={'noisy_scale8':'scale8','noisy_scale12':'scale12','clean_scale12':'scale12','noisy_scale12_extra':'scale12','control':'control_cycle3'}
EPS_OF={'noisy_scale8':0.05,'noisy_scale12':0.05,'clean_scale12':0.0,'noisy_scale12_extra':0.05,'control':0.0}
COUNTS={'noisy_scale8':12,'noisy_scale12':12,'clean_scale12':12,'noisy_scale12_extra':6,'control':6}
TOKEN=re.compile(rb'(?<![0-9.eE\-])(102[0-9]{5})(?![0-9.eE])');ANY=re.compile(rb'102[0-9]{5}')
SCAN_SUFFIX=c33.SCAN_SUFFIX


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_036') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def target_ranges(plan=None):
    """{plan key: (lo, hi)}; keys, not families, because clean and noisy scale12 share a world family."""
    plan=plan or load(PLAN);H=plan['heldout_ranges'];return {k:c33._span(H[k],k) for k in FAMILY_OF}


def ranges_036(plan=None):
    plan=plan or load(PLAN);out={'target/'+k:r for k,r in target_ranges(plan).items()}
    out['smoke']=c33._span(plan['heldout_ranges']['smoke'],'smoke');return out


def check_run_seeds(block,seeds,plan=None,key=None):
    plan=plan or load(PLAN)
    if block=='smoke':
        bad=[s for s in seeds if not (SMOKE[0]<=s<=SMOKE[1])];check(not bad,f'smoke seed outside {SMOKE}: {bad[:5]}');return True
    if block!='target':raise VerificationError('unknown block '+str(block))
    R=target_ranges(plan)
    if key is not None:check(key in R,f'key {key} not in block {block}')
    ks=[key] if key else list(R)
    bad=[s for s in seeds if not any(R[k][0]<=s<=R[k][1] for k in ks)]
    check(not bad,f'{block} seed outside its declared range: {bad[:5]}');return True


def token_scan(ranges):
    files=subprocess.run(['git','ls-files','results','experiments'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.split()
    files=[f for f in files if f.endswith(SCAN_SUFFIX) and not Path(f).name.startswith('BRUTE_PLAN_036') and 'SEEDCHECK_036' not in f]
    inr=lambda v:any(a<=v<=b for a,b in ranges.values());tok=[];emb=0;scanned=0
    for f in files:
        p=ROOT/f
        if not p.exists():continue
        b=gzip.open(p).read() if f.endswith('.gz') else p.read_bytes();scanned+=1
        for m in TOKEN.finditer(b):
            if inr(int(m.group(1))):tok.append([f,int(m.group(1))])
        emb+=sum(1 for m in ANY.finditer(b) if inr(int(m.group(0))))
    return {'files_scanned':scanned,'standalone_tokens_in_036_ranges':tok,'occurrences_any_in_036_ranges':emb,'embedded_only':emb-len(tok)}


NEGATIVE=(('target',10299001,None),('smoke',10299001,None),('target',10290001,None),('smoke',10210001,None),
          ('target',10210013,'noisy_scale8'),('target',10220001,'noisy_scale8'),('target',10230001,'noisy_scale12'),
          ('target',10220001,'clean_scale12'),('target',10260007,'control'),('target',10110001,None),('smoke',10190001,None),
          ('target',10240007,None),('smoke',10290031,None),('target',10209999,None),('target',10240001,'clean_scale12'),
          ('target',10250001,None))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_036(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v33','v0330_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
         'pairwise_overlaps':[],'prior_overlaps':[]}
    ks=list(new)
    for i,a in enumerate(ks):
        for b in ks[i+1:]:
            if _overlap(new[a],new[b]):rep['pairwise_overlaps'].append([a,b])
    for a,r in new.items():
        for b,q in prior.items():
            if _overlap(r,q):rep['prior_overlaps'].append([a,b,list(q)])
    rep['token_scan']=token_scan(new)
    neg=[]
    for blk,seed,k in NEGATIVE:
        try:check_run_seeds(blk,[seed],plan,key=k);neg.append([blk,seed,k,'ACCEPTED'])
        except VerificationError:neg.append([blk,seed,k,'refused'])
    rep['negative_controls']=neg
    check_run_seeds('smoke',list(range(SMOKE[0],SMOKE[1]+1)),plan);check(new['smoke']==SMOKE,'plan smoke range')
    H=plan['heldout_ranges'];rep['cases_by_key']={k:len(H[k]) for k in COUNTS};rep['total_cases']=sum(rep['cases_by_key'].values())
    C=plan['cases'];eps_ok=(C['eps_noisy']==0.05 and C['eps_clean']==0)
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and not rep['token_scan']['standalone_tokens_in_036_ranges']
        and rep['token_scan']['files_scanned']>0 and all(x[3]=='refused' for x in neg) and rep['cases_by_key']==COUNTS
        and rep['total_cases']==48==C['total'] and eps_ok
        and 'BRUTE_PLAN_035.json' in rep['prior_files'] and 'BRUTE_PLAN_036.json' not in rep['prior_files'])
    rep['eps_by_key']=EPS_OF;rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
