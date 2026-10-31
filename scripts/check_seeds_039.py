"""Seed assertion for study-039 (BRUTE_PLAN_039 heldout_ranges: scale12, scale14, scale16, perm12 and control, each an explicit
list of consecutive seeds; the smoke range 10590001-10590012 is declared by the plan's smoke_range). Run and ledgered
(seedcheck_039) BEFORE any v0.36.0 run code touches a target seed. New file (check_seeds_038 logic with the 039 ranges; every
case eps 0).

Asserts (exit 0 iff all hold):
  1. every 039 list is consecutive and the 039 ranges (5 targets + the smoke range) are pairwise disjoint;
  2. disjoint from every [lo, hi] pair in experiments/PLAN.json and every experiments/BRUTE_PLAN_0*.json except
     BRUTE_PLAN_039* (parsed), plus the extra ranges of check_seeds_038 (all earlier extras), the 038 smoke range and the 038 list ranges;
  3. token scan: no git-tracked file under results/ or experiments/ (BRUTE_PLAN_039* and this check's output excluded)
     contains a standalone integer token in any 039 range;
  4. check_run_seeds(block, seeds, key) refuses any seed outside its declared range (negative controls);
  5. 12 + 12 + 12 + 12 + 6 = 54 target seeds -> 54 cases; eps 0 everywhere.
  PYTHONPATH=. python scripts/check_seeds_039.py [--write results/diag-039/SEEDCHECK_039.json]
"""
import gzip,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
from scripts import check_seeds_033 as c33
from scripts import check_seeds_038 as c38
PLAN=ROOT/'experiments/BRUTE_PLAN_039.json'
EXTRA_PRIOR={**c38.EXTRA_PRIOR,'smoke_038':c38.SMOKE,**{'plan038/'+k:v for k,v in c38.ranges_038().items()}}
SMOKE=(10590001,10590012)
FAMILY_OF={'scale12':'scale12','scale14':'scale14','scale16':'scale16','perm12':'perm12','control':'control_cycle3'}
EPS_OF={k:0.0 for k in FAMILY_OF}
COUNTS={'scale12':12,'scale14':12,'scale16':12,'perm12':12,'control':6}
TOKEN=re.compile(rb'(?<![0-9.eE\-])(105[0-9]{5})(?![0-9.eE])');ANY=re.compile(rb'105[0-9]{5}')
SCAN_SUFFIX=c33.SCAN_SUFFIX


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_039') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def target_ranges(plan=None):
    """{plan key: (lo, hi)}; keys, not families, because clean and noisy scale12 share a world family."""
    plan=plan or load(PLAN);H=plan['heldout_ranges'];return {k:c33._span(H[k],k) for k in FAMILY_OF}


def ranges_039(plan=None):
    plan=plan or load(PLAN);out={'target/'+k:r for k,r in target_ranges(plan).items()}
    out['smoke']=SMOKE;return out


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
    files=[f for f in files if f.endswith(SCAN_SUFFIX) and not Path(f).name.startswith('BRUTE_PLAN_039') and 'SEEDCHECK_039' not in f]
    inr=lambda v:any(a<=v<=b for a,b in ranges.values());tok=[];emb=0;scanned=0
    for f in files:
        p=ROOT/f
        if not p.exists():continue
        b=gzip.open(p).read() if f.endswith('.gz') else p.read_bytes();scanned+=1
        for m in TOKEN.finditer(b):
            if inr(int(m.group(1))):tok.append([f,int(m.group(1))])
        emb+=sum(1 for m in ANY.finditer(b) if inr(int(m.group(0))))
    return {'files_scanned':scanned,'standalone_tokens_in_039_ranges':tok,'occurrences_any_in_039_ranges':emb,'embedded_only':emb-len(tok)}


NEGATIVE=(('target',10599001,None),('smoke',10599001,None),('target',10590001,None),('smoke',10510001,None),
          ('target',10510013,'scale12'),('target',10520001,'scale12'),('target',10530001,'scale14'),('target',10540001,'scale16'),
          ('target',10510001,'perm12'),('target',10560007,'control'),('target',10410001,None),('smoke',10490001,None),
          ('smoke',10590013,None),('target',10509999,None),('target',10550001,None),('target',10560001,'perm12'))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_039(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v36','v0360_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
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
    check_run_seeds('smoke',list(range(SMOKE[0],SMOKE[1]+1)),plan);check(new['smoke']==SMOKE,'smoke range')
    H=plan['heldout_ranges'];rep['cases_by_key']={k:len(H[k]) for k in COUNTS};rep['total_cases']=sum(rep['cases_by_key'].values())
    C=plan['cases'];eps_ok=(C['eps']==0)
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and not rep['token_scan']['standalone_tokens_in_039_ranges']
        and rep['token_scan']['files_scanned']>0 and all(x[3]=='refused' for x in neg) and rep['cases_by_key']==COUNTS
        and rep['total_cases']==54==C['total'] and eps_ok
        and 'BRUTE_PLAN_038.json' in rep['prior_files'] and 'BRUTE_PLAN_039.json' not in rep['prior_files'])
    rep['eps_by_key']=EPS_OF;rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
