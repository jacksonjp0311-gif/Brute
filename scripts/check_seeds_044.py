"""Seed assertion for study-044 (BRUTE_PLAN_044 heldout_ranges: lowobs12 and control, each an explicit list of consecutive
seeds; smoke range 10990001-10990006 from the plan's smoke_range). Run and ledgered (seedcheck_044) AFTER
build_authorization_044 and BEFORE any v0.41.0 run code touches a target seed. New file (check_seeds_043 logic, frozen,
with the 044 ranges and the 043 ranges as priors; every case eps 0).

The 043 smoke-counter lesson (plan 044 heldout_ranges.note) is written into this file BEFORE the scan:
  rule J: a standalone in-range token is ALLOWED iff it lies only in the smoke range (never a target range) and every
  JSON key path holding it, on every line of the file that contains it, is under a 'cpu_jiffies' object
  (scripts/check_seeds_043b.allowed). Every in-range token is listed either way; any target-range token fails.

Asserts (exit 0 iff all hold):
  1. every 044 list is consecutive and the 044 ranges (2 targets + smoke) are pairwise disjoint;
  2. disjoint from every [lo, hi] pair in experiments/PLAN.json and every experiments/BRUTE_PLAN_0*.json except
     BRUTE_PLAN_044* (parsed), plus all earlier extras, the 043 smoke range and the 043 target ranges;
  3. token scan of every git-tracked file under results/ or experiments/ (BRUTE_PLAN_044* and SEEDCHECK_044* excluded):
     every standalone token in a 044 range is allowed by rule J;
  4. check_run_seeds refuses any seed outside its declared range (negative controls);
  5. 12 + 6 = 18 target seeds -> 18 fresh cases; eps 0 everywhere.
  PYTHONPATH=. python scripts/check_seeds_044.py [--write results/diag-044/SEEDCHECK_044.json]
"""
import gzip,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
from scripts import check_seeds_033 as c33
from scripts import check_seeds_043 as c43
from scripts.check_seeds_043b import paths_of,allowed
PLAN=ROOT/'experiments/BRUTE_PLAN_044.json'
EXTRA_PRIOR={**c43.EXTRA_PRIOR,'smoke_043':c43.SMOKE,**{'plan043/'+k:v for k,v in c43.ranges_043().items()}}
SMOKE=(10990001,10990006)
FAMILY_OF={'lowobs12':'lowobs12','control':'control_cycle3'}
EPS_OF={k:0.0 for k in FAMILY_OF}
COUNTS={'lowobs12':12,'control':6}
TOKEN=re.compile(rb'(?<![0-9.eE\-])(109[0-9]{5})(?![0-9.eE])');ANY=re.compile(rb"109[0-9]{5}")
SCAN_SUFFIX=c33.SCAN_SUFFIX


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_044') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def target_ranges(plan=None):
    plan=plan or load(PLAN);H=plan['heldout_ranges'];return {k:c33._span(H[k],k) for k in FAMILY_OF}


def ranges_044(plan=None):
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


def _lines(p):
    op=gzip.open if p.suffix=='.gz' else open
    with op(p,'rt',errors='replace') as f:
        for i,l in enumerate(f,1):yield i,l


def rule_j(f,tok,ranges):
    in_r=[k for k,(lo,hi) in ranges.items() if lo<=tok<=hi];hits=[]
    for i,l in _lines(ROOT/f):
        if str(tok) in l:
            try:ps=paths_of(l,tok)
            except ValueError:ps=[]
            hits.append({'line':i,'paths':[list(p) for p in ps],'allowed':allowed(ps)})
    return {'file':f,'token':tok,'ranges':in_r,'smoke_only':in_r==['smoke'],'hits':hits,
            'allowed':in_r==['smoke'] and bool(hits) and all(h['allowed'] for h in hits)}


def token_scan(ranges):
    files=subprocess.run(['git','ls-files','results','experiments'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.split()
    files=[f for f in files if f.endswith(SCAN_SUFFIX) and not Path(f).name.startswith('BRUTE_PLAN_044') and 'SEEDCHECK_044' not in f]
    inr=lambda v:any(a<=v<=b for a,b in ranges.values());tok=[];emb=0;scanned=0;block=[]
    for f in files:
        p=ROOT/f
        if not p.exists():continue
        b=gzip.open(p).read() if f.endswith('.gz') else p.read_bytes();scanned+=1
        for m in TOKEN.finditer(b):
            v=int(m.group(1));block.append([f,v])
            if inr(v) and [f,v] not in tok:tok.append([f,v])
        emb+=sum(1 for m in ANY.finditer(b) if inr(int(m.group(0))))
    return {'files_scanned':scanned,'standalone_tokens_in_044_ranges':tok,'occurrences_any_in_044_ranges':emb,
            'standalone_109_block_count':len(block),'rule_j':[rule_j(f,v,ranges) for f,v in tok]}


NEGATIVE=(('target',10999001,None),('smoke',10999001,None),('target',10990001,None),('smoke',10930001,None),
          ('target',10930013,'lowobs12'),('target',10970001,'lowobs12'),('target',10970007,'control'),('target',10930001,'control'),
          ('target',10910001,None),('target',10920001,None),('target',10960001,None),('target',10980001,None),
          ('smoke',10980005,None),('smoke',10990007,None),('target',10929999,None),('target',10940001,None))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_044(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v41','v0410_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
         'pairwise_overlaps':[],'prior_overlaps':[]}
    ks=list(new)
    for i,a in enumerate(ks):
        for b in ks[i+1:]:
            if _overlap(new[a],new[b]):rep['pairwise_overlaps'].append([a,b])
    for a,r in new.items():
        for b,q in prior.items():
            if _overlap(r,q):rep['prior_overlaps'].append([a,b,list(q)])
    rep['token_scan']=ts=token_scan(new)
    rep['rule_j_all_allowed']=all(o['allowed'] for o in ts['rule_j'])
    neg=[]
    for blk,seed,k in NEGATIVE:
        try:check_run_seeds(blk,[seed],plan,key=k);neg.append([blk,seed,k,'ACCEPTED'])
        except VerificationError:neg.append([blk,seed,k,'refused'])
    rep['negative_controls']=neg
    check_run_seeds('smoke',list(range(SMOKE[0],SMOKE[1]+1)),plan);check(plan['smoke_range'].startswith('10990001-10990006'),'plan smoke_range')
    H=plan['heldout_ranges'];rep['cases_by_key']={k:len(H[k]) for k in COUNTS};rep['total_cases']=sum(rep['cases_by_key'].values())
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and rep['rule_j_all_allowed'] and ts['files_scanned']>0
        and all(x[3]=='refused' for x in neg) and rep['cases_by_key']==COUNTS and rep['total_cases']==18==plan['cases']['total_fresh']
        and 'BRUTE_PLAN_043.json' in rep['prior_files'] and 'BRUTE_PLAN_044.json' not in rep['prior_files'])
    rep['eps_by_key']=EPS_OF;rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
