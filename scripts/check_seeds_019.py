"""Seed assertion for study-019 (BRUTE_PLAN_019 seed_assertion_plan). Run and ledgered (seedcheck_019) BEFORE any
v0.17.0 run, smoke included.

Asserts (exit code 0 iff all hold):
  1. the v0.17.0 ranges (targets per family, smoke 8590001-8590030) are pairwise disjoint;
  2. they are disjoint from every [lo, hi] integer pair in experiments/PLAN.json and every experiments/BRUTE_PLAN_0*.json
     except BRUTE_PLAN_019 (parsed, not hard-coded) plus 901-903, 1591001-1591384 and 9000001-9000002;
  3. check_run_seeds(block, seeds) raises VerificationError for any seed outside its declared block range
     ('target' | 'smoke'; smoke = 8590001-8590030 or the study-018 smoke 8490001-8490030);
  4. 120 two-action target seeds -> 360 main cases (eps 0, 0.01, 0.02) and 120 stress cases (eps 0.05);
     48 rand4a3 seeds -> 96 alphabet3 cases (eps 0, 0.02).

Smoke layout (v0.17.0 code only): 8590001-8590008 smoke targets (two per family in TRANSFER_FAMILIES order; every
eps level + stress = 32 smoke cases, two per family x eps cell, the rate-math sample); 8590009-8590012 API test (one per
family); 8590013-8590015 kill drill (cycle3, switch3, unaliased2); 8590016-8590019 alphabet3 smoke (rand4a3);
8590020-8590030 spare (debug only).

  PYTHONPATH=. python scripts/check_seeds_019.py [--write results/diag-019/SEEDCHECK_019.json]
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap,TRANSFER_FAMILIES
PLAN=ROOT/'experiments/BRUTE_PLAN_019.json'
EXTRA_PRIOR={'smoke_901_903':(901,903),'D78_block':(1591001,1591384),'prefreeze_timing_012':(9000001,9000002)}
SMOKE_018=(8490001,8490030)
SMOKE_TARGETS=tuple(range(8590001,8590009));API_TEST=tuple(range(8590009,8590013));KILL_DRILL=tuple(range(8590013,8590016));A3_SMOKE=tuple(range(8590016,8590020))
EPS_MAIN=(0.0,0.01,0.02);EPS_STRESS=0.05;EPS_A3=(0.0,0.02);MAIN_FAMILIES=TRANSFER_FAMILIES;A3_FAMILY='rand4a3'


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if p.name!=PLAN.name and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def ranges_019(plan=None):
    plan=plan or load(PLAN);out={}
    for f,(lo,hi) in plan['heldout_ranges']['targets'].items():out['target/'+f]=(lo,hi)
    out['smoke']=tuple(plan['smoke_seeds']['range'])
    return out


def check_run_seeds(block,seeds,plan=None,family=None):
    """Raise VerificationError unless every seed is inside the declared range of `block`."""
    plan=plan or load(PLAN)
    if block=='smoke':
        lo,hi=plan['smoke_seeds']['range']
        bad=[s for s in seeds if not (lo<=s<=hi or SMOKE_018[0]<=s<=SMOKE_018[1])]
        check(not bad,f'smoke seed outside {lo}-{hi} and {SMOKE_018[0]}-{SMOKE_018[1]}: {bad[:5]}');return True
    if block!='target':raise VerificationError('unknown block '+str(block))
    R=plan['heldout_ranges']['targets']
    if family is not None:check(family in R,f'family {family} not in block {block}')
    fams=[family] if family else list(R)
    bad=[s for s in seeds if not any(R[f][0]<=s<=R[f][1] for f in fams)]
    check(not bad,f'{block} seed outside its declared range: {bad[:5]}');return True


def smoke_family(seed):
    if seed in SMOKE_TARGETS:return TRANSFER_FAMILIES[(seed-8590001)//2]
    if seed in API_TEST:return TRANSFER_FAMILIES[seed-8590009]
    if seed in KILL_DRILL:return TRANSFER_FAMILIES[seed-8590013]
    if seed in A3_SMOKE:return A3_FAMILY
    raise VerificationError(f'no smoke layout for {seed}')


NEGATIVE=(('smoke',901,None),('smoke',8010001,None),('smoke',8290001,None),('smoke',8390001,None),('smoke',8410001,None),
          ('smoke',8550001,None),('target',8510025,'cycle3'),('target',8410001,None),('target',8490001,None),
          ('target',8540049,None),('target',8550049,None),('target',8550001,'cycle3'),('target',8510001,'rand4a3'),
          ('target',8590001,None),('target',9000001,None),('source',8350001,None),('ood5',8360001,None))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_019(plan);prior=prior_ranges()
    report={'schema':'brute.seedcheck.v19','v0170_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
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
    check_run_seeds('smoke',list(range(8590001,8590031))+list(range(8490001,8490031)),plan)
    check_run_seeds('target',[8510001,8520024,8530001,8540048,8550001,8550048],plan)
    report['smoke_layout']=[[s,smoke_family(s)] for s in SMOKE_TARGETS+API_TEST+KILL_DRILL+A3_SMOKE]
    T=plan['heldout_ranges']['targets'];seeds=sum(T[f][1]-T[f][0]+1 for f in MAIN_FAMILIES);a3=T[A3_FAMILY][1]-T[A3_FAMILY][0]+1
    check(sorted(T)==sorted(MAIN_FAMILIES+(A3_FAMILY,)),'target families')
    report['target_seeds']=seeds;report['cases']=seeds*len(EPS_MAIN);report['stress_cases']=seeds
    report['alphabet3_seeds']=a3;report['alphabet3_cases']=a3*len(EPS_A3)
    lv=plan['noise_model']['levels']
    eps_ok=(lv['eps0_control'],lv['eps1'],lv['eps2'])==EPS_MAIN and lv['eps5_stress']==EPS_STRESS
    report['eps_levels_match_plan']=eps_ok
    ok=(not report['pairwise_overlaps'] and not report['prior_overlaps'] and all(x[2]=='refused' for x in neg)
        and seeds==120 and report['cases']==360 and eps_ok and a3==48 and report['alphabet3_cases']==96
        and 'BRUTE_PLAN_018.json' in report['prior_files'] and 'BRUTE_PLAN_019.json' not in report['prior_files'])
    report['PASS']=ok
    txt=json.dumps(report,indent=1,default=list)
    print(txt)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
