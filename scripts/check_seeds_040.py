"""Seed assertion for study-040 (BRUTE_PLAN_040 heldout_ranges: scale16, scale14, lowobs12 and control, each an explicit
list of consecutive seeds; the smoke range 10680001-10680012 is declared by the plan's smoke_range). Run and ledgered
(seedcheck_040) BEFORE any v0.37.0 run code touches a target seed. New file (check_seeds_039 logic with the 040 ranges; every
case eps 0).

Asserts (exit 0 iff all hold):
  1. every 040 list is consecutive and the 040 ranges (4 targets + the smoke range) are pairwise disjoint;
  2. disjoint from every [lo, hi] pair in experiments/PLAN.json and every experiments/BRUTE_PLAN_0*.json except
     BRUTE_PLAN_040* (parsed), plus the extra ranges of check_seeds_039 (all earlier extras), the 039 smoke range and the 039 list ranges;
  3. token scan: no git-tracked file under results/ or experiments/ (BRUTE_PLAN_040* and this check's output excluded)
     contains a standalone integer token in any 040 range;
  4. check_run_seeds(block, seeds, key) refuses any seed outside its declared range (negative controls);
  5. 12 + 12 + 12 + 6 = 42 target seeds -> 42 cases; eps 0 everywhere.
  PYTHONPATH=. python scripts/check_seeds_040.py [--write results/diag-040/SEEDCHECK_040.json]
"""
import gzip,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
from scripts import check_seeds_033 as c33
from scripts import check_seeds_039 as c39
PLAN=ROOT/'experiments/BRUTE_PLAN_040.json'
EXTRA_PRIOR={**c39.EXTRA_PRIOR,'smoke_039':c39.SMOKE,**{'plan039/'+k:v for k,v in c39.ranges_039().items()}}
SMOKE=(10680001,10680012)
FAMILY_OF={'scale16':'scale16','scale14':'scale14','lowobs12':'lowobs12','control':'control_cycle3'}
EPS_OF={k:0.0 for k in FAMILY_OF}
COUNTS={'scale16':12,'scale14':12,'lowobs12':12,'control':6}
TOKEN=re.compile(rb'(?<![0-9.eE\-])(106[0-9]{5})(?![0-9.eE])');ANY=re.compile(rb"106[0-9]{5}")
SCAN_SUFFIX=c33.SCAN_SUFFIX


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_040') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def target_ranges(plan=None):
    """{plan key: (lo, hi)}; keys, not families, because clean and noisy scale12 share a world family."""
    plan=plan or load(PLAN);H=plan['heldout_ranges'];return {k:c33._span(H[k],k) for k in FAMILY_OF}


def ranges_040(plan=None):
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
    files=[f for f in files if f.endswith(SCAN_SUFFIX) and not Path(f).name.startswith('BRUTE_PLAN_040') and 'SEEDCHECK_040' not in f]
    inr=lambda v:any(a<=v<=b for a,b in ranges.values());tok=[];emb=0;scanned=0
    for f in files:
        p=ROOT/f
        if not p.exists():continue
        b=gzip.open(p).read() if f.endswith('.gz') else p.read_bytes();scanned+=1
        for m in TOKEN.finditer(b):
            if inr(int(m.group(1))):tok.append([f,int(m.group(1))])
        emb+=sum(1 for m in ANY.finditer(b) if inr(int(m.group(0))))
    return {'files_scanned':scanned,'standalone_tokens_in_040_ranges':tok,'occurrences_any_in_040_ranges':emb,'embedded_only':emb-len(tok)}


NEGATIVE=(('target',10699001,None),('smoke',10699001,None),('target',10680001,None),('smoke',10610001,None),
          ('target',10610013,'scale16'),('target',10620001,'scale16'),('target',10630001,'scale14'),('target',10610001,'lowobs12'),
          ('target',10660007,'control'),('target',10530001,None),('smoke',10590001,None),('smoke',10680013,None),
          ('target',10609999,None),('target',10640001,None),('target',10610001,'perm12'),('target',10690024,None))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_040(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v37','v0370_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
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
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and not rep['token_scan']['standalone_tokens_in_040_ranges']
        and rep['token_scan']['files_scanned']>0 and all(x[3]=='refused' for x in neg) and rep['cases_by_key']==COUNTS
        and rep['total_cases']==42==C['total'] and eps_ok
        and 'BRUTE_PLAN_039.json' in rep['prior_files'] and 'BRUTE_PLAN_040.json' not in rep['prior_files'])
    rep['eps_by_key']=EPS_OF;rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
