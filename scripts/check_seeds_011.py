"""Seed assertion for study-011 (BRUTE_PLAN_011 seed_assertion_plan, samples). Run and ledgered (seedcheck_011) BEFORE
any v0.9.0 run, smoke included.

Asserts (exit code 0 iff all hold):
  1. the v0.9.0 ranges (held-out 2x2, smoke 4190001-4190030, feasibility n6/n7/n8) are pairwise disjoint; the G11
     mandatory sample and the --long verify sample are subsets of the held-out block;
  2. they are disjoint from every [lo, hi] integer pair found anywhere in experiments/PLAN.json and every
     experiments/BRUTE_PLAN_0*.json except BRUTE_PLAN_011 (parsed, not hard-coded) plus 901-903 and 1591001-1591384;
  3. check_run_seeds(block, seeds) - used by experiments/brute_study_011.py and scripts/feasibility_011.py - raises
     VerificationError for any seed outside the declared range of its block ('2x2' | 'smoke' | 'feas'; smoke =
     4190001-4190030 or the study-010 smoke seeds 3190001-3190030).

  PYTHONPATH=. python scripts/check_seeds_011.py
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
PLAN=ROOT/'experiments/BRUTE_PLAN_011.json'
EXTRA_PRIOR={'smoke_901_903':(901,903),'D78_block':(1591001,1591384)}
SMOKE_010=(3190001,3190030)
G11_2X2_SEEDS=8;G11_DRIFT_SEEDS=16;LONG_DRIFT_SEEDS=4;LONG_OTHER_SEEDS=1


def int_pairs(obj,path=''):
    if isinstance(obj,dict):
        for k,v in obj.items():yield from int_pairs(v,f'{path}/{k}')
    elif isinstance(obj,list):
        if len(obj)==2 and all(type(x) is int for x in obj) and 100<=obj[0]<=obj[1]:yield path,(obj[0],obj[1])
        else:
            for i,v in enumerate(obj):yield from int_pairs(v,f'{path}[{i}]')


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if p.name!=PLAN.name and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def ranges_011(plan=None):
    plan=plan or load(PLAN);out={}
    for f,(lo,hi) in plan['heldout_ranges_2x2'].items():out['heldout_ranges_2x2/'+f]=(lo,hi)
    out['smoke']=tuple(plan['smoke_seeds']['range'])
    for k in ('n6','n7','n8'):out['feas/'+k]=tuple(plan['feasibility_seeds'][k])
    return out


def _overlap(a,b):return a[0]<=b[1] and b[0]<=a[1]


def check_run_seeds(block,seeds,plan=None,family=None):
    """Raise VerificationError unless every seed is inside the declared range of `block`."""
    plan=plan or load(PLAN)
    if block=='smoke':
        lo,hi=plan['smoke_seeds']['range']
        bad=[s for s in seeds if not (lo<=s<=hi or SMOKE_010[0]<=s<=SMOKE_010[1])]
        check(not bad,f'smoke seed outside {lo}-{hi} and {SMOKE_010[0]}-{SMOKE_010[1]}: {bad[:5]}');return True
    if block=='feas':
        R={k:plan['feasibility_seeds'][k] for k in ('n6','n7','n8')}
    else:
        check(block=='2x2','unknown block '+str(block));R=plan['heldout_ranges_2x2']
    if family is not None:check(family in R,f'family {family} not in block {block}')
    fams=[family] if family else list(R)
    bad=[s for s in seeds if not any(R[f][0]<=s<=R[f][1] for f in fams)]
    check(not bad,f'{block} seed outside its declared range: {bad[:5]}');return True


def g11_mandatory(plan=None):
    """BRUTE_PLAN_011 samples.g11_mandatory_2x2: {family: [seeds]} (offsets 1..8, drift4 1..16; all masks)."""
    plan=plan or load(PLAN)
    return {f:list(range(lo,lo+(G11_DRIFT_SEEDS if f=='drift4' else G11_2X2_SEEDS))) for f,(lo,hi) in plan['heldout_ranges_2x2'].items()}


def long_sample(plan=None):
    """BRUTE_PLAN_011 samples.long_verify: {family: [seeds]} (drift4 offsets 1..4, other families offset 1; all masks)."""
    plan=plan or load(PLAN)
    return {f:list(range(lo,lo+(LONG_DRIFT_SEEDS if f=='drift4' else LONG_OTHER_SEEDS))) for f,(lo,hi) in plan['heldout_ranges_2x2'].items()}


NEGATIVE=(('smoke',901,None),('smoke',4010001,None),('smoke',2190001,None),('2x2',4190001,None),('2x2',3010001,None),
          ('2x2',4010025,'cycle3'),('2x2',4080097,None),('feas',4200013,None),('feas',4010001,None),('2x2',4210001,None),('feas',4220001,'n7'))


def main(argv=()):
    plan=load(PLAN);new=ranges_011(plan);prior=prior_ranges()
    report={'v090_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),'pairwise_overlaps':[],'prior_overlaps':[]}
    ks=list(new)
    for i,a in enumerate(ks):
        for b in ks[i+1:]:
            if _overlap(new[a],new[b]):report['pairwise_overlaps'].append([a,b])
    for a,r in new.items():
        for b,q in prior.items():
            if _overlap(r,q):report['prior_overlaps'].append([a,b,list(q)])
    sub=[];nm=len(plan['mask_rates'])
    for name,S in (('g11',g11_mandatory(plan)),('long',long_sample(plan))):
        for f,seeds in S.items():
            try:check_run_seeds('2x2',seeds,plan,family=f)
            except VerificationError:sub.append([name,f])
    report['subset_violations']=sub
    report['g11_mandatory_cases']=sum(len(v) for v in g11_mandatory(plan).values())*nm
    report['long_verify_cases']=sum(len(v) for v in long_sample(plan).values())*nm
    neg=[]
    for blk,seed,fam in NEGATIVE:
        try:check_run_seeds(blk,[seed],plan,family=fam);neg.append([blk,seed,'ACCEPTED'])
        except VerificationError:neg.append([blk,seed,'refused'])
    report['negative_controls']=neg
    check_run_seeds('smoke',list(range(4190001,4190031))+list(range(3190001,3190031)),plan)
    check_run_seeds('2x2',[4010001,4080096],plan);check_run_seeds('feas',[4200001,4220012],plan)
    ok=(not report['pairwise_overlaps'] and not report['prior_overlaps'] and not sub and all(x[2]=='refused' for x in neg)
        and report['g11_mandatory_cases']==216 and report['long_verify_cases']==33
        and 'BRUTE_PLAN_010.json' in report['prior_files'])
    report['PASS']=ok
    print(json.dumps(report,indent=1,default=list))
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
