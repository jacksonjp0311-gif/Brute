"""Seed assertion for study-008 (BRUTE_PLAN_008 seed_assertion_plan). Run and ledgered (seedcheck_008) BEFORE any
v0.6.0 run, smoke included.

Asserts (exit code 0 iff all hold):
  1. the v0.6.0 ranges (held-out 2x2, held-out breadth, smoke 980001-980030) are pairwise disjoint;
  2. they are disjoint from every [lo, hi] integer pair found anywhere in experiments/BRUTE_PLAN_00[2-7].json (parsed,
     not hard-coded; every pair of ints with 100 <= lo <= hi is treated as a seed range, which is conservative) plus the
     earlier smoke seeds 901-903 and the D78 block 1591001-1591384. (There is no BRUTE_PLAN_001.json in the repo.)
  3. check_run_seeds(block, seeds) — used by experiments/brute_study_008.py — raises VerificationError for any seed
     outside the declared range of its block, and smoke mode accepts only 980001-980030.

  PYTHONPATH=. python scripts/check_seeds_008.py
"""
import json,sys
from pathlib import Path
from experiments.brute_common import VerificationError,check,load
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_008.json'
EXTRA_PRIOR={'smoke_901_903':(901,903),'D78_block':(1591001,1591384)}


def int_pairs(obj,path=''):
    if isinstance(obj,dict):
        for k,v in obj.items():yield from int_pairs(v,f'{path}/{k}')
    elif isinstance(obj,list):
        if len(obj)==2 and all(type(x) is int for x in obj) and 100<=obj[0]<=obj[1]:yield path,(obj[0],obj[1])
        else:
            for i,v in enumerate(obj):yield from int_pairs(v,f'{path}[{i}]')


def prior_ranges():
    out={}
    for p in sorted((ROOT/'experiments').glob('BRUTE_PLAN_00[1-7].json')):
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def ranges_008(plan=None):
    plan=plan or load(PLAN);out={}
    for blk in ('heldout_ranges_2x2','heldout_ranges_breadth'):
        for f,(lo,hi) in plan[blk].items():out[f'{blk}/{f}']=(lo,hi)
    out['smoke']=tuple(plan['smoke_seeds']['range']);return out


def _overlap(a,b):return a[0]<=b[1] and b[0]<=a[1]


def check_run_seeds(block,seeds,plan=None,family=None):
    """Raise VerificationError unless every seed is inside the declared range of `block` ('2x2' | 'breadth' | 'smoke')."""
    plan=plan or load(PLAN)
    if block=='smoke':
        lo,hi=plan['smoke_seeds']['range'];bad=[s for s in seeds if not lo<=s<=hi]
        check(not bad,f'smoke seed outside {lo}-{hi}: {bad[:5]}');return True
    R=plan['heldout_ranges_2x2' if block=='2x2' else 'heldout_ranges_breadth']
    check(block in ('2x2','breadth'),'unknown block '+str(block))
    fams=[family] if family else list(R)
    bad=[s for s in seeds if not any(R[f][0]<=s<=R[f][1] for f in fams)]
    check(not bad,f'{block} seed outside its declared range: {bad[:5]}');return True


def main():
    new=ranges_008();prior=prior_ranges();report={'v060_ranges':new,'prior_range_count':len(prior),'pairwise_overlaps':[],'prior_overlaps':[]}
    ks=list(new)
    for i,a in enumerate(ks):
        for b in ks[i+1:]:
            if _overlap(new[a],new[b]):report['pairwise_overlaps'].append([a,b])
    for a,r in new.items():
        for b,q in prior.items():
            if _overlap(r,q):report['prior_overlaps'].append([a,b,list(q)])
    # runner assertions (negative controls)
    neg=[]
    for blk,seed in (('smoke',901),('smoke',1810001),('2x2',980001),('breadth',1810001),('2x2',1700001)):
        try:check_run_seeds(blk,[seed]);neg.append([blk,seed,'ACCEPTED'])
        except VerificationError:neg.append([blk,seed,'refused'])
    report['negative_controls']=neg
    ok=not report['pairwise_overlaps'] and not report['prior_overlaps'] and all(x[2]=='refused' for x in neg)
    check_run_seeds('smoke',range(980001,980031));check_run_seeds('2x2',[1810001,1880048]);check_run_seeds('breadth',[1940024])
    report['PASS']=ok;print(json.dumps(report,indent=1,default=list))
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main())
