"""Seed assertion for study-010 (BRUTE_PLAN_010 seed_assertion_plan, samples). Run and ledgered (seedcheck_010) BEFORE
any v0.8.0 run, smoke included.

Asserts (exit code 0 iff all hold):
  1. the v0.8.0 ranges (held-out 2x2, held-out breadth, smoke 3190001-3190030) are pairwise disjoint; the G11 mandatory
     samples and the GX2 spot sample are subsets of the held-out blocks;
  2. they are disjoint from every [lo, hi] integer pair found anywhere in experiments/PLAN.json and
     experiments/BRUTE_PLAN_00[1-9].json (parsed, not hard-coded) plus 901-903 and 1591001-1591384;
  3. check_run_seeds(block, seeds) - used by experiments/brute_study_010.py - raises VerificationError for any seed
     outside the declared range of its block ('2x2' | 'breadth' | 'smoke'; smoke = 3190001-3190030 or the study-009
     smoke seeds 2190001-2190030, BRUTE_PLAN_010 smoke_seeds.rule).

  PYTHONPATH=. python scripts/check_seeds_010.py           # check only
  PYTHONPATH=. python scripts/check_seeds_010.py --draw    # check, then write SPOT_SAMPLE_010.json once (refuses overwrite)
"""
import json,random,sys
from pathlib import Path
from experiments.brute_common import VerificationError,check,load,write_new
ROOT=Path(__file__).resolve().parents[1]
PLAN=ROOT/'experiments/BRUTE_PLAN_010.json'
SPOT=ROOT/'results/study-010/SPOT_SAMPLE_010.json'
EXTRA_PRIOR={'smoke_901_903':(901,903),'D78_block':(1591001,1591384)}
SMOKE_009=(2190001,2190030)
SPOT_RNG=20261028
SPOT_FAMILIES=('act3','sens3')
SPOT_PER_FAMILY=3
G11_2X2_SEEDS=8;G11_DRIFT_SEEDS=16;G11_BREADTH_SEEDS=6


def int_pairs(obj,path=''):
    if isinstance(obj,dict):
        for k,v in obj.items():yield from int_pairs(v,f'{path}/{k}')
    elif isinstance(obj,list):
        if len(obj)==2 and all(type(x) is int for x in obj) and 100<=obj[0]<=obj[1]:yield path,(obj[0],obj[1])
        else:
            for i,v in enumerate(obj):yield from int_pairs(v,f'{path}[{i}]')


def prior_ranges():
    out={}
    files=[ROOT/'experiments/PLAN.json']+sorted((ROOT/'experiments').glob('BRUTE_PLAN_00[1-9].json'))
    for p in files:
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def ranges_010(plan=None):
    plan=plan or load(PLAN);out={}
    for blk in ('heldout_ranges_2x2','heldout_ranges_breadth'):
        for f,(lo,hi) in plan[blk].items():out[f'{blk}/{f}']=(lo,hi)
    out['smoke']=tuple(plan['smoke_seeds']['range']);return out


def _overlap(a,b):return a[0]<=b[1] and b[0]<=a[1]


def check_run_seeds(block,seeds,plan=None,family=None):
    """Raise VerificationError unless every seed is inside the declared range of `block`."""
    plan=plan or load(PLAN)
    if block=='smoke':
        lo,hi=plan['smoke_seeds']['range']
        bad=[s for s in seeds if not (lo<=s<=hi or SMOKE_009[0]<=s<=SMOKE_009[1])]
        check(not bad,f'smoke seed outside {lo}-{hi} and {SMOKE_009[0]}-{SMOKE_009[1]}: {bad[:5]}');return True
    check(block in ('2x2','breadth'),'unknown block '+str(block))
    R=plan['heldout_ranges_2x2' if block=='2x2' else 'heldout_ranges_breadth']
    if family is not None:check(family in R,f'family {family} not in block {block}')
    fams=[family] if family else list(R)
    bad=[s for s in seeds if not any(R[f][0]<=s<=R[f][1] for f in fams)]
    check(not bad,f'{block} seed outside its declared range: {bad[:5]}');return True


def g11_mandatory(plan=None):
    """BRUTE_PLAN_010 samples.g11_mandatory_*: {'2x2': {family: [seeds]}, 'breadth': {family: [seeds]}} (offsets 1..n of
    each family range = the first n seeds; drift4 16, other 2x2 families 8, breadth families 6; all masks)."""
    plan=plan or load(PLAN)
    t={f:list(range(lo,lo+(G11_DRIFT_SEEDS if f=='drift4' else G11_2X2_SEEDS))) for f,(lo,hi) in plan['heldout_ranges_2x2'].items()}
    b={f:list(range(lo,lo+G11_BREADTH_SEEDS)) for f,(lo,hi) in plan['heldout_ranges_breadth'].items()}
    return {'2x2':t,'breadth':b}


def draw_spot_sample(plan=None):
    """BRUTE_PLAN_010 samples.gx2_spot: one random.Random(20261028), families in order act3 then sens3, 3 of the 72
    (seed, mask) cases each, listed ascending."""
    plan=plan or load(PLAN);rng=random.Random(SPOT_RNG);out={}
    for f in SPOT_FAMILIES:
        lo,hi=plan['heldout_ranges_breadth'][f]
        cases=[(s,m) for s in range(lo,hi+1) for m in plan['mask_rates']]
        out[f]=sorted(rng.sample(cases,SPOT_PER_FAMILY))
    return out


NEGATIVE=(('smoke',901,None),('smoke',3010001,None),('smoke',2180001,None),('2x2',3190001,None),('breadth',3010001,None),
          ('2x2',2010001,None),('2x2',3010025,'cycle3'),('2x2',3080049,None),('breadth',3110025,'big6'),('breadth',3150001,None))


def main(argv=()):
    plan=load(PLAN);new=ranges_010(plan);prior=prior_ranges()
    report={'v080_ranges':new,'prior_range_count':len(prior),'pairwise_overlaps':[],'prior_overlaps':[]}
    ks=list(new)
    for i,a in enumerate(ks):
        for b in ks[i+1:]:
            if _overlap(new[a],new[b]):report['pairwise_overlaps'].append([a,b])
    for a,r in new.items():
        for b,q in prior.items():
            if _overlap(r,q):report['prior_overlaps'].append([a,b,list(q)])
    sub=[];G=g11_mandatory(plan)
    for blk in ('2x2','breadth'):
        for f,seeds in G[blk].items():
            try:check_run_seeds(blk,seeds,plan,family=f)
            except VerificationError:sub.append(['g11',blk,f])
    spot=draw_spot_sample(plan)
    for f,cases in spot.items():
        try:check_run_seeds('breadth',[s for s,_ in cases],plan,family=f)
        except VerificationError:sub.append(['spot',f])
    report['subset_violations']=sub
    report['g11_mandatory_cases']={'2x2':sum(len(v) for v in G['2x2'].values())*len(plan['mask_rates']),
                                   'breadth':sum(len(v) for v in G['breadth'].values())*len(plan['mask_rates'])}
    neg=[]
    for blk,seed,fam in NEGATIVE:
        try:check_run_seeds(blk,[seed],plan,family=fam);neg.append([blk,seed,'ACCEPTED'])
        except VerificationError:neg.append([blk,seed,'refused'])
    report['negative_controls']=neg
    check_run_seeds('smoke',list(range(3190001,3190031))+list(range(2190001,2190031)),plan)
    check_run_seeds('2x2',[3010001,3080048],plan);check_run_seeds('breadth',[3140024],plan)
    ok=(not report['pairwise_overlaps'] and not report['prior_overlaps'] and not sub and all(x[2]=='refused' for x in neg)
        and report['g11_mandatory_cases']=={'2x2':216,'breadth':72})
    report['PASS']=ok
    if '--draw' in argv and ok:
        write_new(SPOT,{'schema':'brute.spot-sample.v1','study':plan['study'],'rule':plan['samples']['gx2_spot'],
                        'rng':SPOT_RNG,'arm':'B5','max_steps':24,'cases':{f:[list(c) for c in v] for f,v in spot.items()}})
        report['spot_sample_written']=str(SPOT.relative_to(ROOT))
    report['spot_sample']={f:[list(c) for c in v] for f,v in spot.items()}
    print(json.dumps(report,indent=1,default=list))
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
