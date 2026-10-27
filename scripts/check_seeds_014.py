"""Seed assertion for study-014 (BRUTE_PLAN_014 seed_assertion_plan). Run and ledgered (seedcheck_014) BEFORE any
v0.12.0 run, smoke included.

Asserts (exit code 0 iff all hold):
  1. the v0.12.0 ranges (transfer targets per family, sources, smoke 7190001-7190030) are pairwise disjoint;
  2. they are disjoint from every [lo, hi] integer pair in experiments/PLAN.json and every experiments/BRUTE_PLAN_0*.json
     except BRUTE_PLAN_014 (parsed, not hard-coded) plus 901-903, 1591001-1591384 and 9000001-9000002;
  3. check_run_seeds(block, seeds) raises VerificationError for any seed outside its declared block range
     ('target' | 'source' | 'smoke'; smoke = 7190001-7190030 or the study-013 smoke 6190001-6190030);
  4. the positive / negative source maps cover 96 source worlds and the stress map gives 72 wrong-family libraries per
     target family, none of the target family.

  PYTHONPATH=. python scripts/check_seeds_014.py [--write results/diag-014/SEEDCHECK_014.json]
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap,TRANSFER_FAMILIES,ROTATE
PLAN=ROOT/'experiments/BRUTE_PLAN_014.json'
EXTRA_PRIOR={'smoke_901_903':(901,903),'D78_block':(1591001,1591384),'prefreeze_timing_012':(9000001,9000002)}
SMOKE_013=(6190001,6190030)
SMOKE_TRANSFER=tuple(range(7190001,7190009));API_TEST=tuple(range(7190009,7190013));KILL_DRILL=tuple(range(7190013,7190016))


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if p.name!=PLAN.name and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def ranges_014(plan=None):
    plan=plan or load(PLAN);out={}
    for f,(lo,hi) in plan['heldout_ranges_transfer']['targets'].items():out['target/'+f]=(lo,hi)
    out['source']=tuple(plan['heldout_ranges_transfer']['sources'])
    out['smoke']=tuple(plan['smoke_seeds']['range'])
    return out


def check_run_seeds(block,seeds,plan=None,family=None):
    """Raise VerificationError unless every seed is inside the declared range of `block`."""
    plan=plan or load(PLAN)
    if block=='smoke':
        lo,hi=plan['smoke_seeds']['range']
        bad=[s for s in seeds if not (lo<=s<=hi or SMOKE_013[0]<=s<=SMOKE_013[1])]
        check(not bad,f'smoke seed outside {lo}-{hi} and {SMOKE_013[0]}-{SMOKE_013[1]}: {bad[:5]}');return True
    if block=='target':R=plan['heldout_ranges_transfer']['targets']
    elif block=='source':R={'source':plan['heldout_ranges_transfer']['sources']}
    else:raise VerificationError('unknown block '+str(block))
    if family is not None:check(family in R,f'family {family} not in block {block}')
    fams=[family] if family else list(R)
    bad=[s for s in seeds if not any(R[f][0]<=s<=R[f][1] for f in fams)]
    check(not bad,f'{block} seed outside its declared range: {bad[:5]}');return True


def source_seed(target_family,offset,plan=None,negative=False):
    """transfer_definition.pairs: (library family, source seed) for target (family, 1-based offset)."""
    plan=plan or load(PLAN);f=ROTATE[target_family] if negative else target_family
    s=plan['heldout_ranges_transfer']['sources'][0]-1+24*TRANSFER_FAMILIES.index(f)+offset
    check_run_seeds('source',[s],plan);return f,s


def stress_sources(target_family,plan=None):
    """transfer_definition.stress_block: every wrong-family library (3 families x 24 offsets)."""
    plan=plan or load(PLAN);lo=plan['heldout_ranges_transfer']['sources'][0]
    out=[(f,lo-1+24*TRANSFER_FAMILIES.index(f)+o) for f in TRANSFER_FAMILIES if f!=target_family for o in range(1,25)]
    check_run_seeds('source',[s for _,s in out],plan);return out


def smoke_family(seed):
    """smoke layout: 7190001-7190008 two per family in order; 7190009-7190012 one per family; 7190013-7190015 drill."""
    if seed in SMOKE_TRANSFER:return TRANSFER_FAMILIES[(seed-7190001)//2]
    if seed in API_TEST:return TRANSFER_FAMILIES[seed-7190009]
    if seed in KILL_DRILL:return TRANSFER_FAMILIES[seed-7190013]
    raise VerificationError(f'no smoke layout for {seed}')


def smoke_source(seed,negative=False):
    """smoke layout: (library family, source seed) for a smoke target."""
    f=smoke_family(seed);f=ROTATE[f] if negative else f
    if seed in SMOKE_TRANSFER:s=seed+20
    elif seed in API_TEST:s=7190021+(seed-7190009)
    else:s=7190025+(seed-7190013)
    check_run_seeds('smoke',[s]);return f,s


def smoke_stress_sources(seed):
    tf=smoke_family(seed)
    return [(f,s) for f in TRANSFER_FAMILIES if f!=tf for s in range(7190021,7190029)]


NEGATIVE=(('smoke',901,None),('smoke',7010001,None),('smoke',5190001,None),('target',7110025,'cycle3'),
          ('target',7150001,None),('target',6110001,None),('source',7150097,None),('source',7110001,None),
          ('source',6150001,None),('target',9000001,None),('target',7120001,'cycle3'))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_014(plan);prior=prior_ranges()
    report={'schema':'brute.seedcheck.v14','v0120_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
            'pairwise_overlaps':[],'prior_overlaps':[]}
    ks=list(new)
    for i,a in enumerate(ks):
        for b in ks[i+1:]:
            if _overlap(new[a],new[b]):report['pairwise_overlaps'].append([a,b])
    for a,r in new.items():
        for b,q in prior.items():
            if _overlap(r,q):report['prior_overlaps'].append([a,b,list(q)])
    srcs=set()
    for f in TRANSFER_FAMILIES:
        for o in range(1,25):
            for neg in (False,True):srcs.add(source_seed(f,o,plan,neg))
    report['source_worlds']=len(srcs)
    st={f:stress_sources(f,plan) for f in TRANSFER_FAMILIES}
    report['stress_libraries_per_family']={f:len(v) for f,v in st.items()}
    stress_ok=all(len(v)==72 and len(set(v))==72 and all(g!=f for g,_ in v) for f,v in st.items())
    neg=[]
    for blk,seed,fam in NEGATIVE:
        try:check_run_seeds(blk,[seed],plan,family=fam);neg.append([blk,seed,'ACCEPTED'])
        except VerificationError:neg.append([blk,seed,'refused'])
    report['negative_controls']=neg
    check_run_seeds('smoke',list(range(7190001,7190031))+list(range(6190001,6190031)),plan)
    check_run_seeds('target',[7110001,7140024],plan);check_run_seeds('source',[7150001,7150096],plan)
    sm=[[s,smoke_family(s),smoke_source(s),smoke_source(s,True)] for s in SMOKE_TRANSFER+API_TEST+KILL_DRILL]
    report['smoke_layout']=sm
    report['cases']=sum(hi-lo+1 for lo,hi in plan['heldout_ranges_transfer']['targets'].values())*len(plan['mask_rates'])
    ok=(not report['pairwise_overlaps'] and not report['prior_overlaps'] and all(x[2]=='refused' for x in neg) and stress_ok
        and report['source_worlds']==96 and report['cases']==288 and 'BRUTE_PLAN_013.json' in report['prior_files']
        and 'BRUTE_PLAN_014.json' not in report['prior_files'])
    report['PASS']=ok
    txt=json.dumps(report,indent=1,default=list)
    print(txt)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1]
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
