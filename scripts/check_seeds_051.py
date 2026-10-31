"""Seed assertion for study-051 (BRUTE_PLAN_051 heldout_ranges: scale20 '11830001-11830012', control '11850001-11850006',
noise12 '11870001-11870012'; smoke range 11890001-11890006 from the plan's smoke_range). Run and ledgered (seedcheck_051) AFTER
build_authorization_051 and BEFORE any v0.48.0 run code touches a target seed. New file: check_seeds_050 logic (its helpers
imported) with the 051 ranges, and the 050 target and smoke ranges added as priors. eps 0 for scale20 and control, 0.05 for
noise12 (plan design.parts.n). Part c replays the part-k control traces and uses no fresh seed.
Plan rule on a hit: the range moves to the next unused odd prefix (1193, 1195), declared in the pre-run deviation.
  PYTHONPATH=. python scripts/check_seeds_051.py [--write results/diag-051/SEEDCHECK_051.json]
"""
import gzip,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
from scripts import check_seeds_045 as c45
from scripts import check_seeds_049 as c49
from scripts import check_seeds_050 as c50
PLAN=ROOT/'experiments/BRUTE_PLAN_051.json'
EXTRA_PRIOR={**c50.EXTRA_PRIOR,'smoke_050':c50.SMOKE,**{'plan050/'+k:v for k,v in c50.ranges_050(load(ROOT/'experiments/BRUTE_PLAN_050.json')).items()}}
SMOKE=(11890001,11890006)
FAMILY_OF={'scale20':'scale20','control':'scale12','noise12':'scale12'};EPS_OF={'scale20':0.0,'control':0.0,'noise12':0.05}
COUNTS={'scale20':12,'control':6,'noise12':12}
TOKEN=c49.TOKEN;ANY=c49.ANY;span=c45.span


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_051') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def target_ranges(plan=None):
    plan=plan or load(PLAN);H=plan['heldout_ranges'];return {k:span(H[k]) for k in FAMILY_OF}


def ranges_051(plan=None):
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
    """Every tracked file, .gz archives included (plan 051 seedcheck rule)."""
    files=subprocess.run(['git','ls-files'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.split()
    files=[f for f in files if not Path(f).name.startswith('BRUTE_PLAN_051') and 'SEEDCHECK_051' not in f and 'check_seeds_051' not in f]
    inr=lambda v:any(a<=v<=b for a,b in ranges.values());tok=[];emb=0;scanned=0;block=0
    for f in files:
        p=ROOT/f
        if not p.is_file():continue
        try:b=gzip.open(p).read() if f.endswith('.gz') else p.read_bytes()
        except OSError:b=p.read_bytes()
        scanned+=1
        for m in TOKEN.finditer(b):
            v=int(m.group(1));block+=1
            if inr(v) and [f,v] not in tok:tok.append([f,v])
        emb+=sum(1 for m in ANY.finditer(b) if inr(int(m.group(0))))
    J=[c45.rule_j(f,v,ranges) for f,v in tok];K=[c45.rule_k(f,v) for f,v in tok]
    return {'files_scanned':scanned,'standalone_tokens_in_051_ranges':tok,'occurrences_any_in_051_ranges':emb,
            'standalone_11_prefix_token_count':block,'rule_j':J,'rule_k':K,'allowed':[j['allowed'] or k['allowed'] for j,k in zip(J,K)]}


NEGATIVE=(('target',11899001,None),('smoke',11899001,None),('target',11890001,None),('smoke',11830001,None),
          ('target',11830013,'scale20'),('target',11850001,'scale20'),('target',11850007,'control'),('target',11830001,'control'),
          ('target',11870013,'noise12'),('target',11830001,'noise12'),('target',11870001,'scale20'),('target',11730001,None),
          ('target',11790001,None),('smoke',11890007,None),('smoke',11889999,None),('target',11829999,None),('target',11810001,None))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_051(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v48','v0480_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
         'rules_declared_before_scan':['J (cpu_jiffies, smoke only)','K (refused negative_controls probe in a SEEDCHECK file)'],
         'pairwise_overlaps':[],'prior_overlaps':[]}
    ks=list(new)
    for i,a in enumerate(ks):
        for b in ks[i+1:]:
            if _overlap(new[a],new[b]):rep['pairwise_overlaps'].append([a,b])
    for a,r in new.items():
        for b,q in prior.items():
            if _overlap(r,q):rep['prior_overlaps'].append([a,b,list(q)])
    rep['token_scan']=ts=token_scan(new);rep['all_tokens_allowed']=all(ts['allowed'])
    neg=[]
    for blk,seed,k in NEGATIVE:
        try:check_run_seeds(blk,[seed],plan,key=k);neg.append([blk,seed,k,'ACCEPTED'])
        except VerificationError:neg.append([blk,seed,k,'refused'])
    rep['negative_controls']=neg
    check_run_seeds('smoke',list(range(SMOKE[0],SMOKE[1]+1)),plan);check(plan['smoke_range'].startswith('11890001-11890006'),'plan smoke_range')
    T=target_ranges(plan);rep['cases_by_key']={k:T[k][1]-T[k][0]+1 for k in COUNTS};rep['total_cases']=sum(rep['cases_by_key'].values())
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and rep['all_tokens_allowed'] and ts['files_scanned']>0
        and all(x[3]=='refused' for x in neg) and rep['cases_by_key']==COUNTS and rep['total_cases']==30
        and 'BRUTE_PLAN_050.json' in rep['prior_files'] and 'BRUTE_PLAN_051.json' not in rep['prior_files'])
    rep['eps_by_key']=EPS_OF;rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt[-900:])
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
