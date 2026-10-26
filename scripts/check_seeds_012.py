"""Seed assertion for study-012 (BRUTE_PLAN_012 seed_assertion_plan, samples). Run and ledgered (seedcheck_012) BEFORE
any v0.10.0 run, smoke included.

Asserts (exit code 0 iff all hold):
  1. the v0.10.0 ranges (2x2, big78, transfer targets, transfer sources, smoke 5190001-5190030) are pairwise
     disjoint; the G11 mandatory sample, the G11 optional fixed list and the --long sample are subsets of the 2x2
     block and pairwise disjoint (mandatory vs optional);
  2. they are disjoint from every [lo, hi] integer pair in experiments/PLAN.json and every
     experiments/BRUTE_PLAN_0*.json except BRUTE_PLAN_012 (parsed, not hard-coded) plus 901-903, 1591001-1591384 and
     the pre-freeze timing seeds 9000001-9000002;
  3. check_run_seeds(block, seeds) raises VerificationError for any seed outside its declared block range
     ('2x2' | 'big78' | 'target' | 'source' | 'smoke'; smoke = 5190001-5190030 or the study-011 smoke 4190001-4190030).

  PYTHONPATH=. python scripts/check_seeds_012.py
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
PLAN=ROOT/'experiments/BRUTE_PLAN_012.json'
EXTRA_PRIOR={'smoke_901_903':(901,903),'D78_block':(1591001,1591384),'prefreeze_timing_012':(9000001,9000002)}
SMOKE_011=(4190001,4190030)
G11_2X2_SEEDS=8;G11_DRIFT_SEEDS=16;OPT_OTHER=(9,10);OPT_DRIFT=(17,20);LONG_DRIFT_SEEDS=4;LONG_OTHER_SEEDS=1
TRANSFER_FAMILIES=('cycle3','switch3','unaliased2','ood4')
ROTATE={'cycle3':'switch3','switch3':'cycle3','unaliased2':'ood4','ood4':'unaliased2'}


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


def ranges_012(plan=None):
    plan=plan or load(PLAN);out={}
    for f,(lo,hi) in plan['heldout_ranges_2x2'].items():out['2x2/'+f]=(lo,hi)
    out['big78/moore78']=tuple(plan['heldout_ranges_big78']['moore78'])
    for f,(lo,hi) in plan['heldout_ranges_transfer']['targets'].items():out['target/'+f]=(lo,hi)
    out['source']=tuple(plan['heldout_ranges_transfer']['sources'])
    out['smoke']=tuple(plan['smoke_seeds']['range'])
    return out


def _overlap(a,b):return a[0]<=b[1] and b[0]<=a[1]


def check_run_seeds(block,seeds,plan=None,family=None):
    """Raise VerificationError unless every seed is inside the declared range of `block`."""
    plan=plan or load(PLAN)
    if block=='smoke':
        lo,hi=plan['smoke_seeds']['range']
        bad=[s for s in seeds if not (lo<=s<=hi or SMOKE_011[0]<=s<=SMOKE_011[1])]
        check(not bad,f'smoke seed outside {lo}-{hi} and {SMOKE_011[0]}-{SMOKE_011[1]}: {bad[:5]}');return True
    if block=='2x2':R=plan['heldout_ranges_2x2']
    elif block=='big78':R=plan['heldout_ranges_big78']
    elif block=='target':R=plan['heldout_ranges_transfer']['targets']
    elif block=='source':R={'source':plan['heldout_ranges_transfer']['sources']}
    else:raise VerificationError('unknown block '+str(block))
    if family is not None:check(family in R,f'family {family} not in block {block}')
    fams=[family] if family else list(R)
    bad=[s for s in seeds if not any(R[f][0]<=s<=R[f][1] for f in fams)]
    check(not bad,f'{block} seed outside its declared range: {bad[:5]}');return True


def g11_mandatory(plan=None):
    plan=plan or load(PLAN)
    return {f:list(range(lo,lo+(G11_DRIFT_SEEDS if f=='drift4' else G11_2X2_SEEDS))) for f,(lo,hi) in plan['heldout_ranges_2x2'].items()}


def g11_optional(plan=None):
    """samples.g11_optional_fixed: offsets 9..10 (non-drift), drift4 17..20 (1-based offsets; all masks)."""
    plan=plan or load(PLAN);out={}
    for f,(lo,hi) in plan['heldout_ranges_2x2'].items():
        a,b=OPT_DRIFT if f=='drift4' else OPT_OTHER;out[f]=list(range(lo+a-1,lo+b))
    return out


def long_sample(plan=None):
    plan=plan or load(PLAN)
    return {f:list(range(lo,lo+(LONG_DRIFT_SEEDS if f=='drift4' else LONG_OTHER_SEEDS))) for f,(lo,hi) in plan['heldout_ranges_2x2'].items()}


def source_seed(target_family,offset,plan=None,negative=False):
    """transfer_definition.pairs: source seed for target (family, 1-based offset); negative = rotated family."""
    plan=plan or load(PLAN);f=ROTATE[target_family] if negative else target_family
    s=plan['heldout_ranges_transfer']['sources'][0]-1+24*TRANSFER_FAMILIES.index(f)+offset
    check_run_seeds('source',[s],plan);return f,s


NEGATIVE=(('smoke',901,None),('smoke',5010001,None),('smoke',3190001,None),('2x2',5190001,None),('2x2',4010001,None),
          ('2x2',5010025,'cycle3'),('2x2',5080097,None),('big78',5090049,None),('big78',5010001,None),('target',5110025,'cycle3'),
          ('target',5150001,None),('source',5150097,None),('source',5110001,None),('2x2',9000001,None))


def main(argv=()):
    plan=load(PLAN);new=ranges_012(plan);prior=prior_ranges()
    report={'v0100_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),'pairwise_overlaps':[],'prior_overlaps':[]}
    ks=list(new)
    for i,a in enumerate(ks):
        for b in ks[i+1:]:
            if _overlap(new[a],new[b]):report['pairwise_overlaps'].append([a,b])
    for a,r in new.items():
        for b,q in prior.items():
            if _overlap(r,q):report['prior_overlaps'].append([a,b,list(q)])
    sub=[];nm=len(plan['mask_rates'])
    for name,S in (('g11',g11_mandatory(plan)),('g11opt',g11_optional(plan)),('long',long_sample(plan))):
        for f,seeds in S.items():
            try:check_run_seeds('2x2',seeds,plan,family=f)
            except VerificationError:sub.append([name,f])
    M=g11_mandatory(plan);O=g11_optional(plan)
    report['mandatory_optional_overlap']=[f for f in M if set(M[f])&set(O[f])]
    report['subset_violations']=sub
    report['g11_mandatory_cases']=sum(len(v) for v in M.values())*nm
    report['g11_optional_cases']=sum(len(v) for v in O.values())*nm
    report['long_verify_cases']=sum(len(v) for v in long_sample(plan).values())*nm
    srcs=set()
    for f in TRANSFER_FAMILIES:
        for o in range(1,25):
            for neg in (False,True):srcs.add(source_seed(f,o,plan,neg))
    report['source_worlds']=len(srcs)
    neg=[]
    for blk,seed,fam in NEGATIVE:
        try:check_run_seeds(blk,[seed],plan,family=fam);neg.append([blk,seed,'ACCEPTED'])
        except VerificationError:neg.append([blk,seed,'refused'])
    report['negative_controls']=neg
    check_run_seeds('smoke',list(range(5190001,5190031))+list(range(4190001,4190031)),plan)
    check_run_seeds('2x2',[5010001,5080096],plan);check_run_seeds('big78',[5090001,5090048],plan)
    check_run_seeds('target',[5110001,5140024],plan);check_run_seeds('source',[5150001,5150096],plan)
    ok=(not report['pairwise_overlaps'] and not report['prior_overlaps'] and not sub and all(x[2]=='refused' for x in neg)
        and not report['mandatory_optional_overlap'] and report['g11_mandatory_cases']==216 and report['g11_optional_cases']==54
        and report['long_verify_cases']==33 and report['source_worlds']==96 and 'BRUTE_PLAN_011.json' in report['prior_files'])
    report['PASS']=ok
    print(json.dumps(report,indent=1,default=list))
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
