"""Seed assertion for study-009 (BRUTE_PLAN_009 seed_assertion_plan, xcheck_spot_sample). Run and ledgered
(seedcheck_009) BEFORE any v0.7.0 run, smoke included.

Asserts (exit code 0 iff all hold):
  1. the v0.7.0 ranges (held-out 2x2, held-out breadth, smoke 2190001-2190030) are pairwise disjoint; the planning
     block (seeds xx0001-xx0008 of six 2x2 families) and the spot sample are subsets of the held-out blocks;
  2. they are disjoint from every [lo, hi] integer pair found anywhere in experiments/PLAN.json and
     experiments/BRUTE_PLAN_00[2-8].json (parsed, not hard-coded; every pair of ints with 100 <= lo <= hi counts as a
     seed range, which is conservative) plus the earlier smoke seeds 901-903 and the D78 block 1591001-1591384;
  3. check_run_seeds(block, seeds) - used by experiments/brute_study_009.py - raises VerificationError for any seed
     outside the declared range of its block ('2x2' | 'breadth' | 'planning' | 'smoke').

  PYTHONPATH=. python scripts/check_seeds_009.py           # check only
  PYTHONPATH=. python scripts/check_seeds_009.py --draw    # check, then draw the GX2'' spot sample once (refuses overwrite)
"""
import json,random,sys
from pathlib import Path
from experiments.brute_common import VerificationError,check,load,write_new
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_009.json'
SPOT=ROOT/'results/study-009/SPOT_SAMPLE_009.json'
EXTRA_PRIOR={'smoke_901_903':(901,903),'D78_block':(1591001,1591384)}
PLANNING_FAMILIES=('cycle3','switch3','unstructured3','unaliased2','ood4','ood5')
PLANNING_SEEDS_PER_FAMILY=8
SPOT_RNG=20261027
SPOT_FAMILIES=('big6','sens3','act3','ood6s3')
SPOT_PER_FAMILY=6


def int_pairs(obj,path=''):
    if isinstance(obj,dict):
        for k,v in obj.items():yield from int_pairs(v,f'{path}/{k}')
    elif isinstance(obj,list):
        if len(obj)==2 and all(type(x) is int for x in obj) and 100<=obj[0]<=obj[1]:yield path,(obj[0],obj[1])
        else:
            for i,v in enumerate(obj):yield from int_pairs(v,f'{path}[{i}]')


def prior_ranges():
    out={}
    files=[ROOT/'experiments/PLAN.json']+sorted((ROOT/'experiments').glob('BRUTE_PLAN_00[1-8].json'))
    for p in files:
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def ranges_009(plan=None):
    plan=plan or load(PLAN);out={}
    for blk in ('heldout_ranges_2x2','heldout_ranges_breadth'):
        for f,(lo,hi) in plan[blk].items():out[f'{blk}/{f}']=(lo,hi)
    out['smoke']=tuple(plan['smoke_seeds']['range']);return out


def planning_seeds(plan=None):
    """{family: [seed, ...]} for the planning block (first 8 seeds of each planning family's held-out range)."""
    plan=plan or load(PLAN)
    return {f:list(range(plan['heldout_ranges_2x2'][f][0],plan['heldout_ranges_2x2'][f][0]+PLANNING_SEEDS_PER_FAMILY))
            for f in PLANNING_FAMILIES}


def _overlap(a,b):return a[0]<=b[1] and b[0]<=a[1]


def check_run_seeds(block,seeds,plan=None,family=None):
    """Raise VerificationError unless every seed is inside the declared range of `block`."""
    plan=plan or load(PLAN)
    if block=='smoke':
        lo,hi=plan['smoke_seeds']['range'];bad=[s for s in seeds if not lo<=s<=hi]
        check(not bad,f'smoke seed outside {lo}-{hi}: {bad[:5]}');return True
    if block=='planning':
        P=planning_seeds(plan);fams=[family] if family else list(P)
        check(all(f in P for f in fams),'not a planning family: '+str(family))
        bad=[s for s in seeds if not any(s in P[f] for f in fams)]
        check(not bad,f'planning seed outside its declared set: {bad[:5]}');return True
    check(block in ('2x2','breadth'),'unknown block '+str(block))
    R=plan['heldout_ranges_2x2' if block=='2x2' else 'heldout_ranges_breadth']
    if family is not None:check(family in R,f'family {family} not in block {block}')
    fams=[family] if family else list(R)
    bad=[s for s in seeds if not any(R[f][0]<=s<=R[f][1] for f in fams)]
    check(not bad,f'{block} seed outside its declared range: {bad[:5]}');return True


def draw_spot_sample(plan=None):
    """BRUTE_PLAN_009 xcheck_spot_sample: one random.Random(20261027), families in order big6, sens3, act3, ood6s3,
    6 of the 72 (seed, mask) cases each, listed ascending."""
    plan=plan or load(PLAN);rng=random.Random(SPOT_RNG);out={}
    for f in SPOT_FAMILIES:
        lo,hi=plan['heldout_ranges_breadth'][f]
        cases=[(s,m) for s in range(lo,hi+1) for m in plan['mask_rates']]
        out[f]=sorted(rng.sample(cases,SPOT_PER_FAMILY))
    return out


def main(argv=()):
    plan=load(PLAN);new=ranges_009(plan);prior=prior_ranges()
    report={'v070_ranges':new,'prior_range_count':len(prior),'pairwise_overlaps':[],'prior_overlaps':[]}
    ks=list(new)
    for i,a in enumerate(ks):
        for b in ks[i+1:]:
            if _overlap(new[a],new[b]):report['pairwise_overlaps'].append([a,b])
    for a,r in new.items():
        for b,q in prior.items():
            if _overlap(r,q):report['prior_overlaps'].append([a,b,list(q)])
    sub=[]
    for f,seeds in planning_seeds(plan).items():
        try:check_run_seeds('2x2',seeds,plan,family=f)
        except VerificationError:sub.append(['planning',f])
    spot=draw_spot_sample(plan)
    for f,cases in spot.items():
        try:check_run_seeds('breadth',[s for s,_ in cases],plan,family=f)
        except VerificationError:sub.append(['spot',f])
    report['subset_violations']=sub
    neg=[]
    for blk,seed,fam in (('smoke',901,None),('smoke',2010001,None),('smoke',980001,None),('2x2',2190001,None),
                         ('breadth',2010001,None),('2x2',1880001,None),('2x2',2010025,'cycle3'),('planning',2010009,None),
                         ('planning',2080001,None),('breadth',2110025,'big6')):
        try:check_run_seeds(blk,[seed],plan,family=fam);neg.append([blk,seed,'ACCEPTED'])
        except VerificationError:neg.append([blk,seed,'refused'])
    report['negative_controls']=neg
    check_run_seeds('smoke',range(2190001,2190031),plan);check_run_seeds('2x2',[2010001,2080048],plan)
    check_run_seeds('breadth',[2140024],plan);check_run_seeds('planning',[2010001,2070008],plan)
    ok=(not report['pairwise_overlaps'] and not report['prior_overlaps'] and not sub and all(x[2]=='refused' for x in neg))
    report['PASS']=ok
    if '--draw' in argv and ok:
        write_new(SPOT,{'schema':'brute.spot-sample.v1','study':plan['study'],'rule':plan['xcheck_spot_sample']['rule'],
                        'rng':SPOT_RNG,'arm':'B5','cases':{f:[list(c) for c in v] for f,v in spot.items()}})
        report['spot_sample_written']=str(SPOT.relative_to(ROOT))
    report['spot_sample']={f:[list(c) for c in v] for f,v in spot.items()}
    print(json.dumps(report,indent=1,default=list))
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
