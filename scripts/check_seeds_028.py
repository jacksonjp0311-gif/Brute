"""Seed assertion for study-028 (BRUTE_PLAN_028 heldout_ranges; smoke 9490001-9490030 declared here because plan 028
lists none). Run and ledgered (seedcheck_028) BEFORE any v0.25.0 run code touches a target seed. New file (copy of
check_seeds_027 with 028 ranges; main cases are eps 0 only per plan 028).

Asserts (exit 0 iff all hold):
  1. the 028 ranges (4 targets + smoke) are pairwise disjoint;
  2. disjoint from every [lo, hi] integer pair in experiments/PLAN.json and every experiments/BRUTE_PLAN_0*.json except
     BRUTE_PLAN_028 (parsed, not hard-coded) plus 901-903, 1591001-1591384, 9000001-9000002, 9190001-9190030 (025 smoke),
     9290001-9290030 (026 smoke), 9299001 (026 timing) and 9390001-9390030 (027 smoke);
  3. check_run_seeds(block, seeds) refuses any seed outside its declared block range (negative controls);
  4. 42 target seeds -> 42 main cases (eps 0) + 9 stress cases (first 3 seeds of scale8/12/16, eps 0.05) = 51.
Pre-freeze timing uses smoke seeds only (reported, never a gate input).
  PYTHONPATH=. python scripts/check_seeds_028.py [--write results/diag-028/SEEDCHECK_028.json]
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
PLAN=ROOT/'experiments/BRUTE_PLAN_028.json'
EXTRA_PRIOR={'smoke_901_903':(901,903),'D78_block':(1591001,1591384),'prefreeze_timing_012':(9000001,9000002),'smoke_025':(9190001,9190030),'smoke_026':(9290001,9290030),'timing_026':(9299001,9299001),'smoke_027':(9390001,9390030)}
SMOKE=(9490001,9490030)
FAMILIES=('scale8','scale12','scale16','control_cycle3');STRESS_FAMILIES=('scale8','scale12','scale16')
EPS_MAIN=(0.0,);EPS_STRESS=0.05;STRESS_PER_FAMILY=3


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_028') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def ranges_028(plan=None):
    plan=plan or load(PLAN);out={'target/'+f:tuple(r) for f,r in plan['heldout_ranges']['targets'].items()};out['smoke']=SMOKE;return out


def check_run_seeds(block,seeds,plan=None,family=None):
    plan=plan or load(PLAN)
    if block=='smoke':
        bad=[s for s in seeds if not (SMOKE[0]<=s<=SMOKE[1])];check(not bad,f'smoke seed outside {SMOKE}: {bad[:5]}');return True
    if block!='target':raise VerificationError('unknown block '+str(block))
    R=plan['heldout_ranges']['targets']
    if family is not None:check(family in R,f'family {family} not in block {block}')
    fams=[family] if family else list(R)
    bad=[s for s in seeds if not any(R[f][0]<=s<=R[f][1] for f in fams)]
    check(not bad,f'{block} seed outside its declared range: {bad[:5]}');return True


NEGATIVE=(('target',9499001,None),('smoke',9499001,None),('target',9490001,None),('smoke',9410001,None),('target',9410013,'scale8'),
          ('target',9420001,'scale8'),('target',9440007,'control_cycle3'),('target',9310001,None),('smoke',9390001,None),('target',9430013,None),
          ('smoke',9490031,None),('target',9409999,None))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_028(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v26','v0250_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
         'pairwise_overlaps':[],'prior_overlaps':[]}
    ks=list(new)
    for i,a in enumerate(ks):
        for b in ks[i+1:]:
            if _overlap(new[a],new[b]):rep['pairwise_overlaps'].append([a,b])
    for a,r in new.items():
        for b,q in prior.items():
            if _overlap(r,q):rep['prior_overlaps'].append([a,b,list(q)])
    neg=[]
    for blk,seed,fam in NEGATIVE:
        try:check_run_seeds(blk,[seed],plan,family=fam);neg.append([blk,seed,'ACCEPTED'])
        except VerificationError:neg.append([blk,seed,'refused'])
    rep['negative_controls']=neg
    check_run_seeds('smoke',list(range(SMOKE[0],SMOKE[1]+1)),plan)
    T=plan['heldout_ranges']['targets'];check(sorted(T)==sorted(FAMILIES),'target families')
    seeds=sum(T[f][1]-T[f][0]+1 for f in FAMILIES)
    rep['target_seeds']=seeds;rep['main_cases']=seeds*len(EPS_MAIN);rep['stress_cases']=STRESS_PER_FAMILY*len(STRESS_FAMILIES)
    rep['total_cases']=rep['main_cases']+rep['stress_cases']
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and all(x[2]=='refused' for x in neg) and seeds==42
        and rep['main_cases']==42 and rep['stress_cases']==9 and rep['total_cases']==51 and 'BRUTE_PLAN_027.json' in rep['prior_files']
        and 'BRUTE_PLAN_028.json' not in rep['prior_files'])
    rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
