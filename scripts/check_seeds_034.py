"""Seed assertion for study-034 (BRUTE_PLAN_034 heldout_ranges: scale8, scale12, scale16_informational, control and smoke,
each an explicit list of consecutive seeds). Run and ledgered (seedcheck_034) BEFORE any v0.31.0 run code touches a target
seed. New file (check_seeds_033 logic with the 034 ranges; all cases eps 0).

Asserts (exit 0 iff all hold):
  1. every 034 list is consecutive and the 034 ranges (4 targets + smoke) are pairwise disjoint;
  2. disjoint from every [lo, hi] integer pair in experiments/PLAN.json and every experiments/BRUTE_PLAN_0*.json except
     BRUTE_PLAN_034* (parsed), plus the extra ranges of check_seeds_033, the 033 smoke range and the 033 list ranges;
  3. token scan: no git-tracked file under results/ or experiments/ (json, jsonl, txt, md, json.gz; BRUTE_PLAN_034* and
     this check's own output excluded) contains a standalone integer token in any 034 range;
  4. check_run_seeds(block, seeds) refuses any seed outside its declared block range (negative controls);
  5. 12 + 12 + 6 + 6 = 36 target seeds -> 36 cases at eps 0.
  PYTHONPATH=. python scripts/check_seeds_034.py [--write results/diag-034/SEEDCHECK_034.json]
"""
import gzip,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
from scripts import check_seeds_033 as c33
PLAN=ROOT/'experiments/BRUTE_PLAN_034.json'
EXTRA_PRIOR={**c33.EXTRA_PRIOR,'smoke_033':c33.SMOKE,**{'plan033/'+k:v for k,v in c33.ranges_033().items()}}
SMOKE=(10090001,10090030)
FAMILY_OF=c33.FAMILY_OF;COUNTS=c33.COUNTS
TOKEN=re.compile(rb'(?<![0-9.eE\-])(100[0-9]{5})(?![0-9.eE])');ANY=re.compile(rb'100[0-9]{5}')
SCAN_SUFFIX=c33.SCAN_SUFFIX


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_034') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def target_ranges(plan=None):
    plan=plan or load(PLAN);H=plan['heldout_ranges'];return {FAMILY_OF[k]:c33._span(H[k],k) for k in FAMILY_OF}


def ranges_034(plan=None):
    plan=plan or load(PLAN);out={'target/'+f:r for f,r in target_ranges(plan).items()}
    out['smoke']=c33._span(plan['heldout_ranges']['smoke'],'smoke');return out


def check_run_seeds(block,seeds,plan=None,family=None):
    plan=plan or load(PLAN)
    if block=='smoke':
        bad=[s for s in seeds if not (SMOKE[0]<=s<=SMOKE[1])];check(not bad,f'smoke seed outside {SMOKE}: {bad[:5]}');return True
    if block!='target':raise VerificationError('unknown block '+str(block))
    R=target_ranges(plan)
    if family is not None:check(family in R,f'family {family} not in block {block}')
    fams=[family] if family else list(R)
    bad=[s for s in seeds if not any(R[f][0]<=s<=R[f][1] for f in fams)]
    check(not bad,f'{block} seed outside its declared range: {bad[:5]}');return True


def token_scan(ranges):
    files=subprocess.run(['git','ls-files','results','experiments'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.split()
    files=[f for f in files if f.endswith(SCAN_SUFFIX) and not Path(f).name.startswith('BRUTE_PLAN_034') and 'SEEDCHECK_034' not in f]
    inr=lambda v:any(a<=v<=b for a,b in ranges.values());tok=[];emb=0;scanned=0
    for f in files:
        p=ROOT/f
        if not p.exists():continue
        b=gzip.open(p).read() if f.endswith('.gz') else p.read_bytes();scanned+=1
        for m in TOKEN.finditer(b):
            if inr(int(m.group(1))):tok.append([f,int(m.group(1))])
        emb+=sum(1 for m in ANY.finditer(b) if inr(int(m.group(0))))
    return {'files_scanned':scanned,'standalone_tokens_in_034_ranges':tok,'occurrences_any_in_034_ranges':emb,'embedded_only':emb-len(tok)}


NEGATIVE=(('target',10099001,None),('smoke',10099001,None),('target',10090001,None),('smoke',10010001,None),('target',10010013,'scale8'),
          ('target',10020001,'scale8'),('target',10040007,'control_cycle3'),('target',9910001,None),('smoke',9990001,None),('target',10030007,None),
          ('smoke',10090031,None),('target',10009999,None),('target',10020013,'scale12'),('target',10030001,'scale12'))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_034(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v31','v0310_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
         'pairwise_overlaps':[],'prior_overlaps':[]}
    ks=list(new)
    for i,a in enumerate(ks):
        for b in ks[i+1:]:
            if _overlap(new[a],new[b]):rep['pairwise_overlaps'].append([a,b])
    for a,r in new.items():
        for b,q in prior.items():
            if _overlap(r,q):rep['prior_overlaps'].append([a,b,list(q)])
    rep['token_scan']=token_scan(new)
    neg=[]
    for blk,seed,fam in NEGATIVE:
        try:check_run_seeds(blk,[seed],plan,family=fam);neg.append([blk,seed,'ACCEPTED'])
        except VerificationError:neg.append([blk,seed,'refused'])
    rep['negative_controls']=neg
    check_run_seeds('smoke',list(range(SMOKE[0],SMOKE[1]+1)),plan);check(new['smoke']==SMOKE,'plan smoke range')
    H=plan['heldout_ranges'];rep['cases_by_key']={k:len(H[k]) for k in COUNTS};rep['total_cases']=sum(rep['cases_by_key'].values())
    check(plan['cases']['eps']==0,'plan eps')
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and not rep['token_scan']['standalone_tokens_in_034_ranges']
        and rep['token_scan']['files_scanned']>0 and all(x[2]=='refused' for x in neg) and rep['cases_by_key']==COUNTS
        and rep['total_cases']==36==plan['cases']['total']
        and 'BRUTE_PLAN_033.json' in rep['prior_files'] and 'BRUTE_PLAN_034.json' not in rep['prior_files'])
    rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
