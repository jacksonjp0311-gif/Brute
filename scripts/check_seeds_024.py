"""Seed assertion for study-024 (BRUTE_PLAN_024 heldout_ranges; smoke 9090001-9090030 declared in
docs/research/v0.21.0/STITCHED_LEMMA_024.md because plan 024 lists none). Adapted from scripts/check_seeds_023.py (frozen).
Run and ledgered (seedcheck_024) BEFORE any v0.21.0 run, smoke included.

Asserts (exit code 0 iff all hold):
  1. the v0.21.0 ranges (targets per family, smoke 9090001-9090030) are pairwise disjoint;
  2. they are disjoint from every [lo, hi] integer pair in experiments/PLAN.json and every experiments/BRUTE_PLAN_0*.json
     except BRUTE_PLAN_024 (parsed, not hard-coded) plus 901-903, 1591001-1591384 and 9000001-9000002;
  3. check_run_seeds(block, seeds) raises VerificationError for any seed outside its declared block range
     ('target' | 'smoke'; smoke = 9090001-9090030 only);
  4. 120 two-action target seeds -> 360 main cases (eps 0, 0.01, 0.02) and 30 stress cases (eps 0.05; first quarter of each family range).

Smoke layout (v0.21.0 code only): 9090001-9090008 smoke targets (two per family in TRANSFER_FAMILIES order; every eps
level + stress = 32 smoke cases, the rate-math sample); 9090009-9090012 API / per-bit test (one per family);
9090013-9090015 kill drill (cycle3, switch3, unaliased2); 9090016-9090030 spare (debug only).

  PYTHONPATH=. python scripts/check_seeds_024.py [--write results/diag-024/SEEDCHECK_024.json]
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap,TRANSFER_FAMILIES
PLAN=ROOT/'experiments/BRUTE_PLAN_024.json'
EXTRA_PRIOR={'smoke_901_903':(901,903),'D78_block':(1591001,1591384),'prefreeze_timing_012':(9000001,9000002)}
SMOKE=(9090001,9090030)
SMOKE_TARGETS=tuple(range(9090001,9090009));API_TEST=tuple(range(9090009,9090013));KILL_DRILL=tuple(range(9090013,9090016))
EPS_MAIN=(0.0,0.01,0.02);EPS_STRESS=0.05;MAIN_FAMILIES=TRANSFER_FAMILIES


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if p.name!=PLAN.name and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def ranges_024(plan=None):
    plan=plan or load(PLAN);out={}
    for f,(lo,hi) in plan['heldout_ranges']['targets'].items():out['target/'+f]=(lo,hi)
    out['smoke']=SMOKE
    return out


def check_run_seeds(block,seeds,plan=None,family=None):
    """Raise VerificationError unless every seed is inside the declared range of `block`."""
    plan=plan or load(PLAN)
    if block=='smoke':
        lo,hi=SMOKE
        bad=[s for s in seeds if not (lo<=s<=hi)]
        check(not bad,f'smoke seed outside {lo}-{hi}: {bad[:5]}');return True
    if block!='target':raise VerificationError('unknown block '+str(block))
    R=plan['heldout_ranges']['targets']
    if family is not None:check(family in R,f'family {family} not in block {block}')
    fams=[family] if family else list(R)
    bad=[s for s in seeds if not any(R[f][0]<=s<=R[f][1] for f in fams)]
    check(not bad,f'{block} seed outside its declared range: {bad[:5]}');return True


def smoke_family(seed):
    if seed in SMOKE_TARGETS:return TRANSFER_FAMILIES[(seed-9090001)//2]
    if seed in API_TEST:return TRANSFER_FAMILIES[seed-9090009]
    if seed in KILL_DRILL:return TRANSFER_FAMILIES[seed-9090013]
    raise VerificationError(f'no smoke layout for {seed}')


NEGATIVE=(('smoke',901,None),('smoke',8990001,None),('smoke',8790001,None),('smoke',9090031,None),('target',9010025,'cycle3'),
          ('target',9010001,'switch3'),('target',9090001,None),('target',8910001,None),('target',9040049,None),('smoke',8010001,None),('smoke',8590001,None),('smoke',8690001,None),('smoke',8710001,None),
          ('smoke',8890001,None),('smoke',8910001,None),('smoke',8990031,None),('target',8910025,'cycle3'),('target',8710001,None),
          ('target',8810001,None),('target',8940049,None),('target',8910001,'switch3'),('target',8990001,None),('target',8790001,None),
          ('target',9000001,None),('source',8350001,None),('ood5',8360001,None))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_024(plan);prior=prior_ranges()
    report={'schema':'brute.seedcheck.v24','v0210_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
            'pairwise_overlaps':[],'prior_overlaps':[]}
    ks=list(new)
    for i,a in enumerate(ks):
        for b in ks[i+1:]:
            if _overlap(new[a],new[b]):report['pairwise_overlaps'].append([a,b])
    for a,r in new.items():
        for b,q in prior.items():
            if _overlap(r,q):report['prior_overlaps'].append([a,b,list(q)])
    neg=[]
    for blk,seed,fam in NEGATIVE:
        try:check_run_seeds(blk,[seed],plan,family=fam);neg.append([blk,seed,'ACCEPTED'])
        except VerificationError:neg.append([blk,seed,'refused'])
    report['negative_controls']=neg
    check_run_seeds('smoke',list(range(9090001,9090031)),plan)
    check_run_seeds('target',[9010001,9020024,9030001,9040048],plan)
    report['smoke_layout']=[[s,smoke_family(s)] for s in SMOKE_TARGETS+API_TEST+KILL_DRILL]
    T=plan['heldout_ranges']['targets'];seeds=sum(T[f][1]-T[f][0]+1 for f in MAIN_FAMILIES)
    check(sorted(T)==sorted(MAIN_FAMILIES),'target families')
    report['target_seeds']=seeds;report['cases']=seeds*len(EPS_MAIN);report['stress_cases']=sum((T[f][1]-T[f][0]+1)//4 for f in MAIN_FAMILIES)
    ok=(not report['pairwise_overlaps'] and not report['prior_overlaps'] and all(x[2]=='refused' for x in neg)
        and seeds==120 and report['cases']==360 and report['stress_cases']==30 and 'BRUTE_PLAN_023.json' in report['prior_files']
        and 'BRUTE_PLAN_024.json' not in report['prior_files'])
    report['PASS']=ok
    txt=json.dumps(report,indent=1,default=list)
    print(txt)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
