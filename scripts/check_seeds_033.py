"""Seed assertion for study-033 (BRUTE_PLAN_033 heldout_ranges: scale8, scale12, scale16_informational, control and smoke,
each given as an explicit list of consecutive seeds). Run and ledgered (seedcheck_033) BEFORE any v0.30.0 run code touches
a target seed. New file (check_seeds_032 logic with the 033 ranges and list format; all cases eps 0).

Asserts (exit 0 iff all hold):
  1. every 033 list is consecutive and the 033 ranges (4 targets + smoke) are pairwise disjoint;
  2. disjoint from every [lo, hi] integer pair in experiments/PLAN.json and every experiments/BRUTE_PLAN_0*.json except
     BRUTE_PLAN_033* (parsed, not hard-coded) plus the extra ranges of check_seeds_032 and 9890001-9890030 (032 smoke);
  3. token scan: no git-tracked file under results/ or experiments/ (json, jsonl, txt, md, json.gz; BRUTE_PLAN_033* and
     this check's own output excluded) contains a standalone integer token (not preceded or followed by a digit, '.',
     'e' or '-') in any 033 range; digit runs inside longer numbers are counted and reported as embedded, not as seeds;
  4. check_run_seeds(block, seeds) refuses any seed outside its declared block range (negative controls);
  5. 12 + 12 + 6 + 6 = 36 target seeds -> 36 cases at eps 0.
  PYTHONPATH=. python scripts/check_seeds_033.py [--write results/diag-033/SEEDCHECK_033.json]
"""
import gzip,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.brute_common import VerificationError,check,load
from scripts.check_seeds_013 import int_pairs,_overlap
from scripts.check_seeds_032 import EXTRA_PRIOR as EXTRA_032
PLAN=ROOT/'experiments/BRUTE_PLAN_033.json'
EXTRA_PRIOR={**EXTRA_032,'smoke_032':(9890001,9890030)}
SMOKE=(9990001,9990030)
FAMILY_OF={'scale8':'scale8','scale12':'scale12','scale16_informational':'scale16','control':'control_cycle3'}
COUNTS={'scale8':12,'scale12':12,'scale16_informational':6,'control':6}
TOKEN=re.compile(rb'(?<![0-9.eE\-])(99[0-9]{5})(?![0-9.eE])');ANY=re.compile(rb'99[0-9]{5}')
SCAN_SUFFIX=('.json','.jsonl','.txt','.md','.json.gz')


def prior_files():
    return [ROOT/'experiments/PLAN.json']+sorted(p for p in (ROOT/'experiments').glob('BRUTE_PLAN_0*.json')
                                                 if not p.name.startswith('BRUTE_PLAN_033') and 'FREEZE' not in p.name)


def prior_ranges():
    out={}
    for p in prior_files():
        for path,r in int_pairs(load(p)):out[p.name+path]=r
    out.update(EXTRA_PRIOR);return out


def _span(xs,name):
    check(xs==list(range(xs[0],xs[0]+len(xs))),name+' seeds not consecutive');return (xs[0],xs[-1])


def target_ranges(plan=None):
    """{family: (lo, hi)} with the world family names (scale16_informational -> scale16, control -> control_cycle3)."""
    plan=plan or load(PLAN);H=plan['heldout_ranges'];return {FAMILY_OF[k]:_span(H[k],k) for k in FAMILY_OF}


def ranges_033(plan=None):
    plan=plan or load(PLAN);out={'target/'+f:r for f,r in target_ranges(plan).items()}
    out['smoke']=_span(plan['heldout_ranges']['smoke'],'smoke');return out


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
    files=[f for f in files if f.endswith(SCAN_SUFFIX) and not Path(f).name.startswith('BRUTE_PLAN_033') and 'SEEDCHECK_033' not in f]
    inr=lambda v:any(a<=v<=b for a,b in ranges.values());tok=[];emb=0;scanned=0
    for f in files:
        p=ROOT/f
        if not p.exists():continue
        b=gzip.open(p).read() if f.endswith('.gz') else p.read_bytes();scanned+=1
        for m in TOKEN.finditer(b):
            if inr(int(m.group(1))):tok.append([f,int(m.group(1))])
        emb+=sum(1 for m in ANY.finditer(b) if inr(int(m.group(0))))
    return {'files_scanned':scanned,'standalone_tokens_in_033_ranges':tok,'occurrences_any_in_033_ranges':emb,
            'embedded_only':emb-len(tok)}


NEGATIVE=(('target',9999001,None),('smoke',9999001,None),('target',9990001,None),('smoke',9910001,None),('target',9910013,'scale8'),
          ('target',9920001,'scale8'),('target',9940007,'control_cycle3'),('target',9810001,None),('smoke',9890001,None),('target',9930007,None),
          ('smoke',9990031,None),('target',9909999,None),('target',9920013,'scale12'),('target',9930001,'scale12'))


def main(argv=()):
    argv=list(argv);plan=load(PLAN);new=ranges_033(plan);prior=prior_ranges()
    rep={'schema':'brute.seedcheck.v30','v0300_ranges':new,'prior_files':[p.name for p in prior_files()],'prior_range_count':len(prior),
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
    ok=(not rep['pairwise_overlaps'] and not rep['prior_overlaps'] and not rep['token_scan']['standalone_tokens_in_033_ranges']
        and rep['token_scan']['files_scanned']>0 and all(x[2]=='refused' for x in neg) and rep['cases_by_key']==COUNTS
        and rep['total_cases']==36==plan['cases']['total']
        and 'BRUTE_PLAN_032.json' in rep['prior_files'] and 'BRUTE_PLAN_033.json' not in rep['prior_files'])
    rep['PASS']=ok;txt=json.dumps(rep,indent=1,default=list);print(txt)
    if '--write' in argv:
        p=ROOT/argv[argv.index('--write')+1];p.parent.mkdir(parents=True,exist_ok=True)
        with open(p,'x') as fh:fh.write(txt+'\n')
    if not ok:raise VerificationError('seed check failed')
    return 0


if __name__=='__main__':sys.exit(main(sys.argv[1:]))
